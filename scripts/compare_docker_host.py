#!/usr/bin/env python3
"""Compare before/after snapshots for the bounded Aliyun Docker setup."""

import argparse
import json
from pathlib import Path


def compare(before, after):
    checks = {}
    details = {}
    observations = {}
    for name, previous in before["services"].items():
        current = after["services"].get(name, {})
        checks["service_" + name] = all(
            current.get(key) == previous.get(key)
            for key in ["MainPID", "ActiveState", "SubState", "NRestarts"]
        ) and current.get("ActiveState") == "active"
        details[name] = {"before": previous, "after": current}
    for key, expected in [("codex_local", 200), ("engram_local", 200), ("nginx_local", 301)]:
        checks["health_" + key] = before["health"][key].get("status") == expected and after["health"].get(key, {}).get("status") == expected
    checks["health_postgres_ready"] = all(snapshot["health"]["postgres_ready"].get("returncode") == 0 for snapshot in [before, after])
    for key, value in before["network"].items():
        current = after["network"].get(key)
        if key.startswith("net.bridge.") and value.get("returncode") == 255 and "No such file" in value.get("stderr", ""):
            checks["network_optional_sysctl_absence_" + key] = value == current
            observations[key] = "Absent in the baseline; absence checked again. No sysctl value was verified."
        else:
            collected = not isinstance(value, dict) or (value.get("returncode") == 0 and isinstance(current, dict) and current.get("returncode") == 0)
            checks["network_" + key] = collected and value == current
    removed = sorted(set(before["active_service_units"]) - set(after["active_service_units"]))
    checks["no_existing_running_service_removed"] = not removed
    checks["no_default_containerd_data_directory"] = not after["filesystem_state"]["/var/lib/containerd"]
    checks["no_default_docker_data_directory"] = not after["filesystem_state"]["/var/lib/docker"]
    return {
        "passed": all(checks.values()),
        "baseline_captured_at_utc": before["captured_at_utc"],
        "after_captured_at_utc": after["captured_at_utc"],
        "checks": checks,
        "observations": observations,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "services": details,
        "health": {"before": before["health"], "after": after["health"]},
        "memory_available_mib": {
            "before": round(before["memory_kib"]["MemAvailable"] / 1024.0, 1),
            "after": round(after["memory_kib"]["MemAvailable"] / 1024.0, 1),
        },
        "root_disk_free_gib": {
            "before": round(before["root_disk_bytes"]["free"] / 1024.0 ** 3, 2),
            "after": round(after["root_disk_bytes"]["free"] / 1024.0 ** 3, 2),
        },
        "removed_running_service_units": removed,
        "added_running_service_units": sorted(set(after["active_service_units"]) - set(before["active_service_units"])),
        "scope": "Compared recorded service state, local health endpoints, routes, interfaces, TCP listeners, firewall fingerprints, and selected sysctls. This is a bounded observation, not a full application regression test.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "failed_checks": result["failed_checks"],
                      "memory_available_mib": result["memory_available_mib"], "output": str(args.output)}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
