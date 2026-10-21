"""SQLite store for run metadata and progress events (stdlib sqlite3, one connection, one lock).

Concurrency (API-03): one connection is shared by the API threads and the worker. Every statement runs under `_lock`, and
every read materialises its rows while the lock is still held (`_rows`, `_row_one`); no live cursor ever leaves the lock.
Writes go through `_write`. Admission (`create_run_reserving`) checks the visitor quota and the daily budget and inserts the
row under that same lock, so concurrent callers cannot each pass a stale check (API-02).

Daily budget policy (AC-06): the Nebius cap is a conservative UTC-day cap. A run counts against every UTC day on which it was
queued, started, ran or finished: the committed USD of a finished or errored run is charged to a day when its created_at,
started_at or finished_at falls on or after that day's start. A queued or running run reserves the per-run cap regardless
of the day. A run that straddles midnight is therefore charged to both days; the cap never undercounts a day.

Visibility (publication contract): every row carries `visibility`, `public` or `team`. Runs of the development gateway
(provider `codex`, the team profile) are `team`; the API hides them from callers without the team token. Older databases are
migrated and back-filled at startup.

Failures (API-09): `record_failure` keeps the operator-facing message in `error`, the full traceback in `error_detail` and a
correlation reference in `error_ref`; the API publishes only `error_code` and a neutral message carrying the reference.

Reconciliation holds (revision 9, 20 Oct 2026): a run that stopped for reconciliation (an operation whose outcome is uncertain, a record
that could not be made durable), or that a restart found with operations whose outcome is unknown in its journal, is recorded with
`error_code` `reconciliation_required` and opens a hold (table `holds`). While any hold is open the worker starts nothing (queued runs
end `paused_for_reconciliation`, admission is refused) and retention keeps the held run's directory. Only an operator clears a hold,
with a note, after reconciling its items (`python -m attest holds`); clearing never sends anything.

Atomic holds and restart recovery (revision 10, 20 Oct 2026): `record_reconciliation` writes the run's `reconciliation_required` state,
its event and its hold in ONE transaction (BEGIN IMMEDIATE ... COMMIT), so no crash or failed insert can leave one without the other; on
any failure it rolls back, changes nothing and raises (the worker then fails closed). It is idempotent: a run has at most one hold, ever
(a partial unique index enforces it where the database allows), and recording a run that already has one, open or cleared, returns
that hold. After a restart (`startup_recovery`): every queued or running row is settled from its run directory, where the proof bundle's
reconciliation record AND the ledger journal are both read before the row is finalized, so a run that stopped for reconciliation keeps
its hold even when its bundle was written before the process died (`finalize_interrupted`); then `repair_holds` gives every run recorded
as `reconciliation_required` without a hold its hold, and records as held a console run whose own bundle requires reconciliation but
whose row says otherwise (0.9.0 finalized such rows as finished). A hold an operator cleared is never reopened: repair only acts on
runs that have no hold row at all.
"""

from __future__ import annotations

import json
import logging
import shutil
import sqlite3
import threading
import uuid
from pathlib import Path

from ..ledger import utcnow

