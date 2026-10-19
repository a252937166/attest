"""Sealed-test execution with a trust boundary.

Guest side (both programs are plain stdlib Python shipped as `-c` sources):

* SUPERVISOR never imports the sealed module or candidate code. It reads a root-owned job file that names the test
  modules to run, hashes every module file, discovers the expected test IDs statically from each file's AST, runs ONE
  CHILD PROCESS PER TEST with a timeout, feeds the per-run nonce to each child on stdin only after the child has imported
  the test module, and derives every outcome from facts it owns: exit code, signal, timeout, presence and integrity of
  the child's result delivered over a pipe. It writes the trusted result JSON only after the whole suite ran.
* CHILD imports the test module (candidate code may run here), then reads the nonce, runs exactly one test and writes
  its own result to the pipe; the supervisor cross-checks that result against the exit code and the nonce.
* CANARIES: after the suite, the supervisor runs two tests the verifier injects itself (never a model): one that must
  pass and one that must fail, in a child that first imports the first test module (so candidate code is loaded). A
  candidate that forges every outcome flips the must-fail canary and is caught. A targeted forgery that spares the
  canary is not caught by this check; the mutation gate remains the structural detector for that case.

The same supervisor runs three kinds of suite: the model-sealed acceptance module, the model-written adversarial module,
and (for unittest repositories) the repository's own test modules and the held-out modules, so those gates are bound to
the same evidence (per-test exit codes, nonce, file digests) instead of parsed console text.

Host side binds the verdict to the expected IDs proven red, the module digests and the nonce, and refuses VERIFIED on
any nonzero exit, signal, timeout, missing, incomplete or forged result, or a flipped canary.

Privilege separation (verified on Nebius Sandboxes 2026-10-16): the operation runs as root, the supervisor makes the
suite directory, the job and verifier files and the test module files root-owned and read-only, and runs each test
child under an unprivileged uid (65534). A child therefore CANNOT modify the tests or the verifier program, cannot signal
the supervisor and cannot read its memory. Each child delivers its result over a pipe the supervisor owns (no shared
result file the candidate could write), and the supervisor writes the one trusted aggregate result after the whole
suite ran. If the operation is not root, the supervisor records `privilege_separation: false` and the host binding
refuses VERIFIED.

Order rule (M1.1): nothing that imports candidate code may run before the supervisor in the same sandbox operation.
The repository's own suite and the held-out suite therefore run in their own disposable branches.

Residual risk: a candidate can still forge ITS OWN result from inside its child after the nonce was read (for example
by inspecting frames and writing to the inherited result fd), as long as it spares the canaries. It cannot affect any
other test or the verifier files. The mutation gate and held-out tests are the structural detectors for that case.

Supervisor v6 (17 Oct 2026): the per-test result pipe is drained by a thread while the child runs, and the child keeps a
bounded event log (complete per-outcome counts, at most a few hundred labelled events). Up to v5 the supervisor read the
pipe only after the child had exited, so a child whose report exceeded the pipe buffer (64 KiB on Linux, reached at
roughly 1,000 subtests) blocked on its final write until the per-test timeout killed it, and a correct test was recorded
as TIMEOUT. The 17 Oct dry run's `balanced-brackets` hold (`test_exhaustive_short_bracket_streams`, 9,331 subtests) was
this defect, not an excessive workload: the same module runs in well under a second under v6.

Supervisor v7 (19 Oct 2026, audit finding CORE-04): every test child starts in its own session and process group and
carries a unique environment mark. On a timeout the supervisor kills the whole group, drains the child's pipes for a
bounded grace period only (a descendant that inherited stdout/stderr can no longer stall the supervisor), closes them,
reaps the child, kills any marked process that escaped the group (via /proc, where available) and records the cleanup in
the per-test record; `cleanup_incomplete` at the top level counts the tests whose cleanup could not be completed, and the
host binding refuses VERIFIED when it is nonzero.

Evidence classes (CORE-01/03): `structural_problems` names the binding checks whose failure means the EVIDENCE cannot
be trusted (lost or forged results, a changed module, a crash, lost isolation, an incomplete supervisor), as opposed to a
test that merely failed; `outcome_class` labels every per-test record as green (exit 0 with an `ok` report), red (exit 1
with a FAIL or ERROR report bound to the nonce), timeout (killed by the supervisor itself) or untrusted (anything else).
Only an authentic red counts as a kill or as a corrected test's discrimination; untrusted and timeout records never do.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import posixpath
import secrets

SEALED_FILE = "test_sealed.py"
RESULT_FILE = "sealed_result.json"
JOB_FILE = "_job.json"
CHILD_FILE = "_child.py"
CANARY_FILE = "_attest_canary.py"
CANARY_MODULE = "_attest_canary"
CANARY_PASS_ID = f"{CANARY_MODULE}.Canary.test_must_pass"
CANARY_FAIL_ID = f"{CANARY_MODULE}.Canary.test_must_fail"
SUPERVISOR_VERSION = "attest-sealed-supervisor/7"  # v5: per-test failure_tail; v6: result pipe drained concurrently; v7: process-group kill, bounded cleanup
CLEANUP_GRACE_S = 5.0  # seconds a killed test child's pipes may stay open before the supervisor closes them itself
BAD_OUTCOMES = {"FAIL", "ERROR", "unexpected success", "TIMEOUT", "CRASH", "MISSING_RESULT", "FORGED", "INCOMPLETE", "MISMATCH"}

CANARY_SRC = '''import unittest


class Canary(unittest.TestCase):
    """Injected by the verifier, never by a model: one test that must pass and one that must fail.
    A candidate that forges every outcome flips the second one."""

    def test_must_pass(self):
        self.assertEqual(len("attest"), 6)

    def test_must_fail(self):
        self.assertEqual(len("attest"), 7)
'''

CHILD_SRC = r'''
import contextlib, io, json, os, sys, traceback, unittest
test_id, result_fd, import_module = sys.argv[1:4]
result_fd = int(result_fd)
sys.path[:0] = [p for p in sys.argv[4:] if p]
report = {"test_id": test_id, "nonce": None, "completed": False, "outcome": "ERROR", "events": [], "event_counts": {},
          "events_truncated": False, "error": None}
def write():
    try:
        os.write(result_fd, json.dumps(report).encode("utf-8"))
    except OSError:
        pass
    try:
        os.close(result_fd)
    except OSError:
        pass
RANK = {"ERROR": 4, "FAIL": 4, "unexpected success": 4, "skipped": 1, "expected failure": 1, "ok": 0}
EVENT_CAP = 200  # labelled events kept in the report; counts are always complete (a 9,331-subtest report must not grow past a pipe buffer)
class Recorder(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.outs = []
    def _mark(self, outcome, label=None):
        self.outs.append(outcome)
        report["event_counts"][outcome] = report["event_counts"].get(outcome, 0) + 1
        if outcome != "ok" or len(report["events"]) < EVENT_CAP:
            if len(report["events"]) < 4 * EVENT_CAP:
                report["events"].append({"outcome": outcome, "subtest": (label or "")[:120] if label else label})
            else:
                report["events_truncated"] = True
        else:
            report["events_truncated"] = True
    def addSuccess(self, test): super().addSuccess(test); self._mark("ok")
    def addFailure(self, test, err): super().addFailure(test, err); self._mark("FAIL")
    def addError(self, test, err): super().addError(test, err); self._mark("ERROR")
    def addSkip(self, test, reason): super().addSkip(test, reason); self._mark("skipped")
    def addExpectedFailure(self, test, err): super().addExpectedFailure(test, err); self._mark("expected failure")
    def addUnexpectedSuccess(self, test): super().addUnexpectedSuccess(test); self._mark("unexpected success")
    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        label = subtest._subDescription() if hasattr(subtest, "_subDescription") else str(subtest)
        if err is None:
            self._mark("ok", label)
        else:
            self._mark("FAIL" if issubclass(err[0], test.failureException) else "ERROR", label)
try:
    module = __import__(import_module)
    report["nonce"] = sys.stdin.readline().strip()
    suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
    recorder = Recorder()
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        suite.run(recorder)
    if recorder.testsRun != 1:
        report["outcome"] = "ERROR"
        report["error"] = "expected exactly one test to run, got %d" % recorder.testsRun
    else:
        report["outcome"] = max(recorder.outs, key=lambda o: RANK.get(o, 2)) if recorder.outs else "ERROR"
    report["captured_tail"] = captured.getvalue()[-1500:]
    problems = [text for _, text in list(recorder.failures) + list(recorder.errors)]
    report["failure_tail"] = "\n".join(problems)[-1500:]
except BaseException:
    report["error"] = traceback.format_exc()[-2000:]
    if report["nonce"] is None:
        try:
            report["nonce"] = sys.stdin.readline().strip()
        except Exception:
            pass
report["completed"] = True
write()
sys.exit(0 if report["outcome"] == "ok" else 1)
'''

SUPERVISOR_SRC = r'''
import ast, hashlib, json, os, signal, subprocess, sys, threading, time
result_path, nonce, job_path, per_test_timeout = sys.argv[1:5]
per_test_timeout = float(per_test_timeout)
CLEANUP_GRACE = __CLEANUP_GRACE__
TEST_UID, TEST_GID = 65534, 65534
MARK_VAR = "ATTEST_TEST_MARK"
CANARY_PASS, CANARY_FAIL = "__CANARY_PASS__", "__CANARY_FAIL__"
with open(job_path, "rb") as handle:
    job = json.loads(handle.read().decode("utf-8"))
suite_dir = os.path.dirname(os.path.abspath(job_path))
with open(os.path.join(suite_dir, "_child.py")) as handle:
    child_src = handle.read()
modules = list(job.get("modules") or [])
sys_path = [p for p in (job.get("sys_path") or []) if p]
cwd = job.get("cwd") or suite_dir
harden_dirs = list(job.get("harden") or [suite_dir])
canary = bool(job.get("canary"))
canary_import = job.get("canary_import") or (modules[0]["name"] if modules else None)
def digest(path):
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None
def discover(path, module_name):
    with open(path, "rb") as handle:
        tree = ast.parse(handle.read())
    ids = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                bases.append(base.attr)
            elif isinstance(base, ast.Name):
                bases.append(base.id)
        if not any(b.endswith("TestCase") for b in bases):
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                ids.append("%s.%s.%s" % (module_name, node.name, item.name))
    return ids
# Harden: make the suite directory, the verifier files and every test module root-owned and read-only so the
# unprivileged test child cannot modify them, and make every import-path root (repository, dependency directory,
# suite directory, working directory) a root-owned directory so a child cannot plant sitecustomize.py or a module
# shadowing the standard library for the children that follow. Privilege separation is only possible as root.
HOOK_NAMES = ("sitecustomize.py", "usercustomize.py", "sitecustomize", "usercustomize")
# every root a child interpreter consults at start-up: the job's import path, PYTHONPATH of this process (inherited by
# the children) and the working directory (sys.path[0] for `-c` programs)
import_roots = list(dict.fromkeys(sys_path + [p for p in os.environ.get("PYTHONPATH", "").split(":") if p] + [cwd]))
def startup_hooks():
    found = []
    for root in import_roots:
        for name in HOOK_NAMES:
            if os.path.exists(os.path.join(root, name)):
                found.append(os.path.join(root, name))
    return found
separation = False
if os.getuid() == 0:
    try:
        for root_dir in harden_dirs:
            for base, dirs, files in os.walk(root_dir):
                os.chown(base, 0, 0); os.chmod(base, 0o755)
                for name in files:
                    full = os.path.join(base, name); os.chown(full, 0, 0); os.chmod(full, 0o644)
        for m in modules:
            os.chown(m["path"], 0, 0); os.chmod(m["path"], 0o644)
        for root in import_roots:
            if not os.path.isdir(root):
                os.makedirs(root, exist_ok=True)
            os.chown(root, 0, 0); os.chmod(root, 0o755)
        separation = True
    except Exception:
        separation = False
hooks_before = startup_hooks()
report = {"supervisor": "__SUPERVISOR_VERSION__", "nonce": nonce, "completed": False,
          "privilege_separation": separation, "operation_uid": os.getuid(), "test_uid": TEST_UID if separation else os.getuid(),
          "modules": [], "expected_ids": [], "sealed_sha256_before": None, "sealed_sha256_after": None, "discovery_error": None,
          "tests": [], "canaries": [], "canary_ok": None, "ran": 0, "python": sys.version.split()[0],
          "startup_hooks_before": hooks_before, "startup_hooks_after": None, "import_path": import_roots,
          "cleanup_incomplete": 0, "procfs": os.path.isdir("/proc")}
for m in modules:
    entry = {"name": m["name"], "path": m["path"], "sha256_before": digest(m["path"]), "sha256_after": None,
             "expected_ids": [], "discovery_error": None}
    try:
        entry["expected_ids"] = discover(m["path"], m["name"])
    except Exception as error:
        entry["discovery_error"] = "%s: %s" % (type(error).__name__, str(error)[:300])
    report["modules"].append(entry)
    report["expected_ids"].extend(entry["expected_ids"])
if report["modules"]:
    report["sealed_sha256_before"] = report["modules"][0]["sha256_before"]
report["discovery_error"] = next((m["discovery_error"] for m in report["modules"] if m["discovery_error"]), None)
env = dict(os.environ)
env["PYTHONDONTWRITEBYTECODE"] = "1"
child_kw = {"user": TEST_UID, "group": TEST_GID, "extra_groups": []} if separation else {}
def marked_processes(mark, kill):
    # Processes still carrying this test's environment mark after the group kill: descendants that left the group
    # (setsid) and so survived killpg. Only readable where /proc exists (the Linux guest); killed when asked.
    found = 0
    if not os.path.isdir("/proc"):
        return 0
    needle = ("%s=%s" % (MARK_VAR, mark)).encode()
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        try:
            with open("/proc/%s/environ" % name, "rb") as handle:
                environ = handle.read()
        except OSError:
            continue
        if needle in environ.split(b"\0"):
            found += 1
            if kill:
                try:
                    os.kill(int(name), signal.SIGKILL)
                except OSError:
                    pass
    return found
def run_child(test_id, import_module, mark):
    record = {"id": test_id, "exit_code": None, "signal": None, "timed_out": False, "duration_s": None,
              "child_outcome": None, "nonce_ok": False, "outcome": "MISSING_RESULT", "stderr_tail": "", "cleanup": None}
    read_fd, write_fd = os.pipe()  # child delivers its result here; no shared file the candidate could write
    started = time.monotonic()
    child = None
    chunks = []
    child_env = dict(env)
    child_env[MARK_VAR] = mark  # unique per test child: lets the supervisor find descendants that escaped the process group
    def drain():
        # Read the result concurrently with the child's execution. Supervisor v5 read the pipe only after the child had
        # exited, so a report larger than the pipe buffer (64 KiB on Linux; about 1,000 subtest events) blocked the child
        # on its final write until the per-test timeout killed it and the test was recorded as TIMEOUT. Fixed in v6.
        total = 0
        try:
            while True:
                piece = os.read(read_fd, 65536)
                if not piece:
                    break
                total += len(piece)
                if total <= 4000000:
                    chunks.append(piece)
        except OSError:
            pass
    try:
        # start_new_session: the child is the leader of its own session and process group, so a timeout kills the whole
        # tree the test spawned (killpg) instead of the direct child only; the supervisor's own group is never signalled
        proc = subprocess.Popen([sys.executable, "-c", child_src, test_id, str(write_fd), import_module] + sys_path,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=child_env,
                                pass_fds=(write_fd,), start_new_session=True, **child_kw)
        os.close(write_fd)  # parent keeps only the read end; child's copy closes on exit -> clean EOF
        write_fd = None
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            out, err = proc.communicate(input=(nonce + "\n").encode(), timeout=per_test_timeout)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            cleanup = {"group_killed": False, "grace_exceeded": False, "escaped_killed": 0, "escaped_remaining": None, "complete": False}
            record["cleanup"] = cleanup
            try:
                os.killpg(proc.pid, signal.SIGKILL)
                cleanup["group_killed"] = True
            except OSError:
                try:
                    proc.kill()
                except OSError:
                    pass
            try:
                # bounded: a descendant that inherited the pipes and left the group would otherwise hold communicate() open forever
                out, err = proc.communicate(timeout=CLEANUP_GRACE)
            except subprocess.TimeoutExpired:
                cleanup["grace_exceeded"] = True
                out, err = b"", b""
                for stream in (proc.stdout, proc.stderr, proc.stdin):
                    try:
                        if stream is not None:
                            stream.close()
                    except Exception:
                        pass
                try:
                    proc.wait(timeout=CLEANUP_GRACE)  # the group leader itself is dead; reap it
                except Exception:
                    pass
            cleanup["escaped_killed"] = marked_processes(mark, kill=True)
            remaining = marked_processes(mark, kill=False) if os.path.isdir("/proc") else None
            cleanup["escaped_remaining"] = remaining
            # complete when the pipes closed within the grace period (nothing outlived the group kill) or, where /proc lets
            # us look, when no marked process remains after the escape sweep
            cleanup["complete"] = (not cleanup["grace_exceeded"]) or remaining == 0
            if not cleanup["complete"]:
                report["cleanup_incomplete"] += 1
        reader.join(timeout=10)
        raw = b"".join(chunks)
        record["result_bytes"] = len(raw)
        record["duration_s"] = round(time.monotonic() - started, 3)
        code = proc.returncode
        if code is not None and code < 0:
            record["signal"] = -code
            record["exit_code"] = None
        else:
            record["exit_code"] = code
        record["stderr_tail"] = err.decode("utf-8", "replace")[-800:]
        if raw:
            try:
                child = json.loads(raw.decode("utf-8", "replace"))
            except Exception:
                child = None
    except Exception as error:
        record["stderr_tail"] = "supervisor spawn error: %s" % str(error)[:300]
    finally:
        try:
            if write_fd is not None:
                os.close(write_fd)
        except OSError:
            pass
        try:
            os.close(read_fd)
        except OSError:
            pass
    if child is not None:
        record["child_outcome"] = child.get("outcome")
        record["nonce_ok"] = child.get("nonce") == nonce and child.get("test_id") == test_id and child.get("completed") is True
        record["captured_tail"] = (child.get("captured_tail") or child.get("error") or "")[-1200:]
        record["failure_tail"] = (child.get("failure_tail") or "")[-1200:]
    if record["timed_out"]:
        record["outcome"] = "TIMEOUT"
    elif record["signal"] is not None:
        record["outcome"] = "CRASH"
    elif child is None:
        record["outcome"] = "MISSING_RESULT"
    elif not record["nonce_ok"]:
        record["outcome"] = "FORGED"
    elif record["exit_code"] == 0 and child.get("outcome") == "ok":
        record["outcome"] = "ok"
    elif record["exit_code"] == 0 and child.get("outcome") != "ok":
        record["outcome"] = "MISMATCH"
    else:
        record["outcome"] = child.get("outcome") if child.get("outcome") in ("FAIL", "ERROR", "skipped", "expected failure", "unexpected success") else "ERROR"
    return record
mark_seq = 0
for m in report["modules"]:
    for test_id in m["expected_ids"]:
        mark_seq += 1
        report["tests"].append(run_child(test_id, m["name"], "%s-%d" % (nonce[:12], mark_seq)))
if canary and canary_import:
    for canary_id in (CANARY_PASS, CANARY_FAIL):
        mark_seq += 1
        report["canaries"].append(run_child(canary_id, canary_import, "%s-%d" % (nonce[:12], mark_seq)))
    by_id = {c["id"]: c for c in report["canaries"]}
    must_pass, must_fail = by_id.get(CANARY_PASS), by_id.get(CANARY_FAIL)
    report["canary_ok"] = bool(must_pass and must_fail and must_pass["outcome"] == "ok"
                               and must_fail["outcome"] == "FAIL" and must_fail["exit_code"] == 1)
report["ran"] = len(report["tests"])
report["startup_hooks_after"] = startup_hooks()
for m in report["modules"]:
    m["sha256_after"] = digest(m["path"])
if report["modules"]:
    report["sealed_sha256_after"] = report["modules"][0]["sha256_after"]
report["completed"] = True
tmp = result_path + ".tmp"
with open(tmp, "w") as handle:
    json.dump(report, handle)
os.replace(tmp, result_path)
print("SEALED-RESULT-WRITTEN")
ok = bool(report["tests"]) and all(t["outcome"] == "ok" for t in report["tests"]) and report["canary_ok"] is not False
sys.exit(0 if ok else 1)
'''.replace("__CANARY_PASS__", CANARY_PASS_ID).replace("__CANARY_FAIL__", CANARY_FAIL_ID).replace("__SUPERVISOR_VERSION__", SUPERVISOR_VERSION).replace("__CLEANUP_GRACE__", repr(CLEANUP_GRACE_S))

PRINT_RESULT_SRC = "import sys; sys.stdout.write(open(sys.argv[1], encoding='utf-8').read())"


def new_nonce() -> str:
    return secrets.token_hex(16)


def repair_escapes(source: str) -> tuple[str, bool]:
    """Undo one level of JSON escaping some models apply to code strings (literal \\n instead of newlines)."""
    if "\n" in source or "\\n" not in source:
        return source, False
    repaired = source.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
    return repaired, True


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def static_test_ids(source: str | bytes, module_name: str = "test_sealed") -> list[str]:
    """Host-side mirror of the supervisor's static discovery (no execution)."""
    tree = ast.parse(source)
    ids = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "") for b in node.bases]
        if not any(str(b).endswith("TestCase") for b in bases):
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                ids.append(f"{module_name}.{node.name}.{item.name}")
    return ids


