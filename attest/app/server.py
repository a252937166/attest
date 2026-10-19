"""FastAPI application: JSON API plus the static console. Run with `uvicorn attest.app.server:app`.

Public surface (API-04, API-09): every run row leaves the API through `public_run`, an explicit projection. Requester
addresses, host paths and diagnostic text never do; a failed run is published as `error_code` plus a neutral
`error_public` sentence carrying a correlation reference, and an unhandled exception is answered with
`{"error": "internal_error", "correlation_id": ...}` while the traceback goes to the `attest.app` log under that id.

Visibility (publication contract): rows of the development gateway (the team profile) are `team` rows. Every read route
(list, detail, events, artifacts, zip, the current-run reference and the task estimates) hides them unless the caller
presents the team token in an `X-Attest-Token` header or, for downloads, a `token` query parameter.

Requester identity (API-01): the hourly visitor quota uses the peer address, unless the peer is one of the trusted proxies
(`ATTEST_TRUSTED_PROXIES`, default the loopback addresses of the nginx vhost on the same host), in which case the LAST
X-Forwarded-For item is used, validated as an IP literal. A caller cannot choose its own identity.

Downloads (API-05): a ZIP is built from an explicit artifact set (the manifest's listing, or the allowlisted files of a run
recorded before manifests existed), each entry a contained regular file; per-file and aggregate caps are enforced with an
explicit 413, and the archive is spooled to a temporary file rather than held in memory.
"""

from __future__ import annotations

import datetime as dt
import ipaddress
import json
import logging
import os
import re
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import __version__
from ..core.exhibits import summary as exhibit_summary
from ..core.manifest import MANIFEST_FILE, build_manifest
from .db import BUDGET_POLICY, ERROR_TEXT, PUBLIC, TEAM, QuotaError, Store, duration_seconds
from .worker import Worker

LOG = logging.getLogger("attest.app")
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.environ.get("ATTEST_DATA_DIR", ROOT / "data")).resolve()
EXAMPLES_DIR = Path(os.environ.get("ATTEST_EXAMPLES_DIR", ROOT / "examples")).resolve()
ADMIN_TOKEN = os.environ.get("ATTEST_ADMIN_TOKEN", "")
PUBLIC_RUNS_PER_HOUR = int(os.environ.get("ATTEST_PUBLIC_RUNS_PER_HOUR", "3"))
RETENTION_KEEP_ERRORS = int(os.environ.get("ATTEST_RETENTION_KEEP_ERRORS", "10"))


def _parse_proxies(spec: str) -> tuple:
    networks = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            LOG.warning("ignoring an invalid ATTEST_TRUSTED_PROXIES entry: %r", item)
    return tuple(networks)


# Peers whose X-Forwarded-For header is believed: the reverse proxy on this host. IPs or CIDRs, comma-separated.
TRUSTED_PROXIES = _parse_proxies(os.environ.get("ATTEST_TRUSTED_PROXIES", "127.0.0.1,::1"))

# Download caps: one artifact, and the whole archive (uncompressed). Exceeding either is an explicit 413, never an omission.
ZIP_MAX_FILE_BYTES = 32 * 1024 * 1024
ZIP_MAX_TOTAL_BYTES = 128 * 1024 * 1024

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

# The fields of a run row that the API publishes. Everything else on the row (requester, out_dir, error, error_detail,
# error_ref) stays on the server.
PUBLIC_RUN_FIELDS = ("run_id", "task_id", "task_title", "provider", "profile_label", "status", "verdict", "stage", "created_at",
                     "started_at", "finished_at", "cost_usd", "cost_committed_usd", "tokens_in", "tokens_out", "sandbox_ops",
                     "model_calls", "reasons", "warnings", "visibility")

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
                min_free_mb=int(os.environ.get("ATTEST_MIN_FREE_MB", "500")),
                retention_keep_errors=RETENTION_KEEP_ERRORS)