LOG = logging.getLogger("attest.app")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, task_title TEXT NOT NULL, provider TEXT NOT NULL, profile_label TEXT NOT NULL,
  status TEXT NOT NULL, verdict TEXT, stage TEXT, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT,
  out_dir TEXT, cost_usd REAL, cost_committed_usd REAL, tokens_in INTEGER, tokens_out INTEGER, sandbox_ops INTEGER,
  requester TEXT, error TEXT, reasons TEXT, warnings TEXT, model_calls INTEGER,
  visibility TEXT NOT NULL DEFAULT 'public', error_code TEXT, error_ref TEXT, error_detail TEXT
);
CREATE TABLE IF NOT EXISTS events (
  run_id TEXT NOT NULL, seq INTEGER NOT NULL, at_utc TEXT NOT NULL, stage TEXT, message TEXT NOT NULL,
  PRIMARY KEY (run_id, seq)
);
CREATE INDEX IF NOT EXISTS runs_created ON runs(created_at DESC);
CREATE TABLE IF NOT EXISTS holds (
  hold_id TEXT PRIMARY KEY, run_id TEXT, created_at TEXT NOT NULL, reason TEXT NOT NULL, items TEXT,
  cleared_at TEXT, cleared_note TEXT
);
"""

# Columns added after the first release, with the DDL that adds them to an older database.
MIGRATIONS = (
    ("cost_committed_usd", "ALTER TABLE runs ADD COLUMN cost_committed_usd REAL"),
    ("model_calls", "ALTER TABLE runs ADD COLUMN model_calls INTEGER"),               # M3: live meters while a run is in progress
    ("visibility", "ALTER TABLE runs ADD COLUMN visibility TEXT NOT NULL DEFAULT 'public'"),
    ("error_code", "ALTER TABLE runs ADD COLUMN error_code TEXT"),
    ("error_ref", "ALTER TABLE runs ADD COLUMN error_ref TEXT"),
    ("error_detail", "ALTER TABLE runs ADD COLUMN error_detail TEXT"),
)

PUBLIC = "public"
TEAM = "team"
# Providers whose runs belong to the team: the development gateway. Short names, as stored in `runs.provider`.
TEAM_PROVIDERS = frozenset({"codex"})

BUDGET_POLICY = ("conservative UTC-day cap: a run counts against every UTC day on which it was queued, started, ran or finished "
                 "(created_at, started_at or finished_at on that day); queued and running runs reserve the per-run cap on any day")

# Public error codes and the neutral sentence published for each; the reference that follows it identifies the server-side
# record (`error_ref`), never the diagnostic text itself.
ERROR_TEXT = {
    "run_failed": "the run failed before completion",
    "pipeline_error": "the run failed before completion",
    "worker_error": "the run failed before completion",
    "worker_interrupted": "the run was interrupted before completion",
    "interrupted": "the run was interrupted by a service restart before completion",
    "budget_exhausted": "the daily inference budget was exhausted before this run could start",
    "disk_low": "the service paused new runs because disk space was low",
    "queue_full": "the run queue was full when this run was admitted",
    "reconciliation_required": "the run stopped because an operation's outcome is uncertain; nothing was sent again and it is held for reconciliation",
    "paused_for_reconciliation": "the run was not started: the service pauses new runs while an earlier run is reconciled",
}


class BudgetError(RuntimeError):
    """Raised when creating a run would exceed the daily budget; the run is not created."""


class StoreError(RuntimeError):
    """A write that must be atomic (the reconciliation state of a run and its hold) did not happen; nothing was changed (revision 10)."""


# Requesters whose rows were not executed by this console: imported evidence and synthetic replay fixtures. Start-up repair never holds
# them for their own historical records (revision 10).
FOREIGN_REQUESTERS = ("import", "replay")


def read_run_reconciliation(out_dir) -> dict:
    """What a run directory says about reconciliation (revision 10): the proof bundle's record (when the bundle exists and parses) and
    the ledger journal, both read. `required` when either says so; `items` merges both lists (each item once); `bundle` is the parsed
    bundle or None."""
    from ..ledger import JOURNAL_FILE, item_key, read_journal
    state = {"bundle": None, "bundle_required": False, "journal": None, "journal_required": False, "required": False, "items": [], "halt": None,
             "bundle_unreadable": False}
    if not out_dir:
        return state
    bundle_path = Path(out_dir) / "proof_bundle.json"
    if bundle_path.is_file():
        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            state["bundle"] = bundle if isinstance(bundle, dict) else None
        except (OSError, ValueError):
            state["bundle_unreadable"] = True
    record = (state["bundle"] or {}).get("reconciliation")
    items: list = []
    if isinstance(record, dict) and record.get("required"):
        state["bundle_required"] = True
        state["halt"] = record.get("halt")
        items += [i for i in record.get("items") or [] if isinstance(i, dict)]
    try:
        journal = read_journal(Path(out_dir) / JOURNAL_FILE)
    except (OSError, ValueError):
        journal = None
    state["journal"] = journal
    if journal is not None and journal.get("reconciliation_required"):
        state["journal_required"] = True
        state["halt"] = state["halt"] or journal.get("halt")
        known = {str(item_key(i)) for i in items}
        items += [i for i in journal.get("reconciliation_items") or [] if isinstance(i, dict) and str(item_key(i)) not in known]
    state["items"] = items
    state["required"] = state["bundle_required"] or state["journal_required"]
    return state


class QuotaError(RuntimeError):
    """Raised when a visitor has used its hourly allowance; the run is not created."""


def duration_seconds(start: str | None, end: str | None) -> float | None:
    """Seconds between two ISO timestamps, or None when either is missing or unparsable."""
    if not start or not end:
        return None
    try:
        import datetime as dt
        a = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
        b = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
        if a.tzinfo is None:
            a = a.replace(tzinfo=dt.timezone.utc)
        if b.tzinfo is None:
            b = b.replace(tzinfo=dt.timezone.utc)
        return round(max(0.0, (b - a).total_seconds()), 1)
    except ValueError:
        return None


def provider_short_name(bundle_provider: str | None) -> str:
    """`nebius_tokenfactory` -> `nebius`, `codex_gateway` -> `codex`: the short provider names stored in `runs.provider`."""
    return (bundle_provider or "unknown").replace("_gateway", "").replace("_tokenfactory", "")


def visibility_for(provider: str | None) -> str:
    return TEAM if provider in TEAM_PROVIDERS else PUBLIC


def committed_from_ledger(ledger: dict | None, known_cost: float | None = None) -> float | None:
    """Conservative committed USD recomputed from a bundle's call records (legacy bundles without `cost_usd_committed`):
    the known cost of each call, or its reservation when the cost is unknown, plus every open reservation. None when the
    bundle carries no call records at all."""
    if not isinstance(ledger, dict):
        return None
    calls = ledger.get("model_calls")
    if not isinstance(calls, list):
        return None
    committed = 0.0
    for call in calls:
        if not isinstance(call, dict):
            continue
        committed += call["cost_usd"] if call.get("cost_usd") is not None else float(call.get("reserved_usd") or 0.0)
    for reservation in ledger.get("open_reservations") or []:
        if isinstance(reservation, dict):
            committed += float(reservation.get("reserved_usd") or 0.0)
    return round(max(committed, float(known_cost or 0.0)), 6)


class Store:
    """Run rows and progress events. Daily budget policy: a conservative UTC-day cap. A run counts against every UTC day on
    which it was queued, started, ran or finished (its created_at, started_at or finished_at falls on that day), and a queued
    or running run reserves the per-run cap whatever the day; see BUDGET_POLICY, which the health endpoint publishes. Rows
    carry a visibility (`public` or `team`) that every read filters on for callers without the team token."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(runs)").fetchall()}
        for column, ddl in MIGRATIONS:
            if column not in cols:
                self._conn.execute(ddl)
        # Back-fill: rows of the development gateway recorded before the visibility column existed belong to the team.
        marks = ", ".join("?" for _ in TEAM_PROVIDERS)
        self._conn.execute(f"UPDATE runs SET visibility = ? WHERE provider IN ({marks}) AND visibility != ?", (TEAM, *sorted(TEAM_PROVIDERS), TEAM))
        # One hold per run, ever (revision 10): enforced by the database where no earlier duplicate prevents the index; the code checks too.
        duplicates = self._conn.execute("SELECT COUNT(*) FROM (SELECT run_id FROM holds WHERE run_id IS NOT NULL GROUP BY run_id HAVING COUNT(*) > 1)").fetchone()[0]
        if duplicates:
            LOG.warning("holds: %d run(s) have more than one hold; the one-hold-per-run index is not created", duplicates)
        else:
            self._conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS holds_one_per_run ON holds(run_id) WHERE run_id IS NOT NULL")

    # ------------------------------------------------------------------ lock-through-fetch primitives (API-03)
    def _rows(self, sql: str, params=()) -> list[sqlite3.Row]:
        """Run a query and materialise every row while the lock is held."""
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def _row_one(self, sql: str, params=()) -> sqlite3.Row | None:
        """Run a query and materialise its first row while the lock is held."""
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def _write(self, sql: str, params=()) -> int:
        """Run a statement under the lock; returns the number of affected rows."""
        with self._lock:
            return self._conn.execute(sql, params).rowcount

    # ------------------------------------------------------------------ rows
    def create_run(self, **fields) -> None:
        fields.setdefault("visibility", visibility_for(fields.get("provider")))
        cols = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        self._write(f"INSERT INTO runs ({cols}) VALUES ({marks})", tuple(fields.values()))

    def _nebius_committed(self, since_utc: str) -> float:
        """Committed USD of the Nebius runs that count against the day starting at `since_utc`: finished and errored runs
        alike (a crash after paid calls still spent them; an interrupted run carries the conservative reservation set by
        reconcile_interrupted), charged to every day on which they were created, started or finished (see the module
        docstring). Callers hold `_lock`."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(COALESCE(cost_committed_usd, cost_usd, 0)), 0) FROM runs "
            "WHERE provider = 'nebius' AND status IN ('finished', 'error') "
            "AND (created_at >= ? OR COALESCE(started_at, '') >= ? OR COALESCE(finished_at, '') >= ?)",
            (since_utc, since_utc, since_utc)).fetchone()
        return float(row[0] or 0.0)

    def _nebius_active(self) -> int:
        """Queued or running Nebius runs, each holding one per-run reservation whatever day it was created. Callers hold `_lock`."""
        return self._conn.execute(
            "SELECT COUNT(*) FROM runs WHERE provider = 'nebius' AND status IN ('queued', 'running')").fetchone()[0]

    def create_run_reserving(self, per_run_cap: float, daily_cap: float, since_utc: str, quota: tuple[str, str, int] | None = None,
                             **fields) -> dict:
        """Admit a run: the visitor quota (`quota` = (requester, since_hour_utc, limit)) and the daily budget are checked and the
        row is inserted under one lock, so N concurrent callers cannot each pass a stale check. Raises QuotaError or
        BudgetError before anything is written; every queued or running Nebius run reserves per_run_cap."""
        fields.setdefault("visibility", visibility_for(fields.get("provider")))
        with self._lock:
            if quota is not None:
                requester, since_hour, limit = quota
                recent = self._conn.execute("SELECT COUNT(*) FROM runs WHERE requester = ? AND created_at >= ?",
                                            (requester, since_hour)).fetchone()[0]
                if recent >= limit:
                    raise QuotaError(f"rate limit: {limit} runs per hour per visitor")
            projected = None
            if fields.get("provider") == "nebius":
                finished = self._nebius_committed(since_utc)
                active = self._nebius_active()
                projected = finished + (active + 1) * per_run_cap
                if projected > daily_cap + 1e-9:
                    raise BudgetError(
                        f"daily Nebius budget ${daily_cap:.2f} would be exceeded: ${finished:.4f} already committed today "
                        f"plus {active + 1} reservation(s) x ${per_run_cap:.2f} = ${projected:.4f}")
            cols = ", ".join(fields)
            marks = ", ".join("?" for _ in fields)
            self._conn.execute(f"INSERT INTO runs ({cols}) VALUES ({marks})", tuple(fields.values()))
            return {"projected_usd": round(projected, 4) if projected is not None else None}

    def nebius_remaining(self, per_run_cap: float, daily_cap: float, since_utc: str) -> dict:
        """What is left of today's Nebius budget once committed costs and active reservations are counted."""
        with self._lock:
            finished = self._nebius_committed(since_utc)
            active = self._nebius_active()
        reserved = active * per_run_cap
        remaining = max(0.0, daily_cap - finished - reserved)
        return {"committed_usd": round(finished, 4), "active_runs": active, "reserved_usd": round(reserved, 4),
                "remaining_usd": round(remaining, 4), "fits_another_run": finished + (active + 1) * per_run_cap <= daily_cap + 1e-9,
                "policy": BUDGET_POLICY}

    def task_estimates(self, provider: str = "nebius", exclude_verdicts: tuple[str, ...] = ("ERROR", "BASELINE"),
                       include_team: bool = False) -> dict[str, dict]:
        """Per task: the latest recorded run and, from completed runs of the public provider only, how many there are and
        their cost and duration ranges. Runs that ended in an infrastructure ERROR or belonged to the evaluation's baseline
        arm say nothing about what a live run costs, so they are left out of the ranges; synthetic replay fixtures are left
        out entirely. Team runs are considered only for a caller who may see them (`include_team`). `latest_evidence_*` names the
        latest run with an Attest verdict (neither an infrastructure ERROR nor the baseline arm): the run the console opens when a
        visitor browses a task (0.10.3), while `latest_run_id` stays the latest finished run of any kind."""
        visible = "" if include_team else f"AND visibility = '{PUBLIC}' "
        rows = self._rows("SELECT run_id, task_id, verdict, status, provider, cost_usd, cost_committed_usd, started_at, finished_at, created_at "
                          "FROM runs WHERE status = 'finished' AND COALESCE(requester, '') != 'replay' AND profile_label NOT LIKE 'replay%' "
                          f"{visible}ORDER BY created_at DESC")
        out: dict[str, dict] = {}
        for row in rows:
            entry = out.setdefault(row["task_id"], {"runs": 0, "cost_min_usd": None, "cost_max_usd": None, "duration_min_s": None,
                                                     "duration_max_s": None, "latest_run_id": row["run_id"], "latest_verdict": row["verdict"],
                                                     "estimate_provider": provider, "recorded_runs": 0, "latest_evidence_run_id": None,
                                                     "latest_evidence_verdict": None, "latest_evidence_at": None})
            entry["recorded_runs"] += 1
            if entry["latest_evidence_run_id"] is None and row["verdict"] and row["verdict"] not in exclude_verdicts:
                entry["latest_evidence_run_id"], entry["latest_evidence_verdict"] = row["run_id"], row["verdict"]
                entry["latest_evidence_at"] = row["finished_at"] or row["created_at"]
            if row["provider"] != provider or row["verdict"] in exclude_verdicts:
                continue
            entry["runs"] += 1
            cost = row["cost_committed_usd"] if row["cost_committed_usd"] is not None else row["cost_usd"]
            if cost is not None:
                entry["cost_min_usd"] = cost if entry["cost_min_usd"] is None else min(entry["cost_min_usd"], cost)
                entry["cost_max_usd"] = cost if entry["cost_max_usd"] is None else max(entry["cost_max_usd"], cost)
            duration = duration_seconds(row["started_at"] or row["created_at"], row["finished_at"])
            if duration is not None:
                entry["duration_min_s"] = duration if entry["duration_min_s"] is None else min(entry["duration_min_s"], duration)
                entry["duration_max_s"] = duration if entry["duration_max_s"] is None else max(entry["duration_max_s"], duration)
        return out

    def nebius_budget_ok(self, per_run_cap: float, daily_cap: float, since_utc: str, executing: bool = True) -> tuple[bool, str]:
        """Recheck before execution (`executing=True`): this run is already counted among the active runs, so at least one
        reservation is in force. With `executing=False` (the health endpoint of an idle service) only rows that really are
        queued or running count, so an idle service reports zero active reservations instead of a phantom one."""
        with self._lock:
            finished = self._nebius_committed(since_utc)
            active = self._nebius_active()
            if executing:
                active = max(1, active)
            projected = finished + active * per_run_cap
        if projected > daily_cap + 1e-9:
            return False, (f"daily Nebius budget ${daily_cap:.2f} exceeded at execution: ${finished:.4f} committed + "
                           f"{active} active x ${per_run_cap:.2f} reservation = ${projected:.4f}")
        return True, f"${finished:.4f} committed + {active} active reservation(s) within ${daily_cap:.2f}"

    # ------------------------------------------------------------------ failures (API-09)
    def record_failure(self, run_id: str, code: str, message: str, detail: str | None = None, **fields) -> str:
        """Mark a run as failed. `message` is the operator's short message (kept in `error`, never published), `detail` the
        full diagnostic text (`error_detail`, never published). Returns the correlation reference that the public error
        carries and that the server log line records."""
        ref = uuid.uuid4().hex[:12]
        LOG.error("run %s failed [%s] reference %s: %s\n%s", run_id, code, ref, message, (detail or "").rstrip())
        fields.setdefault("finished_at", utcnow())
        self.update_run(run_id, status="error", error=message[-1500:], error_code=code, error_ref=ref,
                        error_detail=(detail or message)[-20000:], **fields)
        return ref

    # ------------------------------------------------------------------ reconciliation holds (revision 9)
    def add_hold(self, run_id: str | None, reason: str, items: list | None = None) -> str:
        """Open a hold: the worker starts nothing until an operator clears it. Returns the hold id. A run that already has a hold, open
        or cleared, keeps it (revision 10: one hold per run; the run's row is recorded with `record_reconciliation`)."""
        if run_id is not None:
            existing = self.hold_for_run(run_id)
            if existing is not None:
                return existing["hold_id"]
        hold_id = uuid.uuid4().hex[:12]
        self._write("INSERT INTO holds (hold_id, run_id, created_at, reason, items) VALUES (?, ?, ?, ?, ?)",
                    (hold_id, run_id, utcnow(), str(reason)[:2000], json.dumps(items or [], ensure_ascii=True, default=str)[:200_000]))
        LOG.error("reconciliation hold %s opened for run %s: %s", hold_id, run_id, reason)
        return hold_id

    def hold_for_run(self, run_id: str) -> dict | None:
        """The run's hold, open or cleared (a run has at most one), or None."""
        row = self._row_one("SELECT * FROM holds WHERE run_id = ? ORDER BY created_at, hold_id LIMIT 1", (run_id,))
        return dict(row) if row else None

    def record_reconciliation(self, run_id: str, message: str, items: list | None = None, detail: str | None = None, source: str = "worker",
                              **fields) -> str:
        """The run stopped for reconciliation: in ONE transaction its row becomes `reconciliation_required` (status error, the message,
        the detail, a correlation reference, `fields`), an event is added and its hold is opened (revision 10). Idempotent: a run that
        already has a hold, open or cleared, keeps that one (no second hold, a cleared one is not reopened) and a row already recorded
        as `reconciliation_required` is not rewritten. Returns the hold id. On any failure the transaction is rolled back, nothing is
        changed, and StoreError is raised."""
        from ..ledger import utcnow as now
        ref = uuid.uuid4().hex[:12]
        at = now()
        with self._lock:
            conn = self._conn
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute("SELECT status, error_code FROM runs WHERE run_id = ?", (run_id,)).fetchone()
                if row is None:
                    raise StoreError(f"no run {run_id} to record")
                existing = conn.execute("SELECT hold_id FROM holds WHERE run_id = ? ORDER BY created_at, hold_id LIMIT 1", (run_id,)).fetchone()
                if row["error_code"] != "reconciliation_required":
                    values = {"status": "error", "error": str(message)[-1500:], "error_code": "reconciliation_required", "error_ref": ref,
                              "error_detail": (detail or message)[-20000:], "stage": "reconciliation", **fields}
                    values.setdefault("finished_at", at)
                    sets = ", ".join(f"{k} = ?" for k in values)
                    conn.execute(f"UPDATE runs SET {sets} WHERE run_id = ?", (*values.values(), run_id))
                if existing is None:
                    hold_id = uuid.uuid4().hex[:12]
                    conn.execute("INSERT INTO holds (hold_id, run_id, created_at, reason, items) VALUES (?, ?, ?, ?, ?)",
                                 (hold_id, run_id, at, str(message)[:2000], json.dumps(items or [], ensure_ascii=True, default=str)[:200_000]))
                    seq = conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE run_id = ?", (run_id,)).fetchone()[0]
                    conn.execute("INSERT INTO events (run_id, seq, at_utc, stage, message) VALUES (?, ?, ?, ?, ?)",
                                 (run_id, seq, at, "reconciliation", str(message)[:2000]))
                else:
                    hold_id = existing["hold_id"]
                conn.execute("COMMIT")
            except BaseException as error:
                try:
                    if conn.in_transaction:
                        conn.execute("ROLLBACK")
                except sqlite3.Error:
                    LOG.exception("rollback failed while recording the reconciliation of run %s", run_id)
                if isinstance(error, StoreError):
                    raise
                if isinstance(error, Exception):
                    raise StoreError(f"the reconciliation state and hold of run {run_id} could not be recorded ({type(error).__name__}: "
                                     f"{str(error)[:200]}); nothing was changed") from error
                raise
        if existing is None:
            LOG.error("run %s stopped for reconciliation [%s] reference %s, hold %s opened (%s): %s\n%s", run_id, "reconciliation_required", ref, hold_id,
                      source, message, (detail or "").rstrip()[:4000])
        return hold_id

    def holds(self, active_only: bool = True) -> list[dict]:
        rows = self._rows("SELECT * FROM holds " + ("WHERE cleared_at IS NULL " if active_only else "") + "ORDER BY created_at, hold_id")
        out = []
        for row in rows:
            data = dict(row)
            try:
                data["items"] = json.loads(data.get("items") or "[]")
            except json.JSONDecodeError:
                data["items"] = []
            out.append(data)
        return out

    def active_holds(self) -> list[dict]:
        return self.holds(active_only=True)

    def clear_hold(self, hold_id: str, note: str) -> bool:
        """Close a hold after reconciliation; the note says what was found. Returns False when no open hold has this id."""
        if not str(note or "").strip():
            raise ValueError("a hold is cleared only with a note saying what the reconciliation found")
        changed = self._write("UPDATE holds SET cleared_at = ?, cleared_note = ? WHERE hold_id = ? AND cleared_at IS NULL",
                              (utcnow(), str(note)[:2000], hold_id))
        if changed:
            LOG.warning("reconciliation hold %s cleared: %s", hold_id, note)
        return bool(changed)

    def finalize_interrupted(self, run_id: str, per_run_cap: float | None = None, detail: str | None = None) -> dict:
        """Settle one queued or running row whose worker is gone (a restart, or the worker thread dying mid-run). The run directory is
        read first, the proof bundle's reconciliation record and the ledger journal both (revision 10, `read_run_reconciliation`): a run
        that either says must be reconciled is recorded as `reconciliation_required` with its hold, in one transaction, whether or not
        its bundle was written. A run whose bundle landed on disk and needs no reconciliation is finalized from it. Otherwise it is marked
        errored (interrupted); a Nebius run takes its committed cost from the run's ledger journal when one exists (known costs plus every
        reservation never closed by a call record, which stays committed until reconciled against the provider's billing); without a
        journal it keeps `per_run_cap` (its real spend is unknown and at most the cap). The daily budget therefore never undercounts it."""
        row = self._row_one("SELECT run_id, out_dir, provider, cost_committed_usd FROM runs WHERE run_id = ?", (run_id,))
        if row is None:
            return {"run_id": run_id, "action": "missing"}
        out_dir = row["out_dir"]
        state = read_run_reconciliation(out_dir)
        bundle, journal = state["bundle"], state["journal"]
        if bundle is not None:
            totals = (bundle.get("ledger") or {}).get("totals") or {}
            committed = totals.get("cost_usd_committed")
            if committed is None:
                committed = committed_from_ledger(bundle.get("ledger"), totals.get("cost_usd"))
            if journal is not None and row["provider"] == "nebius":
                committed = max(float(committed or 0.0), float(journal.get("cost_usd_committed") or 0.0))
            verdict = bundle.get("verdict") or {}
            bundle_fields = dict(verdict=verdict.get("verdict"), finished_at=bundle.get("finished_at_utc") or utcnow(), cost_usd=totals.get("cost_usd"),
                                 cost_committed_usd=committed, reasons=json.dumps(verdict.get("reasons") or []),
                                 warnings=json.dumps(verdict.get("warnings") or []), tokens_in=totals.get("tokens_in"), tokens_out=totals.get("tokens_out"),
                                 sandbox_ops=totals.get("sandbox_operations"), model_calls=totals.get("model_calls"))
            if state["required"]:
                halt = state["halt"] or {}
                source = "its proof bundle" if state["bundle_required"] else "its ledger journal (the bundle's record says otherwise)"
                message = (f"stopped for reconciliation at {halt.get('stage') or 'an unrecorded stage'} ({halt.get('kind') or 'unknown outcome'}): "
                           f"{len(state['items'])} operation(s) to settle, found after a restart in {source}; nothing was sent again")
                hold = self.record_reconciliation(run_id, message, state["items"], detail=detail or json.dumps({"halt": halt}, default=str)[:20000],
                                                  source="restart", **bundle_fields)
                return {"run_id": run_id, "action": "held", "hold": hold, "reconciliation_items": len(state["items"]), "from": "bundle"}
            self.update_run(run_id, status="finished", stage="finished", **bundle_fields)
            return {"run_id": run_id, "action": "finalized"}
        message = "interrupted by a service restart before completion" if detail is None else "interrupted before completion"
        fields: dict = {"stage": "interrupted"}
        if row["provider"] == "nebius":
            if journal is not None:
                fields["cost_committed_usd"] = max(float(row["cost_committed_usd"] or 0.0), float(journal["cost_usd_committed"]))
                fields["cost_usd"] = journal.get("cost_usd")
                fields["model_calls"] = journal.get("model_calls")
                message += (f"; committed cost ${fields['cost_committed_usd']:.4f} read from the run's ledger journal "
                            f"({journal['model_calls']} call record(s), {journal['open_reservations']} open reservation(s) kept at their bound)")
            elif per_run_cap is not None and (row["cost_committed_usd"] is None or row["cost_committed_usd"] < per_run_cap):
                fields["cost_committed_usd"] = per_run_cap  # conservative: the actual spend is unknown, the cap is its bound
                message += f"; committed cost set to the per-run cap ${per_run_cap:.2f} because the actual spend is unknown (no ledger journal)"
        unread = list((journal or {}).get("operations_unread") or [])
        if unread:  # revision 8: accepted sandbox operations whose outcome the run never read; the ids stay for reconciliation
            message += (f"; {len(unread)} sandbox operation(s) were accepted but their outcome was never read ({', '.join(unread[:5])}); "
                        "reconcile with GET /operations/<id>; nothing is replayed")
        unresolved = list((journal or {}).get("spawns_unresolved") or [])
        if unresolved:  # revision 9: spawns that were sent (or being sent) and never answered
            message += (f"; {len(unresolved)} sandbox spawn(s) were sent but never answered ({', '.join(str(u.get('stage')) for u in unresolved[:5])}); "
                        "reconcile by listing the account's operations around their start; nothing is replayed")
        items = list(state["items"])
        in_flight = [i for i in items if i.get("kind") == "model_call_in_flight"]
        if in_flight:
            message += f"; {len(in_flight)} model call(s) were in flight (a pending record without a call record)"
        if state["bundle_unreadable"]:
            message += "; the run's proof bundle exists but could not be read"
        if state["required"]:
            fields.pop("stage", None)  # a held run's stage is `reconciliation`
            hold = self.record_reconciliation(run_id, f"{message}; held: {len(items)} operation(s) whose outcome is unknown", items, detail=detail,
                                              source="restart", **fields)
            return {"run_id": run_id, "action": "held", "hold": hold, "cost_committed_usd": fields.get("cost_committed_usd"), "journal": bool(journal),
                    "operations_unread": unread, "spawns_unresolved": unresolved, "reconciliation_items": len(items), "from": "journal"}
        code = "interrupted" if detail is None else "worker_interrupted"
        self.record_failure(run_id, code, message, detail=detail, **fields)
        return {"run_id": run_id, "action": "interrupted", "cost_committed_usd": fields.get("cost_committed_usd"), "journal": bool(journal),
                "operations_unread": unread, "spawns_unresolved": unresolved, "reconciliation_items": len(items), "hold": None}

    def reconcile_interrupted(self, per_run_cap: float | None = None) -> list[dict]:
        """After a restart, no worker is running the rows left 'queued'/'running': settle each one (`finalize_interrupted`).
        Finished rows and their evidence are left untouched."""
        rows = self._rows("SELECT run_id FROM runs WHERE status IN ('queued', 'running') ORDER BY created_at, run_id")
        return [self.finalize_interrupted(row["run_id"], per_run_cap) for row in rows]

    def repair_holds(self) -> list[dict]:
        """Start-up repair (revision 10). (1) Every run recorded as `reconciliation_required` that has no hold row gets its hold, with
        the items its run directory lists. (2) Every run this console executed (not imported evidence, not a replay fixture) whose own
        proof bundle carries a reconciliation record that is required, but whose row is neither held nor recorded as such (0.9.0's restart
        recovery finalized those as finished), is recorded as `reconciliation_required` with its hold. A run with any hold row, open or
        cleared, is never touched: an operator's clearing stands. Idempotent. Returns what it did."""
        done = []
        missing = self._rows("SELECT run_id, out_dir, error FROM runs WHERE error_code = 'reconciliation_required' "
                             "AND NOT EXISTS (SELECT 1 FROM holds h WHERE h.run_id = runs.run_id) ORDER BY created_at, run_id")
        for row in missing:
            state = read_run_reconciliation(row["out_dir"])
            hold = self.record_reconciliation(row["run_id"], row["error"] or "stopped for reconciliation", state["items"], source="repair")
            done.append({"run_id": row["run_id"], "action": "hold_restored", "hold": hold, "reconciliation_items": len(state["items"])})
        marks = ", ".join("?" for _ in FOREIGN_REQUESTERS)
        candidates = self._rows("SELECT run_id, out_dir FROM runs WHERE status IN ('finished', 'error') AND out_dir IS NOT NULL "
                                "AND COALESCE(error_code, '') != 'reconciliation_required' "
                                f"AND COALESCE(requester, '') NOT IN ({marks}) "
                                "AND NOT EXISTS (SELECT 1 FROM holds h WHERE h.run_id = runs.run_id) ORDER BY created_at, run_id", FOREIGN_REQUESTERS)
        for row in candidates:
            state = read_run_reconciliation(row["out_dir"])
            if not state["bundle_required"]:
                continue
            bundle = state["bundle"] or {}
            halt = state["halt"] or {}
            message = (f"stopped for reconciliation at {halt.get('stage') or 'an unrecorded stage'} ({halt.get('kind') or 'unknown outcome'}): "
                       f"{len(state['items'])} operation(s) to settle; the row had been finalized without its hold and was repaired at start-up")
            hold = self.record_reconciliation(row["run_id"], message, state["items"], source="repair",
                                              verdict=(bundle.get("verdict") or {}).get("verdict"))
            done.append({"run_id": row["run_id"], "action": "held_from_bundle", "hold": hold, "reconciliation_items": len(state["items"])})
        return done

    def startup_recovery(self, per_run_cap: float | None = None) -> dict:
        """Everything a restart does to the store before the worker starts (revision 10): settle the rows a restart orphaned, then
        repair holds. Raises StoreError (or a database error) when a record could not be written; the caller then fails closed."""
        settled = self.reconcile_interrupted(per_run_cap)
        repaired = self.repair_holds()
        return {"settled": settled, "repaired": repaired}

    # ------------------------------------------------------------------ retention (API-06)
    def prune_runs(self, data_runs_dir, keep: int = 40, protect: tuple[str, ...] = ("VERIFIED",), keep_errors: int = 10) -> list[str]:
        """Bounded retention of the console's own run directories: keep the newest `keep` finished runs and the newest
        `keep_errors` errored runs; delete the directories of older ones (their rows and accounting stay). Never touches a
        queued or running run, a protected verdict, or a directory outside `data_runs_dir` (imported evidence lives elsewhere)."""
        base = str(Path(data_runs_dir).resolve())
        held = {h.get("run_id") for h in self.active_holds()}  # a held run's evidence stays until its hold is cleared (revision 9)
        rows = self._rows("SELECT run_id, out_dir, verdict, status FROM runs WHERE status IN ('finished', 'error') AND out_dir IS NOT NULL "
                          "ORDER BY created_at DESC")
        budgets = {"finished": keep, "error": keep_errors}
        seen = {"finished": 0, "error": 0}
        pruned = []
        for row in rows:
            out_dir = row["out_dir"]
            if not out_dir:
                continue
            resolved = str(Path(out_dir).resolve())
            if not resolved.startswith(base + "/"):
                continue  # imported evidence, the run root itself, or anything outside the console's own run directory is left alone
            kind = row["status"]
            seen[kind] += 1
            if seen[kind] <= budgets[kind] or row["verdict"] in protect or row["run_id"] in held:
                continue
            try:
                if Path(resolved).is_dir():
                    shutil.rmtree(resolved)
                self.update_run(row["run_id"], out_dir=None, stage="pruned")
                pruned.append(row["run_id"])
            except OSError:
                pass
        return pruned

    # ------------------------------------------------------------------ reads and writes
    def update_run(self, run_id: str, **fields) -> None:
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._write(f"UPDATE runs SET {sets} WHERE run_id = ?", (*fields.values(), run_id))

    def get_run(self, run_id: str) -> dict | None:
        row = self._row_one("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        return self._row(row) if row else None

    def list_runs(self, limit: int = 50, include_team: bool = False) -> list[dict]:
        if include_team:
            rows = self._rows("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,))
        else:
            rows = self._rows("SELECT * FROM runs WHERE visibility = ? ORDER BY created_at DESC LIMIT ?", (PUBLIC, limit))
        return [self._row(r) for r in rows]

    def add_event(self, run_id: str, at_utc: str, stage: str | None, message: str) -> int:
        with self._lock:
            seq = self._conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE run_id = ?", (run_id,)).fetchone()[0]
            self._conn.execute("INSERT INTO events (run_id, seq, at_utc, stage, message) VALUES (?, ?, ?, ?, ?)",
                               (run_id, seq, at_utc, stage, message[:2000]))
            return seq

    def events(self, run_id: str, after: int = 0) -> list[dict]:
        rows = self._rows("SELECT seq, at_utc, stage, message FROM events WHERE run_id = ? AND seq > ? ORDER BY seq", (run_id, after))
        return [dict(r) for r in rows]

    def count_recent(self, requester: str, since_utc: str) -> int:
        return self._row_one("SELECT COUNT(*) FROM runs WHERE requester = ? AND created_at >= ?", (requester, since_utc))[0]

    def spent_since(self, since_utc: str, provider: str) -> float:
        row = self._row_one("SELECT COALESCE(SUM(cost_usd), 0) FROM runs WHERE provider = ? AND created_at >= ?", (provider, since_utc))
        return float(row[0] or 0.0)

    def has_run(self, run_id: str) -> bool:
        return self._row_one("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)) is not None

    def has_out_dir(self, out_dir: Path) -> bool:
        """True when some row already points at this run directory (a run the console started itself, or an earlier
        import). Console runs used to carry a microsecond run_id while the bundle inside used the pipeline's second-
        resolution id, so matching by run_id alone re-imported the console's own runs as duplicates."""
        resolved = str(Path(out_dir).resolve())
        return self._row_one("SELECT 1 FROM runs WHERE out_dir = ? OR out_dir = ?", (resolved, str(out_dir))) is not None

    def dedupe_imports(self) -> list[dict]:
        """Remove rows that point at a run directory another row already owns, keeping the oldest row (the one the
        console created when it started the run). The committed cost of a removed duplicate is carried over when the kept
        row lacks one, so deduplication never drops accounting. Only rows are touched; run directories are never deleted."""
        rows = self._rows("SELECT run_id, out_dir, requester, created_at, cost_committed_usd, cost_usd FROM runs "
                          "WHERE out_dir IS NOT NULL ORDER BY created_at, run_id")
        seen: dict[str, sqlite3.Row] = {}
        removed = []
        for row in rows:
            key = str(Path(row["out_dir"]).resolve())
            kept = seen.get(key)
            if kept is not None:
                carry = {}
                if kept["cost_committed_usd"] is None and row["cost_committed_usd"] is not None:
                    carry["cost_committed_usd"] = row["cost_committed_usd"]
                if kept["cost_usd"] is None and row["cost_usd"] is not None:
                    carry["cost_usd"] = row["cost_usd"]
                if carry:
                    self.update_run(kept["run_id"], **carry)
                self._write("DELETE FROM events WHERE run_id = ?", (row["run_id"],))
                self._write("DELETE FROM runs WHERE run_id = ?", (row["run_id"],))
                removed.append({"run_id": row["run_id"], "kept": kept["run_id"], "out_dir": key})
            else:
                seen[key] = row
        return removed

    def import_run_dir(self, out_dir: Path, requester: str = "import", providers: set[str] | None = None, hold_if_required: bool = False) -> bool:
        """Register a finished run directory (proof_bundle.json present) that the store does not know yet. `providers`
        restricts imports to runs of those providers (short names such as `nebius`, `codex`): a public console imports
        only the judge profile's runs. A development-gateway bundle that is imported becomes a team row. The conservative
        committed cost is preserved from the bundle's totals; a legacy bundle without it has the figure recomputed from
        its call records, or from the ledger journal in the directory (AC-05)."""
        from ..ledger import JOURNAL_FILE, read_journal
        bundle_path = Path(out_dir) / "proof_bundle.json"
        if not bundle_path.is_file():
            return False
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        run_id = bundle.get("run_id") or Path(out_dir).name
        if self.has_run(run_id) or self.has_out_dir(out_dir):
            return False
        ledger = bundle.get("ledger") or {}
        totals = ledger.get("totals") or {}
        task = bundle.get("task") or {}
        profile = bundle.get("profile") or {}
        provider = provider_short_name((profile.get("provider") or {}).get("provider"))
        if providers is not None and provider not in providers:
            return False
        committed = totals.get("cost_usd_committed")
        if committed is None:
            committed = committed_from_ledger(ledger, totals.get("cost_usd"))
        if committed is None:
            journal = read_journal(Path(out_dir) / JOURNAL_FILE)
            if journal is not None:
                committed = max(float(journal["cost_usd_committed"]), float(totals.get("cost_usd") or 0.0))
        self.create_run(run_id=run_id, task_id=task.get("id") or run_id.rsplit("-", 1)[0], task_title=task.get("title") or run_id,
                        provider=provider, visibility=visibility_for(provider),
                        profile_label=profile.get("label") or "imported", status="finished", verdict=(bundle.get("verdict") or {}).get("verdict"),
                        stage="finished", created_at=bundle.get("started_at_utc") or "", started_at=bundle.get("started_at_utc"),
                        finished_at=bundle.get("finished_at_utc"), out_dir=str(Path(out_dir).resolve()), cost_usd=totals.get("cost_usd"),
                        cost_committed_usd=committed,
                        tokens_in=totals.get("tokens_in"), tokens_out=totals.get("tokens_out"), sandbox_ops=totals.get("sandbox_operations"),
                        requester=requester, reasons=json.dumps((bundle.get("verdict") or {}).get("reasons") or []),
                        warnings=json.dumps((bundle.get("verdict") or {}).get("warnings") or []),
                        model_calls=totals.get("model_calls"))
        # A run that was started from a console and archived with its progress events keeps them (console-record.json).
        record_path = Path(out_dir) / "console-record.json"
        if record_path.is_file():
            try:
                for event in json.loads(record_path.read_text(encoding="utf-8")).get("events") or []:
                    self.add_event(run_id, event.get("at_utc") or "", event.get("stage"), event.get("message") or "")
            except (json.JSONDecodeError, OSError, AttributeError):
                pass
        if hold_if_required:
            # the console's own run directory (revision 10): a run found there without a row (a store restored from an older backup) whose
            # records require reconciliation is held like any other; imported evidence from elsewhere is never held for its history
            state = read_run_reconciliation(out_dir)
            if state["required"]:
                halt = state["halt"] or {}
                self.record_reconciliation(run_id, f"stopped for reconciliation at {halt.get('stage') or 'an unrecorded stage'} "
                                                   f"({halt.get('kind') or 'unknown outcome'}): {len(state['items'])} operation(s) to settle; found in the "
                                                   "console's run directory without a row", state["items"], source="import")
        return True

    def active_count(self) -> int:
        return self._row_one("SELECT COUNT(*) FROM runs WHERE status IN ('queued', 'running')")[0]

    @staticmethod
    def _row(row) -> dict:
        data = dict(row)
        for key in ("reasons", "warnings"):
            if data.get(key):
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    data[key] = [data[key]]
            else:
                data[key] = []
        return data