# ----------------------------------------------------------------------------------------------- guest job files
def suite_job(modules: list[dict], sys_path: list[str], cwd: str, harden: list[str], canary: bool,
              canary_import: str | None) -> dict:
    """The root-owned job the supervisor reads: which module files to run, the child import path, and the canary."""
    return {"modules": [{"name": m["name"], "path": m["path"]} for m in modules], "sys_path": list(sys_path), "cwd": cwd,
            "harden": list(harden), "canary": bool(canary), "canary_import": canary_import}


def _verifier_files(suite_dir: str, job: dict) -> dict[str, bytes]:
    return {f"{suite_dir}/{CHILD_FILE}": CHILD_SRC.encode("utf-8"),
            f"{suite_dir}/{CANARY_FILE}": CANARY_SRC.encode("utf-8"),
            f"{suite_dir}/{JOB_FILE}": (json.dumps(job, indent=1) + "\n").encode("utf-8")}


def guest_files_for(sealed_dir: str, module_name: str, source: str, repo_dir: str = "/tmp/w",
                    extra_paths: list[str] | tuple[str, ...] = (), canary: bool = True) -> dict[str, bytes]:
    """Files the supervisor needs in the guest for one model-written module: the module, the child program, the
    canary module and the job. The child import path is repo, extra paths (dependencies), then the suite directory."""
    module_path = f"{sealed_dir}/{module_name}.py"
    job = suite_job([{"name": module_name, "path": module_path}], [repo_dir, *extra_paths, sealed_dir], repo_dir,
                    [sealed_dir], canary, module_name)
    files = {module_path: source.encode("utf-8")}
    files.update(_verifier_files(sealed_dir, job))
    return files


