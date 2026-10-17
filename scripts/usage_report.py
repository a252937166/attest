#!/usr/bin/env python3
"""Deduplicated usage report: unique runs and committed USD by provider and UTC day.

Scans directories for `proof_bundle.json`, keys every run by the bundle's `run_id` so copies of a run (for example a
run directory copied into `reports/`) count once, and optionally merges a console store (SQLite) whose rows point at
run directories or carry costs for runs whose bundle is not on this machine. Codex gateway usage is allowance, never
USD; Nebius USD comes from the public price table recorded per call, plus the conservative reservation for calls whose
price never came back (`cost_usd_committed`). The Token Factory console remains the authoritative invoice.

Usage: usage_report.py [--roots runs reports data/runs] [--store data/attest.db] [--json out.json] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVIDER_LABELS = {"nebius_tokenfactory": "nebius", "codex_gateway": "codex", "fake": "fake"}


def provider_label(bundle: dict) -> str:
    raw = ((bundle.get("profile") or {}).get("provider") or {}).get("provider") or "unknown"
    return PROVIDER_LABELS.get(raw, raw)


def scan_bundles(roots: list[Path]) -> tuple[dict[str, dict], list[dict]]:
    unique: dict[str, dict] = {}
    copies: list[dict] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("proof_bundle.json")):
            try:
                bundle = json.loads(path.read_text(encoding="utf-8"))
            except Exception as error:  # noqa: BLE001 - a broken file is reported, not fatal
                copies.append({"path": str(path), "error": f"{type(error).__name__}: {str(error)[:80]}"})
                continue
            run_id = bundle.get("run_id") or path.parent.name
            totals = (bundle.get("ledger") or {}).get("totals") or {}
            record = {"run_id": run_id, "path": str(path.parent), "provider": provider_label(bundle),
                      "profile": (bundle.get("profile") or {}).get("label"), "task": (bundle.get("task") or {}).get("id"),
                      "verdict": (bundle.get("verdict") or {}).get("verdict"), "started_at_utc": bundle.get("started_at_utc") or "",
                      "day": (bundle.get("started_at_utc") or "")[:10] or "unknown", "model_calls": totals.get("model_calls") or 0,
                      "tokens_in": totals.get("tokens_in") or 0, "tokens_out": totals.get("tokens_out") or 0,
                      "cost_usd": totals.get("cost_usd"), "cost_usd_committed": totals.get("cost_usd_committed"),
                      "uncertain_calls": totals.get("uncertain_unpriced_calls") or 0, "sandbox_ops": totals.get("sandbox_operations") or 0}
            if run_id in unique:
                copies.append({"run_id": run_id, "path": str(path.parent), "original": unique[run_id]["path"]})
            else:
                unique[run_id] = record
    return unique, copies


def scan_store(store_path: Path, unique: dict[str, dict]) -> list[dict]:
    """Rows of a console store that no scanned bundle covers (matched by run_id, by run directory, or by task and the
    second-resolution start time, which is how the pre-M1 console ids differed from the bundle ids)."""
    if not store_path.is_file():
        return []
    conn = sqlite3.connect(f"file:{store_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    known_dirs = {Path(r["path"]).resolve().name for r in unique.values()}
    known_keys = {(r["task"], r["started_at_utc"][:19]) for r in unique.values()}
    extra = []
    for row in conn.execute("SELECT * FROM runs WHERE status = 'finished'").fetchall():
        row = dict(row)
        if row["run_id"] in unique:
            continue
        if row.get("out_dir") and Path(row["out_dir"]).name in known_dirs:
            continue
        if (row.get("task_id"), (row.get("started_at") or row.get("created_at") or "")[:19]) in known_keys:
            continue
        extra.append({"run_id": row["run_id"], "path": row.get("out_dir"), "provider": row.get("provider"), "profile": row.get("profile_label"),
                      "task": row.get("task_id"), "verdict": row.get("verdict"), "started_at_utc": row.get("started_at") or row.get("created_at") or "",
                      "day": (row.get("started_at") or row.get("created_at") or "")[:10] or "unknown", "model_calls": None,
                      "tokens_in": row.get("tokens_in") or 0, "tokens_out": row.get("tokens_out") or 0, "cost_usd": row.get("cost_usd"),
                      "cost_usd_committed": row.get("cost_committed_usd"), "uncertain_calls": 0, "sandbox_ops": row.get("sandbox_ops") or 0,
                      "source": "store-only"})
    return extra


def aggregate(records: list[dict]) -> dict:
    groups: dict[tuple[str, str], dict] = defaultdict(lambda: {"runs": 0, "model_calls": 0, "tokens_in": 0, "tokens_out": 0,
                                                              "cost_usd": 0.0, "cost_usd_committed": 0.0, "uncertain_calls": 0,
                                                              "verdicts": defaultdict(int)})
    for r in records:
        g = groups[(r["provider"], r["day"])]
        g["runs"] += 1
        g["model_calls"] += r.get("model_calls") or 0
        g["tokens_in"] += r.get("tokens_in") or 0
        g["tokens_out"] += r.get("tokens_out") or 0
        g["cost_usd"] += r.get("cost_usd") or 0.0
        g["cost_usd_committed"] += r.get("cost_usd_committed") if r.get("cost_usd_committed") is not None else (r.get("cost_usd") or 0.0)
        g["uncertain_calls"] += r.get("uncertain_calls") or 0
        g["verdicts"][r.get("verdict") or "?"] += 1
    out = {}
    for (provider, day), g in sorted(groups.items()):
        out.setdefault(provider, {})[day] = {**g, "cost_usd": round(g["cost_usd"], 4), "cost_usd_committed": round(g["cost_usd_committed"], 4),
                                             "verdicts": dict(g["verdicts"])}
    totals = {}
    for provider, days in out.items():
        totals[provider] = {"runs": sum(d["runs"] for d in days.values()), "model_calls": sum(d["model_calls"] for d in days.values()),
                            "cost_usd": round(sum(d["cost_usd"] for d in days.values()), 4),
                            "cost_usd_committed": round(sum(d["cost_usd_committed"] for d in days.values()), 4),
                            "uncertain_calls": sum(d["uncertain_calls"] for d in days.values())}
    return {"by_provider_day": out, "totals": totals}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roots", nargs="*", default=["runs", "reports", "data/runs"], help="directories to scan for proof_bundle.json")
    ap.add_argument("--store", default="", help="console SQLite store to merge (rows not covered by a scanned bundle are added as store-only)")
    ap.add_argument("--json", default="", help="write the full report here")
    ap.add_argument("--verbose", action="store_true", help="list every unique run")
    args = ap.parse_args()
    roots = [Path(r) if Path(r).is_absolute() else ROOT / r for r in args.roots]
    unique, copies = scan_bundles(roots)
    store_rows = scan_store(Path(args.store), unique) if args.store else []
    records = list(unique.values()) + store_rows
    agg = aggregate(records)
    report = {"roots": [str(r) for r in roots], "store": args.store or None, "unique_runs": len(unique), "copies_skipped": len([c for c in copies if "run_id" in c]),
              "unreadable": [c for c in copies if "error" in c], "store_only_runs": len(store_rows), **agg,
              "copies": copies, "runs": sorted(records, key=lambda r: (r["provider"], r["started_at_utc"]))}
    print(f"unique runs: {len(unique)} (skipped {report['copies_skipped']} copies of the same run_id); store-only rows: {len(store_rows)}")
    print(f"{'provider':<9} {'day (UTC)':<11} {'runs':>5} {'calls':>6} {'USD known':>10} {'USD committed':>14} {'uncertain':>9}  verdicts")
    for provider, days in agg["by_provider_day"].items():
        for day, g in days.items():
            print(f"{provider:<9} {day:<11} {g['runs']:>5} {g['model_calls']:>6} {g['cost_usd']:>10.4f} {g['cost_usd_committed']:>14.4f} {g['uncertain_calls']:>9}  {g['verdicts']}")
    for provider, t in agg["totals"].items():
        note = " (allowance, not USD)" if provider == "codex" else ""
        print(f"total {provider:<9} runs {t['runs']:>4} calls {t['model_calls']:>5} USD known {t['cost_usd']:.4f} committed {t['cost_usd_committed']:.4f}{note}")
    if args.verbose:
        for r in report["runs"]:
            print(f"  {r['provider']:<7} {r['day']} {r['run_id']:<48} {str(r['verdict']):<12} committed={r.get('cost_usd_committed')} {r.get('source', 'bundle')}")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
