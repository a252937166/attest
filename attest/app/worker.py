"""Single background worker: runs one task at a time, streams progress into the store, enforces caps."""

from __future__ import annotations

import datetime as dt
import json
import queue
import shutil
import threading
import traceback
from pathlib import Path

from ..ledger import Ledger, utcnow
from ..secrets import SecretError, load_secret, project_id
from .db import BudgetError, Store


class Worker:
    def __init__(self, store: Store, data_dir: Path, examples_dir: Path, max_queue: int = 5, per_run_usd_cap: float = 0.5,
                 daily_usd_cap: float = 2.0, max_turns: int = 14, max_mutants: int = 12, retention_keep: int = 40,
                 min_free_frac: float = 0.07, min_free_mb: int = 500):
        self.store = store
        self.data_dir = Path(data_dir)
        self.examples_dir = Path(examples_dir)
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue)
        self.per_run_usd_cap = per_run_usd_cap
        self.daily_usd_cap = daily_usd_cap
        self.max_turns = max_turns
        self.max_mutants = max_mutants
        self.retention_keep = retention_keep
        self.min_free_frac = min_free_frac
        self.min_free_bytes = min_free_mb * 1024 * 1024
        self.current: str | None = None
        self.thread = threading.Thread(target=self._loop, name="attest-worker", daemon=True)
        self.thread.start()

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
        items = []
        for path in sorted(self.examples_dir.glob("*/task.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            items.append({"task_id": data["id"], "title": data["title"], "runner": data.get("test_runner", "unittest"),
                          "path": str(path), "statement": data["statement"][:400], "criteria": len(data.get("acceptance_criteria", [])),
                          "heldout": bool(data.get("heldout_tests"))})
        return items

    def task_path(self, task_id: str) -> Path | None:
        for item in self.tasks():
            if item["task_id"] == task_id:
                return Path(item["path"])
        return None

    # ------------------------------------------------------------ queueing
    def enqueue(self, task_id: str, provider: str, requester: str, profile_label: str) -> dict:
        path = self.task_path(task_id)
        if path is None:
            raise ValueError(f"unknown task {task_id}")
        self._disk_guard()
        run_id = f"{task_id}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
        title = json.loads(path.read_text(encoding="utf-8"))["title"]
        today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")
        try:
            self.store.create_run_reserving(self.per_run_usd_cap, self.daily_usd_cap, today, run_id=run_id, task_id=task_id,
                                            task_title=title, provider=provider, profile_label=profile_label, status="queued",
                                            stage="queued", created_at=utcnow(), requester=requester)
        except BudgetError as error:
            raise RuntimeError(str(error)) from None
        try:
            self.queue.put_nowait((run_id, path, provider, profile_label))
        except queue.Full:
            self.store.update_run(run_id, status="error", error="queue full", finished_at=utcnow())
            raise RuntimeError("the run queue is full; try again in a few minutes") from None
        return {"run_id": run_id, "status": "queued", "position": self.queue.qsize()}

    # ------------------------------------------------------------ execution
    def _loop(self) -> None:
        while True:
            run_id, path, provider, profile_label = self.queue.get()
            self.current = run_id
            try:
                self._execute(run_id, path, provider, profile_label)
            except Exception:  # noqa: BLE001
                self.store.update_run(run_id, status="error", error=traceback.format_exc()[-1500:], finished_at=utcnow())
            finally:
                self.current = None
                self.queue.task_done()

    def _execute(self, run_id: str, path: Path, provider_name: str, profile_label: str) -> None:
        from ..core.pipeline import Pipeline
        from ..core.task import TaskSpec
        from ..sandbox.tf_sandboxes import TokenFactorySandboxes

        self.store.update_run(run_id, status="running", started_at=utcnow(), stage="starting")
        # Recheck the budget and disk at execution time; queued runs may have been waiting while others spent.
        if provider_name == "nebius":
            today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")
            ok, detail = self.store.nebius_budget_ok(self.per_run_usd_cap, self.daily_usd_cap, today)
            if not ok:
                self.store.update_run(run_id, status="error", error=detail, finished_at=utcnow(), stage="budget")
                return
        try:
            self._disk_guard()
        except RuntimeError as error:
            self.store.update_run(run_id, status="error", error=str(error), finished_at=utcnow(), stage="disk")
            return
        ledger = Ledger()
        if provider_name == "codex":
            from ..models.codex_gateway import CodexGateway
            # pacing waits and gateway rejections are visible in the run's event stream, like every other stage message
            provider = CodexGateway(load_secret("CODEX_API_KEY"), ledger,
                                    notify=lambda message: self.store.add_event(run_id, utcnow(), "pacing", message))
        else:
            from ..models.nebius_tokenfactory import NebiusTokenFactory
            provider = NebiusTokenFactory(load_secret("NEBIUS_API_KEY"), ledger, usd_cap=self.per_run_usd_cap)
        executor = TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)
        try:
            from ..core.grounding import Tavily
            tavily = Tavily(load_secret("TAVILY_API_KEY"))
        except SecretError:
            tavily = None
        task = TaskSpec.load(path)

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

        pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=self.data_dir / "runs",
                            max_turns=self.max_turns, max_mutants=self.max_mutants, tavily=tavily, profile_label=profile_label,
                            progress=progress, run_id=run_id)
        # the run directory, the bundle's run_id and the store row share one id, so a later import recognises this run
        self.store.update_run(run_id, out_dir=str(pipeline.out_dir))
        bundle = pipeline.run()
        totals = bundle["ledger"]["totals"]
        self.store.update_run(run_id, status="finished", verdict=bundle["verdict"]["verdict"], finished_at=utcnow(),
                              out_dir=str(pipeline.out_dir), cost_usd=totals.get("cost_usd"),
                              cost_committed_usd=totals.get("cost_usd_committed"), tokens_in=totals.get("tokens_in"),
                              tokens_out=totals.get("tokens_out"), sandbox_ops=totals.get("sandbox_operations"), stage="finished",
                              model_calls=totals.get("model_calls"),
                              reasons=json.dumps(bundle["verdict"]["reasons"]), warnings=json.dumps(bundle["verdict"].get("warnings", [])))
        try:
            pruned = self.store.prune_runs(self.data_dir / "runs", keep=self.retention_keep)
            if pruned:
                self.store.add_event(run_id, utcnow(), "retention", f"pruned {len(pruned)} old run director(ies) to reclaim disk")
        except Exception:  # noqa: BLE001 - retention must never fail a finished run
            pass