def repo_suite_files(suite_dir: str, modules: list[dict], repo_dir: str = "/tmp/w",
                     extra_paths: list[str] | tuple[str, ...] = (), canary: bool = True,
                     canary_import: str | None = None) -> dict[str, bytes]:
    """Verifier files for running test modules that already live in the repository (the repository's own suite or
    injected held-out modules) through the supervisor. `modules` items carry `name` (dotted) and `path` (guest)."""
    job = suite_job(modules, [repo_dir, *extra_paths, suite_dir], repo_dir, [suite_dir], canary,
                    canary_import or (modules[0]["name"] if modules else None))
    return _verifier_files(suite_dir, job)


def sealed_steps(python: str, repo_dir: str, sealed_dir: str, nonce: str, extra_paths: list[str] | None = None,
                 env: dict | None = None, timeout: int = 180, module_name: str = "test_sealed", per_test_timeout: int = 60,
                 step_prefix: str = "sealed") -> list[dict]:
    """The two guest steps: the supervisor (reads `{sealed_dir}/_job.json`) and a step that prints its result file.
    `extra_paths` and `module_name` are accepted for compatibility; both now travel in the job file."""
    del extra_paths, module_name
    result_path = f"{sealed_dir}/{RESULT_FILE}"
    job_path = f"{sealed_dir}/{JOB_FILE}"
    return [
        {"name": step_prefix, "cmd": [python, "-c", SUPERVISOR_SRC, result_path, nonce, job_path, str(per_test_timeout)],
         "cwd": repo_dir, "timeout": timeout, "env": env or {}},
        {"name": f"{step_prefix}_result", "cmd": [python, "-c", PRINT_RESULT_SRC, result_path], "cwd": repo_dir, "timeout": 20},
    ]


