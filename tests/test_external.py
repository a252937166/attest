"""Milestone M4: bounded import of external repositories. Offline: synthetic tarballs and local directories only."""

import io
import json
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path

from attest.core import external
from attest.core.external import ImportRefused, LIMITS, extract_tarball, external_policy_problems, import_local, parse_github, require_commit, task_skeleton
from attest.core.task import TaskSpec
from attest.core.workspace import snapshot_repo


def make_tarball(entries: dict[str, bytes], links: dict[str, str] | None = None, top: str = "repo-abc") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
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


class ImportBounds(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-ext-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_github_url_and_commit_are_validated(self):
        self.assertEqual(parse_github("https://github.com/python-semver/python-semver"), ("python-semver", "python-semver"))
        self.assertEqual(parse_github("https://github.com/o/r.git/"), ("o", "r"))
        for bad in ("http://github.com/o/r", "https://gitlab.com/o/r", "https://github.com/o", "git@github.com:o/r.git"):
            with self.assertRaises(ImportRefused):
                parse_github(bad)
        self.assertEqual(require_commit("A" * 40), "a" * 40)
        for bad in ("main", "v3.0.0", "abc123", ""):
            with self.assertRaises(ImportRefused) as cm:
                require_commit(bad)
            self.assertIn("pinned as a full 40-character", str(cm.exception))

    def test_tarball_extraction_copies_regular_files_materializes_in_tree_links_and_skips_the_rest(self):
        data = make_tarball({"src/pkg/__init__.py": b"x = 1\n", "docs/advanced/helper.py": b"h = 2\n", "tests/test_a.py": b"import helper\n",
                             ".git/config": b"nope", "src/__pycache__/x.pyc": b"\x00"},
                            links={"tests/helper.py": "../docs/advanced/helper.py", "tests/outside.py": "../../etc/passwd", "tests/missing.py": "../nope.py"})
        record = extract_tarball(data, self.tmp)
        files = snapshot_repo(self.tmp / "repo")
        self.assertEqual(files["tests/helper.py"], b"h = 2\n")
        self.assertNotIn(".git/config", files)
        self.assertNotIn("src/__pycache__/x.pyc", files)
        self.assertEqual(record["files"] if "files" in record else len(files), len(files))
        self.assertEqual(record["materialized_links"], [{"path": "tests/helper.py", "copied_from": "docs/advanced/helper.py"}])
        skipped = {s["path"] for s in record["skipped"]}
        self.assertIn("tests/outside.py", skipped)
        self.assertIn("tests/missing.py", skipped)
        self.assertFalse(any(p.is_symlink() for p in (self.tmp / "repo").rglob("*")))

    def test_unsafe_member_names_refuse_the_whole_import(self):
        data = make_tarball({"ok.py": b"1", "../escape.py": b"2"})
        with self.assertRaises(ImportRefused) as cm:
            extract_tarball(data, self.tmp)
        self.assertIn("unsafe path", str(cm.exception))
        self.assertFalse((self.tmp / "repo").exists())

    def test_size_and_count_limits_name_the_limit_and_write_nothing(self):
        data = make_tarball({"big.bin": b"x" * (LIMITS["max_file_bytes"] + 1), "a.py": b"1"})
        with self.assertRaises(ImportRefused) as cm:
            extract_tarball(data, self.tmp)
        self.assertIn(f"per-file limit of {LIMITS['max_file_bytes']} bytes", str(cm.exception))
        self.assertFalse((self.tmp / "repo").exists())
        record = extract_tarball(data, self.tmp, max_file_bytes=LIMITS["max_file_bytes"] + 10)  # the task may raise the per-file bound
        self.assertEqual(record["limits"]["max_file_bytes"], LIMITS["max_file_bytes"] + 10)
        shutil.rmtree(self.tmp / "repo")
        many = make_tarball({f"f{i}.py": b"1" for i in range(LIMITS["max_files"] + 1)})
        with self.assertRaises(ImportRefused) as cm:
            extract_tarball(many, self.tmp)
        self.assertIn(f"limit is {LIMITS['max_files']} files", str(cm.exception))

    def test_local_import_applies_the_same_bounds(self):
        src = self.tmp / "src"
        (src / "pkg").mkdir(parents=True)
        (src / "pkg" / "__init__.py").write_text("x = 1\n")
        (src / ".git").mkdir()
        (src / ".git" / "HEAD").write_text("ref")
        record = import_local(src, self.tmp / "dest")
        self.assertEqual(record["files"], 1)
        self.assertEqual(snapshot_repo(self.tmp / "dest" / "repo"), {"pkg/__init__.py": b"x = 1\n"})
        (src / "huge.bin").write_bytes(b"x" * (LIMITS["max_file_bytes"] + 1))
        with self.assertRaises(ImportRefused):
            import_local(src, self.tmp / "dest2")

    def _task(self, **overrides) -> TaskSpec:
        self._n = getattr(self, "_n", 0) + 1
        dest = self.tmp / f"task{self._n}"
        (dest / "repo" / "src" / "pkg").mkdir(parents=True)
        (dest / "repo" / "src" / "pkg" / "__init__.py").write_text("x = 1\n")
        (dest / "repo" / "tests").mkdir()
        (dest / "repo" / "tests" / "test_x.py").write_text("import unittest\n")
        (dest / "repo" / "pyproject.toml").write_text("[project]\nname='pkg'\n")
        source = {"url": "https://github.com/o/r", "commit": "a" * 40, "fetched_at_utc": "now", "files": 3, "total_bytes": 30, "tree_sha256": "0" * 64,
                  "limits": {}}
        body = task_skeleton("ext-1", "External", source, "pytest", ["src/pkg/**"], None, None, "do it", ["works"], ["src"],
                             ["/usr/local/bin/python", "-m", "pip", "install", "--target", "/tmp/deps", "pytest==8.3.3"], "pytest==8.3.3", None, 180, "PR 1")
        body.update(overrides)
        (dest / "task.json").write_text(json.dumps(body))
        return TaskSpec.load(dest / "task.json")

    def test_external_policy_accepts_a_bounded_task_and_names_each_violation(self):
        self.assertEqual(external_policy_problems(self._task()), [])
        problems = external_policy_problems(self._task(allowed_write_globs=["**"], protected_globs=["docs/**"], test_timeout=900, test_runner="nose",
                                                       install_command=["/usr/local/bin/python", "-m", "pip", "install", "--target", "/tmp/deps", "pytest"],
                                                       requirements_lock=None, upstream={"url": "https://github.com/o/r", "commit": "main"}))
        text = "\n".join(problems)
        self.assertIn("whole-repository scope such as '**' is refused", text)
        self.assertIn("must protect the test directory", text)
        self.assertIn("packaging file pyproject.toml exists and must be protected", text)
        self.assertIn("exceeds the limit of 300 s", text)
        self.assertIn("test runner 'nose' is not supported", text)
        self.assertIn("must pin every requirement with ==; unpinned: pytest", text)
        self.assertIn("must record requirements_lock", text)
        self.assertIn("must pin upstream.commit to a full 40-character sha", text)

    def test_skeleton_records_upstream_limits_and_protects_tests_and_packaging_by_default(self):
        task = self._task()
        self.assertEqual(task.upstream["commit"], "a" * 40)
        self.assertIn("tests/**", task.protected_globs)
        self.assertIn("pyproject.toml", task.protected_globs)
        self.assertEqual(task.extra["external"]["max_turns"], LIMITS["max_turns"])
        frozen = task.frozen(snapshot_repo(task.repo_dir))
        self.assertEqual(frozen["upstream"]["url"], "https://github.com/o/r")


class PipelineRefusesOutOfBoundsBeforeSandbox(unittest.TestCase):
    def test_external_task_with_whole_repo_scope_is_refused_before_any_operation(self):
        from attest.core.pipeline import Pipeline
        from attest.ledger import Ledger
        from tests.test_verification import TASK, FakeExecutor, FakeProvider
        tmp = Path(tempfile.mkdtemp(prefix="attest-ext-pipe-"))
        try:
            ledger = Ledger()
            task = TaskSpec.load(TASK)
            task.upstream = {"url": "https://github.com/o/r", "commit": "a" * 40, "reference": "x"}
            task.allowed_write_globs = ["**"]
            executor = FakeExecutor(ledger)
            pipeline = Pipeline(task=task, provider=FakeProvider(ledger), executor=executor, ledger=ledger, out_dir=tmp, max_turns=30, tavily=None)
            self.assertEqual(pipeline.max_turns, LIMITS["max_turns"])  # external tasks are capped
            import contextlib, io as _io
            with contextlib.redirect_stdout(_io.StringIO()):
                bundle = pipeline.run()
            self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
            self.assertIn("refused before any sandbox operation", bundle["verdict"]["reasons"][0])
            self.assertIn("whole-repository scope", bundle["verdict"]["reasons"][0])
            self.assertEqual(executor.operations, [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()


class SandboxTransport(unittest.TestCase):
    """The job travels gzip-compressed; a repository that does not fit one request is chained over retained images."""

    def test_guest_runner_accepts_a_gzip_compressed_job(self):
        import base64, gzip, os, subprocess, sys
        from attest.sandbox.tf_sandboxes import GUEST_RUNNER, MARK_BEGIN, MARK_END, TokenFactorySandboxes
        tmp = Path(tempfile.mkdtemp(prefix="attest-guest-"))
        try:
            target = tmp / "hello.txt"
            job = {"write": {str(target): base64.b64encode(b"hello").decode()}, "delete": [],
                   "steps": [{"name": "cat", "cmd": ["/bin/cat", str(target)], "cwd": str(tmp), "timeout": 10}], "stream_cap_bytes": 65536}
            encoded = TokenFactorySandboxes.encode_job(job)
            self.assertEqual(base64.b64decode(encoded)[:2], b"\x1f\x8b")
            # the API decodes the base64 stdin before the guest sees it: feed the decoded gzip bytes, as the sandbox does
            proc = subprocess.run([sys.executable, "-c", GUEST_RUNNER], input=base64.b64decode(encoded), capture_output=True, timeout=60)
            out = proc.stdout.decode()
            report = json.loads(out[out.index(MARK_BEGIN) + len(MARK_BEGIN):out.rindex(MARK_END)])
            self.assertEqual(report["runner"], "attest-guest/2")
            self.assertEqual(report["steps"][0]["stdout"], "hello")
            # the uncompressed encodings still work: plain JSON (what the API delivered before 17 Oct) and base64 text
            for stdin in (json.dumps(job).encode(), base64.b64encode(json.dumps(job).encode()), encoded.encode()):
                proc = subprocess.run([sys.executable, "-c", GUEST_RUNNER], input=stdin, capture_output=True, timeout=60)
                self.assertIn("hello", proc.stdout.decode())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_checkpoint_is_chained_when_the_repository_exceeds_one_request(self):
        import os
        from attest.ledger import Ledger
        from attest.sandbox import tf_sandboxes
        from attest.sandbox.base import RunResult
        from attest.sandbox.tf_sandboxes import MAX_REQUEST_BYTES, SandboxError, TokenFactorySandboxes
        ex = TokenFactorySandboxes("key", "project", Ledger())
        calls = []

        def fake_execute(image, job, stage, disposable, timeout, networking=False):
            calls.append({"image": image, "files": len(job["write"]), "steps": [s["name"] for s in job["steps"]], "stage": stage,
                          "disposable": disposable, "networking": networking, "bytes": len(TokenFactorySandboxes.encode_job(job))})
            return RunResult(stage=stage, operation_uuid=f"op-{len(calls)}", status="SUCCESS", exit_code=0, timed_out=False, signal=None,
                             duration_s=1.0, image_uuid=image, result_image_uuid=f"img-{len(calls)}")
        ex._execute = fake_execute
        # incompressible content so that 1.2 MB of files need several requests
        files = {f"/tmp/w/blob{i}.bin": os.urandom(60_000) for i in range(20)}
        run = ex.create_checkpoint("base", files, [{"name": "existing", "cmd": ["x"], "cwd": "/tmp/w", "timeout": 10}], stage="checkpoint", timeout=300, networking=True)
        self.assertTrue(run.ok)
        self.assertGreater(len(calls), 1)
        self.assertTrue(all(c["bytes"] <= MAX_REQUEST_BYTES for c in calls))
        self.assertEqual(sum(c["files"] for c in calls), 20)
        self.assertTrue(all(c["steps"] == [] and c["networking"] is False and c["disposable"] is False for c in calls[:-1]))
        self.assertEqual(calls[-1]["steps"], ["existing"])
        self.assertTrue(calls[-1]["networking"])
        self.assertEqual(run.chain, [f"op-{i}" for i in range(1, len(calls))])
        self.assertEqual([c["image"] for c in calls], ["base"] + [f"img-{i}" for i in range(1, len(calls))])
        with self.assertRaises(SandboxError) as cm:
            ex.plan_chunks({"/tmp/w/huge.bin": os.urandom(MAX_REQUEST_BYTES)})
        self.assertIn("exceeds the sandbox request limit", str(cm.exception))
        small = {"/tmp/w/a.py": b"print(1)\n" * 1000}
        self.assertEqual(ex.plan_chunks(small), [small])
