#!/usr/bin/env python3
"""Reproduce the failures named in the revision-9 instruction (20 Oct 2026) against one checkout of the code.

Offline and self-contained: provider credentials are removed from the environment, HOME points to an empty directory (so no private
configuration is found), and every network connection or name lookup that is not on the loopback interface is refused inside this
process and counted. Run it against the code before the repair (every defect should show) and after it (none should):

    repro_revision9.py --code <checkout> [--json OUT]

Each scenario prints what it checks, what it observed and PASS (the required behaviour) or FAIL (the defect). The fakes come from the
checkout's own tests (tests/test_verification.py), so the same script runs on both versions.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path
from unittest import mock

HOME = Path(tempfile.mkdtemp(prefix="attest-repro-home-"))
for name in ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY", "ATTEST_CODEX_BASE_URL", "ATTEST_EXPORT_PRIVATE_HOSTS", "NEBIUS_PROJECT_ID",
             "NEBIUS_AI_PROJECT", "ATTEST_SECRETS_NOTES", "HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(name, None)
os.environ["HOME"] = str(HOME)
os.environ["ATTEST_SECRETS_NOTES"] = str(HOME / "no-notes.json")
os.environ["NO_PROXY"] = "*"

# ----------------------------------------------------------------------------- network guard
NETWORK_ATTEMPTS: list[str] = []
_real_getaddrinfo = socket.getaddrinfo
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
LOCAL = {"127.0.0.1", "localhost", "::1"}


def _guard_getaddrinfo(host, *args, **kwargs):
    if host not in LOCAL and host is not None:
        NETWORK_ATTEMPTS.append("name lookup outside the loopback interface")
        raise socket.gaierror(socket.EAI_NONAME, "blocked by the reproduction's network guard")
    return _real_getaddrinfo(host, *args, **kwargs)


def _target_host(address):
    return address[0] if isinstance(address, tuple) else None


def _guard_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and _target_host(address) not in LOCAL:
        NETWORK_ATTEMPTS.append("connection outside the loopback interface")
        raise ConnectionRefusedError(errno.ECONNREFUSED, "blocked by the reproduction's network guard")
    return _real_connect(self, address)


def _guard_connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and _target_host(address) not in LOCAL:
        NETWORK_ATTEMPTS.append("connection outside the loopback interface")
        return errno.ECONNREFUSED
    return _real_connect_ex(self, address)


socket.getaddrinfo = _guard_getaddrinfo
socket.socket.connect = _guard_connect
socket.socket.connect_ex = _guard_connect_ex

RESULTS: list[dict] = []


def record(group, name, check, observed, ok):
    RESULTS.append({"group": group, "scenario": name, "check": check, "observed": observed, "result": "PASS" if ok else "FAIL"})


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args, **kwargs)


# ----------------------------------------------------------------------------- group A: an uncertain Sandbox failure at each pipeline stage
class Requests:
    """Every model call and every sandbox request of one run, in order; `stop` is the index of the injected uncertain failure."""

    def __init__(self):
        self.items: list[tuple[str, str]] = []
        self.stop: int | None = None
        self.lock = threading.Lock()

    def add(self, kind, stage):
        with self.lock:
            self.items.append((kind, stage))
            return len(self.items) - 1

    def after_stop(self):
        return [] if self.stop is None else self.items[self.stop + 1:]


def stage_scenarios():
    return [
        ("checkpoint", "honest", lambda s: s == "checkpoint", {}),
        ("contract-audit witness", "contract_claim_unproven", lambda s: s.startswith("witness-"), {}),
        ("red check", "honest", lambda s: s == "red-1", {}),
        ("implementer run_tests", "honest", lambda s: s.startswith("impl-tests-"), {"inject": True}),
        ("implementer run_python", "honest", lambda s: s.startswith("impl-python-"), {"inject": True}),
        ("verification", "honest", lambda s: s == "verify", {}),
        ("repository suite", "honest", lambda s: s == "existing", {}),
        ("held-out suite", "honest", lambda s: s == "heldout", {"heldout": True}),
        ("mutant", "honest", lambda s: s.startswith("mutant-"), {}),
        ("breaker (adversarial tests)", "honest", lambda s: s == "breaker-tests", {}),
        ("breaker, accepted but unread", "honest", lambda s: s == "breaker-tests", {"accepted_unread": True}),
        ("arbitration candidate re-run", "arb_clear", lambda s: s == "arbitrate-adversarial-candidate", {}),
        ("arbitration base re-run", "arb_clear", lambda s: s == "arbitrate-adversarial-base", {}),
        ("arbitration mutant re-run", "arb_refactor", lambda s: s.startswith("arbitrate-adversarial-") and not s.endswith(("-candidate", "-base")), {}),
        ("sealed arbitration re-run", "sealed_one_timeout", lambda s: s == "arbitrate-sealed-candidate", {}),
    ]


def build_wrappers(Fakes, SandboxError, ModelResult):
    FakeProvider, FakeExecutor = Fakes

    class RecordingProvider:
        def __init__(self, inner, requests, inject):
            self.inner, self.requests, self.inject = inner, requests, inject
            self.name = inner.name
            self.ledger = inner.ledger

        def describe(self):
            return self.inner.describe()

        def structured(self, role, prompt, schema, stage):
            self.requests.add("model", stage)
            result = self.inner.structured(role, prompt, schema, stage)
            if self.inject and role == "implement" and stage in ("implement-2", "implement-3"):
                action = {"action": "run_tests" if stage == "implement-2" else "run_python", "path": None, "content": None, "find": None, "replace": None,
                          "start_line": None, "end_line": None, "code": None if stage == "implement-2" else "print(1)", "reason": "check", "summary": None}
                return ModelResult(json=action, text=None, call=result.call)
            return result

    class FailingExecutor(FakeExecutor):
        def __init__(self, ledger, scenario, requests, predicate, accepted_unread):
            super().__init__(ledger, scenario)
            self.requests, self.predicate, self.accepted_unread, self.raised = requests, predicate, accepted_unread, False

        def _maybe_fail(self, stage):
            index = self.requests.add("sandbox", stage)
            if not self.raised and self.predicate(stage):
                self.raised = True
                self.requests.stop = index
                if self.accepted_unread:
                    raise SandboxError(f"operation op-unread was accepted but its outcome could not be read (TimeoutError); reconcile with "
                                       f"GET /operations/op-unread; not replayed", accepted_unread=True, operation_uuid="op-unread")
                raise SandboxError("spawn outcome uncertain (RemoteDisconnected: Remote end closed connection without response); inspect account "
                                   "operations, do not replay", uncertain=True)

        def resolve_image(self, tag):
            self.requests.add("sandbox", "resolve_image")
            return super().resolve_image(tag)

        def create_checkpoint(self, image, files, steps, stage, timeout=120, networking=False):
            self._maybe_fail(stage)
            return super().create_checkpoint(image, files, steps, stage, timeout, networking)

        def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
            self._maybe_fail(stage)
            return super().run_branch(image, files, steps, stage, deletes, timeout, networking)

    return RecordingProvider, FailingExecutor


def run_stage(label, scenario, predicate, options, modules):
    tv, Pipeline, TaskSpec, Ledger, SandboxError, ModelResult = modules
    RecordingProvider, FailingExecutor = build_wrappers((tv.FakeProvider, tv.FakeExecutor), SandboxError, ModelResult)
    tmp = Path(tempfile.mkdtemp(prefix="attest-repro-"))
    try:
        ledger = Ledger()
        requests = Requests()
        task = TaskSpec.load(tv.TASK)
        if options.get("heldout"):
            task.heldout_tests = {"tests/test_heldout.py": tv.HELDOUT_SRC}
        provider = RecordingProvider(tv.FakeProvider(ledger, scenario), requests, options.get("inject"))
        executor = FailingExecutor(ledger, scenario, requests, predicate, options.get("accepted_unread"))
        pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=tmp, max_turns=6, max_mutants=6, mutant_workers=1,
                            tavily=None, profile_label="repro")
        raised = None
        try:
            bundle = quiet(pipeline.run)
        except Exception as error:  # noqa: BLE001 - the old pipeline re-raises after writing its bundle
            raised = type(error).__name__
            bundle = json.loads((pipeline.out_dir / "proof_bundle.json").read_text(encoding="utf-8"))
        if requests.stop is None:
            record("A stages", label, "the injected failure is reached", "the stage never ran", False)
            return
        after = requests.after_stop()
        recon = bundle.get("reconciliation") or {}
        reasons = " ".join(bundle.get("verdict", {}).get("reasons") or [])
        rerun = [r for r in (bundle.get("verdict", {}).get("reasons") or []) if "rerun" in r.lower() or "re-run the" in r.lower()]
        record("A stages", label, "no model call or sandbox request after the uncertain operation",
               f"{len(after)} after it: " + (", ".join(f"{k}:{s}" for k, s in after[:6]) + (" ..." if len(after) > 6 else "") if after else "none"),
               not after)
        record("A stages", label, "the bundle requires reconciliation (structured) and names the operation",
               f"verdict {bundle['verdict']['verdict']}; reconciliation.required={recon.get('required')}; items={len(recon.get('items') or [])}"
               + (f"; run() raised {raised}" if raised else ""),
               bool(recon.get("required")) and bool(recon.get("items")) and bundle["verdict"]["verdict"] == "ERROR")
        record("A stages", label, "no reason recommends re-running the stage", f"{len(rerun)} such reason(s)" + (f": {rerun[0][:90]}" if rerun else ""), not rerun)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------------- group B: the evaluation harness and the console worker
def harness_module(code):
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_evaluation_repro", code / "scripts" / "run_evaluation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def harness_judge_after_stop(code, modules):
    tv, Pipeline, TaskSpec, Ledger, SandboxError, ModelResult = modules
    RecordingProvider, FailingExecutor = build_wrappers((tv.FakeProvider, tv.FakeExecutor), SandboxError, ModelResult)
    harness = harness_module(code)
    tmp = Path(tempfile.mkdtemp(prefix="attest-repro-harness-"))
    try:
        requests = Requests()
        (tmp / "heldout.py").write_text(tv.HELDOUT_SRC, encoding="utf-8")
        cell = {"task": "durationkit-units-001", "system": "attest", "attempt": 1, "task_path": str(tv.TASK), "heldout": str(tmp / "heldout.py"),
                "ground_truth": "satisfiable"}
        with mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: RecordingProvider(tv.FakeProvider(ledger, "honest"), requests, False)), \
             mock.patch.object(harness, "executor_for", lambda ledger: FailingExecutor(ledger, "honest", requests, lambda s: s == "breaker-tests", False)):
            row = quiet(harness.one_system, cell, "codex", 0.5, None, tmp / "runs", 6, Path("/"))
        after = requests.after_stop()
        record("B harness/worker", "harness: a cell whose adversarial-test spawn was uncertain", "nothing is sent after it (no judge, no further stage)",
               f"{len(after)} after it: " + ", ".join(f"{k}:{s}" for k, s in after[:6]) if after else "none", not after)
        record("B harness/worker", "harness: a cell whose adversarial-test spawn was uncertain", "the row is flagged uncertain from structured state",
               f"row uncertain={row.get('uncertain')}, verdict {row.get('verdict')}, reconciliation items {len(row.get('reconciliation') or [])}",
               bool(row.get("uncertain")) and bool(row.get("reconciliation")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def worker_holds_after_stop(code, modules):
    tv, Pipeline, TaskSpec, Ledger, SandboxError, ModelResult = modules
    RecordingProvider, FailingExecutor = build_wrappers((tv.FakeProvider, tv.FakeExecutor), SandboxError, ModelResult)
    from attest.app.db import Store
    from attest.app.worker import Worker
    from attest.ledger import utcnow
    tmp = Path(tempfile.mkdtemp(prefix="attest-repro-worker-"))
    try:
        store = Store(tmp / "attest.db")
        with mock.patch.object(Worker, "_loop", lambda self: None):
            worker = Worker(store, tmp, tv.TASK.parent.parent, max_turns=6)
        per_run: dict[str, Requests] = {}

        def runtime(run_id, provider_name, ledger):
            requests = per_run.setdefault(run_id, Requests())
            predicate = (lambda s: s == "verify") if run_id == "r1" else (lambda s: False)
            return RecordingProvider(tv.FakeProvider(ledger, "honest"), requests, False), FailingExecutor(ledger, "honest", requests, predicate, False), None
        for run_id in ("r1", "r2"):
            store.create_run(run_id=run_id, task_id="durationkit-units-001", task_title="T", provider="codex", profile_label="development",
                             status="queued", stage="queued", created_at=utcnow(), requester="team")
        with mock.patch.object(worker, "build_runtime", runtime):
            quiet(worker._execute, "r1", tv.TASK, "codex", "development")
            quiet(worker._execute, "r2", tv.TASK, "codex", "development")
        first, second = store.get_run("r1"), store.get_run("r2")
        sent_second = len((per_run.get("r2") or Requests()).items)
        record("B harness/worker", "console worker: the next queued run after an uncertain one", "the worker starts nothing until reconciled",
               f"r1 {first['status']}/{first.get('error_code')}; r2 {second['status']}/{second.get('error_code')} with {sent_second} request(s)",
               sent_second == 0)
        record("B harness/worker", "console worker: the uncertain run's row", "the row says reconciliation is required (its own code)",
               f"error_code={first.get('error_code')}", first.get("error_code") == "reconciliation_required")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------------- group C: ambiguous HTTP failures in the adapters
def sandbox_with(script, journal_dir):
    from attest.ledger import JOURNAL_FILE, Ledger
    from attest.sandbox.tf_sandboxes import TokenFactorySandboxes
    ledger = Ledger()
    ledger.attach_sink(journal_dir / JOURNAL_FILE)
    ex = TokenFactorySandboxes("synthetic-key", "synthetic-project", ledger, poll_interval=0)
    ex._sleep = lambda s: None
    seen = []

    def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
        seen.append(method + " " + url.split("/v1")[-1].split("?")[0])
        outcome = script(method, url, len(seen))
        if isinstance(outcome, BaseException):
            raise outcome
        return 200, outcome, {}
    return ex, ledger, seen, fake


def done_operation(uuid="op-1"):
    report = {"runner": "attest-guest/3", "steps": [{"name": "s", "cmd": ["true"], "exit_code": 0, "timed_out": False, "stdout": "", "stderr": "", "duration_s": 0.1}]}
    stdout = "ATTEST-RESULT-BEGIN\n" + json.dumps(report) + "\nATTEST-RESULT-END\n"
    return {"uuid": uuid, "status": "SUCCESS", "duration": 0.5, "metadata": {"result": {"state": {"exit_code": 0, "timed_out": False, "signal": -1},
            "stdout": {"value": stdout}, "stderr": {"value": ""}, "resources": {"cost": 0.0001}}}}


def adapters(code):
    from attest.http import HttpError, TransportError
    from attest.ledger import JOURNAL_FILE, read_journal
    harness = harness_module(code)
    steps = [{"name": "s", "cmd": ["true"]}]
    with tempfile.TemporaryDirectory(prefix="attest-repro-c-") as tmpname:
        tmp = Path(tmpname)

        # C1: spawn answered 502
        (tmp / "c1").mkdir()
        ex, ledger, seen, fake = sandbox_with(lambda m, u, n: HttpError(502, {"raw": "<html>502 Bad Gateway</html>"}, "https://sandbox.invalid/v1/instances"), tmp / "c1")
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            error = None
            try:
                ex.run_branch("image-1", {}, steps, stage="verify")
            except Exception as caught:  # noqa: BLE001
                error = caught
        op = ledger.sandbox_ops[0]
        items = harness.reconciliation_items(ledger)
        journal = read_journal(tmp / "c1" / JOURNAL_FILE) or {}
        record("C adapters", "Sandbox spawn answered HTTP 502", "uncertain, journaled UNCERTAIN, listed for reconciliation, never resent",
               f"{type(error).__name__} uncertain={getattr(error, 'uncertain', None)}; op status {op.status}; reconciliation items {len(items)}; "
               f"journal unresolved spawns {len(journal.get('spawns_unresolved') or [])}; POSTs {sum(1 for s in seen if s.startswith('POST'))}",
               bool(getattr(error, "uncertain", False)) and op.status == "UNCERTAIN" and len(items) == 1 and len(journal.get("spawns_unresolved") or []) == 1
               and sum(1 for s in seen if s.startswith("POST")) == 1)

        # C1b: after that, the same executor refuses further work
        before = len(seen)
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            try:
                ex.run_branch("image-1", {}, steps, stage="existing")
            except Exception:  # noqa: BLE001
                pass
        record("C adapters", "the same run's next sandbox request after that", "refused before any request", f"{len(seen) - before} request(s) sent",
               len(seen) == before)

        # C2: spawn answered 400 (a definite rejection: positive control)
        (tmp / "c2").mkdir()
        ex, ledger, seen, fake = sandbox_with(lambda m, u, n: HttpError(400, {"detail": "invalid image"}, "https://sandbox.invalid/v1/instances"), tmp / "c2")
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            error = None
            try:
                ex.run_branch("image-1", {}, steps, stage="verify")
            except Exception as caught:  # noqa: BLE001
                error = caught
        op = ledger.sandbox_ops[0]
        record("C adapters", "Sandbox spawn answered HTTP 400", "a definite rejection: REJECTED, not uncertain, nothing to reconcile",
               f"uncertain={getattr(error, 'uncertain', None)}; op status {op.status}; reconciliation items {len(harness.reconciliation_items(ledger))}",
               not getattr(error, "uncertain", True) and op.status == "REJECTED" and not harness.reconciliation_items(ledger))

        # C3: accepted, then every poll answered 503
        (tmp / "c3").mkdir()
        ex, ledger, seen, fake = sandbox_with(lambda m, u, n: {"uuid": "op-1"} if m == "POST" else HttpError(503, {"detail": "unavailable"}, u), tmp / "c3")
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            error = None
            try:
                ex.run_branch("image-1", {}, steps, stage="verify")
            except Exception as caught:  # noqa: BLE001
                error = caught
        op = ledger.sandbox_ops[0]
        gets = sum(1 for s in seen if s.startswith("GET"))
        record("C adapters", "accepted operation whose polls answer HTTP 503", "polls retried (bounded); ACCEPTED_UNREAD with its id; listed for reconciliation",
               f"{gets} poll(s); accepted_unread={getattr(error, 'accepted_unread', None)}; op status {op.status}; reconciliation items "
               f"{len(harness.reconciliation_items(ledger))}; journal unread {read_journal(tmp / 'c3' / JOURNAL_FILE).get('operations_unread')}",
               gets > 1 and bool(getattr(error, "accepted_unread", False)) and op.status == "ACCEPTED_UNREAD" and len(harness.reconciliation_items(ledger)) == 1)

        # C4: one 502 poll, then the outcome
        (tmp / "c4").mkdir()
        ex, ledger, seen, fake = sandbox_with(lambda m, u, n: {"uuid": "op-1"} if m == "POST" else (HttpError(502, {}, u) if n == 2 else done_operation()), tmp / "c4")
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            try:
                run = ex.run_branch("image-1", {}, steps, stage="verify")
                outcome = f"ok={run.ok}"
            except Exception as caught:  # noqa: BLE001
                outcome = f"{type(caught).__name__}"
        record("C adapters", "one poll answered HTTP 502, the next one the outcome", "the read is retried and the run continues", outcome, outcome == "ok=True")

        # C5: never terminal, then the cancel-and-wait path gives up
        (tmp / "c5").mkdir()
        ex, ledger, seen, fake = sandbox_with(lambda m, u, n: {"uuid": "op-1"} if m == "POST" else ({} if m == "DELETE" else {"uuid": "op-1", "status": "RUNNING"}), tmp / "c5")
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake), mock.patch("attest.sandbox.tf_sandboxes.time.sleep", lambda s: None):
            error = None
            try:
                ex._execute("image-1", ex._job({}, steps), "verify", disposable=True, timeout=-90)
            except Exception as caught:  # noqa: BLE001
                error = caught
        op = ledger.sandbox_ops[0]
        record("C adapters", "accepted operation that never reaches a terminal state", "ACCEPTED_UNREAD, listed for reconciliation",
               f"accepted_unread={getattr(error, 'accepted_unread', None)}; op status {op.status}; reconciliation items {len(harness.reconciliation_items(ledger))}",
               bool(getattr(error, "accepted_unread", False)) and op.status == "ACCEPTED_UNREAD" and len(harness.reconciliation_items(ledger)) == 1)

        # C6/C7: the Codex gateway's POST answered 502 and 504; C8: a 400 (control); C9: its catalog read answered 503
        from attest.ledger import Ledger
        from attest.models.base import ModelError
        from attest.models.codex_gateway import CodexGateway
        from attest.models.pacing import RateGovernor

        class Clock:
            now = 1_700_000_000.0

            def time(self):
                return self.now

            def sleep(self, s):
                self.now += s
        schema = {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}
        for status, expect_uncertain in ((502, True), (504, True), (400, False)):
            clock = Clock()
            gov = RateGovernor(f"repro-{status}", time_fn=clock.time, sleep_fn=clock.sleep)
            ledger = Ledger()
            ledger.attach_sink(tmp / f"codex-{status}.jsonl")
            client = CodexGateway("synthetic-key", ledger, base_url="https://gateway.invalid/v1", governor=gov)
            client._catalog = {"gpt-6-sol": ["medium"], "gpt-6-astra": ["low", "medium"], "gpt-6-luna": ["low"]}
            posts = []

            def fake(method, url, headers, payload=None, timeout=60, max_bytes=0, _status=status):
                if url.endswith("/status"):
                    return 200, {}, {}
                posts.append(method)
                raise HttpError(_status, {"error": {"message": "upstream"}}, url)
            with mock.patch("attest.models.codex_gateway.request_json", fake):
                error = None
                try:
                    client.structured("implement", "p", schema, "implement-1")
                except ModelError as caught:
                    error = caught
                second = len(posts)
                try:
                    client.structured("implement", "p", schema, "implement-2")
                except ModelError:
                    pass
            call = ledger.model_calls[0]
            if expect_uncertain:
                record("C adapters", f"Codex gateway answered HTTP {status} to a run", "uncertain (it may have run upstream), phase recorded, nothing sent afterwards",
                       f"uncertain={getattr(error, 'uncertain', None)}; phase {call.transport_phase}; status {getattr(call, 'http_status', None)}; "
                       f"POSTs after it {len(posts) - second}",
                       bool(getattr(error, "uncertain", False)) and call.transport_phase == "response" and len(posts) == second)
            else:
                record("C adapters", "Codex gateway answered HTTP 400 (control)", "a definite rejection, not uncertain",
                       f"uncertain={getattr(error, 'uncertain', None)}", not getattr(error, "uncertain", True))
        clock = Clock()
        gov = RateGovernor("repro-read", time_fn=clock.time, sleep_fn=clock.sleep)
        client = CodexGateway("synthetic-key", Ledger(), base_url="https://gateway.invalid/v1", governor=gov)
        reads = []

        def flaky_read(method, url, headers, payload=None, timeout=60, max_bytes=0):
            reads.append(url)
            if url.endswith("/models") and len([r for r in reads if r.endswith("/models")]) == 1:
                raise HttpError(503, {"error": "busy"}, url)
            return 200, {"data": [{"id": "gpt-6-sol", "supported_reasoning_efforts": ["medium"]}]}, {}
        with mock.patch("attest.models.codex_gateway.request_json", flaky_read):
            try:
                catalog = client.catalog()
                outcome = f"catalog read after {len([r for r in reads if r.endswith('/models')])} attempt(s): {sorted(catalog)}"
                ok = "gpt-6-sol" in catalog
            except Exception as caught:  # noqa: BLE001
                outcome, ok = f"{type(caught).__name__}: {str(caught)[:80]}", False
        record("C adapters", "Codex gateway catalog read answered HTTP 503 once", "the read is retried with backoff", outcome, ok)

        # C10: Nebius Token Factory answered 500
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        ledger = Ledger()
        ledger.attach_sink(tmp / "c10.jsonl")
        client = NebiusTokenFactory("synthetic-key", ledger, base_url="https://tokenfactory.invalid/v1", usd_cap=0.5, max_calls=22)
        client._sleep = lambda s: None
        posts = []

        def fake_tf(method, url, headers, payload=None, timeout=60, max_bytes=0):
            posts.append(method)
            raise HttpError(500, {"error": {"message": "internal"}}, url)
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake_tf):
            error = None
            try:
                client.structured("implement", "p", schema, "implement-1")
            except ModelError as caught:
                error = caught
            first = len(posts)
            try:
                client.structured("implement", "p", schema, "implement-2")
            except ModelError:
                pass
        record("C adapters", "Nebius Token Factory answered HTTP 500", "uncertain, reservation kept, nothing sent afterwards",
               f"uncertain={getattr(error, 'uncertain', None)}; settlement {ledger.model_calls[0].settlement}; POSTs after it {len(posts) - first}",
               bool(getattr(error, "uncertain", False)) and ledger.model_calls[0].settlement == "unsettled" and len(posts) == first)


# ----------------------------------------------------------------------------- group C (continued): cut HTTP error bodies on the loopback interface
class OneShot:
    def __init__(self, respond):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(2)
        self.port = self.sock.getsockname()[1]
        self.respond = respond
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            conn, _ = self.sock.accept()
        except OSError:
            return
        with conn:
            data = b""
            conn.settimeout(5)
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    return
                data += chunk
            head, _, body = data.partition(b"\r\n\r\n")
            length = 0
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    length = int(line.split(b":")[1])
            while len(body) < length:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                body += chunk
            try:
                self.respond(conn)
            except OSError:
                pass

    def close(self):
        self.sock.close()
        self.thread.join(5)


def cut_bodies():
    from attest.http import request_json
    cases = [
        ("a chunked HTTP 502 error body cut mid-chunk", lambda c: c.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: application/json\r\nTransfer-Encoding: chunked\r\n\r\n"
                                                                            b"40\r\n{\"error\": {\"message\": \"upstream res")),
        ("an HTTP 503 error body that stalls after the headers", lambda c: (c.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: application/json\r\n"
                                                                                       b"Content-Length: 200\r\n\r\n{\"err"), time.sleep(3))),
        ("an HTTP 200 body cut mid-chunk", lambda c: c.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nTransfer-Encoding: chunked\r\n\r\n"
                                                                b"40\r\n{\"uuid\": \"op-")),
    ]
    for label, respond in cases:
        server = OneShot(respond)
        try:
            request_json("POST", f"http://127.0.0.1:{server.port}/v1/instances", {}, {"x": 1}, timeout=1.5)
            outcome, ok = "no exception", False
        except Exception as error:  # noqa: BLE001
            kind = type(error).__name__
            status = getattr(error, "status", None)
            sent = getattr(error, "request_sent", None)
            phase = getattr(error, "phase", None)
            complete = getattr(error, "body_complete", None)
            outcome = f"{kind}: status={status}, request_sent={sent}, phase={phase}, body_complete={complete}"
            if "200" in label:  # a success whose body was cut: a TransportError (uncertain) that keeps the status
                ok = kind == "TransportError" and sent is True and phase == "response" and status == 200
            else:  # an error answer: always an HttpError with its status, whatever happened to the body
                ok = kind == "HttpError" and sent is True and phase == "response" and status in (502, 503) and complete is False
        finally:
            server.close()
        record("C adapters", label, "a transport-wrapped error that keeps the status, request_sent and the phase", outcome, ok)


def concurrent_branches():
    """Six sandbox branches in parallel through the real client (HTTP replaced): the third spawn's answer is lost. Every request must have
    been admitted before the halt; the other operations are refused or stop being polled, and every accepted one is listed."""
    from attest.http import TransportError
    from attest.ledger import JOURNAL_FILE, Ledger
    from attest.sandbox.tf_sandboxes import TokenFactorySandboxes
    from concurrent.futures import ThreadPoolExecutor
    with tempfile.TemporaryDirectory(prefix="attest-repro-conc-") as tmpname:
        ledger = Ledger()
        ledger.attach_sink(Path(tmpname) / JOURNAL_FILE)
        ex = TokenFactorySandboxes("synthetic-key", "synthetic-project", ledger, poll_interval=0.01)
        ex._sleep = lambda s: time.sleep(min(s, 0.01))
        lock = threading.Lock()
        seen, state = [], {"posts": 0, "uncertain_at": None, "admitted_at_halt": None}
        if hasattr(ledger, "on_halt"):
            ledger.on_halt = lambda led, rec: state.__setitem__("admitted_at_halt", led.admitted)

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            with lock:
                seen.append(method)
                index = len(seen)
                if method == "POST":
                    state["posts"] += 1
                    number = state["posts"]
            if method == "POST":
                if number == 3:
                    with lock:
                        state["uncertain_at"] = index
                    raise TransportError("RemoteDisconnected: Remote end closed connection without response", request_sent=True, phase="response")
                return 200, {"uuid": f"op-{number}"}, {}
            time.sleep(0.02)
            return 200, {"uuid": url.rsplit("/", 1)[-1], "status": "RUNNING"}, {}
        steps = [{"name": "s", "cmd": ["true"]}]

        def branch(i):
            try:
                ex.run_branch("image-1", {}, steps, stage=f"mutant-{i}", timeout=-89)
            except Exception as error:  # noqa: BLE001
                return type(error).__name__
            return "ok"
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            with ThreadPoolExecutor(max_workers=6) as pool:
                outcomes = list(pool.map(branch, range(6)))
        if state["admitted_at_halt"] is not None:  # revision 9: every request is admitted by the ledger first
            late = max(0, len(seen) - state["admitted_at_halt"])
            observed = (f"{len(seen)} request(s) sent, {state['admitted_at_halt']} admitted when the run halted, {getattr(ledger, 'refused', 0)} refused "
                        f"afterwards; statuses {sorted(o.status for o in ledger.sandbox_ops)}; reconciliation items {len(ledger.reconciliation_items())}")
        else:  # before revision 9 nothing stops the other branches: count what was sent after the uncertain spawn
            late = len(seen) - (state["uncertain_at"] or len(seen))
            observed = f"{len(seen)} request(s) sent, {late} after the uncertain spawn; statuses {sorted(str(o.status) for o in ledger.sandbox_ops)}"
        record("C adapters", "six parallel branches, the third spawn's answer lost", "no request is admitted after the run halts; every accepted one is listed",
               observed, late == 0 and state["admitted_at_halt"] is not None)


# ----------------------------------------------------------------------------- group D: durable operation journaling
def journal_scenarios():
    import attest.ledger as ledger_module
    from attest.ledger import JOURNAL_FILE, read_journal
    steps = [{"name": "s", "cmd": ["true"]}]
    real_write = ledger_module._write_durably

    def failing_on(event, status=None, partial=False, code=errno.ENOSPC):
        def write(path, lines):
            text = "".join(lines)
            try:
                record_ = json.loads(lines[-1])
            except (json.JSONDecodeError, IndexError):
                record_ = {}
            if record_.get("event") == event and (status is None or record_.get("status") == status):
                if partial:
                    with open(path, "a", encoding="utf-8") as handle:
                        handle.write(text[: len(text) // 2])
                raise OSError(code, os.strerror(code))
            return real_write(path, lines)
        return write

    cases = [
        ("disk full on the pending record before dispatch", failing_on("sandbox_op"), "spawn"),
        ("fsync error on the pending record before dispatch", failing_on("sandbox_op", code=errno.EIO), "spawn"),
        ("an interrupted write (half a line) of the pending record", failing_on("sandbox_op", partial=True), "spawn"),
        ("disk full on the accepted id before polling", failing_on("sandbox_op_update", status="ACCEPTED"), "poll"),
    ]
    for label, writer, phase in cases:
        with tempfile.TemporaryDirectory(prefix="attest-repro-d-") as tmpname:
            tmp = Path(tmpname)
            ex, ledger, seen, fake = sandbox_with(lambda m, u, n: {"uuid": "op-1"} if m == "POST" else done_operation(), tmp)
            error = None
            with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake), mock.patch.object(ledger_module, "_write_durably", writer):
                try:
                    ex.run_branch("image-1", {}, steps, stage="verify")
                except Exception as caught:  # noqa: BLE001
                    error = caught
            posts = sum(1 for s in seen if s.startswith("POST"))
            gets = sum(1 for s in seen if s.startswith("GET"))
            journal = read_journal(tmp / JOURNAL_FILE) or {}
            if phase == "spawn":
                record("D journal", label, "nothing is dispatched and the run halts", f"POSTs {posts}; error {type(error).__name__ if error else None}",
                       posts == 0 and error is not None)
            else:
                kept = getattr(error, "operation_uuid", None) == "op-1"
                record("D journal", label, "no poll; halted; the accepted id is kept for account-side reconciliation",
                       f"POSTs {posts}, polls {gets}; error {type(error).__name__ if error else None}; id kept on the error: {kept}",
                       posts == 1 and gets == 0 and error is not None and kept)
            if label.startswith("an interrupted write"):
                after = ledger_module._tail_state(tmp / JOURNAL_FILE)[1]
                record("D journal", label, "restart reads the journal and the cut tail is reported, not misread",
                       f"tail framed {journal.get('tail_framed')}; unparsable lines {journal.get('unparsable_lines')}; cut bytes {len(after)}",
                       journal.get("tail_framed") is False or bool(journal.get("journal_repairs")))

    # restart recovery: the process dies after the spawn request left and before its answer came back
    class Died(BaseException):
        pass
    with tempfile.TemporaryDirectory(prefix="attest-repro-d-") as tmpname:
        tmp = Path(tmpname)
        ex, ledger, seen, fake = sandbox_with(lambda m, u, n: Died(), tmp)
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            try:
                ex.run_branch("image-1", {}, steps, stage="verify")
            except Died:
                pass
        journal = read_journal(tmp / JOURNAL_FILE) or {}
        record("D journal", "restart after the process died between dispatch and answer", "the journal names the dispatched spawn as unresolved",
               f"unresolved spawns {journal.get('spawns_unresolved')}; unread operations {journal.get('operations_unread')}",
               len(journal.get("spawns_unresolved") or []) == 1)
        from attest.app.db import Store
        from attest.ledger import utcnow
        run_dir = tmp
        store = Store(tmp / "attest.db")
        store.create_run(run_id="died", task_id="t", task_title="t", provider="codex", profile_label="development", status="running",
                         created_at=utcnow(), out_dir=str(run_dir), requester="team")
        outcome = store.finalize_interrupted("died")
        row = store.get_run("died")
        record("D journal", "the console's restart recovery of that run", "the row requires reconciliation and names the unresolved spawn",
               f"error_code {row.get('error_code')}; outcome keys {sorted(outcome)}",
               row.get("error_code") == "reconciliation_required" and bool(outcome.get("spawns_unresolved")))


# ----------------------------------------------------------------------------- group E: test isolation
def test_isolation(code):
    import subprocess
    guard = HOME / "guard_runner.py"
    guard.write_text(
        "import errno, os, socket, sys, unittest\n"
        "sys.path.insert(0, os.getcwd())  # the checkout under test (this runner lives in a temporary directory)\n"
        "attempts = []\n"
        "real = socket.socket.connect\n"
        "def connect(self, address):\n"
        "    if self.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in ('127.0.0.1', '::1', 'localhost'):\n"
        "        attempts.append(1)\n"
        "        raise ConnectionRefusedError(errno.ECONNREFUSED, 'blocked')\n"
        "    return real(self, address)\n"
        "socket.socket.connect = connect\n"
        "real_gai = socket.getaddrinfo\n"
        "def gai(host, *a, **k):\n"
        "    if host not in ('127.0.0.1', '::1', 'localhost', None):\n"
        "        attempts.append(1)\n"
        "        raise socket.gaierror(socket.EAI_NONAME, 'blocked')\n"
        "    return real_gai(host, *a, **k)\n"
        "socket.getaddrinfo = gai\n"
        "result = unittest.main(module=None, argv=['x'] + sys.argv[1:], exit=False).result\n"
        "print('NETWORK_ATTEMPTS=%d' % len(attempts))\n"
        "sys.exit(0 if result.wasSuccessful() and not attempts else 1)\n", encoding="utf-8")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(HOME), "ATTEST_SECRETS_NOTES": str(HOME / "no-notes.json"), "NO_PROXY": "*"}
    targets = ["tests.test_reliability.CodexClientPacing", "tests.test_reliability.GovernorPolicy.test_client_adopts_the_gateway_policy_before_the_first_request"]
    runs = [(t, env) for t in targets]
    # the developer's machine has the gateway URL configured: a synthetic one stands in for it, so a request that leaves the mock shows
    runs.append((targets[1] + " (a gateway URL configured)", {**env, "ATTEST_CODEX_BASE_URL": "https://gateway.invalid/v1"}))
    for target, run_env in runs:
        proc = subprocess.run([sys.executable, str(guard), target.split(" (")[0]], cwd=code, env=run_env, capture_output=True, text=True, timeout=300)
        tail = (proc.stdout + proc.stderr).strip().splitlines()
        summary = next((line for line in reversed(tail) if line.startswith(("OK", "FAILED", "Ran "))), tail[-1] if tail else "")
        attempts = next((line for line in tail if line.startswith("NETWORK_ATTEMPTS=")), "NETWORK_ATTEMPTS=?")
        errors = next((line for line in tail if "Error" in line and ("ModelError" in line or "not configured" in line or "AssertionError" in line
                                                                    or "ImportError" in line or "NetworkForbidden" in line)), "")
        record("E tests", target.split(".", 2)[-1], "passes with no credentials and no network, and sends nothing outside its mocks",
               f"exit {proc.returncode}; {summary}; {attempts}" + (f"; {errors[:120]}" if errors else ""), proc.returncode == 0 and attempts == "NETWORK_ATTEMPTS=0")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--code", required=True, help="a checkout of the code to examine")
    parser.add_argument("--json")
    args = parser.parse_args(argv)
    code = Path(args.code).resolve()
    sys.path.insert(0, str(code))
    os.chdir(code)
    import attest
    from attest.core.pipeline import Pipeline
    from attest.core.task import TaskSpec
    from attest.ledger import Ledger
    from attest.models.base import ModelResult
    from attest.sandbox.tf_sandboxes import SandboxError
    import tests.test_verification as tv
    modules = (tv, Pipeline, TaskSpec, Ledger, SandboxError, ModelResult)
    started = time.time()
    for label, scenario, predicate, options in stage_scenarios():
        try:
            run_stage(label, scenario, predicate, options, modules)
        except Exception as error:  # noqa: BLE001
            record("A stages", label, "the scenario runs", f"crashed: {type(error).__name__}: {str(error)[:120]}", False)
    for fn in (lambda: harness_judge_after_stop(code, modules), lambda: worker_holds_after_stop(code, modules), lambda: adapters(code), cut_bodies,
               concurrent_branches, journal_scenarios, lambda: test_isolation(code)):
        try:
            fn()
        except Exception as error:  # noqa: BLE001
            record("crash", getattr(fn, "__name__", "scenario"), "the scenario runs", f"crashed: {type(error).__name__}: {str(error)[:160]}\n" + traceback.format_exc()[-600:], False)
    passed = sum(1 for r in RESULTS if r["result"] == "PASS")
    print(f"code: {code} (attest {attest.__version__}); {len(RESULTS)} checks, {passed} PASS, {len(RESULTS) - passed} FAIL; "
          f"network attempts blocked in this process: {len(NETWORK_ATTEMPTS)}; {time.time() - started:.1f} s")
    group = None
    for r in RESULTS:
        if r["group"] != group:
            group = r["group"]
            print(f"\n[{group}]")
        print(f"  {r['result']}  {r['scenario']}: {r['check']}\n        observed: {r['observed']}")
    if args.json:
        Path(args.json).write_text(json.dumps({"code": str(code), "version": attest.__version__, "results": RESULTS,
                                               "network_attempts_blocked": len(NETWORK_ATTEMPTS)}, indent=2) + "\n", encoding="utf-8")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
