"""FastAPI application: JSON API plus the static console. Run with `uvicorn attest.app.server:app`."""

from __future__ import annotations

import datetime as dt
import io
import json
import os
import re
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import __version__
from ..core.exhibits import summary as exhibit_summary
from ..core.manifest import MANIFEST_FILE, build_manifest
from .db import Store, duration_seconds
from .worker import Worker

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.environ.get("ATTEST_DATA_DIR", ROOT / "data")).resolve()
EXAMPLES_DIR = Path(os.environ.get("ATTEST_EXAMPLES_DIR", ROOT / "examples")).resolve()
ADMIN_TOKEN = os.environ.get("ATTEST_ADMIN_TOKEN", "")
PUBLIC_RUNS_PER_HOUR = int(os.environ.get("ATTEST_PUBLIC_RUNS_PER_HOUR", "3"))

# Artifacts a visitor may download from a run directory: a closed set of shapes, so no path can escape the directory.
ARTIFACT_PATTERN = re.compile(
    r"^(?:PROOF\.md|proof_bundle\.json|manifest\.json|candidate\.patch|ledger\.json|spec\.json|verify\.json|verify_raw\.json|"
    r"breaker\.json|drift\.json|grounding\.json|arbitration\.json|trajectory\.jsonl|tamper_scan\.json|task\.frozen\.json|"
    r"baseline\.json|judge\.json|breaker_tests\.py|red\.attempt\d+\.json|breaker_tests\.attempt\d+\.py|breaker_response\.attempt\d+\.json|"
    r"mutants_[A-Za-z0-9_-]+\.py|sealed/test_sealed\.py|sealed/test_sealed\.attempt\d+\.py|arbitration/(?:sealed|adversarial)_corrected\.py|"
    r"contract_audit\.json|contract_audit/witness_\d+\.py|ledger\.jsonl)$")
MEDIA_TYPES = {".md": "text/markdown", ".json": "application/json", ".jsonl": "application/json", ".patch": "text/x-diff", ".py": "text/x-python"}

# Inference profiles. The public list names only the judge profile; the development profile is returned only to a caller
# who presents the admin token, so the public page and its API responses never carry the development gateway's name.
PUBLIC_PROFILES = [{"id": "nebius", "label": "NVIDIA Nemotron on Nebius Token Factory", "short": "Nemotron", "public": True,
                    "note": "Judge profile. Paid Nebius inference under the per-run and daily caps."}]
TEAM_PROFILES = [{"id": "codex", "label": "Development gateway (team only)", "short": "the development gateway", "public": False,
                  "note": "Team allowance, not a Nebius charge. Development runs are labelled separately from submission runs."}]

store = Store(DATA_DIR / "attest.db")
IMPORT_DIRS = [Path(p).resolve() for p in os.environ.get("ATTEST_IMPORT_DIRS", str(DATA_DIR / "runs")).split(":") if p]
# Recorded evidence imported at startup is limited to the judge profile's provider by default: development-profile bundles
# (and their ledgers) stay in the private tree instead of becoming downloadable from the public console.
IMPORT_PROVIDERS = {p.strip() for p in os.environ.get("ATTEST_IMPORT_PROVIDERS", "nebius").split(",") if p.strip()}
for _dir in IMPORT_DIRS:
    for _run_dir in sorted(_dir.glob("*/")) if _dir.is_dir() else []:
        try:
            store.import_run_dir(_run_dir, providers=IMPORT_PROVIDERS)
        except Exception:  # noqa: BLE001 - a broken directory must not prevent startup
            pass
DEDUPED = store.dedupe_imports()  # console runs re-imported from disk under a second id (pre-M1 hygiene bug)
RECONCILED = store.reconcile_interrupted(per_run_cap=float(os.environ.get("ATTEST_PER_RUN_USD_CAP", "0.5")))  # settle rows a restart orphaned
worker = Worker(store, DATA_DIR, EXAMPLES_DIR,
                per_run_usd_cap=float(os.environ.get("ATTEST_PER_RUN_USD_CAP", "0.5")),
                daily_usd_cap=float(os.environ.get("ATTEST_DAILY_USD_CAP", "2.0")),
                retention_keep=int(os.environ.get("ATTEST_RETENTION_KEEP", "40")),
                min_free_frac=float(os.environ.get("ATTEST_MIN_FREE_FRAC", "0.07")),
                min_free_mb=int(os.environ.get("ATTEST_MIN_FREE_MB", "500")))
