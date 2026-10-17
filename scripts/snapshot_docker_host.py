#!/usr/bin/env python3
"""Read-only host and existing-service snapshot. Compatible with Python 3.6+."""

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request


def command(argv, timeout=15):
    try:
        result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=timeout)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()[:300]}
    except Exception as error:
        return {"error_type": type(error).__name__}


def fingerprint(argv):
    result = command(argv)
    text = result.pop("stdout", "")
    text = re.sub(r"\[\d+:\d+\]", "[0:0]", text)
    text = re.sub(r"counter packets \d+ bytes \d+", "counter", text)
    if argv[0] in ["iptables-save", "ip6tables-save"]:
        # iptables-save inserts the current time in comments on every read.
        text = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
        result["normalization"] = "exclude-save-comments-and-packet-counters-v2"
    result["sha256_normalized"] = hashlib.sha256(text.encode()).hexdigest()
    return result


def http_status(url, host=None):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, file_pointer, code, message, headers, new_url):
            return None

    request = urllib.request.Request(url, headers={"Host": host} if host else {})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=10) as response:
            return {"status": response.status}
    except urllib.error.HTTPError as error:
        return {"status": error.code}
    except Exception as error:
        return {"error_type": type(error).__name__}


def main():
    services = ["codex-api", "codex-api-egress", "postgresql-16", "nginx", "firewalld"]
    snapshot = {
        "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host_role": "Aliyun Beijing development candidate",
        "cpu_count": os.cpu_count(),
        "load_average": os.getloadavg(),
        "memory_kib": {},
        "services": {},
        "network": {},
        "filesystem_state": {},
    }
    with open("/proc/meminfo") as source:
        for line in source:
            key, value = line.split(":", 1)
            if key in ["MemTotal", "MemAvailable", "SwapTotal", "SwapFree"]:
                snapshot["memory_kib"][key] = int(value.strip().split()[0])
    disk = shutil.disk_usage("/")
    snapshot["root_disk_bytes"] = {"total": disk.total, "used": disk.used, "free": disk.free}
    for service in services:
        result = command(["systemctl", "show", service, "-p", "MainPID", "-p", "ActiveState",
                          "-p", "SubState", "-p", "NRestarts", "-p", "MemoryCurrent"])
        snapshot["services"][service] = dict(line.split("=", 1) for line in result.get("stdout", "").splitlines() if "=" in line)
    snapshot["active_service_units"] = [line.split()[0] for line in command([
        "systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--plain"
    ]).get("stdout", "").splitlines() if line.strip()]
    snapshot["network"]["ipv4_routes"] = command(["ip", "-4", "route", "show"])
    snapshot["network"]["ipv6_routes"] = command(["ip", "-6", "route", "show"])
    snapshot["network"]["links"] = command(["ip", "-o", "link", "show"])
    listeners = command(["ss", "-H", "-lnt"])
    snapshot["network"]["listening_tcp"] = sorted(line.split()[3] for line in listeners.get("stdout", "").splitlines() if len(line.split()) >= 5)
    snapshot["network"]["listening_tcp_command"] = {key: value for key, value in listeners.items() if key != "stdout"}
    for name, argv in [
        ("iptables", ["iptables-save"]),
        ("ip6tables", ["ip6tables-save"]),
        ("nftables", ["nft", "-s", "list", "ruleset"]),
        ("firewalld_zones", ["firewall-cmd", "--get-active-zones"]),
    ]:
        snapshot["network"][name] = fingerprint(argv)
    for name in ["net.ipv4.ip_forward", "net.ipv6.conf.all.forwarding",
                 "net.bridge.bridge-nf-call-iptables", "net.bridge.bridge-nf-call-ip6tables"]:
        snapshot["network"][name] = command(["sysctl", "-n", name])
    for path in ["/etc/docker", "/var/lib/docker", "/var/lib/containerd", "/opt/attest-docker",
                 "/usr/local/bin/docker", "/usr/local/bin/attest-docker"]:
        snapshot["filesystem_state"][path] = os.path.exists(path)
    snapshot["health"] = {
        "codex_local": http_status("http://127.0.0.1:34101/health"),
        "nginx_local": http_status("http://127.0.0.1/", "www.hackthon.site"),
        "engram_local": http_status("http://127.0.0.1:8788/api/health"),
        "postgres_ready": command(["/usr/pgsql-16/bin/pg_isready", "-h", "127.0.0.1", "-p", "5432"]),
    }
    print(json.dumps(snapshot, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
