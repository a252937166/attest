"""Reliability round (17 Oct 2026): the three dry-run holds, Codex pacing, and provenance of the code actually executed.

Offline only. The real supervisor runs locally (not as root) for the pipe-drain regression; the Codex client is exercised
against a fake transport; the harness helpers are exercised on a temporary copy of the tree.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from attest.core import exhibits as exhibits_module
from attest.core.prompts import ARBITRATION_SCHEMA, arbitrate_prompt, breaker_prompt
from attest.core.sealed import SUPERVISOR_VERSION, guest_files_for, new_nonce, sealed_steps, summarize
from attest.http import HttpError, TransportError
from attest.ledger import Ledger
from attest.models.base import ModelError
from attest.models.codex_gateway import CodexGateway
from attest.models.pacing import MAX_429_RETRIES, PacingError, RateGovernor
from tests.test_verification import run_scenario

ROOT = Path(__file__).resolve().parent.parent
HOLDS = ROOT / "reports" / "attest-reliability-2026-10-17" / "holds"


def run_supervisor_locally(repo: Path, module_src: str, per_test_timeout: int = 20) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="attest-rel-"))
    try:
        suite_dir = tmp / "suite"
        files = guest_files_for(str(suite_dir), "test_mod", module_src, repo_dir=str(repo), extra_paths=[], canary=True)
        for path, data in files.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(data)
        nonce = new_nonce()
        steps = sealed_steps(sys.executable, str(repo), str(suite_dir), nonce, [], {"PYTHONPATH": str(repo)}, timeout=120,
                             module_name="test_mod", per_test_timeout=per_test_timeout, step_prefix="s")
        outputs = {}
        for step in steps:
            proc = subprocess.run(step["cmd"], cwd=step["cwd"], env={**os.environ, "PYTHONPATH": str(repo)}, capture_output=True, timeout=180)
            outputs[step["name"]] = proc.stdout.decode()
        return json.loads(outputs["s_result"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class SupervisorPipeDrain(unittest.TestCase):
    """Hold 2 (balanced-brackets): a correct 9,331-subtest test was recorded as TIMEOUT because the v5 supervisor read the
    child's result pipe only after the child exited. v6 drains it concurrently and bounds the event log."""

    def test_read_after_exit_blocks_a_child_whose_report_exceeds_the_pipe_buffer(self):
        child = "import os, sys\nos.write(int(sys.argv[1]), b'x' * 600000)\n"  # 600 KB > 64 KiB pipe buffer
        read_fd, write_fd = os.pipe()
        proc = subprocess.Popen([sys.executable, "-c", child, str(write_fd)], pass_fds=(write_fd,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.close(write_fd)
        with self.assertRaises(subprocess.TimeoutExpired):
            proc.communicate(timeout=2)  # the v5 order: wait for exit before reading the pipe -> the child never exits
        proc.kill()
        proc.communicate()
        os.close(read_fd)

        read_fd, write_fd = os.pipe()
        proc = subprocess.Popen([sys.executable, "-c", child, str(write_fd)], pass_fds=(write_fd,), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.close(write_fd)
        chunks = []

        def drain():
            while True:
                piece = os.read(read_fd, 65536)
                if not piece:
                    break
                chunks.append(piece)
        reader = threading.Thread(target=drain)
        reader.start()
        proc.communicate(timeout=10)  # the v6 order: drained while running -> the child exits promptly
        reader.join(5)
        os.close(read_fd)
        self.assertEqual(sum(map(len, chunks)), 600000)

    def test_v6_runs_a_test_with_many_subtests_within_the_budget(self):
        self.assertEqual(SUPERVISOR_VERSION, "attest-sealed-supervisor/7")
        tmp = Path(tempfile.mkdtemp(prefix="attest-rel-repo-"))
        try:
            (tmp / "pkg").mkdir()
            (tmp / "pkg" / "__init__.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
            module = ("import unittest\nfrom pkg import f\n\nclass T(unittest.TestCase):\n"
                      "    def test_many(self):\n        for i in range(20000):\n            with self.subTest(i=i):\n                self.assertEqual(f(i), i + 1)\n"
                      "    def test_one(self):\n        self.assertEqual(f(1), 2)\n")
            result = run_supervisor_locally(tmp, module, per_test_timeout=30)
            by = {t["id"].split(".")[-1]: t for t in result["tests"]}
            self.assertEqual(by["test_many"]["outcome"], "ok", by["test_many"])
            self.assertFalse(by["test_many"]["timed_out"])
            self.assertLess(by["test_many"]["duration_s"], 20)
            self.assertLess(by["test_many"]["result_bytes"], 65536)  # the bounded event log keeps the report far below a pipe buffer
            self.assertTrue(summarize(result)["all_passed"] or result["privilege_separation"] is False)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_recorded_brackets_module_passes_on_its_candidate_under_v6(self):
        """The recorded hold replayed offline: the original module passes on the reconstructed candidate and fails on the base."""
        for name in ("replay-brackets-local.json", "replay-roman-local.json", "replay-durationkit-local.json"):
            path = HOLDS / name
            if not path.is_file():
                self.skipTest(f"{path} not present")
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(record["candidate"]["identical_to_recorded"], name)
            self.assertTrue(record["base_repo_identical_to_frozen_task"], name)
            label = "original" if "brackets" in name else "corrected"
            entry = record["modules"][label]["local"]
            self.assertTrue(entry["candidate"]["all_passed"] or entry["candidate"]["binding_failed_checks"] == ["verifier_isolation_active"], (name, entry["candidate"]["summary_line"]))
            self.assertGreater(entry["base"]["failing"], 0, name)


class BreakerAndArbiterPrompts(unittest.TestCase):
    def test_breaker_prompt_states_scope_rules_and_the_workload_budget(self):
        class Task:
            import_hint = "from pkg import f"
        spec = {"restated_task": "r", "interface_contract": [], "acceptance_criteria": []}
        text = breaker_prompt(Task(), spec, "diff", ["test_a"], per_test_timeout=45)
        self.assertIn("45 seconds", text)
        self.assertIn("never use subclasses or wrapper objects that override operators", text)
        self.assertIn("Scope rules: test only behaviour the contract states", text)
        self.assertIn("not required, do not test it", text)
        self.assertIn("recorded as a failure of the test, not as a finding against the candidate", text)

    def test_arbiter_prompt_explains_timeouts_and_unspecified_behaviour_and_schema_accepts_defect_kind(self):
        class Task:
            statement = "s"
        spec = {"restated_task": "r", "interface_contract": [], "acceptance_criteria": [], "out_of_scope": []}
        failing = [{"id": "test_mod.T.test_slow", "outcome": "TIMEOUT", "timed_out": True, "duration_s": 60.0, "captured_tail": ""}]
        text = arbitrate_prompt(Task(), spec, "diff", "import unittest", "test_mod", failing)
        self.assertIn("TIMEOUT: the test did not finish within the per-test budget (60.0 s elapsed)", text)
        self.assertIn("excessive_workload", text)
        self.assertIn("unspecified_behavior", text)
        kinds = ARBITRATION_SCHEMA["properties"]["classifications"]["items"]["properties"]["defect_kind"]["enum"]
        self.assertIn("wrong_expectation", kinds)
        self.assertIn("defect_kind", ARBITRATION_SCHEMA["properties"]["classifications"]["items"]["required"])  # strict mode: nullable, never optional
        self.assertIn(None, kinds)

    def test_arbitration_of_an_adversarial_module_checks_the_base_and_advisory_mode_keeps_the_hold(self):
        bundle = run_scenario("arb_clear", apply=False)
        module = bundle["arbitration"]["modules"][0]
        self.assertEqual(module["module"], "adversarial")
        self.assertIsNotNone(module["base_rerun"], "the corrected adversarial module must be shown to still fail on the base")
        self.assertGreater(module["base_rerun"]["failing"], 0)
        self.assertEqual(module["base_rerun"]["corrected_tests_failing_on_base"], ["test_breaker.B.test_a"])
        self.assertTrue(module["cleared_module"] and module["validated"])
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")  # advisory mode: the gate is not re-run, the hold stands


class ExhibitsTimeouts(unittest.TestCase):
    def _bundle(self, outcome, arbitration=None):
        tests = [{"id": "test_breaker.B.test_big", "outcome": outcome, "timed_out": outcome == "TIMEOUT", "exit_code": None if outcome == "TIMEOUT" else 1,
                  "signal": 9 if outcome == "TIMEOUT" else None, "failure_tail": "", "duration_s": 60.0}]
        return {"verdict": {"verdict": "NEEDS HUMAN", "reasons": ["x"]}, "candidate": {"implementer_finished": True, "scope_ok": True},
                "gates": {"existing_suite": {"ok": True}, "sealed_binding": {"ok": True}, "mutation": {"ok": True},
                          "adversarial_tests": {"ok": False, "failing": [tests[0]["id"]]}, "drift_audit": {"ok": True}},
                "verification": {"binding": {"ok": True, "checks": {}}, "sealed": {"tests": []}},
                "breaker": {"mutation": {"generated": 4, "evaluated": 4, "killed": 4, "survived": 0, "unknown": 0, "score": 1.0, "threshold": 0.5, "mutants": []},
                            "adversarial": {"summary": {"ran": 1, "passed": 0, "failing": 1, "all_passed": False, "tests": tests}, "binding": {"ok": False, "checks": {"no_timeout": False}}}},
                "arbitration": arbitration, "task": {"title": "t"}, "spec": {}}

    def test_unarbitrated_timeout_is_its_own_reason_class(self):
        bundle = self._bundle("TIMEOUT")
        self.assertEqual(exhibits_module.reason_class(bundle), "adversarial_timeout")
        decision = exhibits_module.decision(bundle)
        self.assertIn("did not finish within its per-test time budget", decision["explanation"])
        self.assertIn("not a demonstrated defect", decision["explanation"])
        e3 = next(e for e in exhibits_module.exhibits(bundle) if e["ref"] == "E3")
        self.assertIn("timed out, no assertion failed", e3["summary"])
        self.assertEqual(e3["detail"]["timeout_ids"], ["test_breaker.B.test_big"])
        self.assertEqual(exhibits_module.reason_class(self._bundle("FAIL")), "adversarial_failed")

    def test_arbitrated_test_defects_name_their_kinds(self):
        arbitration = {"counts": {"implementation_bug": 0, "test_defect": 1, "contract_dispute": 0}, "cleared": True, "headline": "h",
                       "modules": [{"module": "adversarial", "classifications": [{"test_id": "test_breaker.B.test_big", "classification": "test_defect",
                                                                                 "defect_kind": "excessive_workload", "rationale": "r", "contract_basis": "c"}]}]}
        bundle = self._bundle("TIMEOUT", arbitration)
        self.assertEqual(exhibits_module.reason_class(bundle), "adversarial_test_defects")
        self.assertIn("excessive workload", exhibits_module.decision(bundle)["explanation"])
        example = exhibits_module.counterexamples(bundle)[0]
        self.assertEqual(example["defect_kind"], "excessive_workload")
        self.assertEqual(example["duration_s"], 60.0)


class FakeClock:
    def __init__(self, start=1_700_000_000.0):
        self.now = start
        self.slept = 0.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.slept += seconds


class Governor(unittest.TestCase):
    def governor(self, **kw):
        clock = FakeClock()
        gov = RateGovernor("k", hourly_limit=kw.pop("hourly_limit", 60), safety=kw.pop("safety", 0.9), max_concurrency=kw.pop("max_concurrency", 2),
                           max_wait_s=kw.pop("max_wait_s", 3900), state_path=kw.pop("state_path", None), time_fn=clock.time, sleep_fn=clock.sleep)
        return gov, clock

    def test_budget_is_a_safety_fraction_of_the_hourly_limit_and_the_window_rolls(self):
        gov, clock = self.governor()
        self.assertEqual(gov.budget, 54)
        for _ in range(54):
            slot = gov.acquire()
            gov.release()
            clock.now += 10  # 54 calls over 9 minutes
            self.assertEqual(slot["waited_s"], 0.0)
        messages = []
        slot = gov.acquire(notify=messages.append)  # the 55th call must wait until the oldest entry is an hour old
        gov.release()
        self.assertGreater(slot["waited_s"], 3000)
        self.assertTrue(any("hourly budget used (54 of 54" in m for m in messages), messages)
        self.assertEqual(len(gov.waits), 1)

    def test_bounded_wait_fails_visibly_instead_of_blocking(self):
        gov, clock = self.governor(max_wait_s=600)
        for _ in range(54):
            gov.acquire(); gov.release()
        with self.assertRaises(PacingError) as cm:
            gov.acquire()
        self.assertIn("the request was not sent", str(cm.exception))
        self.assertIn("nothing fell back to another provider", str(cm.exception))
        self.assertEqual(gov.in_flight, 0)
        clock.now += 4000  # the permit was returned: another acquire after the window rolled works
        gov.acquire(); gov.release()

    def test_rejection_blocks_the_key_until_retry_after_or_the_window_reopens(self):
        gov, clock = self.governor()
        gov.acquire(); gov.release()
        until = gov.record_rejection(retry_after_s=120)
        self.assertEqual(until, clock.now + 120)
        slot = gov.acquire(); gov.release()
        self.assertEqual(slot["waited_s"], 120.0)
        gov2, clock2 = self.governor()
        for _ in range(3):
            gov2.acquire(); gov2.release(); clock2.now += 60
        until = gov2.record_rejection()  # no Retry-After: wait for the oldest attempt to age out of the window (+30 s)
        self.assertEqual(until, clock2.now - 180 + 3600 + 30)
        gov3, clock3 = self.governor()
        until = gov3.record_rejection()  # empty window: another process used the budget -> next clock hour + 60 s
        self.assertEqual(until, (clock3.now // 3600 + 1) * 3600 + 60)
        self.assertEqual(gov3.rejections, 1)

    def test_state_file_shares_the_window_between_two_governors_like_two_processes(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-pacing-"))
        try:
            path = tmp / "state.json"
            a, clock_a = self.governor(state_path=path)
            b, clock_b = self.governor(state_path=path)
            clock_b.now = clock_a.now
            for _ in range(30):
                a.acquire(); a.release()
            for _ in range(24):
                b.acquire(); b.release()
            self.assertEqual(b.headroom(), 0)
            self.assertEqual(a.headroom(), 0)  # a sees b's calls through the file
            self.assertTrue(a.snapshot()["state_shared_across_processes"])
            self.assertEqual(json.loads(path.read_text())["calls"].__len__(), 54)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_concurrency_permits_cap_requests_in_flight(self):
        gov, clock = self.governor(max_concurrency=2, max_wait_s=1)
        gov.acquire(); gov.acquire()
        self.assertEqual(gov.in_flight, 2)
        with self.assertRaises(PacingError):
            gov.acquire()
        gov.release(); gov.release()
        self.assertEqual(gov.in_flight, 0)

    def test_headroom_wait_for_a_cell(self):
        gov, clock = self.governor()
        for _ in range(50):
            gov.acquire(); gov.release(); clock.now += 1
        waited = gov.wait_for_headroom(15)  # needs 15, has 4 -> wait until 11 entries aged out
        self.assertGreater(waited, 3500)
        self.assertGreaterEqual(gov.headroom(), 15)


class CodexClientPacing(unittest.TestCase):
    """The Codex client against a fake transport: 429 is recorded, waited out (bounded) and retried; transport errors stay uncertain."""

    def client(self, responses, max_wait_s=3900):
        clock = FakeClock()
        gov = RateGovernor("k", max_wait_s=max_wait_s, time_fn=clock.time, sleep_fn=clock.sleep)
        ledger = Ledger()
        messages = []
        client = CodexGateway("cxk_test", ledger, governor=gov, notify=messages.append)
        client._catalog = {"gpt-6-sol": ["low", "medium"], "gpt-6-astra": ["low", "medium"], "gpt-6-luna": ["low"]}
        calls = []

        def fake_request(method, url, headers, payload=None, timeout=60, max_bytes=0):
            if url.endswith("/status"):  # the policy check before the first request: an enforced 60-per-hour gateway
                return 200, {"limits": {"hourly_requests": 60, "hourly_requests_enforced": True, "max_concurrent_requests": 1}}, {}
            calls.append((method, url))
            outcome = responses.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 200, outcome, {}
        return client, ledger, gov, clock, messages, calls, fake_request

    def test_429_is_recorded_then_retried_after_a_bounded_wait(self):
        ok = {"model": "gpt-6-sol", "effort": "medium", "json": {"result": 4}, "output": '{"result": 4}', "usage": {"input_tokens": 10, "output_tokens": 2}, "duration_ms": 1}
        rejection = HttpError(429, {"error": {"message": "hourly limit reached for this key"}}, "https://gw/v1/run", {"Retry-After": "90"})
        client, ledger, gov, clock, messages, calls, fake = self.client([rejection, ok])
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            result = client.structured("implement", "p", {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}, "s")
        self.assertEqual(result.json, {"result": 4})
        self.assertEqual(len(ledger.model_calls), 2)
        first, second = ledger.model_calls
        self.assertFalse(first.ok)
        self.assertIn("HTTP 429", first.error)
        self.assertEqual(first.attempt, 1)
        self.assertTrue(second.ok)
        self.assertEqual(second.attempt, 2)
        self.assertEqual(second.pacing_wait_ms, 90_000)
        totals = ledger.totals()
        self.assertEqual(totals["rate_limited_calls"], 1)
        self.assertEqual(totals["pacing_wait_ms"], 90_000)
        self.assertTrue(any("rejected the request" in m for m in messages))
        self.assertEqual(gov.in_flight, 0)

    def test_persistent_429_fails_visibly_as_rate_limited_not_uncertain(self):
        rejection = lambda: HttpError(429, {"error": {"message": "hourly limit reached for this key"}}, "https://gw/v1/run", {"Retry-After": "60"})  # noqa: E731
        client, ledger, gov, clock, messages, calls, fake = self.client([rejection() for _ in range(MAX_429_RETRIES + 1)])
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            with self.assertRaises(ModelError) as cm:
                client.structured("implement", "p", {"type": "object"}, "s")
        self.assertTrue(cm.exception.rate_limited)
        self.assertFalse(cm.exception.uncertain)
        self.assertIn("hourly limit", str(cm.exception))
        self.assertEqual(len(ledger.model_calls), MAX_429_RETRIES + 1)
        self.assertEqual(len(calls), MAX_429_RETRIES + 1)

    def test_bounded_wait_exceeded_sends_nothing_and_names_no_fallback(self):
        client, ledger, gov, clock, messages, calls, fake = self.client([], max_wait_s=30)
        gov.record_rejection(retry_after_s=600)
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            with self.assertRaises(ModelError) as cm:
                client.structured("implement", "p", {"type": "object"}, "s")
        self.assertTrue(cm.exception.rate_limited)
        self.assertEqual(calls, [])
        self.assertIn("nothing fell back to another provider", str(cm.exception))

    def test_transport_failure_is_still_uncertain_and_never_retried(self):
        client, ledger, gov, clock, messages, calls, fake = self.client([TransportError("timed out")])
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            with self.assertRaises(ModelError) as cm:
                client.structured("implement", "p", {"type": "object"}, "s")
        self.assertTrue(cm.exception.uncertain)
        self.assertEqual(len(calls), 1)

    def test_codex_client_never_references_the_paid_provider(self):
        for name in ("codex_gateway.py", "pacing.py"):
            source = (ROOT / "attest" / "models" / name).read_text(encoding="utf-8")
            self.assertNotIn("nebius_tokenfactory", source, name)
            self.assertNotIn("NebiusTokenFactory", source, name)
            self.assertNotIn("import", [line for line in source.splitlines() if "nebius" in line.lower() and "import" in line], name)


class HarnessProvenance(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import importlib
        self.harness = importlib.import_module("run_evaluation")

    def test_snapshot_records_digests_and_detects_changes(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-snap-"))
        try:
            record = self.harness.make_snapshot(ROOT, tmp / "snapshot")
            self.assertEqual(record["attest_revision"]["digest"], record["working_tree_revision_at_launch"])
            self.assertTrue((tmp / "snapshot" / "scripts" / "run_evaluation.py").is_file())
            self.assertTrue((tmp / "snapshot" / "examples" / "eval" / "SUITE.json").is_file())
            self.assertFalse(list((tmp / "snapshot").rglob("__pycache__")))
            again = self.harness.snapshot_digests(tmp / "snapshot")
            self.assertEqual(again["attest_revision"]["digest"], record["attest_revision"]["digest"])
            (tmp / "snapshot" / "attest" / "__init__.py").write_text("# edited\n", encoding="utf-8")
            self.assertNotEqual(self.harness.snapshot_digests(tmp / "snapshot")["attest_revision"]["digest"], record["attest_revision"]["digest"])
            with self.assertRaises(FileExistsError):
                self.harness.make_snapshot(ROOT, tmp / "snapshot")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_comparisons_are_invalid_when_cells_ran_different_revisions_or_the_snapshot_changed(self):
        rows = [{"task": "t1", "system": "baseline", "attempt": 1, "status": "completed", "revision_digest": "a" * 64},
                {"task": "t1", "system": "attest", "attempt": 1, "status": "completed", "revision_digest": "b" * 64},
                {"task": "t2", "system": "baseline", "attempt": 1, "status": "completed", "revision_digest": "a" * 64},
                {"task": "t2", "system": "attest", "attempt": 1, "status": "not_run"}]
        validity = self.harness.comparison_validity(rows, "a" * 64, snapshot_intact=True)
        self.assertFalse(validity["t1"]["valid"])
        self.assertIn("differs from the registered", validity["t1"]["reasons"][0])
        self.assertTrue(validity["t2"]["valid"])
        validity = self.harness.comparison_validity(rows, "a" * 64, snapshot_intact=False)
        self.assertFalse(validity["t2"]["valid"])
        for row in rows:
            row["confusion"] = "unknown"
        summary = self.harness.summarize(rows, ["baseline", "attest"], validity)
        self.assertEqual(summary["attest"]["cells_in_invalid_comparisons"], 2)

    def test_launcher_refuses_nebius_without_approval_and_resume_without_schedule(self):
        with redirect_stdout(io.StringIO()):
            with mock.patch("sys.stderr", new=io.StringIO()) as err:
                self.assertEqual(self.harness.main(["--provider", "nebius"]), 2)
                self.assertIn("explicit batch approval", err.getvalue())
            with mock.patch("sys.stderr", new=io.StringIO()) as err:
                self.assertEqual(self.harness.main(["--resume", tempfile.mkdtemp(prefix="attest-noresume-")]), 2)
                self.assertIn("no schedule.json", err.getvalue())

    def test_runtime_provenance_refuses_a_package_outside_the_snapshot(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-snap2-"))
        try:
            self.harness.make_snapshot(ROOT, tmp / "snapshot")
            with self.assertRaises(SystemExit) as cm:
                self.harness.runtime_provenance(tmp / "snapshot", ROOT)
            self.assertIn("not the snapshot", str(cm.exception))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()


class GovernorPolicy(unittest.TestCase):
    def test_declared_policy_disables_or_sets_the_hourly_window(self):
        clock = FakeClock()
        gov = RateGovernor("k", time_fn=clock.time, sleep_fn=clock.sleep)
        self.assertEqual(gov.budget, 54)
        gov.configure_from_status({"limits": {"hourly_requests": None, "hourly_requests_enforced": False, "max_concurrent_requests": 1, "max_waiting_requests": 8}})
        self.assertIsNone(gov.budget)
        self.assertIn("not enforced", gov.policy_source)
        for _ in range(200):
            self.assertEqual(gov.acquire()["waited_s"], 0.0)  # no window: never waits for an hourly budget
            gov.release()
        self.assertIsNone(gov.headroom())
        self.assertEqual(gov.wait_for_headroom(15), 0.0)
        until = gov.record_rejection(retry_after_s=90)  # a 429 (queue full, daily cap) still blocks the key
        self.assertEqual(gov.acquire()["waited_s"], 90.0)
        gov.release()
        gov.configure_from_status({"limits": {"hourly_requests": 120, "hourly_requests_enforced": True}})
        self.assertEqual((gov.hourly_limit, gov.budget), (120, 108))
        gov.configure_from_status({"no": "limits"})
        self.assertEqual(gov.budget, 108)
        self.assertIn("no limits declared", gov.policy_source)
        self.assertIn("no hourly window", gov.snapshot()["model"]) if gov.budget is None else self.assertIn("rolling window", gov.snapshot()["model"])

    def test_client_adopts_the_gateway_policy_before_the_first_request(self):
        clock = FakeClock()
        gov = RateGovernor("k", time_fn=clock.time, sleep_fn=clock.sleep)
        ledger = Ledger()
        client = CodexGateway("cxk_test", ledger, governor=gov)
        client._catalog = {"gpt-6-sol": ["medium"]}
        ok = {"model": "gpt-6-sol", "effort": "medium", "json": {"result": 4}, "output": "{}", "usage": {}, "duration_ms": 1}
        status = {"limits": {"hourly_requests": None, "hourly_requests_enforced": False, "max_concurrent_requests": 1}}

        def fake_request(method, url, headers, payload=None, timeout=60, max_bytes=0):
            if url.endswith("/status"):
                return 200, status, {}
            return 200, ok, {}
        with mock.patch("attest.models.codex_gateway.request_json", fake_request):
            client.structured("implement", "p", {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}, "s")
        self.assertIsNone(gov.budget)
        self.assertIn("not enforced", client.describe()["pacing"]["policy_source"])
        # describe() itself adopts the policy, so a bundle's provenance shows the adopted policy even before the first call
        gov3 = RateGovernor("k3", time_fn=clock.time, sleep_fn=clock.sleep)
        client3 = CodexGateway("cxk_test", ledger, governor=gov3)
        with mock.patch("attest.models.codex_gateway.request_json", fake_request):
            self.assertIn("not enforced", client3.describe()["pacing"]["policy_source"])
        self.assertIsNone(gov3.budget)

        def failing_status(method, url, headers, payload=None, timeout=60, max_bytes=0):
            if url.endswith("/status"):
                raise TransportError("timed out")
            return 200, ok, {}
        gov2 = RateGovernor("k2", time_fn=clock.time, sleep_fn=clock.sleep)
        client2 = CodexGateway("cxk_test", ledger, governor=gov2)
        client2._catalog = {"gpt-6-sol": ["medium"]}
        with mock.patch("attest.models.codex_gateway.request_json", failing_status):
            client2.structured("implement", "p", {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}, "s")
        self.assertEqual(gov2.budget, 54)  # unreadable policy keeps the conservative default
        self.assertIn("status unreadable", gov2.policy_source)


class StrictSchemas(unittest.TestCase):
    """Both providers run structured output in strict mode: every object property must be listed in `required`, every
    object must forbid additional properties. An optional field is nullable, never missing from `required` (the external
    run of 17 Oct lost its arbitration to HTTP 502 'required is required to include every key in properties')."""

    def test_every_schema_is_strict_mode_compatible(self):
        from attest.core import prompts

        def walk(node, path):
            if not isinstance(node, dict):
                return
            if node.get("type") == "object" or "properties" in node:
                props = node.get("properties") or {}
                self.assertEqual(node.get("additionalProperties"), False, f"{path}: additionalProperties must be false")
                self.assertEqual(sorted(node.get("required") or []), sorted(props), f"{path}: required must list every property")
                for name, child in props.items():
                    walk(child, f"{path}.{name}")
            if "items" in node:
                walk(node["items"], f"{path}[]")
        for name in ("SPEC_SCHEMA", "DRIFT_SCHEMA", "SEAL_SCHEMA", "BREAKER_SCHEMA", "ARBITRATION_SCHEMA", "ACTION_SCHEMA", "CONTRACT_AUDIT_SCHEMA"):
            walk(getattr(prompts, name), name)


class MutationIncomplete(unittest.TestCase):
    """A mutation gate held because mutants could not be evaluated (no survivor) names the infrastructure cause, not the tests."""

    def test_unknown_mutants_without_survivors_is_its_own_reason_class(self):
        bundle = {"verdict": {"verdict": "NEEDS HUMAN", "reasons": ["mutation gate incomplete: only 3 of 4 mutants could be evaluated (1 unknown)"]},
                  "candidate": {"implementer_finished": True, "scope_ok": True},
                  "gates": {"existing_suite": {"ok": True}, "sealed_binding": {"ok": True}, "mutation": {"ok": False, "detail": "only 3 of 4"},
                            "adversarial_tests": {"ok": True}, "drift_audit": {"ok": True}},
                  "verification": {"binding": {"ok": True, "checks": {}}, "sealed": {"tests": []}},
                  "breaker": {"mutation": {"generated": 4, "evaluated": 3, "killed": 3, "survived": 0, "unknown": 1, "score": 1.0, "threshold": 0.5,
                                           "mutants": [{"id": "m04", "status": "unknown", "error": "SandboxError: spawn outcome uncertain"}]},
                              "adversarial": {"summary": {"ran": 5, "passed": 5, "failing": 0, "all_passed": True, "tests": []}, "binding": {"ok": True, "checks": {}}}},
                  "task": {"title": "t"}, "spec": {}}
        self.assertEqual(exhibits_module.reason_class(bundle), "mutation_incomplete")
        decision = exhibits_module.decision(bundle)
        self.assertIn("could not be evaluated", decision["explanation"])
        self.assertIn("not a finding against the patch", decision["explanation"])
        self.assertNotIn("surviving mutants", " ".join(decision["decide"]))
        bundle["breaker"]["mutation"].update({"survived": 1, "killed": 2, "score": 0.667})
        self.assertEqual(exhibits_module.reason_class(bundle), "mutation_failed")


class SealerSelfErrors(unittest.TestCase):
    """A sealed test that crashes inside its own body on the unmodified code is a defective test; the red check sends it back."""

    def test_test_internal_errors_detects_unpacking_bugs_but_not_missing_behaviour(self):
        from attest.core.pipeline import test_internal_errors
        tests = [
            {"id": "test_sealed.T.test_bug", "outcome": "ERROR", "failure_tail": 'Traceback (most recent call last):\n  File "/tmp/sealed/test_sealed.py", line 12, in test_bug\n    for a, b in ((1, 2, 3),):\nValueError: too many values to unpack (expected 2)'},
            {"id": "test_sealed.T.test_missing", "outcome": "ERROR", "failure_tail": 'Traceback (most recent call last):\n  File "/tmp/sealed/test_sealed.py", line 20, in test_missing\n    to_roman(4)\n  File "/tmp/w/roman/core.py", line 9, in to_roman\n    raise NotImplementedError("x")\nNotImplementedError: x'},
            {"id": "test_sealed.T.test_attr", "outcome": "ERROR", "failure_tail": 'Traceback (most recent call last):\n  File "/tmp/sealed/test_sealed.py", line 30, in test_attr\n    m.new_function()\nAttributeError: module m has no attribute new_function'},
            {"id": "test_sealed.T.test_assert", "outcome": "FAIL", "failure_tail": 'Traceback (most recent call last):\n  File "/tmp/sealed/test_sealed.py", line 40, in test_assert\n    self.assertEqual(f(1), 2)\nAssertionError: 1 != 2'},
        ]
        found = test_internal_errors(tests)
        self.assertEqual(found, ["test_bug: ValueError: too many values to unpack (expected 2)"])

    def test_arbitration_headline_is_honest_when_the_mutation_check_was_skipped(self):
        bundle = run_scenario("arb_clear_sealed") if False else None  # the fake cannot produce a sealed failure with a clean correction; covered by the headline unit below
        from attest.core import exhibits as ex
        bundle = {"verdict": {"verdict": "NEEDS HUMAN", "reasons": ["x"]}, "candidate": {"implementer_finished": True, "scope_ok": True},
                  "gates": {"existing_suite": {"ok": True}, "sealed_binding": {"ok": False}, "mutation": {"ok": False, "skipped": True},
                            "adversarial_tests": {"ok": False, "skipped": True}, "drift_audit": {"ok": True}},
                  "sealed_tests": {"test_count": 20}, "red_run": {"ran": 20, "failing": 8},
                  "verification": {"binding": {"ok": False, "checks": {"all_expected_pass": False}}, "sealed": {"tests": [{"id": "test_sealed.T.test_bug", "outcome": "ERROR", "failure_tail": "ValueError: too many values to unpack (expected 2)"}], "passed": 19, "failing": 1, "ran": 20}},
                  "arbitration": {"counts": {"implementation_bug": 0, "test_defect": 1, "contract_dispute": 0}, "cleared": False, "all_corrected": True, "mutation_ran_ok": False,
                                  "headline": "h", "modules": [{"module": "sealed", "classifications": [{"test_id": "test_sealed.T.test_bug", "classification": "test_defect", "defect_kind": "other", "rationale": "r", "contract_basis": "c"}],
                                                                 "cleared_module": True}]},
                  "task": {"title": "t"}, "spec": {}}
        decision = ex.decision(bundle)
        self.assertEqual(decision["reason_class"], "sealed_failed")
        self.assertIn("arbiter classified every failing sealed test as defective", decision["explanation"])
        self.assertIn("corrected tests pass on the candidate and still fail on the base", decision["explanation"])


class MessageAssertionRule(unittest.TestCase):
    def test_seal_and_breaker_prompts_forbid_asserting_on_exception_messages(self):
        from attest.core.prompts import seal_prompt
        class Task:
            import_hint = "from pkg import f"
            allowed_write_globs = ["pkg/**"]
        spec = {"restated_task": "r", "interface_contract": [], "acceptance_criteria": []}
        self.assertIn("never assert on exception message text", seal_prompt(Task(), spec, {"pkg/__init__.py": b""}, None))
        self.assertIn("Assert exception types, never exception message text", breaker_prompt(Task(), spec, "diff", [], per_test_timeout=60))


class NebiusReasoningRunaway(unittest.TestCase):
    """A Nemotron answer that spent its whole completion budget on reasoning (finish_reason=length, no content) is retried once at
    low reasoning effort; both attempts are in the ledger; a second runaway fails visibly."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-runaway-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _client(self, responses):
        from attest.ledger import JOURNAL_FILE
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        ledger = Ledger()
        ledger.attach_sink(self.tmp / JOURNAL_FILE)  # a reservation needs a journal before any request is sent (audit finding AC-03)
        client = NebiusTokenFactory("key", ledger, usd_cap=0.5)
        sent = []

        def fake_request(method, url, headers, payload=None, timeout=60, max_bytes=0):
            sent.append(payload)
            body = responses.pop(0)
            return 200, body, {}
        return client, ledger, sent, fake_request

    @staticmethod
    def _answer(content, finish, reasoning):
        return {"model": "nvidia/nemotron-3-super-120b-a12b", "choices": [{"message": {"content": content}, "finish_reason": finish}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 16000 if finish == "length" else 200, "completion_tokens_details": {"reasoning_tokens": reasoning}}}

    def test_length_runaway_is_retried_once_at_low_effort(self):
        schema = {"type": "object", "additionalProperties": False, "properties": {"x": {"type": "integer"}}, "required": ["x"]}
        client, ledger, sent, fake = self._client([self._answer("", "length", 16000), self._answer('{"x": 1}', "stop", 40)])
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            result = client.structured("seal", "prompt", schema, "seal-1")
        self.assertEqual(result.json, {"x": 1})
        self.assertEqual(sent[0]["reasoning_effort"], "low")  # the sealer runs at low effort by default
        self.assertEqual(sent[1]["reasoning_effort"], "low")
        self.assertEqual([c.stage for c in ledger.model_calls], ["seal-1", "seal-1-lowretry"])
        self.assertFalse(ledger.model_calls[0].ok)
        self.assertIn("finish_reason=length", ledger.model_calls[0].error)
        self.assertTrue(ledger.model_calls[1].ok)
        self.assertGreater(ledger.totals()["cost_usd_committed"], 0)

    def test_second_runaway_fails_visibly_and_implementer_uses_medium(self):
        schema = {"type": "object", "additionalProperties": False, "properties": {"x": {"type": "integer"}}, "required": ["x"]}
        client, ledger, sent, fake = self._client([self._answer("", "length", 16000), self._answer("", "length", 16000)])
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            with self.assertRaises(ModelError) as cm:
                client.structured("implement", "prompt", schema, "implement-1")
        self.assertIn("finish_reason=length", str(cm.exception))
        self.assertEqual(sent[0]["reasoning_effort"], "medium")
        self.assertEqual(sent[1]["reasoning_effort"], "low")
        self.assertEqual(len(ledger.model_calls), 2)
        self.assertEqual(client.describe()["reasoning_effort"], {"seal": "low", "implement": "medium", "break": "low", "summary": "low"})
