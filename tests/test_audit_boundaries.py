"""Acceptance tests for the runtime-boundary and release repairs of the audit of 19 Oct 2026: BOUND-01 (bounded search),
BOUND-02 (link-safe snapshots), BOUND-03 (streamed, pre-read-bounded tarballs), BOUND-04 (bounded guest capture and
process-group cleanup), REL-01 (release exclusions and a whole-tree scan) and REL-02 (export destinations and staging).

Offline: synthetic files and child processes of this interpreter only; no model, Sandbox API or network. The audit-only
sentinels are assembled at run time so that the public export's own scan never finds them in this module."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tracemalloc
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from attest.core import external
from attest.core.external import ImportRefused, extract_tarball, import_local
from attest.core.workspace import SEARCH_TIMEOUT_S, Workspace, snapshot_repo
from attest.sandbox.tf_sandboxes import GUEST_RUNNER, MARK_BEGIN, MARK_END

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import export_public  # noqa: E402

GUEST_GRACE_S = 2.0  # GRACE_S of the guest runner: one bounded wait for reaping, one for the pipes, one more after a late group kill


def fake_key() -> str:
    return "cxk_" + "SYNTHETIC_AUDIT_SENTINEL_" + "0" * 8


def fake_bearer() -> str:
    return "Authorization: " + "Bearer " + "SYNTHETICTOKEN" + "A" * 20


def fake_pem() -> str:
    return "-----BEGIN " + "RSA PRIVATE KEY-----\nMIIBOgIBAAJBAKsynthetic\n-----END " + "RSA PRIVATE KEY-----\n"


def fake_assignment() -> str:
    return "service_" + "token = '" + "z" * 24 + "'"


def make_tarball(entries: dict[str, bytes], links: dict[str, str] | None = None, dirs: tuple[str, ...] = (), top: str = "repo-abc") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in dirs:
            info = tarfile.TarInfo(f"{top}/{name}")
            info.type = tarfile.DIRTYPE
            archive.addfile(info)
        for rel, data in entries.items():
            info = tarfile.TarInfo(f"{top}/{rel}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        for rel, target in (links or {}).items():
            info = tarfile.TarInfo(f"{top}/{rel}")
            info.type = tarfile.SYMTYPE
            info.linkname = target
            archive.addfile(info)
    return buffer.getvalue()


def run_guest(job: dict, timeout: float = 60) -> tuple[dict, int]:
    """Run GUEST_RUNNER the way the Sandbox does (`python -I -c`, job on stdin) and report (guest report, peak RSS in bytes)."""
    program = GUEST_RUNNER + "\nimport resource\nsys.stderr.write('MAXRSS=%d\\n' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)\n"
    proc = subprocess.run([sys.executable, "-I", "-c", program], input=json.dumps(job).encode(), capture_output=True, timeout=timeout)
    out = proc.stdout.decode()
    report = json.loads(out[out.index(MARK_BEGIN) + len(MARK_BEGIN):out.rindex(MARK_END)])
    rss = int(proc.stderr.decode().rsplit("MAXRSS=", 1)[1].split()[0])
    return report, (rss if sys.platform == "darwin" else rss * 1024)   # ru_maxrss is bytes on macOS, kilobytes on Linux


def step(cmd_source: str, timeout: float, cwd: str, name: str = "step") -> dict:
    return {"name": name, "cmd": [sys.executable, "-c", cmd_source], "cwd": cwd, "timeout": timeout}


def process_gone(pid: int, wait_s: float = 3.0) -> bool:
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


class Bound01SearchIsLiteralByDefaultAndRegexIsBounded(unittest.TestCase):
    def setUp(self):
        src = b"import os\n\n\nclass Version:\n    @classmethod\n    def _nat_cmp(cls, a, b):\n        return 0\n"
        self.ws = Workspace({"src/pkg/version.py": src, "x.txt": b"a" * 28 + b"!", "bin.dat": b"\0\0def _nat_cmp"}, ["src/**"], [])

    def test_literal_search_is_the_default_so_the_pathological_text_returns_at_once(self):
        started = time.monotonic()
        self.assertIn("no match", self.ws.search("(a+)+$"))
        self.assertLess(time.monotonic() - started, 1.0)
        hits = self.ws.search("_nat_cmp")
        self.assertIn("src/pkg/version.py:6:     def _nat_cmp(cls, a, b):", hits)
        self.assertNotIn("bin.dat", hits)                                   # binary files are not searched
        self.assertIn("no match", self.ws.search(r"def _nat_cmp\("))        # without the prefix a backslash is a literal character
        self.assertIn("no match", self.ws.search("[unbalanced"))
        self.assertIn("1 matching line(s)", self.ws.search("def _nat_cmp(", "src/pkg/version.py"))
        with self.assertRaises(FileNotFoundError):
            self.ws.search("x", "missing.py")

    def test_regex_prefix_runs_in_a_child_and_is_cut_at_the_deadline(self):
        started = time.monotonic()
        text = self.ws.search("re:(a+)+$")
        elapsed = time.monotonic() - started
        self.assertEqual(text, f"search aborted: the regular expression exceeded {SEARCH_TIMEOUT_S:g} s; use a literal search")
        self.assertLess(elapsed, SEARCH_TIMEOUT_S + 2.0)
        only = self.ws.search(r"re:def _nat_cmp\(", "src/pkg/version.py")
        self.assertIn("1 matching line(s)", only)
        self.assertIn("src/pkg/version.py:6:", only)
        self.assertTrue(self.ws.search("re:[unbalanced").startswith("INVALID ACTION: invalid regular expression"))   # never silently literal
        self.assertTrue(self.ws.search("re:").startswith("INVALID ACTION"))
        self.assertIn("no match for regular expression", self.ws.search("re:^zzz$"))

    def test_long_lines_and_a_large_tree_return_promptly(self):
        files = {f"pkg/mod{i:03d}.py": (("def f%d():\n    return %d\n" % (i, i)) * 200).encode() for i in range(400)}
        files["long.txt"] = b"x" * 2_000_000 + b"needle"
        ws = Workspace(files, ["**"], [])
        started = time.monotonic()
        self.assertIn("long.txt:1:", ws.search("needle"))
        literal = ws.search("def f7(")
        self.assertIn("200 matching line(s) (showing the first 60)", literal)
        self.assertEqual(literal.count("\n"), 60)
        regex = ws.search("re:^def f7\\(")
        self.assertIn("200 matching line(s) (showing the first 60)", regex)
        self.assertLess(time.monotonic() - started, 2 * SEARCH_TIMEOUT_S + 4.0)
        started = time.monotonic()
        text = ws.search("re:x+y", "long.txt")   # quadratic on a 2 MB line: either no match or the deadline, never a hang
        self.assertTrue(text.startswith("no match") or text.startswith("search aborted"), text)
        self.assertLess(time.monotonic() - started, SEARCH_TIMEOUT_S + 2.0)


class Bound02SnapshotNeverFollowsLinks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-bound02-"))
        self.repo = self.tmp / "repo"
        (self.repo / "pkg").mkdir(parents=True)
        (self.repo / "pkg" / "mod.py").write_bytes(b"x = 1\n")
        self.sentinel = self.tmp / "outside.txt"
        self.sentinel.write_bytes(b"SYNTHETIC_OUTSIDE_REPOSITORY_SENTINEL")
        outside = self.tmp / "outside-dir"
        outside.mkdir()
        (outside / "secret.txt").write_bytes(b"SYNTHETIC_OUTSIDE_DIRECTORY_SENTINEL")
        (self.repo / "file-link.txt").symlink_to(self.sentinel)
        (self.repo / "dir-link").symlink_to(outside, target_is_directory=True)
        (self.repo / "broken-link").symlink_to(self.tmp / "missing")
        (self.repo / "pkg" / "inner-link.py").symlink_to(self.repo / "pkg" / "mod.py")   # even an in-repository link is not followed

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_outside_file_and_directory_links_and_broken_links_are_skipped_and_recorded(self):
        skipped: list[dict] = []
        files = snapshot_repo(self.repo, skipped=skipped)
        self.assertEqual(files, {"pkg/mod.py": b"x = 1\n"})
        self.assertNotIn(b"SENTINEL", b"".join(files.values()))
        self.assertEqual({(s["path"], s["reason"]) for s in skipped},
                         {("file-link.txt", "symbolic link"), ("dir-link", "symbolic link"), ("broken-link", "symbolic link"),
                          ("pkg/inner-link.py", "symbolic link")})
        self.assertEqual(snapshot_repo(self.repo), files)   # the skipped list is optional

    def test_a_link_swapped_in_between_listing_and_open_is_refused_by_the_kernel(self):
        victim = self.repo / "victim.txt"
        victim.write_bytes(b"regular content")
        real_open = os.open
        swapped: list[bool] = []

        def swapping_open(path, flags, mode=0o777, *, dir_fd=None):
            if os.fsdecode(path).endswith("victim.txt") and not swapped:   # the attacker wins the race after the listing
                swapped.append(True)
                victim.unlink()
                victim.symlink_to(self.sentinel)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        skipped: list[dict] = []
        with mock.patch("attest.core.workspace.os.open", swapping_open):
            files = snapshot_repo(self.repo, skipped=skipped)
        self.assertTrue(swapped)
        self.assertNotIn("victim.txt", files)
        self.assertNotIn(b"SENTINEL", b"".join(files.values()))
        self.assertIn({"path": "victim.txt", "reason": "symbolic link"}, skipped)

    def test_special_files_are_skipped_without_blocking_and_limits_name_themselves(self):
        os.mkfifo(self.repo / "pipe")
        skipped: list[dict] = []
        files = snapshot_repo(self.repo, skipped=skipped)
        self.assertNotIn("pipe", files)
        self.assertIn({"path": "pipe", "reason": "not a regular file"}, skipped)
        (self.repo / "pkg" / "big.py").write_bytes(b"x" * 11)
        with self.assertRaises(ValueError) as cm:
            snapshot_repo(self.repo, max_file_bytes=10)
        self.assertEqual(str(cm.exception), "pkg/big.py exceeds the per-file limit of 10 bytes")
        with self.assertRaises(ValueError) as cm:
            snapshot_repo(self.repo, max_files=1)
        self.assertIn("limit is 1 files", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            snapshot_repo(self.repo, max_total_bytes=12)
        self.assertIn("total limit of 12 bytes", str(cm.exception))

    def test_import_local_and_the_direct_snapshot_see_the_same_regular_files(self):
        record = import_local(self.repo, self.tmp / "imported")
        self.assertEqual(snapshot_repo(self.tmp / "imported" / "repo"), snapshot_repo(self.repo))
        self.assertEqual(record["files"], 1)
        self.assertEqual({s["path"] for s in record["skipped"]}, {"file-link.txt", "dir-link", "broken-link", "pkg/inner-link.py"})
        self.assertFalse(any(p.is_symlink() for p in (self.tmp / "imported").rglob("*")))

    def test_the_semver_example_links_are_skipped_not_fatal_also_in_a_harness_copy(self):
        repo = ROOT / "examples" / "semver-is-compatible" / "repo"
        skipped: list[dict] = []
        files = snapshot_repo(repo, skipped=skipped)
        self.assertIn("tests/conftest.py", files)
        self.assertNotIn("tests/coerce.py", files)
        self.assertEqual({s["path"] for s in skipped}, {"tests/coerce.py", "tests/semverwithvprefix.py"})
        copy = self.tmp / "harness-copy"
        shutil.copytree(repo, copy, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))  # as run_evaluation.make_snapshot does
        self.assertEqual(snapshot_repo(copy), files)


class Bound03TarballIsStreamedAndBoundedBeforeReading(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-bound03-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def tracked_reads(self):
        """Patch TarFile.extractfile the way the auditor did, recording every read request against member contents."""
        reads: list[dict] = []
        real_extract = tarfile.TarFile.extractfile

        class Tracked:
            def __init__(self, handle):
                self.handle = handle

            def read(self, size=-1):
                output = self.handle.read(size)
                reads.append({"requested_bytes": size, "returned_bytes": len(output)})
                return output

        return reads, mock.patch.object(tarfile.TarFile, "extractfile", lambda archive, member: Tracked(real_extract(archive, member)))

    def test_an_oversized_declared_member_is_refused_before_any_read(self):
        data = make_tarball({"file.txt": b"x" * 64}, top="repo")
        reads, patcher = self.tracked_reads()
        with patcher, self.assertRaises(ImportRefused) as cm:
            extract_tarball(data, self.tmp / "imported", max_file_bytes=16)
        self.assertIn("per-file limit of 16 bytes", str(cm.exception))
        self.assertEqual(reads, [])
        self.assertFalse((self.tmp / "imported").exists())

    def test_the_total_bound_is_checked_against_declarations_and_every_read_is_capped(self):
        data = make_tarball({f"f{i}.bin": b"x" * 1000 for i in range(5)})
        reads, patcher = self.tracked_reads()
        with patcher, mock.patch.dict(external.LIMITS, {"max_total_bytes": 2500}), self.assertRaises(ImportRefused) as cm:
            extract_tarball(data, self.tmp / "imported", max_file_bytes=1000)
        self.assertIn("exceed the limit of 2500 bytes", str(cm.exception))
        self.assertEqual([r["requested_bytes"] for r in reads], [1001, 1001])   # f0 and f1 read with a cap; f2 refused before its read

    def test_excessive_link_entries_and_headers_are_refused_before_contents_are_loaded(self):
        reads, patcher = self.tracked_reads()
        links_only = make_tarball({}, links={f"l{i}.py": "a.py" for i in range(12)})
        with patcher, mock.patch.dict(external.LIMITS, {"max_link_entries": 10}), self.assertRaises(ImportRefused) as cm:
            extract_tarball(links_only, self.tmp / "imported")
        self.assertIn("limit is 10 links", str(cm.exception))
        dirs_only = make_tarball({}, dirs=tuple(f"d{i}" for i in range(30)))
        with patcher, mock.patch.dict(external.LIMITS, {"max_tar_members": 20}), self.assertRaises(ImportRefused) as cm:
            extract_tarball(dirs_only, self.tmp / "imported")
        self.assertIn("limit is 20 entries", str(cm.exception))
        self.assertEqual(reads, [])

    def test_duplicate_paths_unsafe_link_names_and_unreadable_archives_refuse(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for _ in range(2):
                info = tarfile.TarInfo("repo/a.py")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"1"))
        with self.assertRaises(ImportRefused) as cm:
            extract_tarball(buffer.getvalue(), self.tmp / "dup")
        self.assertIn("duplicate member path", str(cm.exception))
        with self.assertRaises(ImportRefused) as cm:
            extract_tarball(make_tarball({"a.py": b"1"}, links={"../escape.py": "a.py"}), self.tmp / "esc")
        self.assertIn("unsafe path", str(cm.exception))
        with self.assertRaises(ImportRefused):
            extract_tarball(b"\x1f\x8bnot a tarball", self.tmp / "bad")
        self.assertFalse(any((self.tmp / name).exists() for name in ("dup", "esc", "bad")))

    def test_a_highly_compressible_archive_stays_within_a_small_memory_ceiling(self):
        data = make_tarball({f"zeros{i:02d}.bin": bytes(1 << 20) for i in range(40)})   # 40 MiB declared, a few tens of KB compressed
        self.assertLess(len(data), 200_000)
        tracemalloc.start()
        try:
            with mock.patch.dict(external.LIMITS, {"max_total_bytes": 3_000_000}), self.assertRaises(ImportRefused) as cm:
                extract_tarball(data, self.tmp / "imported", max_file_bytes=1 << 20)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertIn("exceed the limit of 3000000 bytes", str(cm.exception))
        self.assertLess(peak, 8 * 1024 * 1024)   # two members held plus buffers; the previous code read all 40 MiB before refusing


class Bound04GuestRunnerCapturesBoundedlyAndCleansUpGroups(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="attest-bound04-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def job(self, *steps, cap=65536, **extra) -> dict:
        return {"stream_cap_bytes": cap, "write": {}, "delete": [], "steps": list(steps)} | extra

    def test_a_noisy_child_is_drained_into_bounded_buffers_and_truncation_is_reported(self):
        quiet, quiet_rss = run_guest(self.job(step("print('hi')", 10, self.tmp)))
        self.assertEqual(quiet["runner"], "attest-guest/3")
        self.assertEqual(quiet["steps"][0]["stdout"], "hi\n")
        noisy_source = ("import sys\nchunk = b'x' * 65536\nfor _ in range(1024): sys.stdout.buffer.write(chunk)\n"
                        "sys.stderr.buffer.write(b'e' * (16 << 20))\n")
        report, noisy_rss = run_guest(self.job(step(noisy_source, 30, self.tmp), output_limit_bytes=400_000_000))
        record = report["steps"][0]
        self.assertEqual((record["stdout_bytes"], record["stderr_bytes"]), (64 << 20, 16 << 20))
        self.assertTrue(record["stdout_truncated"] and record["stderr_truncated"])
        self.assertLessEqual(len(record["stdout"]), 65536 + 100)
        self.assertIn(f"...[truncated: {(64 << 20) - 65536} of {64 << 20} bytes omitted]...", record["stdout"])
        self.assertTrue(record["stdout"].startswith("x" * 100) and record["stdout"].endswith("x" * 100))
        self.assertEqual(record["exit_code"], 0)
        self.assertFalse(record["timed_out"] or record["output_exhausted"])
        self.assertLess(noisy_rss - quiet_rss, 40 * 1024 * 1024, (quiet_rss, noisy_rss))   # 80 MiB passed through; the runner held a bounded part

    def test_output_exhaustion_kills_the_process_group_and_is_recorded(self):
        report, _ = run_guest(self.job(step("import sys\nwhile True: sys.stdout.buffer.write(b'y' * 65536)\n", 20, self.tmp),
                                       cap=1024, output_limit_bytes=1_000_000))
        record = report["steps"][0]
        self.assertTrue(record["output_exhausted"])
        self.assertFalse(record["timed_out"])
        self.assertIsNone(record["exit_code"])
        self.assertGreater(record["stdout_bytes"], 1_000_000)
        self.assertLess(record["duration_s"], 5.0)
        self.assertTrue(record["cleanup"]["killed_group"] and record["cleanup"]["reaped"] and record["cleanup"]["pipes_closed"])

    def test_a_grandchild_holding_the_pipes_is_killed_within_the_documented_grace(self):
        source = ("import subprocess, sys\np = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                  "print('GRANDCHILD', p.pid, flush=True)\n")
        started = time.monotonic()
        report, _ = run_guest(self.job(step(source, 10, self.tmp)))
        elapsed = time.monotonic() - started
        record = report["steps"][0]
        pid = int(record["stdout"].split()[1])
        self.assertTrue(process_gone(pid))
        self.assertEqual(record["exit_code"], 0)                  # the step itself finished; the record says what was cleaned up
        self.assertTrue(record["cleanup"]["killed_group"] and record["cleanup"]["pipes_closed"])
        self.assertLess(record["duration_s"], GUEST_GRACE_S + 1.5)
        self.assertLess(elapsed, GUEST_GRACE_S + 5.0)

    def test_a_timeout_kills_the_whole_group_including_a_sleeping_grandchild(self):
        source = ("import subprocess, sys, time\np = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                  "print('GRANDCHILD', p.pid, flush=True)\ntime.sleep(60)\n")
        report, _ = run_guest(self.job(step(source, 1, self.tmp)))
        record = report["steps"][0]
        pid = int(record["stdout"].split()[1])
        self.assertTrue(process_gone(pid))
        self.assertTrue(record["timed_out"])
        self.assertIsNone(record["exit_code"])
        self.assertLess(record["duration_s"], 1 + GUEST_GRACE_S + 0.5)
        self.assertTrue(record["cleanup"]["killed_group"])

    def test_a_large_normal_result_is_read_in_full_on_both_streams(self):
        source = "import sys\nsys.stdout.write('a' * 300000)\nsys.stderr.write('b' * 300000)\n"
        report, _ = run_guest(self.job(step(source, 10, self.tmp), cap=2_000_000))
        record = report["steps"][0]
        self.assertEqual((len(record["stdout"]), len(record["stderr"])), (300000, 300000))
        self.assertFalse(record["stdout_truncated"] or record["stderr_truncated"])
        self.assertEqual(record["exit_code"], 0)
        for field in ("stdout", "stderr", "exit_code", "timed_out", "duration_s", "stdout_bytes", "stderr_bytes", "cleanup"):
            self.assertIn(field, record)

    def test_the_host_adapter_reads_the_report_and_flags_exhaustion_as_a_step_error(self):
        from attest.ledger import Ledger
        from attest.sandbox.tf_sandboxes import TokenFactorySandboxes
        executor = TokenFactorySandboxes("key", "project", Ledger())
        report = {"runner": "attest-guest/3", "steps": [{"name": "tests", "cmd": ["x"], "cwd": "/tmp", "exit_code": None, "timed_out": False,
                                                        "output_exhausted": True, "stdout": "y", "stderr": "", "stdout_bytes": 2_000_000,
                                                        "stderr_bytes": 0, "stdout_truncated": True, "stderr_truncated": False,
                                                        "cleanup": {"killed_group": True}, "duration_s": 0.5}]}
        stdout = MARK_BEGIN + "\n" + json.dumps(report) + "\n" + MARK_END + "\n"
        operation = {"status": "SUCCESS", "duration": 1.0, "metadata": {"result": {"state": {"exit_code": 0, "timed_out": False},
                                                                                     "stdout": {"value": stdout}, "stderr": {"value": ""}}}}
        with mock.patch.object(executor, "_request", return_value=({"uuid": "op-1"}, {})), mock.patch.object(executor, "_wait", return_value=operation):
            run = executor.run_branch("image", {}, [{"name": "tests", "cmd": ["x"], "cwd": "/tmp", "timeout": 10}], stage="tests")
        self.assertTrue(run.ok)
        self.assertIsNone(run.steps[0].exit_code)
        self.assertTrue(run.steps[0].error.startswith("output exhausted"))
        self.assertFalse(run.steps[0].ok)


class Rel01ReleaseExclusionsAndWholeTreeScan(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-rel01-"))
        self.stats = {"files": 0, "redactions": 0, "redacted_files": [], "skipped_large": [], "redacted_pairs": []}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_credential_environment_archive_database_and_binary_files_are_excluded_at_every_depth(self):
        source = self.tmp / "source"
        deploy = source / "deploy"
        (deploy / "nested").mkdir(parents=True)
        (deploy / ".env").write_text("API_KEY='" + fake_key() + "'\n")
        (deploy / "nested" / "secrets.env").write_text("X=1\n")
        (deploy / "nested" / ".env.local").write_text("X=1\n")
        (deploy / "server.pem").write_text(fake_pem())
        (deploy / "host.key").write_text("k\n")
        (deploy / "id_ed25519").write_text("k\n")
        with zipfile.ZipFile(deploy / "evidence.zip", "w") as archive:
            archive.writestr("record.json", '{"key":"' + fake_key() + '"}')
        (deploy / "state.db").write_bytes(b"\0" * 16)
        (deploy / "mod.pyc").write_bytes(b"\0" * 16)
        (deploy / "bundle.tar.gz").write_bytes(b"\x1f\x8b")
        (deploy / "attest.env.example").write_text("NEBIUS_API_KEY=\n")
        (deploy / "README.md").write_text("# deploy\n")
        with mock.patch.object(export_public, "ROOT", source):
            export_public.copy_tree(deploy, self.tmp / "out" / "deploy", self.stats)
            hits = export_public.scan(self.tmp / "out")
        exported = sorted(p.relative_to(self.tmp / "out").as_posix() for p in (self.tmp / "out").rglob("*") if p.is_file())
        self.assertEqual(exported, ["deploy/README.md", "deploy/attest.env.example"])
        self.assertEqual(hits, [])
        self.assertEqual({e["path"] for e in self.stats["excluded"]},
                         {"deploy/.env", "deploy/nested/secrets.env", "deploy/nested/.env.local", "deploy/server.pem", "deploy/host.key",
                          "deploy/id_ed25519", "deploy/evidence.zip", "deploy/state.db", "deploy/mod.pyc", "deploy/bundle.tar.gz"})
        self.assertEqual(self.stats["files"], 2)

    def test_the_export_keeps_scripts_executable_and_nothing_else(self):
        """Revision 7: the export used to copy content only, so every exported script, including the rehearsal shims that
        tests/test_audit_ops.py runs, was published non-executable and a clean checkout of the export failed those tests."""
        import stat
        source = self.tmp / "source"
        shims = source / "deploy" / "rehearsal" / "shims"
        shims.mkdir(parents=True)
        (shims / "systemctl").write_text("#!/bin/sh\nexit 0\n")
        (shims / "systemctl").chmod(0o755)
        (shims / "_log.sh").write_text("log() { :; }\n")
        (shims / "_log.sh").chmod(0o644)
        (shims / "owner-only").write_text("#!/bin/sh\n")
        (shims / "owner-only").chmod(0o700)
        (shims / "too-open").write_text("#!/bin/sh\n")
        (shims / "too-open").chmod(0o777 | stat.S_ISUID)
        (shims / "group-writable.txt").write_text("x\n")
        (shims / "group-writable.txt").chmod(0o664)
        out = self.tmp / "out" / "deploy"
        with mock.patch.object(export_public, "ROOT", source):
            export_public.copy_tree(source / "deploy", out, self.stats)
        modes = {p.name: stat.S_IMODE(p.stat().st_mode) for p in (out / "rehearsal" / "shims").iterdir()}
        self.assertEqual(modes, {"systemctl": 0o755, "_log.sh": 0o644, "owner-only": 0o755, "too-open": 0o755, "group-writable.txt": 0o644})
        completed = subprocess.run([str(out / "rehearsal" / "shims" / "systemctl")], capture_output=True)
        self.assertEqual(completed.returncode, 0, "an exported shim runs as it does in the source tree")

    def test_every_staged_file_is_scanned_whatever_its_name(self):
        out = self.tmp / "staged"
        out.mkdir()
        (out / "notes").write_text("gateway " + fake_key() + "\n")                                   # extensionless text
        (out / "dump.txt.bak").write_text(fake_bearer() + "\n")                                       # alternate extension
        (out / "cert.md").write_text(fake_pem())                                                      # private key block
        (out / "config.cfg").write_text(fake_assignment() + "\n")                                     # token= assignment
        (out / "latin1.txt").write_bytes("caf\xe9 ".encode("latin-1") + fake_key().encode("ascii"))  # not UTF-8, no NUL: still scanned
        (out / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0\rIHDR" + bytes(range(256)))        # binary: skipped
        (out / "clean.md").write_text("Authorization: Bearer <your token>\nmax_tokens: 4096\nheaders = {'Authorization': 'Bearer ' + key}\n"
                                      "ATTEST_ADMIN_TOKEN=\ntokens_in: 1234567890123456789\n")
        hits = export_public.scan(out)
        self.assertEqual({hit.split(":")[0] for hit in hits}, {"notes", "dump.txt.bak", "cert.md", "config.cfg", "latin1.txt"})

    def test_zip_members_are_inspected_with_bounded_decompression_and_archives_are_excluded_by_default(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as archive:
            archive.writestr("record.json", '{"key":"' + fake_key() + '"}')
        outer = self.tmp / "evidence.zip"
        with zipfile.ZipFile(outer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("inner.zip", inner.getvalue())
            archive.writestr("big.txt", b"a" * (export_public.ZIP_MEMBER_BYTES + 1))   # highly compressible, over the member bound
            archive.writestr("notes/.env", "X=1\n")
            archive.writestr("clean.txt", "nothing here\n")
        self.assertEqual(export_public.ARCHIVE_POLICY, "exclude")
        with mock.patch.object(export_public, "ARCHIVE_POLICY", "inspect"):
            findings = dict(export_public.scan_zip(outer))
            inspected_hits = export_public.scan(self.tmp)
        self.assertIn("cxk_", findings["inner.zip!record.json"])
        self.assertIn("inspection bound", findings["big.txt"])
        self.assertIn("environment or credential file", findings["notes/.env"])
        self.assertNotIn("clean.txt", findings)
        self.assertTrue(inspected_hits and all(hit.startswith("evidence.zip!") for hit in inspected_hits))
        self.assertIsNotNone(export_public.exclusion_reason(outer))                   # the default policy never copies it
        default_hits = export_public.scan(self.tmp)
        self.assertEqual(len(default_hits), 1)
        self.assertIn("archive in the staged tree", default_hits[0])                   # and one that got in anyway is a hit

    def test_main_fails_closed_on_a_planted_secret_and_leaves_the_previous_export_intact(self):
        root = self.tmp / "project"
        (root / "deploy").mkdir(parents=True)
        (root / "dist").mkdir()
        (root / "README.md").write_text("# project\n")
        (root / "deploy" / ".env").write_text("API_KEY='" + fake_key() + "'\n")
        (root / "deploy" / "notes").write_text("pasted by mistake:\n" + fake_pem())   # extensionless text; not a redaction target
        dest = root / "dist" / "public"
        dest.mkdir()
        (dest / "EXPORT.json").write_text("{}\n")
        (dest / "OLD.md").write_text("previous export\n")
        code, err = run_export(root, "--force", "--out", "dist/public")
        self.assertEqual(code, 1)
        self.assertIn("SCAN FAILED", err)
        self.assertIn("deploy/notes", err)
        self.assertTrue((dest / "OLD.md").exists())
        self.assertFalse((dest / "deploy").exists())
        self.assertEqual([p.name for p in (root / "dist").iterdir()], ["public"])   # no staging residue
        (root / "deploy" / "notes").write_text("gateway key " + fake_key() + "\n")   # the gateway key shape is redacted, whatever the suffix
        code, err = run_export(root, "--force", "--out", "dist/public")
        self.assertEqual(code, 0, err)
        self.assertFalse((dest / "OLD.md").exists())
        self.assertEqual((dest / "deploy" / "notes").read_text(), "gateway key [REDACTED-KEY]\n")
        self.assertFalse((dest / "deploy" / ".env").exists())
        record = json.loads((dest / "EXPORT.json").read_text())
        self.assertEqual([e["path"] for e in record["excluded"]], ["deploy/.env"])
        self.assertEqual(record["redacted_files"], ["deploy/notes"])
        self.assertEqual(record["scan_hits"], [])


def run_export(root: Path, *argv: str) -> tuple[int, str]:
    """export_public.main() against a disposable ROOT, with stdout and stderr captured."""
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(export_public, "ROOT", root), mock.patch.object(sys, "argv", ["export_public.py", *argv]), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = export_public.main()
    return code, err.getvalue()


class Rel02ExportDestinationsAreRefusedBeforeDeletion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-rel02-"))
        self.root = self.tmp / "project"
        (self.root / "src").mkdir(parents=True)
        (self.root / "DO_NOT_DELETE.txt").write_text("SYNTHETIC_SOURCE_SENTINEL\n")
        (self.root / "src" / "keep.py").write_text("x = 1\n")
        (self.root / "README.md").write_text("# project\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_root_ancestor_and_nested_source_destinations_are_refused_with_exit_2(self):
        for out in (".", "", str(self.root), "..", str(self.root.parent), "src", "src/out", str(self.root / "src"), "dist", "/"):
            code, err = run_export(self.root, "--force", "--out", out)
            self.assertEqual(code, 2, out)
            self.assertTrue(err.startswith("refusing:"), err)
        self.assertTrue((self.root / "DO_NOT_DELETE.txt").exists())
        self.assertTrue((self.root / "src" / "keep.py").exists())
        self.assertFalse((self.root / "dist").exists())
        foreign = self.tmp / "foreign"
        (foreign / ".git").mkdir(parents=True)
        (foreign / "theirs.txt").write_text("x\n")
        code, err = run_export(self.root, "--force", "--out", str(foreign))
        self.assertEqual(code, 2)
        self.assertIn("Git checkout this tool did not produce", err)
        self.assertTrue((foreign / "theirs.txt").exists())
        other = self.tmp / "other"
        other.mkdir()
        (other / "mine.txt").write_text("x\n")
        code, err = run_export(self.root, "--force", "--out", str(other))
        self.assertEqual(code, 2)
        self.assertIn("not a previous export", err)
        self.assertTrue((other / "mine.txt").exists())

    def test_a_normal_export_replaces_only_the_previous_export_and_keeps_its_git(self):
        dest = self.root / "dist" / "public"
        (dest / ".git").mkdir(parents=True)
        (dest / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (dest / "EXPORT.json").write_text("{}\n")
        (dest / "stale.md").write_text("old\n")
        (dest / "attest").mkdir()
        (dest / "attest" / "gone.py").write_text("old\n")
        code, err = run_export(self.root, "--out", "dist/public")
        self.assertEqual(code, 2)                                                   # a previous export needs --force
        self.assertTrue((dest / "stale.md").exists())
        code, err = run_export(self.root, "--force", "--out", "dist/public")
        self.assertEqual(code, 0, err)
        self.assertEqual((dest / ".git" / "HEAD").read_text(), "ref: refs/heads/main\n")
        self.assertFalse((dest / "stale.md").exists())
        self.assertFalse((dest / "attest").exists())
        self.assertEqual((dest / "README.md").read_text(), "# project\n")
        record = json.loads((dest / "EXPORT.json").read_text())
        self.assertEqual(record["out"], "dist/public")
        self.assertEqual(sorted(p.name for p in (self.root / "dist").iterdir()), ["public"])   # the staging directory is gone
        self.assertTrue((self.root / "DO_NOT_DELETE.txt").exists())
        fresh = self.tmp / "fresh"
        fresh.mkdir()
        code, err = run_export(self.root, "--out", str(fresh))                      # an empty directory outside the project needs no --force
        self.assertEqual(code, 0, err)
        self.assertTrue((fresh / "EXPORT.json").exists())


if __name__ == "__main__":
    unittest.main()