app = FastAPI(title="Attest console", version=__version__, docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class RunRequest(BaseModel):
    task_id: str
    provider: str = "nebius"
    admin_token: str | None = None


class TokenRequest(BaseModel):
    admin_token: str | None = None


# ------------------------------------------------------------------ identity and visibility
def _is_trusted_proxy(host: str | None) -> bool:
    try:
        address = ipaddress.ip_address(host or "")
    except ValueError:
        return False
    return any(address in network for network in TRUSTED_PROXIES)


def requester_from(peer: str | None, forwarded: str | None) -> str:
    """The visitor identity behind the hourly quota. Only a trusted proxy's X-Forwarded-For is believed, and only its LAST
    item (the address that proxy appended), which must be an IP literal; a malformed item attributes the request to the
    proxy itself. Any other peer is identified by its own address and the header is ignored."""
    peer = peer or "unknown"
    if not forwarded or not _is_trusted_proxy(peer):
        return peer
    items = [item.strip() for item in forwarded.split(",") if item.strip()]
    if not items:
        return peer
    try:
        return str(ipaddress.ip_address(items[-1]))
    except ValueError:
        return peer


def _requester(request: Request) -> str:
    return requester_from(request.client.host if request.client else None, request.headers.get("x-forwarded-for"))


def _is_admin(token: str | None) -> bool:
    return bool(ADMIN_TOKEN) and token == ADMIN_TOKEN


def _caller_token(request: Request) -> str | None:
    return request.headers.get("x-attest-token") or request.query_params.get("token")


def _team_caller(request: Request) -> bool:
    """A caller who presents the team token may see team runs."""
    return _is_admin(_caller_token(request))


def _visible(run: dict, team: bool) -> bool:
    return team or run.get("visibility", PUBLIC) != TEAM


def _visible_run(run_id: str, request: Request) -> tuple[dict, bool]:
    """The row, or 404; a team row is 'unknown' to a caller without the token, exactly like a missing one."""
    team = _team_caller(request)
    run = store.get_run(run_id)
    if not run or not _visible(run, team):
        raise HTTPException(404, "unknown run")
    return run, team


def _current_ref(team: bool) -> str | None:
    """The id of the run being executed, when the caller may see it."""
    current = worker.current
    if not current:
        return None
    if team:
        return current
    run = store.get_run(current)
    return current if run and _visible(run, team) else None


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")


# ------------------------------------------------------------------ public projection
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


def public_error(run: dict) -> tuple[str | None, str | None]:
    """The published form of a failure: a stable code and a neutral sentence with the correlation reference. Rows recorded
    before error codes existed (imported, replayed or legacy rows) get the generic code and the run id as their reference."""
    if run.get("status") != "error" and not run.get("error"):
        return None, None
    code = run.get("error_code") or "run_failed"
    text = ERROR_TEXT.get(code, ERROR_TEXT["run_failed"])
    return code, f"{text}; reference {run.get('error_ref') or run.get('run_id')}"


def public_run(run: dict) -> dict:
    """The explicit public model of a run row: allowlisted fields, a boolean for the presence of artifacts instead of the
    directory, and the sanitized error pair instead of the stored message."""
    out = {key: run.get(key) for key in PUBLIC_RUN_FIELDS}
    out_dir = run.get("out_dir")
    out["has_artifacts"] = bool(out_dir) and Path(out_dir).is_dir()
    out["error_code"], out["error_public"] = public_error(run)
    out["summary"] = run_summary(run)
    out["provenance"] = out["summary"]["provenance"]
    return out


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


# ------------------------------------------------------------------ artifact containment (API-05, publication boundary)
class ArtifactSetError(Exception):
    """The download cannot be produced as advertised; answered explicitly, never with a silently partial archive."""

    def __init__(self, code: str, message: str, status: int = 409, **extra):
        super().__init__(message)
        self.code, self.message, self.status, self.extra = code, message, status, extra

    def payload(self) -> dict:
        return {"error": self.code, "detail": self.message, **self.extra}


def contained_file(root: Path, rel: str) -> Path | None:
    """`rel` as a regular file inside the run directory `root`, or None. Rejects absolute or dotted segments, any symlink at or
    below the run directory (a link could point outside it), and a resolved path that leaves the resolved run directory."""
    rel_path = Path(rel)
    if not rel or rel_path.is_absolute() or "\\" in rel or any(part in ("", ".", "..") for part in rel_path.parts):
        return None
    if root.is_symlink():
        return None
    try:
        base = root.resolve(strict=True)
    except OSError:
        return None
    current = root
    for part in rel_path.parts:
        current = current / part
        if current.is_symlink():
            return None
    if not current.is_file():
        return None
    try:
        resolved = current.resolve(strict=True)
    except OSError:
        return None
    if base != resolved and base not in resolved.parents:
        return None
    return current


def artifact_set(root: Path) -> list[tuple[str, Path]]:
    """The files a download contains. With a manifest: exactly the files it lists, plus the manifest itself; a listed file
    that is missing, a link or outside the run directory is an error, never a silent omission. Without a manifest (runs
    recorded before milestone M2): the contained regular files matching ARTIFACT_PATTERN. The per-file and aggregate caps
    are enforced before any byte is written."""
    manifest_path = root / MANIFEST_FILE
    items: list[tuple[str, Path]] = []
    if manifest_path.is_file() and not manifest_path.is_symlink():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = [str(entry.get("path") or "") for entry in (manifest.get("files") or []) if isinstance(entry, dict)]
        except (ValueError, OSError, AttributeError):
            raise ArtifactSetError("manifest_unreadable", "the run's manifest cannot be read") from None
        items.append((MANIFEST_FILE, manifest_path))
        for rel in entries:
            path = contained_file(root, rel)
            if path is None:
                raise ArtifactSetError("manifest_mismatch", f"the manifested artifact {rel!r} is missing, a link or outside the run directory; "
                                                            "a download would not match the manifest")
            items.append((rel, path))
    else:
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if not ARTIFACT_PATTERN.match(rel) or contained_file(root, rel) is None:
                continue
            items.append((rel, path))
    total = 0
    for rel, path in items:
        size = path.stat().st_size
        if size > ZIP_MAX_FILE_BYTES:
            raise ArtifactSetError("export_too_large", f"artifact {rel} is {size} bytes; the download limit is {ZIP_MAX_FILE_BYTES} bytes per file",
                                   status=413, limit_bytes=ZIP_MAX_FILE_BYTES)
        total += size
    if total > ZIP_MAX_TOTAL_BYTES:
        raise ArtifactSetError("export_too_large", f"the run's artifacts total {total} bytes; the download limit is {ZIP_MAX_TOTAL_BYTES} bytes",
                               status=413, limit_bytes=ZIP_MAX_TOTAL_BYTES)
    return items


# ------------------------------------------------------------------ routes
@app.get("/api/health")
def health(request: Request):
    team = _team_caller(request)
    today = _today()
    alive = worker.ensure_alive()
    disk = worker.disk()
    # executing=False: the health report describes the service as it is; an idle service has zero active reservations
    budget_ok, budget_detail = store.nebius_budget_ok(worker.per_run_usd_cap, worker.daily_usd_cap, today, executing=False)
    remaining = store.nebius_remaining(worker.per_run_usd_cap, worker.daily_usd_cap, today)
    return {"ok": True, "version": __version__, "worker_alive": alive, "worker_restarts": worker.restarts,
            "ready": alive and not disk.get("low"), "queue": worker.queue.qsize(), "busy": worker.current is not None,
            "current": _current_ref(team), "time_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "disk": {"free_mb": disk.get("free_mb"), "free_frac": disk.get("free_frac"), "low": disk.get("low"),
                     "accepting_runs": not disk.get("low")},
            "budget": {"daily_cap_usd": worker.daily_usd_cap, "per_run_cap_usd": worker.per_run_usd_cap,
                       "nebius_ok": budget_ok, "detail": budget_detail, "remaining_usd": remaining["remaining_usd"],
                       "committed_today_usd": remaining["committed_usd"], "reserved_usd": remaining["reserved_usd"],
                       "active_runs": remaining["active_runs"], "policy": BUDGET_POLICY},
            "public_runs_per_hour": PUBLIC_RUNS_PER_HOUR,
            "startup": {"reconciled": len(RECONCILED), "deduplicated": len(DEDUPED)}, "team": team}