def is_supervisor_step(step: dict) -> bool:
    cmd = step.get("cmd") or []
    return len(cmd) >= 3 and cmd[1] == "-c" and SUPERVISOR_VERSION in cmd[2]


# ----------------------------------------------------------------------------------------------- repository suites
def unittest_discover_args(test_command: list[str]) -> dict | None:
    """Recognise `python -m unittest discover [-s START] [-t TOP] [-p PATTERN] [-v]` (or bare `python -m unittest -v`)
    and return its start, top and pattern; None when the command is anything else (pytest, explicit module names)."""
    cmd = list(test_command or [])
    if "-m" not in cmd or cmd[cmd.index("-m") + 1:cmd.index("-m") + 2] != ["unittest"]:
        return None
    rest = cmd[cmd.index("-m") + 2:]
    start, top, pattern = None, None, "test*.py"
    if rest[:1] == ["discover"]:
        rest = rest[1:]
    positional = []
    index = 0
    while index < len(rest):
        item = rest[index]
        if item in ("-s", "--start-directory", "-t", "--top-level-directory", "-p", "--pattern"):
            if index + 1 >= len(rest):
                return None
            value = rest[index + 1]
            if item in ("-s", "--start-directory"):
                start = value
            elif item in ("-t", "--top-level-directory"):
                top = value
            else:
                pattern = value
            index += 2
            continue
        if item.startswith("-"):
            index += 1
            continue
        positional.append(item)
        index += 1
    if positional:
        return None  # explicit module or test names: not a discovery run
    start = start or "."
    top = top or start
    return {"start": start, "top": top, "pattern": pattern}


