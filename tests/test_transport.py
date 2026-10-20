"""Transport phases and safe retries (revision 8, 19 Oct 2026).

The client classifies a failure by how far the request got: a failure while the connection is being set up (TCP, the proxy's
CONNECT tunnel, the TLS handshake) means no byte of the request was written, so sending it again is safe; any later failure
leaves the outcome uncertain. These tests drive the real client against servers on the loopback interface that fail at each
point, including a CONNECT proxy that accepts the tunnel and then drops it (the failure mode observed on 19 Oct through this
machine's proxy). Connections to any address other than 127.0.0.1 are refused for the whole module."""

from __future__ import annotations

import contextlib
import os
import socket
import threading
import time
import unittest
from unittest import mock

import attest.http as http_module
from attest.http import TransportError, request_json


@contextlib.contextmanager
def explicit_proxy_allowed():
    """The offline suite sets no_proxy=* (tests/_isolation.py), so that no request takes this machine's proxy; a test that drives a proxy
    of its own on the loopback interface lifts that for its duration."""
    with mock.patch.dict(os.environ):
        os.environ.pop("no_proxy", None)
        os.environ.pop("NO_PROXY", None)
        yield

_real_create_connection = socket.create_connection


def _loopback_only(address, *args, **kwargs):
    host = address[0]
    if host not in ("127.0.0.1", "localhost"):
        raise AssertionError(f"network access outside the loopback interface is forbidden in these tests: {host}")
    return _real_create_connection(address, *args, **kwargs)


class _Server:
    """A one-shot TCP server on 127.0.0.1 whose handler decides how to fail."""

    def __init__(self, handler):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(4)
        self.port = self.sock.getsockname()[1]
        self.handler = handler
        self.received = b""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            conn, _ = self.sock.accept()
        except OSError:
            return
        with conn:
            try:
                self.handler(self, conn)
            except OSError:
                pass

    def read_until(self, conn, marker: bytes, limit: int = 1 << 20):
        conn.settimeout(5)
        while marker not in self.received and len(self.received) < limit:
            chunk = conn.recv(65536)
            if not chunk:
                break
            self.received += chunk

    def close(self):
        self.sock.close()
        self.thread.join(5)