app = FastAPI(title="Attest console", version=__version__, docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class RunRequest(BaseModel):
    task_id: str
    provider: str = "nebius"
    admin_token: str | None = None


class TokenRequest(BaseModel):
    admin_token: str | None = None


def _requester(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return (forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown"))


def _is_admin(token: str | None) -> bool:
    return bool(ADMIN_TOKEN) and token == ADMIN_TOKEN


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")


def provenance_of(run: dict) -> str:
    """Where a run row came from: `live` (started from this console), `imported` (recorded evidence registered from disk)
    or `synthetic` (a replay fixture; see scripts/console_replay.py)."""
    requester = run.get("requester") or ""
    if requester == "replay" or (run.get("profile_label") or "").startswith("replay"):
        return "synthetic"
    if requester == "import":
        return "imported"
    out_dir = run.get("out_dir")
    if out_dir:
        resolved = str(Path(out_dir).resolve())
        base = str((DATA_DIR / "runs").resolve())
        if resolved != base and not resolved.startswith(base + "/"):
            return "imported"
    return "live"


def run_summary(run: dict) -> dict:
    """Verdict, cost, duration and provenance for a history row, without loading the bundle."""
    return {"verdict": run.get("verdict"), "status": run.get("status"), "stage": run.get("stage"), "cost_usd": run.get("cost_usd"),
            "cost_committed_usd": run.get("cost_committed_usd"),
            "duration_s": duration_seconds(run.get("started_at") or run.get("created_at"), run.get("finished_at")),
            "provenance": provenance_of(run), "model_calls": run.get("model_calls"), "sandbox_ops": run.get("sandbox_ops")}


def _with_summary(run: dict) -> dict:
    run = dict(run)
    run["summary"] = run_summary(run)
    run["provenance"] = run["summary"]["provenance"]
    return run


def _manifest_for(out_dir: Path, run_id: str) -> dict | None:
    path = out_dir / MANIFEST_FILE
    if path.is_file():
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["recorded"] = True  # written by the run itself; an integrity check, not a signature
            return manifest
        except (json.JSONDecodeError, OSError):
            pass
    if not out_dir.is_dir():
        return None
    manifest = build_manifest(out_dir, run_id)
    manifest["recorded"] = False
    manifest["note"] = "no manifest.json in this run directory (recorded before milestone M2); digests computed on request"
    return manifest


@app.get("/api/health")
def health():
    today = _today()
    disk = worker.disk()
    # executing=False: the health report describes the service as it is; an idle service has zero active reservations
    budget_ok, budget_detail = store.nebius_budget_ok(worker.per_run_usd_cap, worker.daily_usd_cap, today, executing=False)
    remaining = store.nebius_remaining(worker.per_run_usd_cap, worker.daily_usd_cap, today)
    return {"ok": True, "version": __version__, "worker_alive": worker.thread.is_alive(), "queue": worker.queue.qsize(),
            "current": worker.current, "data_dir": str(DATA_DIR), "time_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "disk": {"free_mb": disk.get("free_mb"), "free_frac": disk.get("free_frac"), "low": disk.get("low"),
                     "accepting_runs": not disk.get("low")},
            "budget": {"daily_cap_usd": worker.daily_usd_cap, "per_run_cap_usd": worker.per_run_usd_cap,
                       "nebius_ok": budget_ok, "detail": budget_detail, "remaining_usd": remaining["remaining_usd"],
                       "committed_today_usd": remaining["committed_usd"], "reserved_usd": remaining["reserved_usd"],
                       "active_runs": remaining["active_runs"]},
            "public_runs_per_hour": PUBLIC_RUNS_PER_HOUR,
            "reconciled_at_startup": RECONCILED, "deduplicated_at_startup": DEDUPED}


@app.get("/api/profiles")
def profiles_public():
    return {"profiles": PUBLIC_PROFILES, "team": False}


@app.post("/api/profiles")
def profiles(body: TokenRequest):
    """The profile list for a caller. Only a valid admin token reveals the team profile."""
    if _is_admin(body.admin_token):
        return {"profiles": PUBLIC_PROFILES + TEAM_PROFILES, "team": True}
    return {"profiles": PUBLIC_PROFILES, "team": False}


@app.get("/api/tasks")
def tasks():
    estimates = store.task_estimates()
    items = []
    for item in worker.tasks():
        estimate = estimates.get(item["task_id"]) or {"runs": 0, "cost_min_usd": None, "cost_max_usd": None, "duration_min_s": None,
                                                      "duration_max_s": None, "latest_run_id": None, "latest_verdict": None}
        items.append({**item, "estimate": estimate})
    return {"tasks": items}


@app.get("/api/runs")
def runs(limit: int = 50):
    rows = [_with_summary(r) for r in store.list_runs(limit=min(max(limit, 1), 200))]
    return {"runs": rows, "current": worker.current, "queue": worker.queue.qsize()}


@app.post("/api/runs")
def start_run(body: RunRequest, request: Request):
    requester = _requester(request)
    admin = _is_admin(body.admin_token)
    if body.provider not in ("nebius", "codex"):
        raise HTTPException(400, "unknown inference profile")
    if body.provider == "codex" and not admin:
        raise HTTPException(403, "the development profile is reserved for the project team; judges run the Nemotron profile")
    if not admin:
        since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).isoformat()
        if store.count_recent(requester, since) >= PUBLIC_RUNS_PER_HOUR:
            raise HTTPException(429, f"rate limit: {PUBLIC_RUNS_PER_HOUR} runs per hour per visitor")
    profile = "development" if body.provider == "codex" else ("submission" if admin else "judge-demo")
    try:
        return worker.enqueue(body.task_id, body.provider, requester, profile)
    except ValueError as error:
        raise HTTPException(404, str(error)) from None
    except RuntimeError as error:
        raise HTTPException(503, str(error)) from None


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "unknown run")
    bundle = None
    manifest = None
    if run.get("out_dir"):
        out_dir = Path(run["out_dir"])
        path = out_dir / "proof_bundle.json"
        if path.is_file():
            bundle = json.loads(path.read_text(encoding="utf-8"))
            manifest = _manifest_for(out_dir, run_id)
    run = _with_summary(run)
    return {"run": run, "bundle": bundle, "events": store.events(run_id), "provenance": run["provenance"],
            "exhibits": exhibit_summary(bundle) if bundle else None, "manifest": manifest}