def _norm(rel: str) -> str:
    rel = posixpath.normpath(rel.replace("\\", "/"))
    return "" if rel in (".", "/") else rel.strip("/")


def static_repo_tests(snapshot: dict[str, bytes], test_command: list[str]) -> dict | None:
    """Statically enumerate the unittest modules a discovery command would load from the frozen snapshot, with their
    digests and test IDs. Mirrors unittest discovery closely enough for plain repositories: files matching the pattern
    under the start directory, descending only into packages (directories with `__init__.py`). Returns None when the
    command is not a unittest discovery run."""
    args = unittest_discover_args(test_command)
    if args is None:
        return None
    start, top, pattern = _norm(args["start"]), _norm(args["top"]), args["pattern"]
    if top and not (start == top or start.startswith(top + "/")):
        return None

    def is_package(rel: str) -> bool:
        return rel == "" or f"{rel}/__init__.py" in snapshot

    modules = []
    for rel in sorted(snapshot):
        parent = posixpath.dirname(rel)
        if start and not (parent == start or parent.startswith(start + "/")):
            continue
        name = posixpath.basename(rel)
        if not fnmatch.fnmatch(name, pattern) or not name.endswith(".py"):
            continue
        # every directory from top (exclusive) down to the file's directory must be a package
        if top:
            if not (parent == top or parent.startswith(top + "/")):
                continue
            relative_dir = parent[len(top):].strip("/")
        else:
            relative_dir = parent
        parts = [p for p in relative_dir.split("/") if p]
        ok = True
        for depth in range(1, len(parts) + 1):
            pkg = "/".join(parts[:depth])
            pkg_abs = f"{top}/{pkg}" if top else pkg
            if not is_package(pkg_abs):
                ok = False
                break
        if not ok:
            continue
        module_name = ".".join(parts + [name[:-3]])
        source = snapshot[rel]
        try:
            ids = static_test_ids(source, module_name)
        except SyntaxError:
            ids = []
        modules.append({"name": module_name, "rel": rel, "sha256": sha256_bytes(source), "ids": ids})
    return {"start": start or ".", "top": top or ".", "pattern": pattern, "modules": modules,
            "ids": [i for m in modules for i in m["ids"]]}