@app.get("/api/profiles")
def profiles_public():
    return {"profiles": PUBLIC_PROFILES, "team": False}


@app.post("/api/profiles")
def profiles(body: TokenRequest):
    """The profile list for a caller. Only a valid team token reveals the team profile."""
    if _is_admin(body.admin_token):
        return {"profiles": PUBLIC_PROFILES + TEAM_PROFILES, "team": True}
    return {"profiles": PUBLIC_PROFILES, "team": False}


@app.get("/api/tasks")
def tasks(request: Request):
    estimates = store.task_estimates(include_team=_team_caller(request))
    items = []
    for item in worker.tasks():
        estimate = estimates.get(item["task_id"]) or {"runs": 0, "recorded_runs": 0, "cost_min_usd": None, "cost_max_usd": None, "duration_min_s": None,
                                                      "duration_max_s": None, "latest_run_id": None, "latest_verdict": None, "estimate_provider": "nebius"}
        items.append({**{k: v for k, v in item.items() if k != "path"}, "estimate": estimate})
    return {"tasks": items}


@app.get("/api/runs")
def runs(request: Request, limit: int = 50):
    team = _team_caller(request)
    rows = [public_run(r) for r in store.list_runs(limit=min(max(limit, 1), 200), include_team=team)]
    return {"runs": rows, "current": _current_ref(team), "queue": worker.queue.qsize(), "busy": worker.current is not None}


