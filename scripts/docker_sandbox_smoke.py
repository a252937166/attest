#!/usr/bin/env python3
"""Run one bounded, offline Docker smoke container and verify its removal.

Requires Python 3.6+ on the host and an already loaded image containing python3.
This program never pulls an image or forwards host environment variables into
the container. It reports observations, not host service or model quality claims.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import uuid


MEMORY_BYTES = 256 * 1024 * 1024
NANO_CPUS = 500000000
PIDS_LIMIT = 64
EXECUTION_TIMEOUT = 60
LABEL_KEY = "ai.attest.smoke.run-id"

# Only these inspect fields are serialized. In particular, Config.Env and raw
# image/container inspect responses are never copied into the report.
HOST_CONFIG_FIELDS = (
    "AutoRemove", "Binds", "CapAdd", "CapDrop", "Cgroup", "CgroupParent",
    "CgroupnsMode", "ConsoleSize", "ContainerIDFile", "CpuCount", "CpuPercent",
    "CpuPeriod", "CpuQuota", "CpuRealtimePeriod", "CpuRealtimeRuntime",
    "CpuShares", "CpusetCpus", "CpusetMems", "DeviceCgroupRules", "DeviceRequests",
    "Devices", "Dns", "DnsOptions", "DnsSearch", "ExtraHosts", "GroupAdd",
    "IOMaximumBandwidth", "IOMaximumIOps", "IpcMode", "Isolation", "Links",
    "LogConfig", "MaskedPaths", "Memory", "MemoryReservation", "MemorySwap",
    "MemorySwappiness", "Mounts", "NanoCpus", "NetworkMode", "OomKillDisable",
    "OomScoreAdj", "PidMode", "PidsLimit", "PortBindings", "Privileged",
    "PublishAllPorts", "ReadonlyPaths", "ReadonlyRootfs", "RestartPolicy",
    "Runtime", "SecurityOpt", "ShmSize", "StorageOpt", "Tmpfs", "UTSMode",
    "Ulimits", "UsernsMode", "VolumeDriver", "VolumesFrom",
)

CONTAINER_PROGRAM = r'''
import json
import os
import re
import sys
import time
import unittest


def read_text(filename):
    try:
        with open(filename, "r") as source:
            return source.read().strip()
    except (IOError, OSError):
        return None


def unescape_mount(value):
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)


def mount_records():
    records = []
    for line in (read_text("/proc/self/mountinfo") or "").splitlines():
        fields = line.split()
        if "-" not in fields:
            continue
        split = fields.index("-")
        if split + 3 >= len(fields):
            continue
        records.append({
            "root": unescape_mount(fields[3]),
            "mountpoint": unescape_mount(fields[4]),
            "options": fields[5].split(","),
            "fs_type": fields[split + 1],
            "super_options": fields[split + 3].split(","),
        })
    return records


def cgroup_memberships():
    groups = {}
    for line in (read_text("/proc/self/cgroup") or "").splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        controllers = parts[1].split(",") if parts[1] else ["v2"]
        for controller in controllers:
            groups[controller] = parts[2]
    return groups


def read_cgroup_file(records, groups, controller, filename, version):
    candidates = []
    for record in records:
        if record["fs_type"] != ("cgroup2" if version == 2 else "cgroup"):
            continue
        if version == 1 and controller not in record["super_options"]:
            continue
        member = groups.get("v2" if version == 2 else controller)
        root = record["root"].rstrip("/") or "/"
        relative = None
        if member == "/" or member == root:
            relative = ""
        elif member is not None and root == "/":
            relative = member.lstrip("/")
        elif member is not None and member.startswith(root + "/"):
            relative = member[len(root) + 1:]
        if relative is not None and ".." not in relative.split("/"):
            candidates.append(os.path.join(record["mountpoint"], relative, filename))
        candidates.append(os.path.join(record["mountpoint"], filename))
    if version == 2:
        candidates.append(os.path.join("/sys/fs/cgroup", filename))
    else:
        for directory in (controller, "cpu,cpuacct", "cpuacct,cpu"):
            candidates.append(os.path.join("/sys/fs/cgroup", directory, filename))
    for filename in dict.fromkeys(candidates):
        value = read_text(filename)
        if value is not None:
            return value, filename
    return None, None


def integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


records = mount_records()
groups = cgroup_memberships()
memory_raw, memory_path = read_cgroup_file(records, groups, "memory", "memory.max", 2)
version = 2 if memory_raw is not None else 1
if version == 1:
    memory_raw, memory_path = read_cgroup_file(records, groups, "memory", "memory.limit_in_bytes", 1)
    quota_raw, quota_path = read_cgroup_file(records, groups, "cpu", "cpu.cfs_quota_us", 1)
    period_raw, period_path = read_cgroup_file(records, groups, "cpu", "cpu.cfs_period_us", 1)
    swap_raw, swap_path = read_cgroup_file(records, groups, "memory", "memory.memsw.limit_in_bytes", 1)
    pids_raw, pids_path = read_cgroup_file(records, groups, "pids", "pids.max", 1)
else:
    cpu_raw, quota_path = read_cgroup_file(records, groups, "cpu", "cpu.max", 2)
    cpu_parts = (cpu_raw or "").split()
    quota_raw = cpu_parts[0] if len(cpu_parts) == 2 else None
    period_raw = cpu_parts[1] if len(cpu_parts) == 2 else None
    period_path = quota_path
    swap_raw, swap_path = read_cgroup_file(records, groups, "memory", "memory.swap.max", 2)
    pids_raw, pids_path = read_cgroup_file(records, groups, "pids", "pids.max", 2)

try:
    interfaces = sorted(os.listdir("/sys/class/net"))
except OSError:
    interfaces = None
status_fields = {}
for line in (read_text("/proc/self/status") or "").splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        status_fields[key] = value.strip()
root_options = next((row["options"] for row in records if row["mountpoint"] == "/"), [])
tmp_options = next((row["options"] for row in records if row["mountpoint"] == "/tmp"), [])
quota = integer(quota_raw)
period = integer(period_raw)
observations = {
    "uid": os.getuid(),
    "effective_uid": os.geteuid(),
    "interfaces": interfaces,
    "cgroup_version": version,
    "memory_limit_bytes": integer(memory_raw),
    "memory_limit_raw": memory_raw,
    "cpu_quota_us": quota,
    "cpu_period_us": period,
    "swap_limit_bytes": integer(swap_raw),
    "swap_limit_kind": "additional_swap" if version == 2 else "memory_plus_swap",
    "pids_limit": integer(pids_raw),
    "limit_files": {
        "memory": memory_path, "cpu_quota": quota_path,
        "cpu_period": period_path, "swap": swap_path, "pids": pids_path,
    },
    "root_mount_options": root_options,
    "tmp_mount_options": tmp_options,
    "no_new_privileges": integer(status_fields.get("NoNewPrivs")),
    "effective_capabilities_hex": status_fields.get("CapEff"),
}
checks = {
    "uid_is_65534": observations["uid"] == 65534 and observations["effective_uid"] == 65534,
    "only_loopback_interface": interfaces == ["lo"],
    "memory_limit_is_256_mib": observations["memory_limit_bytes"] == EXPECTED_MEMORY,
    "cpu_limit_is_half_cpu": quota is not None and period is not None and quota > 0 and period > 0 and quota * 2 == period,
    "pids_limit_is_64": observations["pids_limit"] == EXPECTED_PIDS,
    "no_additional_swap": observations["swap_limit_bytes"] == (0 if version == 2 else EXPECTED_MEMORY),
    "root_filesystem_is_read_only": "ro" in root_options,
    "tmp_mount_has_requested_safety_options": all(option in tmp_options for option in ("rw", "noexec", "nosuid", "nodev")),
    "no_new_privileges_enabled": observations["no_new_privileges"] == 1,
    "no_effective_capabilities": status_fields.get("CapEff") is not None and int(status_fields["CapEff"], 16) == 0,
}


def bounded_sum(values):
    if any(type(value) is not int or value < 0 or value > 10 for value in values):
        raise ValueError("Each value must be an integer between zero and ten.")
    return sum(values)


class SandboxSmokeTests(unittest.TestCase):
    def test_empty_sum(self):
        self.assertEqual(bounded_sum([]), 0)

    def test_boundary_sum(self):
        self.assertEqual(bounded_sum([0, 5, 10]), 15)

    def test_outside_boundary_is_rejected(self):
        with self.assertRaises(ValueError):
            bounded_sum([-1])

    def test_runtime_constraints(self):
        for name, passed in sorted(checks.items()):
            with self.subTest(check=name):
                self.assertTrue(passed, name)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(SandboxSmokeTests)
result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
print(json.dumps({
    "type": "attest_smoke_evidence", "run_id": RUN_ID,
    "observations": observations, "checks": checks,
    "unittest": {
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "successful": result.wasSuccessful(),
    },
}, sort_keys=True), flush=True)
time.sleep(3)
sys.exit(0 if result.wasSuccessful() else 1)
'''


class ProbeFailure(Exception):
    pass


def utc_now():
    return datetime.datetime.utcnow().isoformat() + "Z"


def command_metadata(result):
    return {key: result.get(key) for key in (
        "command", "return_code", "timed_out", "elapsed_seconds", "stderr", "error"
    ) if key in result}


def single_inspect_object(result):
    if result.get("return_code") != 0 or result.get("timed_out"):
        return None
    try:
        value = json.loads(result["stdout"])
    except (ValueError, KeyError):
        return None
    return value[0] if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict) else None


def confirmed_missing(result, identifier):
    pattern = r"No such (?:container|object):\s*[\"']?" + re.escape(identifier) + r"[\"']?(?:\s|$)"
    return (result.get("return_code") not in (None, 0)
            and not result.get("timed_out")
            and re.search(pattern, result.get("stderr", ""), re.IGNORECASE) is not None)


def container_snapshot(document):
    config = document.get("HostConfig") or {}
    state = document.get("State") or {}
    return {
        "id": document.get("Id"),
        "image_id": document.get("Image"),
        "host_config": {field: config.get(field) for field in HOST_CONFIG_FIELDS},
        "host_config_omitted_keys": sorted(set(config) - set(HOST_CONFIG_FIELDS)),
        "state": {field: state.get(field) for field in (
            "Status", "Running", "Paused", "Restarting", "OOMKilled", "Dead",
            "Pid", "ExitCode", "Error", "StartedAt", "FinishedAt",
        )},
        "mounts": [{field: mount.get(field) for field in ("Type", "Destination", "RW")}
                   for mount in document.get("Mounts", [])],
    }


def validate_configuration(document, image, name, run_id):
    config = document.get("Config") or {}
    host = document.get("HostConfig") or {}
    security = set(host.get("SecurityOpt") or [])
    tmpfs = host.get("Tmpfs") or {}
    tmp_options = set(tmpfs.get("/tmp", "").split(","))
    mounts = document.get("Mounts") or []
    return {
        "owned_unique_container": document.get("Name") == "/" + name and (config.get("Labels") or {}).get(LABEL_KEY) == run_id,
        "requested_image_id": document.get("Image") == image.get("Id"),
        "user_65534": config.get("User") == "65534:65534",
        "stdin_python_entrypoint": config.get("Entrypoint") == ["python3"] and config.get("Cmd") == ["-B", "-u", "-"],
        "no_host_environment_injected": config.get("Env") == (image.get("Config") or {}).get("Env"),
        "memory_256_mib": host.get("Memory") == MEMORY_BYTES,
        "memory_and_swap_equal": host.get("MemorySwap") == MEMORY_BYTES,
        "half_cpu": host.get("NanoCpus") == NANO_CPUS,
        "pids_64": host.get("PidsLimit") == PIDS_LIMIT,
        "network_none": host.get("NetworkMode") == "none",
        "read_only_rootfs": host.get("ReadonlyRootfs") is True,
        "all_capabilities_dropped": set(str(value).upper() for value in (host.get("CapDrop") or [])) == {"ALL"} and not host.get("CapAdd"),
        "no_new_privileges": bool(security.intersection({"no-new-privileges", "no-new-privileges:true", "no-new-privileges=true"})),
        "tmpfs_options": set(tmpfs) == {"/tmp"} and {"rw", "noexec", "nosuid", "nodev"}.issubset(tmp_options) and bool(tmp_options.intersection({"size=32m", "size=33554432", "size=32768k"})),
        "no_bind_mounts": not host.get("Binds") and not host.get("Mounts") and not host.get("VolumesFrom"),
        "no_extra_mounts": all(mount.get("Type") == "tmpfs" and mount.get("Destination") == "/tmp" for mount in mounts),
        "no_host_ports": not host.get("PortBindings") and not host.get("PublishAllPorts"),
        "not_privileged": not host.get("Privileged"),
        "no_host_pid_or_ipc": host.get("PidMode") != "host" and host.get("IpcMode") != "host",
        "no_extra_devices": not host.get("Devices") and not host.get("DeviceRequests"),
        "logging_disabled": (host.get("LogConfig") or {}).get("Type") == "none",
        "no_restart": (host.get("RestartPolicy") or {}).get("Name") in ("", "no"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-bin", default="/usr/local/bin/attest-docker")
    parser.add_argument("--image", required=True, help="An already loaded full immutable image ID, optionally prefixed with sha256:.")
    parser.add_argument("--output", type=Path, required=True, help="Destination JSON evidence report.")
    args = parser.parse_args()
    if not os.path.isabs(args.docker_bin):
        parser.error("--docker-bin must be an absolute executable path.")
    if not re.match(r"^(?:sha256:)?[0-9a-f]{64}$", args.image):
        parser.error("--image must be a full 64-character lowercase hexadecimal image ID, optionally prefixed with sha256:.")
    image_id = args.image if args.image.startswith("sha256:") else "sha256:" + args.image
    run_id = uuid.uuid4().hex
    name = "attest-smoke-" + datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S") + "-" + run_id[:12]
    started = time.monotonic()
    report = {
        "schema_version": 1, "started_at_utc": utc_now(), "run_id": run_id,
        "container_name": name, "container_label": {LABEL_KEY: run_id},
        "requested_image_id": image_id,
        "execution_timeout_seconds": EXECUTION_TIMEOUT,
        "requested_limits": {"memory_bytes": MEMORY_BYTES, "memory_swap_bytes": MEMORY_BYTES,
                             "cpus": 0.5, "pids": PIDS_LIMIT, "network": "none"},
        "host_config_allowed_fields": list(HOST_CONFIG_FIELDS),
        "failures": [],
    }
    # Do not let ambient Docker contexts, proxy settings, registry credentials, or
    # model credentials enter the client process. The wrapper supplies its socket.
    client_env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": "/nonexistent", "DOCKER_CONFIG": "/nonexistent/attest-smoke-docker-config",
        "LANG": "C", "LC_ALL": "C",
    }

    def cli(arguments, timeout=10, input_text=None):
        command = [args.docker_bin] + list(arguments)
        command_started = time.monotonic()
        result = {"command": command, "timed_out": False}
        process = None
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                encoding="utf-8", errors="replace", env=client_env, start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, stderr = process.communicate(timeout=5)
            result.update({"return_code": process.returncode, "stdout": stdout, "stderr": stderr})
        except (OSError, subprocess.SubprocessError) as error:
            result.update({"return_code": process.returncode if process else None,
                           "stdout": "", "stderr": "", "error": type(error).__name__ + ": " + str(error)})
        result["elapsed_seconds"] = round(time.monotonic() - command_started, 3)
        return result

    def inspect(reference):
        result = cli(["container", "inspect", reference], timeout=5)
        return single_inspect_object(result), result

    container_id = None
    observer = None
    observer_stop = threading.Event()

    def observe_running():
        evidence = {"inspect_attempts": 0, "running_observed": False}
        report["running_observation"] = evidence
        deadline = time.monotonic() + 8
        while not observer_stop.is_set() and time.monotonic() < deadline:
            document, result = inspect(container_id)
            evidence["inspect_attempts"] += 1
            evidence["last_inspect_command"] = command_metadata(result)
            if document and (document.get("State") or {}).get("Running"):
                evidence["running_observed"] = True
                evidence["inspect"] = container_snapshot(document)
                stats = cli(["stats", "--no-stream", "--format", "{{json .}}", container_id], timeout=5)
                evidence["stats"] = stats
                try:
                    evidence["stats_json"] = json.loads(stats.get("stdout", ""))
                except ValueError:
                    evidence["stats_json"] = None
                return
            observer_stop.wait(0.1)
        evidence["error"] = "A running container was not observed within the bounded observation window."

    def cleanup():
        evidence = {"complete": False, "verified_absent_by_id": False}
        document, lookup = inspect(container_id or name)
        evidence["ownership_lookup"] = command_metadata(lookup)
        if document is None:
            if confirmed_missing(lookup, container_id or name):
                evidence["complete"] = True
                evidence["verified_absent_by_id"] = container_id is not None
                evidence["absence_identifier"] = container_id or name
                evidence["remove_skipped"] = "The exact identifier was already absent."
            else:
                evidence["error"] = "Could not establish ownership or absence; no removal was attempted."
            return evidence
        labels = (document.get("Config") or {}).get("Labels") or {}
        owned_id = document.get("Id")
        if (document.get("Name") != "/" + name or labels.get(LABEL_KEY) != run_id
                or not isinstance(owned_id, str) or not re.match(r"^[0-9a-f]{64}$", owned_id)
                or (container_id is not None and owned_id != container_id)):
            evidence["error"] = "Ownership check failed; no removal was attempted."
            return evidence
        evidence["owned_container_id"] = owned_id
        evidence["before_removal"] = container_snapshot(document)
        evidence["remove"] = cli(["rm", "--force", owned_id], timeout=10)
        _, absence = inspect(owned_id)
        evidence["absence_check"] = command_metadata(absence)
        evidence["verified_absent_by_id"] = confirmed_missing(absence, owned_id)
        evidence["complete"] = (evidence["remove"].get("return_code") == 0
                                and not evidence["remove"].get("timed_out")
                                and evidence["verified_absent_by_id"])
        return evidence

    try:
        image_result = cli(["image", "inspect", image_id], timeout=10)
        image = single_inspect_object(image_result)
        report["image_inspection"] = command_metadata(image_result)
        if image is None or image.get("Id") != image_id:
            raise ProbeFailure("The requested exact image ID could not be inspected locally; no pull was attempted.")
        if image.get("Os") != "linux":
            raise ProbeFailure("The supplied image must be a Linux image.")
        if (image.get("Config") or {}).get("Volumes"):
            raise ProbeFailure("Images declaring volumes are refused to avoid creating anonymous host-backed volumes.")
        report["image_inspection"].update({"id": image.get("Id"), "os": image.get("Os"),
                                           "architecture": image.get("Architecture"), "declared_volumes": False})
        create = cli([
            "create", "--pull=never", "--name", name, "--label", LABEL_KEY + "=" + run_id,
            "--memory=" + str(MEMORY_BYTES), "--memory-swap=" + str(MEMORY_BYTES),
            "--cpus=0.5", "--pids-limit=64", "--network=none", "--read-only",
            "--user=65534:65534", "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=32m", "--log-driver=none",
            "--restart=no", "--interactive", "--entrypoint=python3", image_id, "-B", "-u", "-",
        ], timeout=15)
        report["create"] = create
        if create.get("return_code") != 0 or create.get("timed_out"):
            raise ProbeFailure("Container creation failed or timed out.")
        candidate = create.get("stdout", "").strip()
        if not re.match(r"^[0-9a-f]{64}$", candidate):
            raise ProbeFailure("Creation did not return an unambiguous full container ID.")
        container_id = candidate
        report["container_id"] = container_id
        created, inspect_result = inspect(container_id)
        report["created_inspection"] = command_metadata(inspect_result)
        if created is None:
            raise ProbeFailure("The created container could not be inspected before execution.")
        report["created_inspection"].update(container_snapshot(created))
        configuration_checks = validate_configuration(created, image, name, run_id)
        report["host_config_validation"] = configuration_checks
        if not all(configuration_checks.values()):
            raise ProbeFailure("Requested isolation settings did not match the created container: " + ", ".join(sorted(key for key, value in configuration_checks.items() if not value)))
        program = ("RUN_ID = " + json.dumps(run_id) + "\nEXPECTED_MEMORY = " + str(MEMORY_BYTES)
                   + "\nEXPECTED_PIDS = " + str(PIDS_LIMIT) + "\n" + CONTAINER_PROGRAM)
        observer = threading.Thread(target=observe_running, name="attest-smoke-observer")
        observer.daemon = True
        observer.start()
        execution = cli(["start", "--attach", "--interactive", container_id],
                        timeout=EXECUTION_TIMEOUT, input_text=program)
        report["execution"] = execution
        observer_stop.set()
        observer.join(timeout=8)
        if observer.is_alive():
            raise ProbeFailure("The bounded inspection observer did not finish.")
        exited, exit_inspect = inspect(container_id)
        report["exited_inspection"] = command_metadata(exit_inspect)
        if exited is not None:
            report["exited_inspection"].update(container_snapshot(exited))
        evidence_lines = []
        for line in execution.get("stdout", "").splitlines():
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and value.get("type") == "attest_smoke_evidence" and value.get("run_id") == run_id:
                evidence_lines.append(value)
        runtime = evidence_lines[0] if len(evidence_lines) == 1 else None
        report["container_evidence"] = runtime
        running = report.get("running_observation") or {}
        state = (exited or {}).get("State") or {}
        stats = running.get("stats") or {}
        checks = {
            "execution_completed_within_timeout": not execution.get("timed_out"),
            "client_exit_zero": execution.get("return_code") == 0,
            "container_exited_zero": state.get("Status") == "exited" and state.get("ExitCode") == 0,
            "not_oom_killed": exited is not None and state.get("OOMKilled") is False,
            "no_runtime_error": exited is not None and not state.get("Error"),
            "running_inspect_recorded": running.get("running_observed") is True,
            "stats_recorded": stats.get("return_code") == 0 and not stats.get("timed_out") and isinstance(running.get("stats_json"), dict),
            "one_machine_readable_evidence_record": runtime is not None,
            "runtime_constraints_verified": runtime is not None and bool(runtime.get("checks")) and all(value is True for value in runtime["checks"].values()),
            "four_unittests_passed": runtime is not None and runtime.get("unittest") == {"tests_run": 4, "failures": 0, "errors": 0, "successful": True},
        }
        report["limits_and_execution_validation"] = checks
        report["failures"].extend("Validation failed: " + key for key, value in checks.items() if not value)
    except KeyboardInterrupt:
        report["failures"].append("Interrupted by the operator.")
    except Exception as error:
        report["failures"].append(type(error).__name__ + ": " + str(error))
    finally:
        observer_stop.set()
        if observer is not None and observer.is_alive():
            observer.join(timeout=8)
        try:
            report["cleanup"] = cleanup()
        except Exception as error:
            report["cleanup"] = {"complete": False, "verified_absent_by_id": False,
                                 "error": type(error).__name__ + ": " + str(error)}
        if not report["cleanup"].get("complete"):
            report["failures"].append("Cleanup was not fully verified.")
        if container_id is not None and not report["cleanup"].get("verified_absent_by_id"):
            report["failures"].append("Absence of the exact container ID was not verified.")
        report["finished_at_utc"] = utc_now()
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["passed"] = not report["failures"]
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except (IOError, OSError, ValueError) as error:
            print("Could not write the JSON evidence report: " + type(error).__name__ + ": " + str(error), file=sys.stderr)
            return 1
    print(json.dumps({"output": str(args.output), "passed": report["passed"],
                      "container_id": container_id,
                      "cleanup_verified": report["cleanup"].get("verified_absent_by_id", False)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