class Phases(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(socket, "create_connection", _loopback_only)
        patcher.start()
        self.addCleanup(patcher.stop)
        # requests to 127.0.0.1 go straight to the test server: no system proxy is consulted
        direct = http_module.build_opener(proxies={})
        patcher = mock.patch.object(http_module, "opener", lambda: direct)
        patcher.start()
        self.addCleanup(patcher.stop)

    def serve(self, handler):
        server = _Server(handler)
        self.addCleanup(server.close)
        return server

    def test_tls_handshake_dropped_by_the_server_is_not_sent(self):
        server = self.serve(lambda s, conn: conn.close())
        with self.assertRaises(TransportError) as caught:
            request_json("POST", f"https://127.0.0.1:{server.port}/v1/run", {}, {"prompt": "x"}, timeout=5)
        self.assertFalse(caught.exception.request_sent)
        self.assertEqual(caught.exception.phase, "connect")
        self.assertIn("no byte of the request was sent", str(caught.exception))

    def test_tls_handshake_timeout_is_not_sent(self):
        server = self.serve(lambda s, conn: time.sleep(2.5))
        with self.assertRaises(TransportError) as caught:
            request_json("POST", f"https://127.0.0.1:{server.port}/instances", {}, {"command": "x"}, timeout=1)
        self.assertFalse(caught.exception.request_sent)
        self.assertEqual(caught.exception.phase, "connect")

    def test_proxy_that_accepts_the_tunnel_and_drops_it_is_not_sent(self):
        def proxy(s, conn):
            s.read_until(conn, b"\r\n\r\n")
            conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            conn.close()  # the proxy's upstream failed: the client's TLS handshake sees an end of file
        server = self.serve(proxy)
        via_proxy = http_module.build_opener(proxies={"https": f"http://127.0.0.1:{server.port}"})
        with explicit_proxy_allowed(), mock.patch.object(http_module, "opener", lambda: via_proxy):
            with self.assertRaises(TransportError) as caught:
                request_json("POST", "https://gateway.invalid/v1/run", {"Authorization": "Bearer secret"}, {"prompt": "x"}, timeout=5)
        self.assertFalse(caught.exception.request_sent)
        self.assertEqual(caught.exception.phase, "connect")
        self.assertTrue(server.received.startswith(b"CONNECT gateway.invalid:443"))
        self.assertNotIn(b"secret", server.received)  # the proxy saw the tunnel request only, never the request or its headers

    def test_proxy_that_refuses_the_tunnel_is_not_sent(self):
        def proxy(s, conn):
            s.read_until(conn, b"\r\n\r\n")
            conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
        server = self.serve(proxy)
        via_proxy = http_module.build_opener(proxies={"https": f"http://127.0.0.1:{server.port}"})
        with explicit_proxy_allowed(), mock.patch.object(http_module, "opener", lambda: via_proxy):
            with self.assertRaises(TransportError) as caught:
                request_json("POST", "https://gateway.invalid/v1/run", {}, {"prompt": "x"}, timeout=5)
        self.assertFalse(caught.exception.request_sent)

    def test_request_written_but_unanswered_is_uncertain(self):
        def swallow(s, conn):
            s.read_until(conn, b'"x"}')
            conn.close()  # read the whole request, answer nothing: the observed RemoteDisconnected
        server = self.serve(swallow)
        with self.assertRaises(TransportError) as caught:
            request_json("POST", f"http://127.0.0.1:{server.port}/v1/run", {}, {"prompt": "x"}, timeout=5)
        self.assertTrue(caught.exception.request_sent)
        self.assertEqual(caught.exception.phase, "response")
        self.assertIn(b"POST /v1/run", server.received)

    def test_body_cut_while_sending_is_uncertain(self):
        def cut(s, conn):
            s.read_until(conn, b"\r\n\r\n")
            conn.recv(1024)
            conn.close()  # headers and part of the body arrived, then the connection went away (the observed nginx 408 case)
        server = self.serve(cut)
        with self.assertRaises(TransportError) as caught:
            request_json("POST", f"http://127.0.0.1:{server.port}/v1/run", {}, {"prompt": "y" * 4_000_000}, timeout=5)
        self.assertTrue(caught.exception.request_sent)
        self.assertIn(caught.exception.phase, ("send", "response"))

    def test_an_answer_is_returned_and_a_cut_answer_is_uncertain(self):
        def answer(s, conn):
            s.read_until(conn, b"\r\n\r\n")
            conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 12\r\n\r\n{"ok": true}')
        server = self.serve(answer)
        status, body, _ = request_json("GET", f"http://127.0.0.1:{server.port}/v1/status", {}, timeout=5)
        self.assertEqual((status, body), (200, {"ok": True}))

        def cut_answer(s, conn):
            s.read_until(conn, b"\r\n\r\n")
            conn.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 400\r\n\r\n{"json": ')
        server = self.serve(cut_answer)
        with self.assertRaises(TransportError) as caught:
            request_json("POST", f"http://127.0.0.1:{server.port}/v1/run", {}, {"prompt": "x"}, timeout=5)
        self.assertTrue(caught.exception.request_sent)

    def test_an_error_without_a_recorded_phase_is_treated_as_sent(self):
        self.assertTrue(TransportError("timed out").request_sent)
        self.assertEqual(TransportError("timed out").phase, "unknown")


if __name__ == "__main__":
    unittest.main()


# ----------------------------------------------------------------------------- the adapters' retry rules
import json  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from attest.core.diagnostics import classify_error  # noqa: E402
from attest.ledger import JOURNAL_FILE, Ledger, read_journal  # noqa: E402
from attest.models.base import ModelError  # noqa: E402
from attest.models.codex_gateway import CodexGateway  # noqa: E402
from attest.models.nebius_tokenfactory import NebiusTokenFactory  # noqa: E402
from attest.models.pacing import RateGovernor  # noqa: E402
from attest.sandbox.tf_sandboxes import SandboxError, TokenFactorySandboxes  # noqa: E402

NOT_SENT = lambda: TransportError("URLError: EOF in violation of protocol (while the connection was being set up)", request_sent=False, phase="connect")  # noqa: E731
LOST = lambda: TransportError("RemoteDisconnected: Remote end closed connection without response", request_sent=True, phase="response")  # noqa: E731
SCHEMA = {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}


def journaled(test: unittest.TestCase) -> Ledger:
    """A ledger with a journal in a temporary directory: every call and operation takes a pending record before it is sent (revision 9)."""
    import shutil
    directory = Path(tempfile.mkdtemp(prefix="attest-transport-journal-"))
    test.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
    ledger = Ledger()
    ledger.attach_sink(directory / JOURNAL_FILE)
    return ledger


class FakeClock:
    def __init__(self):
        self.now, self.slept = 1_700_000_000.0, []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.slept.append(seconds)


class GatewayRetries(unittest.TestCase):
    """The development gateway client: a request that was never sent is sent again (bounded, every attempt recorded); a request
    whose bytes were written is never sent again; reads are retried on any failure."""

    def client(self, outcomes):
        clock = FakeClock()
        gov = RateGovernor("k", time_fn=clock.time, sleep_fn=clock.sleep)
        gov.configure_from_status({"limits": {"hourly_requests": None, "hourly_requests_enforced": False}})
        ledger = journaled(self)
        client = CodexGateway("cxk_test", ledger, base_url="https://gateway.invalid/v1", governor=gov, notify=lambda m: None)
        client._catalog = {"gpt-6-sol": ["medium"], "gpt-6-astra": ["low", "medium"], "gpt-6-luna": ["low"]}
        sent = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            if url.endswith("/status"):
                return 200, {"limits": {"hourly_requests_enforced": False}}, {}
            sent.append(method)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 200, outcome, {}
        return client, ledger, gov, clock, sent, fake

    OK = {"model": "gpt-6-sol", "effort": "medium", "json": {"result": 4}, "output": '{"result": 4}', "usage": {"input_tokens": 9, "output_tokens": 2}, "duration_ms": 5}

    def test_a_request_that_was_never_sent_is_sent_again_and_both_attempts_are_recorded(self):
        client, ledger, gov, clock, sent, fake = self.client([NOT_SENT(), dict(self.OK)])
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            result = client.structured("implement", "p", SCHEMA, "implement-1")
        self.assertEqual(result.json, {"result": 4})
        self.assertEqual(sent, ["POST", "POST"])
        first, second = ledger.model_calls
        self.assertEqual((first.ok, first.request_sent, first.transport_phase, first.attempt), (False, False, "connect", 1))
        self.assertIn("never sent", first.error)
        self.assertEqual((second.ok, second.request_sent, second.attempt), (True, True, 2))
        self.assertEqual(clock.slept, [2.0])
        self.assertEqual(ledger.totals()["calls_not_sent"], 1)
        self.assertEqual(gov.in_flight, 0)

    def test_three_unsent_attempts_fail_definitely_not_uncertain(self):
        client, ledger, gov, clock, sent, fake = self.client([NOT_SENT(), NOT_SENT(), NOT_SENT()])
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            with self.assertRaises(ModelError) as caught:
                client.structured("implement", "p", SCHEMA, "implement-1")
        self.assertTrue(caught.exception.unreachable)
        self.assertFalse(caught.exception.uncertain)
        self.assertEqual(len(sent), 3)
        self.assertEqual(classify_error(caught.exception)[0], "provider_unreachable")
        self.assertNotIn("gateway.invalid", str(caught.exception))  # the gateway's host never enters a public text
        self.assertEqual(clock.slept, [2.0, 6.0])

    def test_a_written_request_is_never_sent_again(self):
        client, ledger, gov, clock, sent, fake = self.client([NOT_SENT(), LOST(), dict(self.OK)])
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            with self.assertRaises(ModelError) as caught:
                client.structured("implement", "p", SCHEMA, "implement-1")
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(sent, ["POST", "POST"], "after the lost answer nothing is sent")
        self.assertEqual([c.request_sent for c in ledger.model_calls], [False, True])
        self.assertEqual(classify_error(caught.exception)[0], "provider_transport_uncertain")

    def test_reads_are_retried_on_any_transport_failure(self):
        client, ledger, gov, clock, sent, fake = self.client([])
        calls = []

        def flaky_catalog(method, url, headers, payload=None, timeout=60, max_bytes=0):
            calls.append(url)
            if len(calls) <= 2:
                raise LOST() if len(calls) == 1 else NOT_SENT()
            return 200, {"data": [{"id": "gpt-6-sol", "supported_reasoning_efforts": ["medium"]}]}, {}
        client._catalog = None
        with mock.patch("attest.models.codex_gateway.request_json", flaky_catalog):
            self.assertEqual(client.catalog(), {"gpt-6-sol": ["medium"]})
        self.assertEqual(len(calls), 3)
        self.assertEqual(clock.slept, [1.0, 2.0])


class TokenFactoryRetries(unittest.TestCase):
    """The paid provider: a never-sent attempt closes its reservation at a known zero and is sent again under a new reservation;
    the committed figure counts only what may have been billed. Nothing here touches the network (every request is a fake)."""

    def provider(self, outcomes, **kwargs):
        run_dir = Path(tempfile.mkdtemp(prefix="attest-transport-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(run_dir, ignore_errors=True))
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        provider = NebiusTokenFactory("synthetic-key", ledger, usd_cap=0.5, max_calls=kwargs.get("max_calls", 22))
        slept = []
        provider._sleep = slept.append
        sent = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            sent.append(method)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return 200, outcome, {}
        return provider, ledger, run_dir, sent, slept, fake

    ANSWER = {"model": "nvidia/nemotron-3-super-120b-a12b", "usage": {"prompt_tokens": 1000, "completion_tokens": 100},
              "choices": [{"message": {"content": '{"result": 4}'}, "finish_reason": "stop"}]}

    def test_a_never_sent_attempt_costs_nothing_and_is_sent_again(self):
        provider, ledger, run_dir, sent, slept, fake = self.provider([NOT_SENT(), dict(self.ANSWER)])
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            result = provider.structured("implement", "p", SCHEMA, "implement-1")
        self.assertEqual(result.json, {"result": 4})
        self.assertEqual(sent, ["POST", "POST"])
        first, second = ledger.model_calls
        self.assertEqual((first.request_sent, first.cost_usd, first.settlement), (False, 0.0, "known"))
        self.assertTrue(second.ok)
        totals = ledger.totals()
        self.assertEqual(totals["open_reservations"], 0)
        self.assertAlmostEqual(totals["cost_usd_committed"], second.cost_usd, places=9, msg="only the answered call is committed")
        journal = read_journal(run_dir / JOURNAL_FILE)
        self.assertEqual((journal["open_reservations"], journal["model_calls"]), (0, 2))
        self.assertAlmostEqual(journal["cost_usd_committed"], second.cost_usd, places=9)
        self.assertEqual(slept, [2.0])

    def test_exhausted_unsent_attempts_commit_nothing(self):
        provider, ledger, run_dir, sent, slept, fake = self.provider([NOT_SENT(), NOT_SENT(), NOT_SENT()])
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            with self.assertRaises(ModelError) as caught:
                provider.structured("implement", "p", SCHEMA, "implement-1")
        self.assertTrue(caught.exception.unreachable)
        self.assertEqual(len(sent), 3)
        self.assertEqual(ledger.totals()["cost_usd_committed"], 0.0)
        self.assertEqual(read_journal(run_dir / JOURNAL_FILE)["cost_usd_committed"], 0.0)

    def test_a_lost_answer_keeps_its_reservation_committed_and_is_never_resent(self):
        provider, ledger, run_dir, sent, slept, fake = self.provider([LOST(), dict(self.ANSWER)])
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            with self.assertRaises(ModelError) as caught:
                provider.structured("implement", "p", SCHEMA, "implement-1")
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(sent, ["POST"])
        call = ledger.model_calls[0]
        self.assertEqual((call.settlement, call.cost_usd), ("unsettled", None))
        self.assertGreater(ledger.totals()["cost_usd_committed"], 0.0)

    def test_the_call_cap_also_bounds_resends(self):
        provider, ledger, run_dir, sent, slept, fake = self.provider([NOT_SENT(), dict(self.ANSWER)], max_calls=1)
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            with self.assertRaises(ModelError) as caught:
                provider.structured("implement", "p", SCHEMA, "implement-1")
        self.assertTrue(caught.exception.unreachable)
        self.assertEqual(sent, ["POST"], "the cap counts the unsent attempt, so no second request is made")


class SandboxRetries(unittest.TestCase):
    """The sandbox adapter: spawns are resent only when never sent, polls are retried, the accepted id is journaled before polling,
    and an accepted operation whose outcome cannot be read is kept for reconciliation, never spawned again."""

    def executor(self, script):
        run_dir = Path(tempfile.mkdtemp(prefix="attest-transport-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(run_dir, ignore_errors=True))
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        ex = TokenFactorySandboxes("synthetic-key", "project", ledger, poll_interval=0)
        ex._sleep = lambda s: None
        seen = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            seen.append((method, url.split("/v1")[-1]))
            outcome = script(method, url, len(seen))
            if isinstance(outcome, Exception):
                raise outcome
            return 200, outcome, {}
        return ex, ledger, run_dir, seen, fake

    @staticmethod
    def done(uuid="01a2-op"):
        report = {"runner": "attest-guest/3", "steps": [{"name": "s", "cmd": ["true"], "exit_code": 0, "timed_out": False, "stdout": "", "stderr": "", "duration_s": 0.1}]}
        stdout = "ATTEST-RESULT-BEGIN\n" + json.dumps(report) + "\nATTEST-RESULT-END\n"
        return {"uuid": uuid, "status": "SUCCESS", "duration": 0.5, "metadata": {"result": {"state": {"exit_code": 0, "timed_out": False, "signal": -1},
                "stdout": {"value": stdout}, "stderr": {"value": ""}, "resources": {"cost": 0.0001}}}}

    def test_a_never_sent_spawn_is_sent_again_and_the_accepted_id_is_journaled_before_polling(self):
        def script(method, url, n):
            if method == "POST":
                return NOT_SENT() if n == 1 else {"uuid": "01a2-op"}
            return self.done()
        ex, ledger, run_dir, seen, fake = self.executor(script)
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            run = ex.run_branch("image-1", {}, [{"name": "s", "cmd": ["true"]}], stage="verify")
        self.assertTrue(run.ok)
        self.assertEqual([m for m, _ in seen], ["POST", "POST", "GET"])
        op = ledger.sandbox_ops[0]
        self.assertEqual((op.attempts, op.status, len(op.transport_failures)), (2, "SUCCESS", 1))
        self.assertFalse(op.transport_failures[0]["request_sent"])
        lines = [json.loads(l) for l in (run_dir / JOURNAL_FILE).read_text().splitlines()]
        updates = [l for l in lines if l.get("event") == "sandbox_op_update"]
        self.assertEqual([u["status"] for u in updates], ["ACCEPTED", "SUCCESS"], "the accepted id is journaled before the outcome")
        self.assertEqual(updates[0]["operation_uuid"], "01a2-op")
        self.assertEqual(ledger.totals()["sandbox_spawn_retries"], 1)

    def test_a_spawn_whose_answer_was_lost_is_uncertain_and_never_sent_again(self):
        ex, ledger, run_dir, seen, fake = self.executor(lambda method, url, n: LOST())
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            with self.assertRaises(SandboxError) as caught:
                ex.run_branch("image-1", {}, [{"name": "s", "cmd": ["true"]}], stage="verify")
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(seen, [("POST", "/instances")])
        self.assertEqual(ledger.sandbox_ops[0].status, "UNCERTAIN")
        self.assertEqual(classify_error(caught.exception)[0], "sandbox_uncertain")
        self.assertIn("a sandbox operation's outcome is uncertain", ledger.sandbox_ops[0].transport_failures[0]["error"])

    def test_spawns_that_never_left_fail_definitely(self):
        ex, ledger, run_dir, seen, fake = self.executor(lambda method, url, n: NOT_SENT())
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            with self.assertRaises(SandboxError) as caught:
                ex.run_branch("image-1", {}, [{"name": "s", "cmd": ["true"]}], stage="verify")
        self.assertTrue(caught.exception.unreachable)
        self.assertFalse(caught.exception.uncertain)
        self.assertEqual(len(seen), 3)
        self.assertEqual(ledger.sandbox_ops[0].status, "NOT_SENT")
        self.assertEqual(classify_error(caught.exception)[0], "sandbox_unreachable")

    def test_polls_are_retried_and_an_unreadable_outcome_keeps_the_id_for_reconciliation(self):
        def flaky(method, url, n):
            if method == "POST":
                return {"uuid": "01a2-op"}
            return LOST() if n in (2, 3) else self.done()
        ex, ledger, run_dir, seen, fake = self.executor(flaky)
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            self.assertTrue(ex.run_branch("image-1", {}, [{"name": "s", "cmd": ["true"]}], stage="verify").ok)
        self.assertEqual([m for m, _ in seen], ["POST", "GET", "GET", "GET"])

        ex, ledger, run_dir, seen, fake = self.executor(lambda method, url, n: {"uuid": "01a2-op"} if method == "POST" else LOST())
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", fake):
            with self.assertRaises(SandboxError) as caught:
                ex.run_branch("image-1", {}, [{"name": "s", "cmd": ["true"]}], stage="verify")
        self.assertTrue(caught.exception.accepted_unread)
        self.assertEqual(caught.exception.operation_uuid, "01a2-op")
        self.assertEqual(sum(1 for m, _ in seen if m == "POST"), 1, "the accepted operation is never spawned again")
        self.assertEqual(ledger.sandbox_ops[0].status, "ACCEPTED_UNREAD")
        self.assertEqual(classify_error(caught.exception)[0], "sandbox_accepted_unread")
        self.assertEqual(read_journal(run_dir / JOURNAL_FILE)["operations_unread"], ["01a2-op"])


class Reconciliation(unittest.TestCase):
    """The evaluation harness lists what an uncertain cell leaves to settle, and the console's restart recovery names accepted
    operations whose outcome a run never read."""

    def test_the_harness_lists_uncertain_calls_and_operations(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_evaluation", Path(__file__).resolve().parents[1] / "scripts" / "run_evaluation.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        clock = FakeClock()
        gov = RateGovernor("k2", time_fn=clock.time, sleep_fn=clock.sleep)
        ledger = journaled(self)
        client = CodexGateway("cxk_test", ledger, base_url="https://gateway.invalid/v1", governor=gov)
        client._catalog = {"gpt-6-sol": ["medium"]}
        outcomes = [NOT_SENT(), LOST()]

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            if url.endswith("/status"):
                return 200, {}, {}
            raise outcomes.pop(0)
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            with self.assertRaises(ModelError):
                client.structured("implement", "p", SCHEMA, "implement-1")
        ledger.halted, ledger.halt_events = None, []  # the second half is another run's spawn on the same records (revision 9 halts the first)
        ex = TokenFactorySandboxes("synthetic-key", "project", ledger)
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", lambda *a, **k: (_ for _ in ()).throw(LOST())):
            with self.assertRaises(SandboxError):
                ex.run_branch("image-1", {}, [], stage="verify")
        items = module.reconciliation_items(ledger)
        # revision 9: a spawn without a known id is a `sandbox_spawn` (settled by listing the account's operations), one with its id a
        # `sandbox_operation` (settled by reading it)
        self.assertEqual([i["kind"] for i in items], ["model_call", "sandbox_spawn"], "the unsent attempt needs no reconciliation")
        self.assertEqual(items[0]["phase"], "response")
        self.assertIn("GET /operations?kind=instance", items[1]["how"])
        self.assertEqual(items[1]["image_uuid"], "image-1")

    def test_restart_recovery_names_unread_accepted_operations(self):
        from attest.app.db import Store
        from attest.ledger import SandboxOp, utcnow
        root = Path(tempfile.mkdtemp(prefix="attest-transport-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        run_dir = root / "runs" / "interrupted-run"
        run_dir.mkdir(parents=True)
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        op = SandboxOp(stage="verify", operation_uuid=None, image_uuid="image-1", result_image_uuid=None, disposable=True, networking_enabled=False,
                       status=None, exit_code=None, timed_out=None, signal=None, duration_s=None, raw_cost_diag=None, stdout_truncated=None,
                       started_at_utc=utcnow())
        ledger.add_op(op)
        op.operation_uuid, op.status = "01a2-op", "ACCEPTED"
        ledger.update_op(op)  # the process dies here, while polling
        store = Store(root / "attest.db")
        store.create_run(run_id="interrupted-run", task_id="t", task_title="t", provider="codex", profile_label="development", status="running",
                         created_at=utcnow(), out_dir=str(run_dir), requester="team")
        outcome = store.finalize_interrupted("interrupted-run")
        self.assertEqual(outcome["operations_unread"], ["01a2-op"])
        self.assertIn("01a2-op", store.get_run("interrupted-run")["error"])


class CheckerTransportCounters(unittest.TestCase):
    """attest check recomputes the transport counters a revision-8 bundle carries: a forged count, or a cost charged to an attempt
    that was never sent, fails `ledger_totals`; the genuine bundle passes (the positive control)."""

    def test_forged_transport_counters_are_refused(self):
        import shutil as _shutil
        from tests.test_audit_core import failed_checks, kept_run, rewrite_bundle
        from attest.core.check import check_bundle
        bundle, run_dir, tmp = kept_run("honest")
        self.addCleanup(lambda: _shutil.rmtree(tmp, ignore_errors=True))
        clean = check_bundle(run_dir)
        self.assertTrue(clean["ok"], failed_checks(clean))
        self.assertIn("calls_not_sent", bundle["ledger"]["totals"])

        def forge_count(b):
            b["ledger"]["totals"]["calls_not_sent"] = 3
        rewrite_bundle(run_dir, forge_count)
        self.assertIn("ledger_totals", failed_checks(check_bundle(run_dir)))

        def forge_cost(b):
            b["ledger"]["totals"]["calls_not_sent"] = 1
            call = b["ledger"]["model_calls"][0]
            call["request_sent"] = False
            call["ok"] = False
            call["cost_usd"] = 0.25
            b["ledger"]["totals"]["model_calls_failed"] = sum(1 for c in b["ledger"]["model_calls"] if not c.get("ok"))
            usd = [c["cost_usd"] for c in b["ledger"]["model_calls"] if c.get("cost_usd") is not None]
            b["ledger"]["totals"]["cost_usd"] = round(sum(usd), 6) if usd else None
            b["ledger"]["totals"]["cost_usd_committed"] = round(sum(c["cost_usd"] if c.get("cost_usd") is not None else (c.get("reserved_usd") or 0.0)
                                                                    for c in b["ledger"]["model_calls"]), 6)
        rewrite_bundle(run_dir, forge_cost)
        detail = failed_checks(check_bundle(run_dir)).get("ledger_totals", "")
        self.assertIn("never sent carries a cost", detail)


class UncertainStopsTheRun(unittest.TestCase):
    """Revision 8: once a model call's outcome is uncertain the run sends nothing further and ends ERROR (uncertain, not retried):
    in sealing (whose next attempt would have sent the same prompt again), in the adversarial tests' authoring, in the drift audit
    and in arbitration, as already in the specification, the contract audit and the implementation loop. The offline pipeline and its
    fake provider are used; the wrapper fails the first call of one stage and records every call."""

    class UncertainAt:
        def __init__(self, inner, stage_prefix):
            self.inner, self.stage_prefix, self.calls, self.raised = inner, stage_prefix, [], False
            self.name = inner.name

        def __getattr__(self, attr):
            return getattr(self.inner, attr)

        def describe(self):
            return self.inner.describe()

        def structured(self, role, prompt, schema, stage):
            self.calls.append(stage)
            if not self.raised and stage.startswith(self.stage_prefix):
                self.raised = True
                raise ModelError("inference outcome uncertain (RemoteDisconnected: Remote end closed connection without response); not retried",
                                 uncertain=True)
            return self.inner.structured(role, prompt, schema, stage)

    def run_with(self, scenario, stage_prefix):
        import contextlib, io, shutil
        from attest.core.pipeline import Pipeline
        from attest.core.task import TaskSpec
        from tests.test_verification import TASK, FakeExecutor, FakeProvider
        tmp = Path(tempfile.mkdtemp(prefix="attest-uncertain-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        ledger = Ledger()
        provider = self.UncertainAt(FakeProvider(ledger, scenario), stage_prefix)
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=provider, executor=FakeExecutor(ledger, scenario), ledger=ledger, out_dir=tmp,
                            max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="test")
        with contextlib.redirect_stdout(io.StringIO()):
            bundle = pipeline.run()
        return bundle, provider

    def assert_stopped(self, bundle, provider, stage_prefix):
        self.assertTrue(provider.raised, f"the scenario never reached {stage_prefix}")
        self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
        self.assertIn("outcome uncertain; not retried", bundle["verdict"]["reasons"][0])
        failed_at = next(i for i, stage in enumerate(provider.calls) if stage.startswith(stage_prefix))
        self.assertEqual(len(provider.calls), failed_at + 1, f"calls after the uncertain one: {provider.calls[failed_at + 1:]}")

    def test_sealing_does_not_send_the_same_prompt_again(self):
        bundle, provider = self.run_with("honest", "seal-1")
        self.assert_stopped(bundle, provider, "seal-1")
        self.assertNotIn("seal-2", provider.calls)

    def test_adversarial_authoring_stops_the_run(self):
        bundle, provider = self.run_with("honest", "break-tests")
        self.assert_stopped(bundle, provider, "break-tests")

    def test_drift_audit_stops_the_run(self):
        bundle, provider = self.run_with("honest", "drift-audit")
        self.assert_stopped(bundle, provider, "drift-audit")

    def test_arbitration_stops_the_run(self):
        bundle, provider = self.run_with("arb_clear", "arbitrate")
        self.assert_stopped(bundle, provider, "arbitrate")

    def test_the_honest_run_without_failures_is_verified(self):
        bundle, provider = self.run_with("honest", "no-such-stage")
        self.assertFalse(provider.raised)
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED")
