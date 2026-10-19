#!/usr/bin/env python3
"""Bounded offline reproductions; synthetic sentinels only; no product edits."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tarfile
import tempfile
from unittest.mock import patch
import zipfile

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parent.parent
sys.path.insert(0, str(ROOT))


def blocked(*args, **kwargs):
    raise AssertionError("No network is authorized for this offline reproduction")


def run():
    from attest.core.workspace import snapshot_repo
    from attest.core.external import extract_tarball, ImportRefused
    from attest.sandbox.tf_sandboxes import GUEST_RUNNER

    spec = importlib.util.spec_from_file_location("audit_export", ROOT / "scripts/export_public.py")
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    results = {"scope": "offline, bounded synthetic sentinels only", "checks": {}}
    checks = results["checks"]
    with tempfile.TemporaryDirectory(prefix="attest-boundaries-") as scratch:
        tmp = Path(scratch)
        repo = tmp / "repo"
        repo.mkdir()
        sentinel = tmp / "outside-sentinel.txt"
        sentinel.write_text("SYNTHETIC_OUTSIDE_REPOSITORY_SENTINEL")
        (repo / "linked.txt").symlink_to(sentinel)
        files = snapshot_repo(repo)
        checks["snapshot_reads_outside_symlink"] = {
            "confirmed": files["linked.txt"] == sentinel.read_bytes(),
            "scope": "direct local CLI snapshot; no remote symlink creation demonstrated",
        }

        # A child process prevents an unsafe regex from ever blocking the auditor.
        script = ("from attest.core.workspace import Workspace; "
                  "w=Workspace({'x.txt':b'a'*28+b'!'},['**'],[]); "
                  "w.search('(a+)+$')")
        try:
            subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT,
                           capture_output=True, timeout=1.0, check=True)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
        checks["host_regex_exceeds_deadline"] = {"confirmed": timed_out, "child_killed_at_s": 1.0,
                                                "input_bytes": 29, "pattern": "(a+)+$"}

        # Tiny archive: show unbounded read(-1) precedes a 16-byte file limit.
        compressed = io.BytesIO()
        with tarfile.open(fileobj=compressed, mode="w:gz") as archive:
            member = tarfile.TarInfo("repo/file.txt")
            member.size = 64
            archive.addfile(member, io.BytesIO(b"x" * 64))
        reads = []
        real_extract = tarfile.TarFile.extractfile

        class Tracked:
            def __init__(self, handle):
                self.handle = handle

            def read(self, size=-1):
                output = self.handle.read(size)
                reads.append({"requested_bytes": size, "returned_bytes": len(output)})
                return output

        def tracked_extract(archive, member):
            return Tracked(real_extract(archive, member))

        refused = False
        with patch.object(tarfile.TarFile, "extractfile", tracked_extract):
            try:
                extract_tarball(compressed.getvalue(), tmp / "imported", max_file_bytes=16)
            except ImportRefused:
                refused = True
        checks["tar_file_limit_after_read"] = {"confirmed": refused and reads == [{"requested_bytes": -1, "returned_bytes": 64}],
                                               "file_limit_bytes": 16, "reads": reads,
                                               "no_extraction_written": not (tmp / "imported").exists()}

        source = tmp / "export-source"
        (source / "deploy").mkdir(parents=True)
        (source / "deploy/.env").write_text("API_KEY='[REDACTED-KEY]'\n")
        with zipfile.ZipFile(source / "deploy/evidence.zip", "w") as archive:
            archive.writestr("record.json", '{"key":"[REDACTED-KEY]"}')
        stats = {"files": 0, "redactions": 0, "redacted_files": [], "skipped_large": [], "redacted_pairs": []}
        with patch.object(export, "ROOT", source):
            export.copy_tree(source / "deploy", tmp / "exported/deploy", stats)
            hits = export.scan(tmp / "exported")
        checks["public_export_unscanned_env_and_zip"] = {
            "confirmed": (tmp / "exported/deploy/.env").exists() and (tmp / "exported/deploy/evidence.zip").exists() and hits == [],
            "copied_files": stats["files"], "scan_hits": hits, "actual_secret_used": False,
        }

        # Invoke the actual --force deletion against a disposable synthetic ROOT.
        disposable = tmp / "disposable-root"
        disposable.mkdir()
        (disposable / "DO_NOT_DELETE.txt").write_text("SYNTHETIC_SOURCE_SENTINEL")
        with patch.object(export, "ROOT", disposable), patch.object(sys, "argv", ["export_public.py", "--force", "--out", "."]), contextlib.redirect_stdout(io.StringIO()):
            code = export.main()
        checks["export_force_can_target_source_root"] = {"confirmed": code == 0 and not (disposable / "DO_NOT_DELETE.txt").exists(),
                                                         "target": "disposable temporary ROOT only", "exit_code": code}

        job = {"stream_cap_bytes": 1024, "write": {}, "delete": [],
               "steps": [{"name": "bounded-output-sentinel", "cmd": [sys.executable, "-c", "print('x'*8192)"], "cwd": str(tmp), "timeout": 2}]}
        process = subprocess.run([sys.executable, "-B", "-c", GUEST_RUNNER], input=json.dumps(job).encode(),
                                 capture_output=True, timeout=5, check=True)
        report = json.loads(process.stdout.decode().splitlines()[1])
        step = report["steps"][0]
        checks["guest_stream_cap_applied_after_capture"] = {"confirmed": step["stdout_bytes"] == 8193 and len(step["stdout"]) < 1100,
                                                            "configured_cap": 1024, "captured_stdout_bytes": step["stdout_bytes"],
                                                            "reported_text_chars": len(step["stdout"]), "sandbox_api_called": False}
    results["source_sha256"] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        "attest/core/workspace.py", "attest/core/external.py", "attest/sandbox/tf_sandboxes.py", "scripts/export_public.py",
        "deploy/yungou/build_bundle.sh", "deploy/yungou/install.sh", "deploy/yungou/rollback.sh")}
    return results


if __name__ == "__main__":
    with patch.object(socket.socket, "connect", blocked), patch.object(socket, "create_connection", blocked):
        outcome = run()
    (AUDIT / "boundaries-repro-results.json").write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps({key: value["confirmed"] for key, value in outcome["checks"].items()}, indent=2))