def module_name_for(rel_path: str, top: str) -> str | None:
    rel, top = _norm(rel_path), _norm(top)
    if not rel.endswith(".py"):
        return None
    if top:
        if not rel.startswith(top + "/"):
            return None
        rel = rel[len(top) + 1:]
    return rel[:-3].replace("/", ".")


# ----------------------------------------------------------------------------------------------- host-side reading
def read_sealed_result(run, step_prefix: str = "sealed") -> dict | None:
    step = run.step(f"{step_prefix}_result")
    if run.runner_error or step is None or step.exit_code != 0 or not step.stdout.strip():
        return None
    try:
        data = json.loads(step.stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and data.get("supervisor") else None


def summarize(result: dict | None) -> dict:
    if not result:
        return {"ran": 0, "tests": [], "passed": 0, "failing": 0, "subtest_events": 0, "import_error": None,
                "all_passed": False, "canary_ok": None, "summary_line": "no trusted sealed result (supervisor did not complete)"}
    tests = result.get("tests") or []
    passed = sum(1 for t in tests if t.get("outcome") == "ok")
    failing = sum(1 for t in tests if t.get("outcome") in BAD_OUTCOMES)
    ran = len(tests)
    discovery_error = result.get("discovery_error")
    ok = result.get("completed") is True and not discovery_error and ran > 0 and failing == 0
    if discovery_error:
        line = f"sealed module could not be parsed: {discovery_error}"
    elif failing:
        kinds = {}
        for t in tests:
            if t.get("outcome") in BAD_OUTCOMES:
                kinds[t["outcome"]] = kinds.get(t["outcome"], 0) + 1
        line = f"FAILED ({failing} of {ran} methods: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + ")"
    else:
        line = f"OK ({passed} of {ran} methods, each in its own process)"
    if result.get("canary_ok") is False:
        line += "; CANARY FLIPPED (results in the test process were forged)"
    return {"ran": ran, "tests": [{"id": t["id"], "outcome": t["outcome"], "events": 1, "exit_code": t.get("exit_code"),
                                   "signal": t.get("signal"), "timed_out": t.get("timed_out"), "duration_s": t.get("duration_s"),
                                   "captured_tail": (t.get("captured_tail") or "")[:1200],
                                   "failure_tail": (t.get("failure_tail") or "")[:1200]} for t in tests],
            "passed": passed, "failing": failing, "subtest_events": 0, "import_error": discovery_error,
            "all_passed": ok, "canary_ok": result.get("canary_ok"), "summary_line": line}


# Binding checks whose failure is a test outcome the supervisor itself recorded (a test failed, so its child exited 1, or it
# was killed at the per-test timeout), not a reason to distrust the record. Every other failing check is structural.
STRUCTURAL_EXCUSED = ("all_expected_pass", "no_nonzero_exit", "no_timeout")


