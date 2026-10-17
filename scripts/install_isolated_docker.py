#!/usr/bin/env python3
"""Install an official Docker static archive as a dedicated offline test daemon.

Run as root on the authorized test host. No package manager, firewall, routing,
existing service configuration, or user group is modified. Python 3.6+.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile


def run(argv, timeout=90):
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError("Command failed: {}\n{}".format(" ".join(argv), result.stderr[-1500:]))
    return result.stdout.strip()


def write_file(path, text, mode):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(mode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("Run as root on the authorized test host.")
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version) or not re.fullmatch(r"[a-f0-9]{64}", args.sha256):
        raise SystemExit("Use an exact stable version and a lowercase SHA-256 digest.")
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    if digest != args.sha256:
        raise SystemExit("Archive transfer checksum mismatch; refusing installation.")
    root = Path("/opt/attest-docker")
    marker = root / "installation.json"
    unit_path = Path("/etc/systemd/system/attest-docker.service")
    config_path = Path("/etc/attest-docker/daemon.json")
    if root.exists() and not marker.exists():
        raise SystemExit("Refusing to reuse an unowned /opt/attest-docker directory.")
    if not marker.exists():
        for path in [unit_path, config_path, Path("/usr/local/bin/attest-docker")]:
            if path.exists() or path.is_symlink():
                raise SystemExit("Refusing to overwrite existing path: " + str(path))
    else:
        previous = json.loads(marker.read_text())
        if previous.get("archive_sha256") != digest or previous.get("version") != args.version:
            raise SystemExit("Existing dedicated installation has different metadata.")
        active = subprocess.run(["systemctl", "is-active", "--quiet", "attest-docker"])
        if active.returncode == 0:
            raise SystemExit("The dedicated daemon is already running. Use the smoke runner; stop only this daemon before reviewed maintenance.")
    version_dir = root / args.version
    version_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(str(args.archive), "r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if not parts or parts[0] != "docker" or ".." in parts or member.name.startswith("/"):
                raise SystemExit("Unexpected archive path; refusing extraction.")
            if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
                raise SystemExit("Unexpected archive entry type; refusing extraction.")
        archive.extractall(str(version_dir))
    for path in [version_dir] + list(version_dir.rglob("*")):
        os.chown(str(path), 0, 0)
        path.chmod(0o755)
    binaries = version_dir / "docker"
    for name in ["docker", "dockerd", "containerd", "runc", "containerd-shim-runc-v2"]:
        if not (binaries / name).is_file():
            raise SystemExit("Required Docker component is missing: " + name)
    current = root / "current"
    if current.is_symlink():
        current.unlink()
    elif current.exists():
        raise SystemExit("Refusing to replace a non-symlink current path.")
    current.symlink_to(binaries)
    metadata = {
        "version": args.version,
        "archive_sha256": digest,
        "installed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "https://download.docker.com/linux/static/stable/x86_64/docker-" + args.version + ".tgz",
        "method": "official-static-binaries-dedicated-test-daemon",
    }
    write_file(marker, json.dumps(metadata, indent=2) + "\n", 0o644)
    config = {
        "hosts": ["unix:///run/attest-docker/docker.sock"],
        "group": "root",
        "pidfile": "/run/attest-docker/dockerd.pid",
        "data-root": "/var/lib/attest-docker",
        "exec-root": "/run/attest-docker",
        "bridge": "none",
        "iptables": False,
        "ip6tables": False,
        "ip-forward": False,
        "ip-masq": False,
        "ipv6": False,
        "userland-proxy": False,
        "features": {"containerd-snapshotter": False},
        "storage-driver": "overlay2",
        "no-new-privileges": True,
        "max-concurrent-downloads": 1,
        "max-concurrent-uploads": 1,
        "max-download-attempts": 1,
        "log-driver": "local",
        "log-opts": {"max-size": "5m", "max-file": "2"},
    }
    write_file(config_path, json.dumps(config, indent=2) + "\n", 0o600)
    validation = run([str(binaries / "dockerd"), "--validate", "--config-file=" + str(config_path)])
    unit = """[Unit]
Description=Attest isolated Docker development daemon
After=network.target
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
Type=notify
Environment=PATH=/opt/attest-docker/current:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/attest-docker/current/dockerd --config-file=/etc/attest-docker/daemon.json
ExecReload=/bin/kill -s HUP $MAINPID
RuntimeDirectory=attest-docker
RuntimeDirectoryMode=0700
StateDirectory=attest-docker
StateDirectoryMode=0700
Delegate=yes
KillMode=mixed
TimeoutStartSec=90
TimeoutStopSec=30
Restart=on-failure
RestartSec=5
MemoryAccounting=yes
MemoryMax=256M
CPUAccounting=yes
CPUQuota=25%
TasksMax=512
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
LimitNOFILE=262144
LimitCORE=0

[Install]
WantedBy=multi-user.target
"""
    write_file(unit_path, unit, 0o644)
    wrapper = """#!/bin/sh
# Always select this dedicated daemon; leave the global Docker command untouched.
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
exec /opt/attest-docker/current/docker --host unix:///run/attest-docker/docker.sock "$@"
"""
    write_file("/usr/local/bin/attest-docker", wrapper, 0o755)
    run(["systemctl", "daemon-reload"])
    try:
        run(["systemctl", "start", "attest-docker"], timeout=100)
        docker = "/usr/local/bin/attest-docker"
        version = json.loads(run([docker, "version", "--format", "{{json .}}"]))
        info = json.loads(run([docker, "info", "--format", "{{json .}}"]))
        selected = {key: info.get(key) for key in ["ServerVersion", "Driver", "DockerRootDir", "CgroupDriver",
                    "CgroupVersion", "MemoryLimit", "SwapLimit", "CpuCfsPeriod", "CpuCfsQuota", "PidsLimit",
                    "Containers", "ContainersRunning", "NCPU", "MemTotal", "Warnings"]}
        if selected["DockerRootDir"] != "/var/lib/attest-docker" or selected["Driver"] != "overlay2":
            raise SystemExit("Unexpected Docker storage configuration.")
        if not all(selected.get(key) for key in ["MemoryLimit", "CpuCfsPeriod", "CpuCfsQuota", "PidsLimit"]):
            raise SystemExit("Required resource controllers are unavailable.")
    except (Exception, SystemExit) as error:
        stopped = subprocess.run(["systemctl", "stop", "attest-docker"], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, universal_newlines=True, timeout=40)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"status": "installation-verification-failed",
            "error_type": type(error).__name__, "error": str(error)[:2000],
            "dedicated_service_stop_returncode": stopped.returncode,
            "version": args.version, "archive_sha256": digest}, indent=2) + "\n")
        raise
    metadata.update({"daemon_config": config, "daemon_config_validation": validation,
                     "docker_version": version, "docker_info": selected,
                     "service": "attest-docker.service", "service_enabled": False,
                     "status": "installed-and-started-pending-smoke-test"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"version": args.version, "service": "attest-docker.service", "status": metadata["status"],
                      "report": str(args.output), "daemon_config_validated": True}))


if __name__ == "__main__":
    main()