@app.post("/api/runs")
def start_run(body: RunRequest, request: Request):
    requester = _requester(request)
    admin = _is_admin(body.admin_token) or _team_caller(request)
    if body.provider not in ("nebius", "codex"):
        raise HTTPException(400, "unknown inference profile")
    if body.provider == "codex" and not admin:
        raise HTTPException(403, "the development profile is reserved for the project team; judges run the Nemotron profile")
    if worker.task_path(body.task_id) is None:
        raise HTTPException(404, f"unknown task {body.task_id}")
    if not worker.ensure_alive():  # readiness is checked before any row or reservation exists (API-07)
        raise HTTPException(503, "the run worker is not available; nothing was queued")
    quota = None
    if not admin:
        since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).isoformat()
        quota = (requester, since, PUBLIC_RUNS_PER_HOUR)
    profile = "development" if body.provider == "codex" else ("submission" if admin else "judge-demo")
    try:
        return worker.enqueue(body.task_id, body.provider, requester, profile, quota=quota)
    except QuotaError as error:
        raise HTTPException(429, str(error)) from None
    except ValueError as error:
        raise HTTPException(404, str(error)) from None
    except RuntimeError as error:  # budget, disk, queue capacity, worker availability
        raise HTTPException(503, str(error)) from None


def _bundle_incomplete() -> JSONResponse:
    return JSONResponse(status_code=503, headers={"Retry-After": "2"},
                        content={"error": "bundle_incomplete", "retry_after_s": 2, "detail": "the run record is still being written; retry shortly"})


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str, request: Request):
    run, _ = _visible_run(run_id, request)
    bundle = None
    manifest = None
    if run.get("out_dir"):
        out_dir = Path(run["out_dir"])
        path = out_dir / "proof_bundle.json"
        if path.is_file():
            try:
                bundle = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(bundle, dict):
                    raise ValueError("the bundle is not a JSON object")
            except (ValueError, OSError):  # a partial or unreadable bundle: deliberately retryable, never a 500
                return _bundle_incomplete()
            manifest = _manifest_for(out_dir, run_id)
    public = public_run(run)
    return {"run": public, "bundle": bundle, "events": store.events(run_id), "provenance": public["provenance"],
            "exhibits": exhibit_summary(bundle) if bundle else None, "manifest": manifest}


@app.get("/api/runs/{run_id}/events")
def run_events(run_id: str, request: Request, after: int = 0):
    run, team = _visible_run(run_id, request)
    code, public = public_error(run)
    return {"events": store.events(run_id, after), "status": run["status"], "stage": run.get("stage"), "verdict": run.get("verdict"),
            "meters": {"model_calls": run.get("model_calls"), "sandbox_ops": run.get("sandbox_ops"), "cost_committed_usd": run.get("cost_committed_usd"),
                       "tokens_in": run.get("tokens_in"), "tokens_out": run.get("tokens_out"), "started_at": run.get("started_at"),
                       "finished_at": run.get("finished_at"), "created_at": run.get("created_at")},
            "queue": worker.queue.qsize(), "busy": worker.current is not None, "current": _current_ref(team),
            "position": worker.position(run_id), "error_code": code, "error_public": public}


@app.get("/api/runs/{run_id}/artifacts/{name:path}")
def artifact(run_id: str, name: str, request: Request):
    run, _ = _visible_run(run_id, request)
    if not run.get("out_dir"):
        raise HTTPException(404, "unknown run or no artifacts yet")
    if not ARTIFACT_PATTERN.match(name):
        raise HTTPException(404, "artifact not available")
    path = contained_file(Path(run["out_dir"]), name)
    if path is None:
        raise HTTPException(404, "artifact not available")
    return FileResponse(str(path), media_type=MEDIA_TYPES.get(path.suffix, "application/octet-stream"), filename=path.name)


@app.get("/api/runs/{run_id}/bundle.zip")
def bundle_zip(run_id: str, request: Request):
    run, _ = _visible_run(run_id, request)
    if not run.get("out_dir"):
        raise HTTPException(404, "unknown run or no artifacts yet")
    root = Path(run["out_dir"])
    if root.is_symlink() or not root.is_dir():
        raise HTTPException(404, "unknown run or no artifacts yet")
    try:
        items = artifact_set(root)
    except ArtifactSetError as error:
        return JSONResponse(status_code=error.status, content=error.payload())
    spool = tempfile.TemporaryFile(prefix="attest-bundle-")
    try:
        with zipfile.ZipFile(spool, "w", zipfile.ZIP_DEFLATED) as archive:
            for rel, path in items:
                archive.write(path, arcname=f"{root.name}/{rel}")
        size = spool.tell()
        spool.seek(0)
    except BaseException:
        spool.close()
        raise

    def stream():
        try:
            while True:
                chunk = spool.read(1 << 16)
                if not chunk:
                    break
                yield chunk
        finally:
            spool.close()

    return StreamingResponse(stream(), media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{root.name}-proof-bundle.zip"', "Content-Length": str(size)})


@app.get("/", response_class=HTMLResponse)
@app.get("/runs/{run_id}", response_class=HTMLResponse)
def index(run_id: str | None = None):
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    correlation_id = uuid.uuid4().hex
    LOG.error("internal error %s on %s %s", correlation_id, request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "internal_error", "correlation_id": correlation_id},
                        headers={"X-Correlation-ID": correlation_id})
