"""Single background worker: runs one task at a time, streams progress into the store, enforces caps.

Supervision (API-07): the loop survives any failure of a run (any BaseException other than SystemExit/KeyboardInterrupt
is recorded on the row and the loop continues). If the thread does die, `ensure_alive()` restarts it, at most once per
RESTART_BACKOFF_S so a loop that dies on start cannot spin; `stop()` is a deliberate stop that is never undone by a
restart. Admission (`enqueue`) refuses work when no live thread exists, before any row or reservation is created.

Queue order (API-11): `_queued` mirrors the order of run ids in the queue under `_state_lock`, so `position(run_id)` is the
authoritative number of runs ahead of a run (0 while it executes).

Retention (API-06): `housekeeping()` applies the bounded retention after every job, successful or not, and whenever the
queue has been idle for `housekeeping_s`, so a period of failures still reclaims disk.

Reconciliation (revision 9, 20 Oct 2026): a run that stopped for reconciliation (its bundle's `reconciliation.required`, or a halted
ledger when the pipeline failed) is recorded as `reconciliation_required` and opens a hold in the store. While a hold is open the
worker starts nothing: admission raises `ReconciliationHold` (the API answers 503) and a queued run ends `paused_for_reconciliation`
before any provider exists. Only an operator clears a hold (`python -m attest holds`).

Fail closed (revision 10, 20 Oct 2026): the stopped run's state and its hold are recorded in one transaction (`Store.record_reconciliation`).
When that transaction fails (the database refused the insert, the disk is full), the worker fails closed: it starts nothing further,
admission is refused (503) and `/api/health` reports it, the run's row is left as the store had it (queued or running) so that the
restart recovery finds it from its run directory, and the record is retried at every housekeeping pass; once it succeeds the hold in the
store keeps runs paused until an operator clears it. A failure of the start-up recovery fails the worker closed the same way.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import queue
import re
import shutil
import threading
import time
import traceback
from pathlib import Path

from ..ledger import Ledger, utcnow
from ..secrets import SecretError, load_secret, project_id
from .db import Store, visibility_for

LOG = logging.getLogger("attest.app")
RESTART_BACKOFF_S = 5.0
# Per-run model-call cap of every paid console run (review finding R5-05, 19 Oct 2026): ATTEST_PER_RUN_MAX_CALLS, default 22, the
# figure the freeze promises and the harness and CLI default to. Read when a run's provider is built, so the bundle's profile.provider
# shows the cap that actually governed the run.
PER_RUN_MAX_CALLS_ENV = "ATTEST_PER_RUN_MAX_CALLS"
DEFAULT_PER_RUN_MAX_CALLS = 22


def per_run_max_calls() -> int:
    """The console's per-run call cap for the paid provider. An unusable value (not an integer, or below 1) keeps the default: a
    misconfiguration must never remove the cap."""
    raw = os.environ.get(PER_RUN_MAX_CALLS_ENV, "").strip()
    if not raw:
        return DEFAULT_PER_RUN_MAX_CALLS
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        LOG.warning("ignoring an unusable %s=%r; the per-run call cap stays %d", PER_RUN_MAX_CALLS_ENV, raw, DEFAULT_PER_RUN_MAX_CALLS)
        return DEFAULT_PER_RUN_MAX_CALLS
    return value


# A title that cites its upstream issue: "<what> to <repo> (upstream issue #N)[, <qualifier>]" or "<what> (<repo> issue #N)"
TITLE_REFERENCE = re.compile(r"^(?P<title>.+?)(?: to (?P<repo>[\w.-]+))? \((?:upstream )?(?:(?P<repo2>[\w.-]+) )?issue #(?P<issue>\d+)\)(?:, (?P<note>.+))?$")


def task_display(data: dict) -> dict:
    """How the console's task picker names a task, derived from the task file without changing it (the evaluated examples keep their
    digests): a short title, the repository (the upstream project, or the bundled sample package when there is no upstream), the issue
    the title cites, and the qualifier that tells two variants of one task apart. A title that does not follow the pattern, or that names
    another repository than its upstream, is shown whole."""
    title = data.get("title") or data.get("id") or ""
    upstream = data.get("upstream") if isinstance(data.get("upstream"), dict) else {}
    url = str(upstream.get("url") or "").rstrip("/")
    repository = url.rsplit("/", 1)[-1] if url else None
    short, issue, note = title, None, None
    match = TITLE_REFERENCE.match(title)
    named = match and (match.group("repo") or match.group("repo2"))
    if match and (not named or repository is None or named == repository):
        short, issue, note = match.group("title"), f"issue #{match.group('issue')}", match.group("note")
        repository = repository or named or None
    if repository is None:
        globs = [g for g in data.get("allowed_write_globs") or [] if isinstance(g, str) and "/" in g]
        repository = globs[0].split("/", 1)[0] if globs else None
    commit = str(upstream.get("commit") or "")[:7] or None
    return {"title": short, "note": note, "repository": repository, "sample": not url, "issue": issue,
            "upstream_url": url or None, "upstream_commit": commit}


class WorkerUnavailable(RuntimeError):
    """Raised by `enqueue` when no live worker thread exists; nothing was written."""


class ReconciliationHold(RuntimeError):
    """Raised by `enqueue` while a reconciliation hold is open, or while the worker has failed closed; nothing was written."""


class HoldNotRecorded(RuntimeError):
    """A run stopped for reconciliation and its state and hold could not be recorded; the worker has failed closed (revision 10)."""


class Worker:
    def __init__(self, store: Store, data_dir: Path, examples_dir: Path, max_queue: int = 5, per_run_usd_cap: float = 0.5,
                 daily_usd_cap: float = 2.0, max_turns: int = 14, max_mutants: int = 12, retention_keep: int = 40,
                 min_free_frac: float = 0.07, min_free_mb: int = 500, retention_keep_errors: int = 10, housekeeping_s: float = 300.0):
        self.store = store
        self.data_dir = Path(data_dir)
        self.examples_dir = Path(examples_dir)
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue)
        self.max_queue = max_queue
        self.per_run_usd_cap = per_run_usd_cap
        self.daily_usd_cap = daily_usd_cap
        self.max_turns = max_turns
        self.max_mutants = max_mutants
        self.retention_keep = retention_keep
        self.retention_keep_errors = retention_keep_errors
        self.housekeeping_s = housekeeping_s
        self.min_free_frac = min_free_frac
        self.min_free_bytes = min_free_mb * 1024 * 1024
        self.current: str | None = None
        self._queued: list[str] = []            # run ids in queue order (API-11), under _state_lock
        self._state_lock = threading.Lock()     # current, _queued, thread, restart bookkeeping
        self._admit_lock = threading.Lock()     # one admission at a time: capacity check, row, queue slot
        self._stop = threading.Event()
        self.restarts = 0
        self._last_restart: float | None = None
        # fail-closed state (revision 10): why the worker starts nothing although no hold may be in the store, and the reconciliation
        # records still to be written (retried at every housekeeping pass)
        self.closed: dict | None = None
        self._pending_records: list[dict] = []
        self.thread = self._spawn()

    # ------------------------------------------------------------ supervision (API-07)
    def _spawn(self) -> threading.Thread:
        thread = threading.Thread(target=self._loop, name="attest-worker", daemon=True)
        thread.start()
        return thread

    def alive(self) -> bool:
        return self.thread.is_alive()

    def ensure_alive(self) -> bool:
        """True when the loop thread is running. A thread that died unexpectedly is restarted, at most once per
        RESTART_BACKOFF_S; a deliberate `stop()` is respected until `start()`."""
        with self._state_lock:
            if self.thread.is_alive():
                return True
            if self._stop.is_set():
                return False
            now = time.monotonic()
            if self._last_restart is not None and now - self._last_restart < RESTART_BACKOFF_S:
                return False
            self._last_restart = now
            self.restarts += 1
            LOG.error("worker thread is dead; restarting it (restart %d)", self.restarts)
            self.thread = self._spawn()
            self.thread.join(timeout=0.05)  # a loop that dies on start is reported dead, not alive for an instant
            return self.thread.is_alive()

    def stop(self) -> None:
        """Stop the loop deliberately (shutdown, tests): `ensure_alive()` will not restart it until `start()`."""
        self._stop.set()

    def start(self) -> bool:
        self._stop.clear()
        with self._state_lock:
            self._last_restart = None
        return self.ensure_alive()

    # ------------------------------------------------------------ fail closed (revision 10)
    def fail_closed(self, reason: str, run_id: str | None = None, cause: str = "record") -> None:
        """Start nothing further until the cause is gone or the service restarts and recovers. `cause` is `record` (a reconciliation
        record that could not be written; the state ends when every pending record is written) or `startup` (the start-up recovery
        failed; only a restart ends it). A start-up cause is never replaced by a record cause."""
        with self._state_lock:
            if self.closed is None or (self.closed.get("cause") == "record" and cause == "startup"):
                self.closed = {"reason": str(reason)[:1000], "run_id": run_id, "at_utc": utcnow(), "cause": cause}
        LOG.critical("worker failed closed (%s): %s", cause, reason)

    def accepting(self) -> bool:
        return self.closed is None

    def retry_pending_records(self) -> int:
        """Write the reconciliation records that failed; returns how many are still pending. When none is left the fail-closed state
        caused by them ends: the holds now in the store keep runs paused until an operator clears them."""
        with self._state_lock:
            pending = list(self._pending_records)
        still = []
        for record in pending:
            try:
                self.store.record_reconciliation(record["run_id"], record["message"], record["items"], detail=record.get("detail"),
                                                 source="worker-retry", **record["fields"])
                LOG.warning("the reconciliation record of run %s was written on retry", record["run_id"])
            except Exception:  # noqa: BLE001 - still failing: stay closed
                still.append(record)
        with self._state_lock:
            self._pending_records = still + [r for r in self._pending_records if r not in pending]
            if not self._pending_records and self.closed is not None and self.closed.get("cause") == "record":
                self.closed = None
            remaining = len(self._pending_records)
        return remaining

    # ------------------------------------------------------------ disk
    def disk(self) -> dict:
        try:
            usage = shutil.disk_usage(self.data_dir)
        except OSError:
            return {"total": None, "free": None, "free_frac": None, "low": False, "error": "disk usage unavailable"}
        free_frac = usage.free / usage.total if usage.total else 0.0
        low = usage.free < self.min_free_bytes or free_frac < self.min_free_frac
        return {"total": usage.total, "free": usage.free, "free_mb": round(usage.free / 1024 / 1024),
                "free_frac": round(free_frac, 4), "low": low}

    def _disk_guard(self) -> None:
        state = self.disk()
        if state.get("low"):
            raise RuntimeError(f"low disk space ({state.get('free_mb')} MB free, {state.get('free_frac')} of volume); "
                               "new runs are paused until space is reclaimed")

    # ------------------------------------------------------------ tasks
    def tasks(self) -> list[dict]:
        """Configured sample tasks. `path` is the task file on the host and stays internal (the API drops it)."""
        items = []
        for path in sorted(self.examples_dir.glob("*/task.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            items.append({"task_id": data["id"], "title": data["title"], "runner": data.get("test_runner", "unittest"),
                          "path": str(path), "statement": data["statement"][:400], "criteria": len(data.get("acceptance_criteria", [])),
                          "heldout": bool(data.get("heldout_tests")), "display": task_display(data)})
        return items

    def task_path(self, task_id: str) -> Path | None:
        for item in self.tasks():
            if item["task_id"] == task_id:
                return Path(item["path"])
        return None

    # ------------------------------------------------------------ queueing
    def position(self, run_id: str) -> int | None:
        """Runs ahead of `run_id`: 0 while it executes, N when N runs precede it (the one executing plus the queued runs
        before it); None when it is neither executing nor queued."""
        with self._state_lock:
            if self.current == run_id:
                return 0
            if run_id in self._queued:
                return self._queued.index(run_id) + (1 if self.current else 0)
        return None

    def enqueue(self, task_id: str, provider: str, requester: str, profile_label: str, quota: tuple[str, str, int] | None = None) -> dict:
        """Admit a run. Raises ValueError for an unknown task, WorkerUnavailable when no live worker exists, QuotaError when the
        visitor's hourly allowance is used up, BudgetError when the daily budget has no room, RuntimeError when the disk is
        low or the queue is full. Nothing is written unless the run is admitted."""
        path = self.task_path(task_id)
        if path is None:
            raise ValueError(f"unknown task {task_id}")
        if not self.ensure_alive():
            raise WorkerUnavailable("the run worker is not available; nothing was queued")
        if self.closed is not None:
            raise ReconciliationHold("live runs are paused: a stopped run's reconciliation record could not be written, so the service is closed "
                                     "until it is; nothing was queued")
        if self.store.active_holds():
            raise ReconciliationHold("live runs are paused while an earlier run's operations are reconciled; nothing was queued")
        self._disk_guard()
        title = json.loads(path.read_text(encoding="utf-8"))["title"]
        visibility = visibility_for(provider)
        with self._admit_lock:
            if self.queue.full():
                raise RuntimeError("the run queue is full; try again in a few minutes")
            run_id = f"{task_id}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
            today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")
            self.store.create_run_reserving(self.per_run_usd_cap, self.daily_usd_cap, today, quota=quota, run_id=run_id, task_id=task_id,
                                            task_title=title, provider=provider, profile_label=profile_label, status="queued",
                                            stage="queued", created_at=utcnow(), requester=requester, visibility=visibility)
            with self._state_lock:
                self._queued.append(run_id)
            try:
                self.queue.put_nowait((run_id, path, provider, profile_label))
            except queue.Full:
                with self._state_lock:
                    self._queued.remove(run_id)
                self.store.record_failure(run_id, "queue_full", "queue full")
                raise RuntimeError("the run queue is full; try again in a few minutes") from None
        return {"run_id": run_id, "status": "queued", "position": self.position(run_id), "visibility": visibility}

    # ------------------------------------------------------------ execution
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                item = self.queue.get(timeout=self.housekeeping_s)
            except queue.Empty:
                if not self._stop.is_set():
                    self.housekeeping()
                continue
            self._run_one(item)

    def _begin(self, run_id: str) -> None:
        with self._state_lock:
            self.current = run_id
            if run_id in self._queued:
                self._queued.remove(run_id)

    def _run_one(self, item: tuple) -> None:
        """One queue item, start to finish. Any failure of the run is recorded on its row and the loop goes on; only a
        SystemExit/KeyboardInterrupt ends the thread, and even then the row is settled first."""
        run_id, path, provider, profile_label = item
        self._begin(run_id)
        try:
            self._execute(run_id, path, provider, profile_label)
        except (SystemExit, KeyboardInterrupt):
            self._settle(run_id, traceback.format_exc(), interrupted=True)
            raise
        except HoldNotRecorded:
            # revision 10: the row is left as it is (queued or running) so that a restart recovers the run from its directory; recording
            # anything else here would replace the reconciliation state with an ordinary failure
            LOG.critical("run %s stopped for reconciliation and its record could not be written; the worker is closed", run_id)
        except BaseException:  # noqa: BLE001 - the loop survives anything else (API-07)
            self._settle(run_id, traceback.format_exc(), interrupted=False)
        finally:
            with self._state_lock:
                self.current = None
            self.queue.task_done()
            self.housekeeping(run_id)

    def _settle(self, run_id: str, detail: str, interrupted: bool) -> None:
        """Record a failure that escaped `_execute` on the row, unless `_execute` already finalized it."""
        try:
            row = self.store.get_run(run_id)
            if row is None or row["status"] not in ("queued", "running"):
                return
            if interrupted:
                self.store.finalize_interrupted(run_id, self.per_run_usd_cap, detail=detail)
            else:
                self.store.record_failure(run_id, "worker_error", "the worker failed before completion", detail=detail, stage="error")
        except Exception:  # noqa: BLE001 - a failing store must not take the loop down with it
            LOG.exception("could not record the failure of run %s", run_id)

    def housekeeping(self, run_id: str | None = None) -> list[str]:
        """Bounded retention, independent of any run finishing (API-06), after retrying any reconciliation record still pending
        (revision 10). Returns the ids whose directories were reclaimed."""
        if self._pending_records:
            try:
                self.retry_pending_records()
            except Exception:  # noqa: BLE001
                LOG.exception("retrying the pending reconciliation records failed")
        try:
            pruned = self.store.prune_runs(self.data_dir / "runs", keep=self.retention_keep, keep_errors=self.retention_keep_errors)
        except Exception:  # noqa: BLE001 - retention must never fail a run or the loop
            LOG.exception("housekeeping failed")
            return []
        if pruned and run_id:
            try:
                self.store.add_event(run_id, utcnow(), "retention", f"pruned {len(pruned)} old run director(ies) to reclaim disk")
            except Exception:  # noqa: BLE001
                pass
        return pruned

    def _hold(self, run_id: str, halt: dict, items: list, detail: str | None = None, **fields) -> None:
        """Record a run that stopped for reconciliation and open the hold that pauses the worker: the row, its event and the hold in one
        transaction (revision 10). When that fails the worker fails closed and HoldNotRecorded is raised; the record is retried later."""
        message = (f"stopped for reconciliation at {halt.get('stage') or 'an unrecorded stage'} ({halt.get('kind') or 'unknown outcome'}): "
                   f"{len(items)} operation(s) to settle; nothing was sent again")
        try:
            self.store.record_reconciliation(run_id, message, items, detail=detail, **fields)
        except Exception as error:  # noqa: BLE001 - any failure: nothing was recorded, so nothing further may start
            with self._state_lock:
                self._pending_records.append({"run_id": run_id, "message": message, "items": items, "detail": detail, "fields": fields})
            self.fail_closed(f"the reconciliation record of run {run_id} could not be written ({type(error).__name__}); retried at every housekeeping pass",
                             run_id=run_id, cause="record")
            raise HoldNotRecorded(f"run {run_id}: {error}") from error

    def build_runtime(self, run_id: str, provider_name: str, ledger: Ledger):
        """The provider, executor and grounding client for one run (separated so tests can substitute fakes)."""
        from ..sandbox.tf_sandboxes import TokenFactorySandboxes
        if provider_name == "codex":
            from ..models.codex_gateway import CodexGateway
            # pacing waits and gateway rejections are visible in the run's event stream, like every other stage message
            provider = CodexGateway(load_secret("CODEX_API_KEY"), ledger,
                                    notify=lambda message: self.store.add_event(run_id, utcnow(), "pacing", message))
        else:
            from ..models.nebius_tokenfactory import NebiusTokenFactory
            # the per-run call cap is enforced by the provider before dispatch and recorded in the bundle's profile.provider (R5-05)
            provider = NebiusTokenFactory(load_secret("NEBIUS_API_KEY"), ledger, usd_cap=self.per_run_usd_cap, max_calls=per_run_max_calls())
        executor = TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)
        try:
            from ..core.grounding import Tavily
            tavily = Tavily(load_secret("TAVILY_API_KEY"))
        except SecretError:
            tavily = None
        return provider, executor, tavily

    def _execute(self, run_id: str, path: Path, provider_name: str, profile_label: str) -> None:
        from ..core.pipeline import Pipeline
        from ..core.task import TaskSpec

        if self.closed is not None:  # revision 10: failed closed; nothing starts, no provider is built
            try:
                self.store.record_failure(run_id, "paused_for_reconciliation", f"not started: the service is closed ({self.closed.get('reason')})", stage="paused")
            except Exception:  # noqa: BLE001 - the store may be the cause; the row stays queued and a restart settles it
                LOG.exception("could not record that run %s was not started", run_id)
            return
        holds = self.store.active_holds()
        if holds:  # revision 9: nothing starts while an earlier run's operations are being reconciled; no provider is built
            self.store.record_failure(run_id, "paused_for_reconciliation", f"not started: hold {holds[0]['hold_id']} (run {holds[0]['run_id']}) is open "
                                      "until an operator reconciles it", stage="paused")
            return
        self.store.update_run(run_id, status="running", started_at=utcnow(), stage="starting")
        # Recheck the budget and disk at execution time; queued runs may have been waiting while others spent.
        if provider_name == "nebius":
            today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")
            ok, detail = self.store.nebius_budget_ok(self.per_run_usd_cap, self.daily_usd_cap, today)
            if not ok:
                self.store.record_failure(run_id, "budget_exhausted", detail, stage="budget")
                return
        try:
            self._disk_guard()
        except RuntimeError as error:
            self.store.record_failure(run_id, "disk_low", str(error), stage="disk")
            return
        def meters(live: dict) -> None:
            # every reservation and every call record updates the row at once, so a process that dies mid-run leaves the
            # committed figure (known costs plus open reservations) in the store, not only in memory
            try:
                self.store.update_run(run_id, model_calls=live.get("model_calls"), sandbox_ops=live.get("sandbox_operations"),
                                      cost_committed_usd=live.get("cost_usd_committed"), cost_usd=live.get("cost_usd"),
                                      tokens_in=live.get("tokens_in"), tokens_out=live.get("tokens_out"))
            except Exception:  # noqa: BLE001 - meters never break a run; the ledger journal in the run directory is the record
                pass

        ledger = Ledger(on_change=meters)
        provider, executor, tavily = self.build_runtime(run_id, provider_name, ledger)
        task = TaskSpec.load(path)

        def stopped(detail: str, **costs) -> bool:
            """Hold the run when its ledger halted or lists an operation whose outcome is unknown (revision 9; atomic since revision 10)."""
            items = ledger.reconciliation_items()
            if ledger.halted or items:
                self._hold(run_id, ledger.halted or {}, items, detail=detail, **costs)
                return True
            return False

        def progress(event: dict) -> None:
            self.store.add_event(run_id, event["at_utc"], event.get("stage"), event["message"])
            # live meters for the console: real ledger totals, not numbers parsed from the log text
            try:
                live = ledger.totals()
                self.store.update_run(run_id, stage=event.get("stage"), model_calls=live.get("model_calls"),
                                      sandbox_ops=live.get("sandbox_operations"), cost_committed_usd=live.get("cost_usd_committed"),
                                      tokens_in=live.get("tokens_in"), tokens_out=live.get("tokens_out"))
            except Exception:  # noqa: BLE001 - meters are a convenience; the event itself is already stored
                self.store.update_run(run_id, stage=event.get("stage"))

        try:
            pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=self.data_dir / "runs",
                                max_turns=self.max_turns, max_mutants=self.max_mutants, tavily=tavily, profile_label=profile_label,
                                progress=progress, run_id=run_id)
        except Exception as error:  # noqa: BLE001 - e.g. a journal that cannot be created; a halt recorded while describing the provider holds
            if not stopped(traceback.format_exc()):
                self.store.record_failure(run_id, "pipeline_error", f"{type(error).__name__}: {str(error)[:300]}", detail=traceback.format_exc(), stage="error")
            return
        # the run directory, the bundle's run_id and the store row share one id, so a later import recognises this run
        self.store.update_run(run_id, out_dir=str(pipeline.out_dir))
        try:
            bundle = pipeline.run()
        except Exception as error:  # noqa: BLE001 - the paid calls made before the crash stay on the row and in the daily budget
            totals = ledger.totals()
            costs = dict(out_dir=str(pipeline.out_dir), cost_usd=totals.get("cost_usd"), cost_committed_usd=totals.get("cost_usd_committed"),
                         tokens_in=totals.get("tokens_in"), tokens_out=totals.get("tokens_out"), sandbox_ops=totals.get("sandbox_operations"),
                         model_calls=totals.get("model_calls"))
            if stopped(traceback.format_exc(), **costs):
                return
            self.store.record_failure(run_id, "pipeline_error", f"{type(error).__name__}: {str(error)[:300]}", detail=traceback.format_exc(),
                                      stage="error", **costs)
            return
        totals = bundle["ledger"]["totals"]
        reconciliation = bundle.get("reconciliation") or {}
        if reconciliation.get("required"):
            self._hold(run_id, reconciliation.get("halt") or {}, reconciliation.get("items") or [], detail=json.dumps(reconciliation, default=str)[:20000],
                       out_dir=str(pipeline.out_dir), cost_usd=totals.get("cost_usd"), cost_committed_usd=totals.get("cost_usd_committed"),
                       tokens_in=totals.get("tokens_in"), tokens_out=totals.get("tokens_out"), sandbox_ops=totals.get("sandbox_operations"),
                       model_calls=totals.get("model_calls"), verdict=bundle["verdict"]["verdict"], reasons=json.dumps(bundle["verdict"]["reasons"]),
                       warnings=json.dumps(bundle["verdict"].get("warnings", [])))
            return
        self.store.update_run(run_id, status="finished", verdict=bundle["verdict"]["verdict"], finished_at=utcnow(),
                              out_dir=str(pipeline.out_dir), cost_usd=totals.get("cost_usd"),
                              cost_committed_usd=totals.get("cost_usd_committed"), tokens_in=totals.get("tokens_in"),
                              tokens_out=totals.get("tokens_out"), sandbox_ops=totals.get("sandbox_operations"), stage="finished",
                              model_calls=totals.get("model_calls"),
                              reasons=json.dumps(bundle["verdict"]["reasons"]), warnings=json.dumps(bundle["verdict"].get("warnings", [])))
