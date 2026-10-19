#!/usr/bin/env python3
"""The six checks of reports/attest-audit-2026-10-19/boundaries-repro.py, evaluated after the repairs.

The auditor's script indexes `files["linked.txt"]` directly; once the snapshot stops following links that is a KeyError, so
the unmodified script stops at its first check (see boundaries-repro-after-fix.txt). This companion repeats each check with
the auditor's own expressions, reading the link entry with `.get` so that the remaining five checks run too. The historical
script and its results file are not modified. Offline, synthetic sentinels only, no network."""
from __future__ import annotations

import contextlib
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT))


def blocked(*args, **kwargs):
    raise AssertionError("No network is authorized for this offline reproduction")


def run() -> dict:
    from attest.core.workspace import snapshot_repo
    from attest.core.external import extract_tarball, ImportRefused
    from attest.sandbox.tf_sandboxes import GUEST_RUNNER

    spec = importlib.util.spec_from_file_location("audit_export", ROOT / "scripts/export_public.py")
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    checks: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="attest-boundaries-after-") as scratch:
        tmp = Path(scratch)
        repo = tmp / "repo"
        repo.mkdir()
        sentinel = tmp / "outside-sentinel.txt"
        sentinel.write_text("SYNTHETIC_OUTSIDE_REPOSITORY_SENTINEL")
        (repo / "linked.txt").symlink_to(sentinel)
        skipped: list[dict] = []
        files = snapshot_repo(repo, skipped=skipped)
        checks["snapshot_reads_outside_symlink"] = {"confirmed": files.get("linked.txt") == sentinel.read_bytes(),
                                                   "snapshot_keys": sorted(files), "skipped": skipped}

        script = ("from attest.core.workspace import Workspace; "
                  "w=Workspace({'x.txt':b'a'*28+b'!'},['**'],[]); "
                  "print(w.search('(a+)+$')); print(w.search('re:(a+)+$'))")
        try:
            proc = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, capture_output=True, timeout=6.0, check=True)
            timed_out, output = False, proc.stdout.decode()
        except subprocess.TimeoutExpired:
            timed_out, output = True, ""
        checks["host_regex_exceeds_deadline"] = {"confirmed": timed_out, "pattern": "(a+)+$", "input_bytes": 29,
                                                "literal_then_regex_output": output.strip().splitlines()}

        compressed = io.BytesIO()
        with tarfile.open(fileobj=compressed, mode="w:gz") as archive:
            member = tarfile.TarInfo("repo/file.txt")
            member.size = 64
            archive.addfile(member, io.BytesIO(b"x" * 64))
        reads: list[dict] = []
        real_extract = tarfile.TarFile.extractfile

        class Tracked:
            def __init__(self, handle):
                self.handle = handle

            def read(self, size=-1):
                output = self.handle.read(size)
                reads.append({"requested_bytes": size, "returned_bytes": len(output)})
                return output

        refused = False
        with patch.object(tarfile.TarFile, "extractfile", lambda archive, member: Tracked(real_extract(archive, member))):
            try:
                extract_tarball(compressed.getvalue(), tmp / "imported", max_file_bytes=16)
            except ImportRefused as error:
                refused, message = True, str(error)
        checks["tar_file_limit_after_read"] = {"confirmed": refused and reads == [{"requested_bytes": -1, "returned_bytes": 64}],
                                               "refused": refused, "refusal": message if refused else None, "reads": reads,
                                               "no_extraction_written": not (tmp / "imported").exists()}

        source = tmp / "export-source"
        (source / "deploy").mkdir(parents=True)
        sentinel_key = "cxk_" + "SYNTHETIC_AUDIT_SENTINEL_" + "123456"   # assembled at run time: this file is exported and scanned
        (source / "deploy/.env").write_text("API_KEY='" + sentinel_key + "'\n")
        with zipfile.ZipFile(source / "deploy/evidence.zip", "w") as archive:
            archive.writestr("record.json", '{"key":"' + sentinel_key + '"}')
        stats = {"files": 0, "redactions": 0, "redacted_files": [], "skipped_large": [], "redacted_pairs": []}
        with patch.object(export, "ROOT", source):
            export.copy_tree(source / "deploy", tmp / "exported/deploy", stats)
            hits = export.scan(tmp / "exported")
        checks["public_export_unscanned_env_and_zip"] = {
            "confirmed": (tmp / "exported/deploy/.env").exists() and (tmp / "exported/deploy/evidence.zip").exists() and hits == [],
            "copied_files": stats["files"], "excluded": stats.get("excluded"), "scan_hits": hits, "actual_secret_used": False}

        disposable = tmp / "disposable-root"
        disposable.mkdir()
        (disposable / "DO_NOT_DELETE.txt").write_text("SYNTHETIC_SOURCE_SENTINEL")
        stderr = io.StringIO()
        with patch.object(export, "ROOT", disposable), patch.object(sys, "argv", ["export_public.py", "--force", "--out", "."]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            code = export.main()
        checks["export_force_can_target_source_root"] = {"confirmed": code == 0 and not (disposable / "DO_NOT_DELETE.txt").exists(),
                                                         "exit_code": code, "sentinel_survives": (disposable / "DO_NOT_DELETE.txt").exists(),
                                                         "refusal": stderr.getvalue().strip()}

        job = {"stream_cap_bytes": 1024, "write": {}, "delete": [],
               "steps": [{"name": "bounded-output-sentinel", "cmd": [sys.executable, "-c", "print('x'*8192)"], "cwd": str(tmp), "timeout": 2}]}
        process = subprocess.run([sys.executable, "-B", "-c", GUEST_RUNNER], input=json.dumps(job).encode(), capture_output=True, timeout=5, check=True)
        report = json.loads(process.stdout.decode().splitlines()[1])
        step = report["steps"][0]
        checks["guest_stream_cap_applied_after_capture"] = {
            "confirmed": step["stdout_bytes"] == 8193 and len(step["stdout"]) < 1100,
            "note": ("the auditor's expression equates stdout_bytes with bytes held in memory; attest-guest/3 reports stdout_bytes as the"
                     " bytes OBSERVED on the stream while holding at most stream_cap_bytes of them, so this expression stays true by"
                     " construction; see test_a_noisy_child_is_drained_into_bounded_buffers_and_truncation_is_reported for the memory bound"),
            "runner": report["runner"], "configured_cap": 1024, "stdout_bytes_observed": step["stdout_bytes"],
            "stdout_truncated": step["stdout_truncated"], "reported_text_chars": len(step["stdout"]), "sandbox_api_called": False}
    return {"scope": "offline, bounded synthetic sentinels only; companion of boundaries-repro.py run after the repairs", "checks": checks}


if __name__ == "__main__":
    with patch.object(socket.socket, "connect", blocked), patch.object(socket, "create_connection", blocked):
        outcome = run()
    (HERE / "repro-checks-after-fix.json").write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps({key: value["confirmed"] for key, value in outcome["checks"].items()}, indent=2))