def structural_problems(binding: dict | None, result: dict | None) -> list[str]:
    """Names of the binding checks whose failure means the execution evidence cannot be trusted: lost, forged, mismatched or
    incomplete results, a changed module, a crash, lost isolation, an unfinished cleanup, a start-up hook, a flipped canary.
    Plain test failures and supervisor-observed timeouts are excused (they are the evidence, not a defect of it); a signal is
    excused only when every signalled test is one the supervisor killed at its timeout."""
    if not binding or not result:
        return ["result_file_present"]
    checks = binding.get("checks") or {}
    problems = [name for name, ok in checks.items() if not ok and name not in STRUCTURAL_EXCUSED]
    tests = list(result.get("tests") or []) + list(result.get("canaries") or [])
    if "no_signal" in problems and all(t.get("timed_out") for t in tests if t.get("signal") is not None):
        problems.remove("no_signal")
    return problems


def outcome_class(test: dict) -> str:
    """green: exit 0 with an `ok` report bound to the nonce; red: exit 1 with a FAIL or ERROR report bound to the nonce (the
    child ran the test and reported a failure consistent with its exit); timeout: killed by the supervisor at the per-test
    budget; untrusted: everything else (missing, forged, mismatched or incomplete report, crash, skipped)."""
    if test.get("timed_out") or test.get("outcome") == "TIMEOUT":
        return "timeout"
    if test.get("signal") is not None or test.get("nonce_ok") is False:
        return "untrusted"
    if test.get("exit_code") == 0 and test.get("outcome") == "ok":
        return "green"
    if test.get("exit_code") == 1 and test.get("outcome") in ("FAIL", "ERROR"):
        return "red"
    return "untrusted"


def outcome_classes(result: dict | None) -> dict[str, str]:
    return {t.get("id"): outcome_class(t) for t in ((result or {}).get("tests") or [])}


def _bind_tests(result: dict, expected_ids: list[str], nonce: str, canary: bool, checks: dict, reasons: list[str]) -> None:
    """Checks shared by every supervisor run: completion, isolation, nonce, id sets, per-test facts and canaries."""
    tests = result.get("tests") or []
    observed = [t.get("id") for t in tests]
    expected = set(expected_ids)
    checks["supervisor_completed"] = result.get("completed") is True
    # isolation must be recorded as active in so many words: a result without the field is not evidence of isolation (CORE-06)
    checks["verifier_isolation_active"] = result.get("privilege_separation") is True
    checks["supervisor_cleanup_complete"] = not result.get("cleanup_incomplete")
    checks["nonce_matches"] = result.get("nonce") == nonce
    checks["no_discovery_error"] = not result.get("discovery_error")
    checks["expected_test_ids_present"] = set(observed) >= expected
    checks["no_unexpected_test_ids"] = set(observed) <= expected
    checks["no_nonzero_exit"] = all(t.get("exit_code") == 0 for t in tests)
    checks["no_signal"] = all(t.get("signal") is None for t in tests)
    checks["no_timeout"] = not any(t.get("timed_out") for t in tests)
    checks["no_missing_or_forged_result"] = not any(t.get("outcome") in ("MISSING_RESULT", "FORGED", "INCOMPLETE", "MISMATCH") for t in tests)
    checks["all_expected_pass"] = bool(expected) and all(t.get("outcome") == "ok" for t in tests if t.get("id") in expected)
    hooks = list(result.get("startup_hooks_before") or []) + list(result.get("startup_hooks_after") or [])
    checks["no_startup_hooks_on_import_path"] = not hooks
    if canary:
        canaries = {c.get("id"): c for c in (result.get("canaries") or [])}
        must_pass, must_fail = canaries.get(CANARY_PASS_ID), canaries.get(CANARY_FAIL_ID)
        checks["canary_must_pass_ok"] = bool(must_pass) and must_pass.get("outcome") == "ok"
        checks["canary_must_fail_failed"] = bool(must_fail) and must_fail.get("outcome") == "FAIL" and must_fail.get("exit_code") == 1
    if not checks["supervisor_completed"]:
        reasons.append("sealed supervisor did not record completion")
    if not checks["verifier_isolation_active"]:
        reasons.append("verifier privilege separation was not recorded as active: the sandbox operation did not run as root (or the result does not say), "
                       "so the sealed tests could not be protected from the candidate process; re-run on a root-capable sandbox")
    if not checks["supervisor_cleanup_complete"]:
        reasons.append(f"the supervisor could not complete the cleanup of {result.get('cleanup_incomplete')} timed-out test child(ren) "
                       "(descendants kept running after the process group was killed); the result is not trusted")
    if not checks["nonce_matches"]:
        reasons.append("sealed result nonce does not match this run (stale or forged result file)")
    if not checks["no_discovery_error"]:
        reasons.append(f"sealed module could not be parsed statically: {result.get('discovery_error')}")
    if not checks["expected_test_ids_present"]:
        reasons.append("expected test IDs missing from the verification result: " + ", ".join(sorted(expected - set(observed)))[:300])
    if not checks["no_unexpected_test_ids"]:
        reasons.append("unexpected test IDs appeared in the verification result: " + ", ".join(sorted(set(observed) - expected))[:300])
    if not checks["no_nonzero_exit"]:
        bad = [f"{t['id'].split('.')[-1]} exit {t.get('exit_code')}" for t in tests if t.get("exit_code") != 0]
        reasons.append("child process nonzero exit: " + ", ".join(bad)[:300])
    if not checks["no_signal"]:
        reasons.append("child process killed by signal: " + ", ".join(f"{t['id'].split('.')[-1]} sig {t.get('signal')}" for t in tests if t.get("signal") is not None)[:300])
    if not checks["no_timeout"]:
        reasons.append("child process timed out: " + ", ".join(t["id"].split(".")[-1] for t in tests if t.get("timed_out"))[:300])
    if not checks["no_missing_or_forged_result"]:
        reasons.append("missing, forged or inconsistent child results: " + ", ".join(f"{t['id'].split('.')[-1]} {t['outcome']}" for t in tests if t.get("outcome") in ("MISSING_RESULT", "FORGED", "INCOMPLETE", "MISMATCH"))[:300])
    if not checks["no_startup_hooks_on_import_path"]:
        reasons.append("interpreter start-up hook on the test import path (sitecustomize/usercustomize): "
                       + ", ".join(sorted(set(hooks)))[:300] + "; candidate code could run in every test process before the nonce was read")
    if canary and not (checks["canary_must_pass_ok"] and checks["canary_must_fail_failed"]):
        if not (result.get("canaries") or []):
            reasons.append("verifier canaries did not run (supervisor job without canaries); results cannot be trusted as unforged")
        elif not checks["canary_must_fail_failed"]:
            reasons.append("verifier canary flipped: a test that must fail was reported as passing, so outcomes in the test "
                           "process were forged by candidate code; the run is recorded as tampered")
        else:
            reasons.append("verifier canary that must pass did not pass (the test process is broken or tampered)")
    if not checks["all_expected_pass"] and checks["no_missing_or_forged_result"] and checks["no_nonzero_exit"]:
        failing = [t["id"] for t in tests if t.get("outcome") != "ok"]
        reasons.append(f"sealed tests failed on the candidate: {len(failing)} ({', '.join(failing)[:300]})")
    elif not checks["all_expected_pass"] and not any("sealed tests failed" in r for r in reasons):
        failing = [t["id"] for t in tests if t.get("outcome") not in ("ok",)]
        if failing and not reasons:
            reasons.append(f"sealed tests failed on the candidate: {len(failing)}")


