#!/usr/bin/env python3
"""Run one bounded Sandboxes smoke suite (three sequential operations).

Credentials stay in the client process. No POST is retried. The public REST API
has no configurable VM CPU/RAM quotas: Python rlimits below bound only the test
process. A synthetic, untagged checkpoint is retained by the service; there is no
documented image-delete endpoint. This script does not reconcile billing.
"""

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path
import re
import ssl
import time
import urllib.error
import urllib.request

BASE = "https://api.tokenfactory.nebius.com/sandboxes/v1"
TERMINAL = {"SUCCESS", "FAILED", "CANCELLED"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def guest_code(stage):
    return '''import hashlib,json,os,pathlib,resource,socket,sys
resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456))
resource.setrlimit(resource.RLIMIT_CPU,(2,2))
stage=STAGE
root=pathlib.Path('/tmp/attest-api-smoke')
marker=root/'state.txt'
checks={}
if stage=='checkpoint':
    root.mkdir(exist_ok=False)
    marker.write_text('baseline\\n')
    checks['checkpoint_write']=marker.read_text()=='baseline\\n'
elif stage=='branch_a':
    checks['baseline_restored']=marker.read_text()=='baseline\\n'
    marker.write_text('branch-a\\n')
    checks['branch_write']=marker.read_text()=='branch-a\\n'
else:
    checks['baseline_restored']=marker.read_text()=='baseline\\n'
    checks['branch_a_write_absent']='branch-a' not in marker.read_text()
checks['python_312']=sys.version_info[:2]==(3,12)
checks['arithmetic']=sum(i*i for i in range(1000))==332833500
checks['uid_gid']=os.getuid()==65534 and os.getgid()==65534
interfaces=sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir())
checks['no_guest_nic']=all(n=='lo' for n in interfaces)
checks['address_space_limit']=resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456)
checks['cpu_time_limit']=resource.getrlimit(resource.RLIMIT_CPU)==(2,2)
def read(path):
    try:return pathlib.Path(path).read_text().strip()[:3000]
    except OSError:return None
meminfo=read('/proc/meminfo')
memtotal=next((line for line in (meminfo or '').splitlines() if line.startswith('MemTotal:')),None)
report={'stage':stage,'checks':checks,'python':sys.version.split()[0],
 'uid':os.getuid(),'gid':os.getgid(),'cpu_count_visible':os.cpu_count(),
 'memtotal_visible':memtotal,'interfaces':interfaces,
 'routes':read('/proc/net/route'),
 'cgroup_cpu_max':read('/sys/fs/cgroup/cpu.max'),
 'cgroup_memory_max':read('/sys/fs/cgroup/memory.max'),
 'cgroup_pids_max':read('/sys/fs/cgroup/pids.max'),
 'process_rlimit_as_bytes':resource.getrlimit(resource.RLIMIT_AS),
 'process_rlimit_cpu_seconds':resource.getrlimit(resource.RLIMIT_CPU),
 'state_sha256':hashlib.sha256(marker.read_bytes()).hexdigest()}
print(json.dumps(report,sort_keys=True),flush=True)
sys.exit(0 if all(checks.values()) else 1)
'''.replace("STAGE", repr(stage))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default=os.environ.get("NEBIUS_PROJECT_ID"))
    parser.add_argument("--credential-note", type=Path,
                        help="Optional private note with a NEBIUS_API_KEY assignment.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="Authorize three tiny remote operations.")
    parser.add_argument("--resume", action="store_true", help="Reuse recorded operation IDs; never replay their POSTs.")
    args = parser.parse_args()
    key = os.environ.get("NEBIUS_API_KEY", "")
    if not key and args.credential_note:
        match = re.search(r"(?m)^\s*(?:export\s+)?NEBIUS_API_KEY\s*=\s*([^\r\n]+)",
                          args.credential_note.read_text())
        if match:
            key = match.group(1).strip().strip("\"'`")
    if not key or not args.project_id:
        parser.error("Supply a private API key and a separate project identifier.")
    if not args.live:
        parser.error("This smoke creates one retained checkpoint; explicitly pass --live.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "api-smoke.json"
    if output.exists() and not args.resume:
        parser.error("api-smoke.json already exists; use a fresh directory to avoid replaying POSTs.")
    if args.resume and not output.exists():
        parser.error("No recorded run to resume.")
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=context))
    report = {"started_at_utc": utcnow(), "base_url": BASE,
              "project_id": args.project_id, "tls_verification": True,
              "post_retries": 0, "requests": [], "operations": [],
              "billing_reconciliation": "Separate before/after console evidence required.",
              "resource_boundary": "rlimits bound the process, not the VM; no REST CPU/RAM quota fields.",
              "retention": "One synthetic untagged checkpoint; two disposable branches. No delete API documented."}
    if args.resume:
        report = json.loads(output.read_text())
        if report.get("project_id") != args.project_id or report.get("base_url") != BASE:
            parser.error("Recorded account does not match the requested account.")
        if report.get("passed") is True:
            parser.error("Recorded smoke already passed; no further operations needed.")
        if any(not o.get("accepted", {}).get("uuid") for o in report.get("operations", [])):
            parser.error("A previous POST outcome is uncertain. Inspect account operations before proceeding.")
        report.setdefault("harness_corrections", []).append({
            "at_utc": utcnow(), "previous_failure": report.pop("failure", None),
            "previous_finished_at_utc": report.pop("finished_at_utc", None),
            "reason": "Accept observed no-signal sentinel -1 and validate named checks (checkpoint has seven).",
            "previous_operation_posts_replayed": 0})

    def save():
        text = json.dumps(report, indent=2) + "\n"
        if key in text:
            raise RuntimeError("Refusing to save credential-containing evidence")
        temporary = output.with_suffix(".json.tmp")
        with temporary.open("w") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)

    def request(path, payload=None, method=None):
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": "Bearer " + key, "Project": args.project_id,
                   "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
        record = {"at_utc": utcnow(), "method": req.get_method(), "path": path}
        report["requests"].append(record)
        save()
        try:
            with opener.open(req, timeout=20) as response:
                record["http_status"] = response.status
                record["retry_after"] = response.headers.get("Retry-After")
                data = json.loads(response.read(2_000_000))
        except urllib.error.HTTPError as error:
            record["http_status"] = error.code
            # Avoid persisting arbitrary server echoes of headers or credentials.
            save()
            raise RuntimeError("HTTP failure " + str(error.code)) from None
        except Exception as error:
            record["transport_error_type"] = type(error).__name__
            save()
            raise RuntimeError("Request outcome uncertain; do not replay a POST. Inspect server operations.") from None
        save()
        return data

    def wait_for(operation_id):
        deadline = time.monotonic() + 80
        while time.monotonic() < deadline:
            data = request("/operations/" + operation_id)
            if data.get("status") in TERMINAL:
                return data
            retry_after = report["requests"][-1].get("retry_after")
            try:
                delay = max(1.5, float(retry_after)) if retry_after else 1.5
            except ValueError:
                delay = 1.5
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(delay, remaining))
        request("/operations/" + operation_id, method="DELETE")
        # A cancellation request is not confirmation; read terminal state.
        for _ in range(10):
            data = request("/operations/" + operation_id)
            if data.get("status") in TERMINAL:
                return data
            time.sleep(1)
        raise RuntimeError("Cancellation requested; terminal cleanup remains unconfirmed")

    def decode(stream):
        if stream.get("truncated"):
            raise RuntimeError("Output truncated")
        value = stream.get("value", "")
        return base64.b64decode(value).decode() if stream.get("encoding") == "base64" else value

    save()
    try:
        who = request("/whoami")
        report["account"] = {k: who.get(k) for k in ("permissions", "limits")}
        if not all(who.get("permissions", {}).get(p) for p in ("spawn", "spawn_disposable", "list", "cancel")):
            raise RuntimeError("Required permissions unavailable")
        images = request("/images?tag=python:3.12-slim&limit=100")
        matches = [i for i in images.get("images", []) if i.get("tag") == "python:3.12-slim"]
        if len(matches) != 1:
            raise RuntimeError("Resolve one exact public base image before running")
        base_image = matches[0]["uuid"]
        report["base_image"] = matches[0]
        checkpoint = None
        for stage in ("checkpoint", "branch_a", "branch_b"):
            payload = {"command": "/usr/local/bin/python", "args": ["-c", guest_code(stage)],
                       "image": base_image if stage == "checkpoint" else checkpoint,
                       "shell": False, "uid": 65534, "gid": 65534,
                       "cwd": "/tmp", "env": {}, "preserve_env": False,
                       "timeout": 20, "truncate_output_at": 16384,
                       "networking": {"enabled": False},
                       "resources_limits": {"max_layer_bytes": 67108864},
                       "disposable": stage != "checkpoint"}
            recorded = [o for o in report["operations"] if o["stage"] == stage]
            if recorded:
                if len(recorded) != 1 or recorded[0]["request"] != payload:
                    raise RuntimeError("Recorded request differs; refusing to replay or reinterpret it")
                operation = recorded[0]
                accepted = operation["accepted"]
            else:
                operation = {"stage": stage, "request": payload}
                report["operations"].append(operation)
                save()
                accepted = request("/instances", payload)
                operation["accepted"] = accepted
                save()
            operation_id = accepted["uuid"]
            print(json.dumps({"stage": stage, "operation_id": operation_id, "status": "accepted"}), flush=True)
            result = wait_for(operation_id)
            operation["result"] = result
            save()
            execution = result.get("metadata", {}).get("result", {})
            stdout = decode(execution.get("stdout", {}))
            operation["stderr"] = decode(execution.get("stderr", {}))
            operation["guest"] = json.loads(stdout) if stdout.strip() else None
            state = execution.get("state", {})
            required = {"python_312", "arithmetic", "uid_gid", "no_guest_nic",
                        "address_space_limit", "cpu_time_limit"}
            required |= ({"checkpoint_write"} if stage == "checkpoint" else
                         {"baseline_restored", "branch_write" if stage == "branch_a" else "branch_a_write_absent"})
            checks = (operation["guest"] or {}).get("checks", {})
            operation["passed"] = (result.get("status") == "SUCCESS" and state.get("exit_code") == 0
                                   and not state.get("timed_out") and state.get("signal") in (None, 0, -1)
                                   and operation["guest"] is not None
                                   and operation["guest"].get("stage") == stage
                                   and required.issubset(checks) and all(v is True for v in checks.values()))
            save()
            print(json.dumps({"stage": stage, "operation_id": operation_id, "passed": operation["passed"],
                              "duration_seconds": result.get("duration"), "state": state,
                              "guest": operation["guest"], "resources": execution.get("resources")}), flush=True)
            if not operation["passed"]:
                raise RuntimeError("Smoke operation failed; inspect saved evidence")
            if stage == "checkpoint":
                checkpoint = result.get("result_image_uuid") or result.get("result", {}).get("image")
                if not checkpoint:
                    raise RuntimeError("No retained checkpoint returned")
                report["checkpoint_image_uuid"] = checkpoint
            elif result.get("result_image_uuid") or result.get("result", {}).get("image"):
                raise RuntimeError("Disposable operation unexpectedly returned a retained image")
        report["passed"] = True
        report["cleanup"] = {"all_owned_operations_terminal": True,
                             "retained_image_uuid": checkpoint,
                             "retained_image_tag_created": False,
                             "disposable_branches_retained_images": 0,
                             "checkpoint_deletion": "Not performed; no documented image-delete endpoint."}
    except Exception as error:
        report["passed"] = False
        report["failure"] = str(error).replace(key, "[REDACTED]")
        cleanup_records = []
        for operation in report["operations"]:
            operation_id = operation.get("accepted", {}).get("uuid")
            state = operation.get("result", {}).get("status")
            cleanup = {"stage": operation["stage"], "operation_id": operation_id,
                       "status": state or "UNKNOWN"}
            cleanup_records.append(cleanup)
            if not operation_id or state in TERMINAL:
                continue
            try:
                current = request("/operations/" + operation_id)
                if current.get("status") not in TERMINAL:
                    request("/operations/" + operation_id, method="DELETE")
                    current = wait_for(operation_id)
                cleanup["status"] = current.get("status", "UNKNOWN")
                operation["result"] = current
            except Exception as cleanup_error:
                cleanup["status"] = "UNKNOWN"
                cleanup["error_type"] = type(cleanup_error).__name__
        report["cleanup_after_failure"] = cleanup_records
        raise SystemExit(report["failure"]) from None
    finally:
        report["finished_at_utc"] = utcnow()
        save()
    print(json.dumps({"passed": True, "evidence": str(output)}), flush=True)


if __name__ == "__main__":
    main()
