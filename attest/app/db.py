"""SQLite store for run metadata and progress events (stdlib sqlite3, one writer thread)."""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from pathlib import Path

from ..ledger import utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, task_title TEXT NOT NULL, provider TEXT NOT NULL, profile_label TEXT NOT NULL,
  status TEXT NOT NULL, verdict TEXT, stage TEXT, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT,
  out_dir TEXT, cost_usd REAL, cost_committed_usd REAL, tokens_in INTEGER, tokens_out INTEGER, sandbox_ops INTEGER,
  requester TEXT, error TEXT, reasons TEXT, warnings TEXT
);
CREATE TABLE IF NOT EXISTS events (
  run_id TEXT NOT NULL, seq INTEGER NOT NULL, at_utc TEXT NOT NULL, stage TEXT, message TEXT NOT NULL,
  PRIMARY KEY (run_id, seq)
);
CREATE INDEX IF NOT EXISTS runs_created ON runs(created_at DESC);
"""


class BudgetError(RuntimeError):
    """Raised when creating a run would exceed the daily budget; the run is not created."""


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


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        # Migrate older databases that predate the committed-cost column.
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(runs)").fetchall()}
        if "cost_committed_usd" not in cols:
            self._conn.execute("ALTER TABLE runs ADD COLUMN cost_committed_usd REAL")
        if "model_calls" not in cols:  # M3: live meters while a run is in progress
            self._conn.execute("ALTER TABLE runs ADD COLUMN model_calls INTEGER")

    def _exec(self, sql: str, params=()):
        with self._lock:
            return self._conn.execute(sql, params)

    def create_run(self, **fields) -> None:
        cols = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        self._exec(f"INSERT INTO runs ({cols}) VALUES ({marks})", tuple(fields.values()))

    def _nebius_committed(self, since_utc: str) -> float:
        """Committed USD of today's Nebius runs: finished runs and errored runs alike (a crash after paid calls still spent them;
        an interrupted run carries the conservative reservation set by reconcile_interrupted)."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(COALESCE(cost_committed_usd, cost_usd, 0)), 0) FROM runs "
            "WHERE provider = 'nebius' AND status IN ('finished', 'error') AND created_at >= ?", (since_utc,)).fetchone()
        return float(row[0] or 0.0)

    def _nebius_active(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM runs WHERE provider = 'nebius' AND status IN ('queued', 'running')").fetchone()[0]

    def create_run_reserving(self, per_run_cap: float, daily_cap: float, since_utc: str, **fields) -> dict:
        """Create a run only if its reservation still fits the daily budget. Check and insert happen under one lock,
        so N concurrent callers cannot each pass a stale check: every queued or running Nebius run reserves per_run_cap."""
        with self._lock:
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
                "remaining_usd": round(remaining, 4), "fits_another_run": finished + (active + 1) * per_run_cap <= daily_cap + 1e-9}

    def task_estimates(self, provider: str = "nebius", exclude_verdicts: tuple[str, ...] = ("ERROR", "BASELINE")) -> dict[str, dict]:
        """Per task: the latest recorded run (any provider) and, from completed runs of the public provider only, how
        many there are and their cost and duration ranges. Runs that ended in an infrastructure ERROR or belonged to
        the evaluation's baseline arm say nothing about what a live run costs, so they are left out of the ranges;
        synthetic replay fixtures are left out entirely."""
        rows = self._exec("SELECT run_id, task_id, verdict, status, provider, cost_usd, cost_committed_usd, started_at, finished_at, created_at "
                          "FROM runs WHERE status = 'finished' AND COALESCE(requester, '') != 'replay' AND profile_label NOT LIKE 'replay%' "
                          "ORDER BY created_at DESC").fetchall()
        out: dict[str, dict] = {}
        for row in rows:
            entry = out.setdefault(row["task_id"], {"runs": 0, "cost_min_usd": None, "cost_max_usd": None, "duration_min_s": None,
                                                     "duration_max_s": None, "latest_run_id": row["run_id"], "latest_verdict": row["verdict"],
                                                     "estimate_provider": provider, "recorded_runs": 0})
            entry["recorded_runs"] += 1
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

    def nebius_budget_ok(self, per_run_cap: float, daily_cap: float, since_utc: str) -> tuple[bool, str]:
        """Recheck before execution: this run is already counted among the active runs, so it reserves one slot."""
        with self._lock:
            finished = self._nebius_committed(since_utc)
            active = max(1, self._nebius_active())
            projected = finished + active * per_run_cap
        if projected > daily_cap + 1e-9:
            return False, (f"daily Nebius budget ${daily_cap:.2f} exceeded at execution: ${finished:.4f} committed + "
                           f"{active} active x ${per_run_cap:.2f} reservation = ${projected:.4f}")
        return True, f"${finished:.4f} committed + {active} active reservation(s) within ${daily_cap:.2f}"

    def reconcile_interrupted(self, per_run_cap: float | None = None) -> list[dict]:
        """After a restart, no worker is running the rows left 'queued'/'running'. Finalize any whose bundle landed on
        disk; mark the rest as errored (interrupted). A Nebius run interrupted without a bundle keeps `per_run_cap` as its
        committed cost (its real spend is unknown and at most the cap), so the daily budget never undercounts it.
        Finished rows and their evidence are left untouched."""
        rows = self._exec("SELECT run_id, out_dir, provider, cost_committed_usd FROM runs WHERE status IN ('queued', 'running')").fetchall()
        reconciled = []
        for row in rows:
            run_id, out_dir = row["run_id"], row["out_dir"]
            bundle_path = (Path(out_dir) / "proof_bundle.json") if out_dir else None
            if bundle_path and bundle_path.is_file():
                try:
                    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
                    totals = (bundle.get("ledger") or {}).get("totals") or {}
                    self.update_run(run_id, status="finished", verdict=(bundle.get("verdict") or {}).get("verdict"),
                                    finished_at=bundle.get("finished_at_utc") or utcnow(), stage="finished",
                                    cost_usd=totals.get("cost_usd"), cost_committed_usd=totals.get("cost_usd_committed"),
                                    reasons=json.dumps((bundle.get("verdict") or {}).get("reasons") or []),
                                    warnings=json.dumps((bundle.get("verdict") or {}).get("warnings") or []))
                    reconciled.append({"run_id": run_id, "action": "finalized"})
                    continue
                except Exception:  # noqa: BLE001 - fall through to error marking
                    pass
            fields = {"status": "error", "error": "interrupted by a service restart before completion", "finished_at": utcnow(), "stage": "interrupted"}
            if row["provider"] == "nebius" and per_run_cap is not None and (row["cost_committed_usd"] is None or row["cost_committed_usd"] < per_run_cap):
                fields["cost_committed_usd"] = per_run_cap  # conservative: the actual spend is unknown, the cap is its bound
                fields["error"] += f"; committed cost set to the per-run cap ${per_run_cap:.2f} because the actual spend is unknown"
            self.update_run(run_id, **fields)
            reconciled.append({"run_id": run_id, "action": "interrupted", "cost_committed_usd": fields.get("cost_committed_usd")})
        return reconciled

    def prune_runs(self, data_runs_dir, keep: int = 40, protect: tuple[str, ...] = ("VERIFIED",)) -> list[str]:
        """Keep the newest `keep` console-run directories; delete older ones. Never touches directories outside
        data_runs_dir (imported evidence lives elsewhere) and never deletes a protected verdict."""
        base = str(Path(data_runs_dir).resolve())
        rows = self._exec("SELECT run_id, out_dir, verdict FROM runs WHERE status = 'finished' AND out_dir IS NOT NULL "
                          "ORDER BY created_at DESC").fetchall()
        pruned, seen = [], 0
        for row in rows:
            out_dir = row["out_dir"]
            if not out_dir:
                continue
            resolved = str(Path(out_dir).resolve())
            if resolved != base and not resolved.startswith(base + "/"):
                continue  # imported evidence or anything outside the console's own run directory is left alone
            seen += 1
            if seen <= keep or row["verdict"] in protect:
                continue
            try:
                if Path(resolved).is_dir():
                    shutil.rmtree(resolved)
                self.update_run(row["run_id"], out_dir=None, stage="pruned")
                pruned.append(row["run_id"])
            except OSError:
                pass
        return pruned

    def update_run(self, run_id: str, **fields) -> None:
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._exec(f"UPDATE runs SET {sets} WHERE run_id = ?", (*fields.values(), run_id))

    def get_run(self, run_id: str) -> dict | None:
        row = self._exec("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return self._row(row) if row else None

    def list_runs(self, limit: int = 50) -> list[dict]:
        rows = self._exec("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(r) for r in rows]

    def add_event(self, run_id: str, at_utc: str, stage: str | None, message: str) -> int:
        with self._lock:
            seq = self._conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE run_id = ?", (run_id,)).fetchone()[0]
            self._conn.execute("INSERT INTO events (run_id, seq, at_utc, stage, message) VALUES (?, ?, ?, ?, ?)",
                               (run_id, seq, at_utc, stage, message[:2000]))
            return seq

    def events(self, run_id: str, after: int = 0) -> list[dict]:
        rows = self._exec("SELECT seq, at_utc, stage, message FROM events WHERE run_id = ? AND seq > ? ORDER BY seq", (run_id, after)).fetchall()
        return [dict(r) for r in rows]

    def count_recent(self, requester: str, since_utc: str) -> int:
        return self._exec("SELECT COUNT(*) FROM runs WHERE requester = ? AND created_at >= ?", (requester, since_utc)).fetchone()[0]

    def spent_since(self, since_utc: str, provider: str) -> float:
        row = self._exec("SELECT COALESCE(SUM(cost_usd), 0) FROM runs WHERE provider = ? AND created_at >= ?", (provider, since_utc)).fetchone()
        return float(row[0] or 0.0)

    def has_run(self, run_id: str) -> bool:
        return self._exec("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone() is not None

    def has_out_dir(self, out_dir: Path) -> bool:
        """True when some row already points at this run directory (a run the console started itself, or an earlier
        import). Console runs used to carry a microsecond run_id while the bundle inside used the pipeline's second-
        resolution id, so matching by run_id alone re-imported the console's own runs as duplicates."""
        resolved = str(Path(out_dir).resolve())
        return self._exec("SELECT 1 FROM runs WHERE out_dir = ? OR out_dir = ?", (resolved, str(out_dir))).fetchone() is not None

    def dedupe_imports(self) -> list[dict]:
        """Remove rows that point at a run directory another row already owns, keeping the oldest row (the one the
        console created when it started the run). Only rows are touched; run directories are never deleted."""
        rows = self._exec("SELECT run_id, out_dir, requester, created_at FROM runs WHERE out_dir IS NOT NULL ORDER BY created_at, run_id").fetchall()
        seen: dict[str, str] = {}
        removed = []
        for row in rows:
            key = str(Path(row["out_dir"]).resolve())
            if key in seen:
                self._exec("DELETE FROM events WHERE run_id = ?", (row["run_id"],))
                self._exec("DELETE FROM runs WHERE run_id = ?", (row["run_id"],))
                removed.append({"run_id": row["run_id"], "kept": seen[key], "out_dir": key})
            else:
                seen[key] = row["run_id"]
        return removed

    def import_run_dir(self, out_dir: Path, requester: str = "import", providers: set[str] | None = None) -> bool:
        """Register a finished run directory (proof_bundle.json present) that the store does not know yet. `providers`
        restricts imports to runs of those providers (short names such as `nebius`, `codex`): a public console imports
        only the judge profile's runs, so recorded development runs never become downloadable there."""
        bundle_path = Path(out_dir) / "proof_bundle.json"
        if not bundle_path.is_file():
            return False
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        run_id = bundle.get("run_id") or Path(out_dir).name
        if self.has_run(run_id) or self.has_out_dir(out_dir):
            return False
        totals = (bundle.get("ledger") or {}).get("totals") or {}
        task = bundle.get("task") or {}
        profile = bundle.get("profile") or {}
        provider = ((profile.get("provider") or {}).get("provider") or "unknown").replace("_gateway", "").replace("_tokenfactory", "")
        if providers is not None and provider not in providers:
            return False
        self.create_run(run_id=run_id, task_id=task.get("id") or run_id.rsplit("-", 1)[0], task_title=task.get("title") or run_id,
                        provider=provider,
                        profile_label=profile.get("label") or "imported", status="finished", verdict=(bundle.get("verdict") or {}).get("verdict"),
                        stage="finished", created_at=bundle.get("started_at_utc") or "", started_at=bundle.get("started_at_utc"),
                        finished_at=bundle.get("finished_at_utc"), out_dir=str(Path(out_dir).resolve()), cost_usd=totals.get("cost_usd"),
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
        return True

    def active_count(self) -> int:
        return self._exec("SELECT COUNT(*) FROM runs WHERE status IN ('queued', 'running')").fetchone()[0]

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