def bind_verification(result: dict | None, expected_ids: list[str], expected_sha256: str, nonce: str,
                      canary: bool = True) -> dict:
    """Bind a single-module verification result (the sealed or adversarial suite) to the module proven red. Every check
    is recorded; any failure blocks VERIFIED. With `canary`, the supervisor must also have run both verifier canaries."""
    checks: dict[str, bool] = {}
    reasons: list[str] = []
    if not result:
        checks["result_file_present"] = False
        reasons.append("no trusted sealed result: the supervisor did not write results (premature exit, crash or runner failure)")
        return {"ok": False, "checks": checks, "reasons": reasons}
    checks["result_file_present"] = True
    checks["sealed_file_unchanged_before"] = result.get("sealed_sha256_before") == expected_sha256
    checks["sealed_file_unchanged_after"] = result.get("sealed_sha256_after") == expected_sha256
    checks["static_ids_match_red"] = set(result.get("expected_ids") or []) == set(expected_ids)
    if not (checks["sealed_file_unchanged_before"] and checks["sealed_file_unchanged_after"]):
        reasons.append("sealed test file digest changed (integrity check failed)")
    if not checks["static_ids_match_red"]:
        reasons.append("statically discovered test IDs differ from the red check (sealed module changed)")
    _bind_tests(result, expected_ids, nonce, canary, checks, reasons)
    return {"ok": not reasons, "checks": checks, "reasons": reasons}


def bind_modules(result: dict | None, expected_modules: list[dict], nonce: str, canary: bool = True) -> dict:
    """Bind a multi-module supervisor result (the repository's own suite or held-out modules) to the frozen module
    digests and statically expected IDs. `expected_modules` items carry `name`, `sha256` and `ids`."""
    checks: dict[str, bool] = {}
    reasons: list[str] = []
    if not result:
        checks["result_file_present"] = False
        reasons.append("no trusted suite result: the supervisor did not write results (premature exit, crash or runner failure)")
        return {"ok": False, "checks": checks, "reasons": reasons}
    checks["result_file_present"] = True
    reported = {m.get("name"): m for m in (result.get("modules") or [])}
    expected_names = {m["name"] for m in expected_modules}
    checks["module_set_matches"] = set(reported) == expected_names
    checks["module_digests_unchanged"] = all(
        (reported.get(m["name"]) or {}).get("sha256_before") == m["sha256"] and (reported.get(m["name"]) or {}).get("sha256_after") == m["sha256"]
        for m in expected_modules)
    expected_ids = [i for m in expected_modules for i in m["ids"]]
    checks["static_ids_match_expected"] = set(result.get("expected_ids") or []) == set(expected_ids)
    if not checks["module_set_matches"]:
        reasons.append("the supervisor ran a different set of test modules than the frozen task names: "
                       + ", ".join(sorted(set(reported) ^ expected_names))[:300])
    if not checks["module_digests_unchanged"]:
        changed = [m["name"] for m in expected_modules if (reported.get(m["name"]) or {}).get("sha256_before") != m["sha256"]
                   or (reported.get(m["name"]) or {}).get("sha256_after") != m["sha256"]]
        reasons.append("test module digest changed (integrity check failed): " + ", ".join(changed)[:300])
    if not checks["static_ids_match_expected"]:
        reasons.append("statically discovered test IDs differ from the frozen snapshot (test modules changed)")
    _bind_tests(result, expected_ids, nonce, canary, checks, reasons)
    reasons = [r.replace("sealed tests failed on the candidate", "tests failed on the candidate") for r in reasons]
    return {"ok": not reasons, "checks": checks, "reasons": reasons}