@app.get("/api/runs/{run_id}/events")
def run_events(run_id: str, after: int = 0):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "unknown run")
    return {"events": store.events(run_id, after), "status": run["status"], "stage": run.get("stage"), "verdict": run.get("verdict"),
            "meters": {"model_calls": run.get("model_calls"), "sandbox_ops": run.get("sandbox_ops"), "cost_committed_usd": run.get("cost_committed_usd"),
                       "tokens_in": run.get("tokens_in"), "tokens_out": run.get("tokens_out"), "started_at": run.get("started_at"),
                       "finished_at": run.get("finished_at"), "created_at": run.get("created_at")},
            "queue": worker.queue.qsize(), "current": worker.current, "error": run.get("error")}


@app.get("/api/runs/{run_id}/artifacts/{name:path}")
def artifact(run_id: str, name: str):
    run = store.get_run(run_id)
    if not run or not run.get("out_dir"):
        raise HTTPException(404, "unknown run or no artifacts yet")
    if not ARTIFACT_PATTERN.match(name):
        raise HTTPException(404, "artifact not available")
    path = Path(run["out_dir"]) / name
    if not path.is_file():
        raise HTTPException(404, "artifact missing")
    return FileResponse(str(path), media_type=MEDIA_TYPES.get(path.suffix, "application/octet-stream"), filename=path.name)


@app.get("/api/runs/{run_id}/bundle.zip")
def bundle_zip(run_id: str):
    run = store.get_run(run_id)
    if not run or not run.get("out_dir"):
        raise HTTPException(404, "unknown run or no artifacts yet")
    root = Path(run["out_dir"])
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.stat().st_size < 5_000_000:
                archive.write(path, arcname=f"{root.name}/{path.relative_to(root).as_posix()}")
    buffer.seek(0)
    return Response(buffer.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{root.name}-proof-bundle.zip"'})


@app.get("/", response_class=HTMLResponse)
@app.get("/runs/{run_id}", response_class=HTMLResponse)
def index(run_id: str | None = None):
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": type(exc).__name__, "detail": str(exc)[:300]})
