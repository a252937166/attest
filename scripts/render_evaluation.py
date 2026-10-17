#!/usr/bin/env python3
"""Render an evaluation report (`evaluation.json` written by run_evaluation.py) as Markdown: every scheduled cell, the
confusion counts per system, costs, provenance and pacing. Nothing is filtered or merged; the table is the schedule.

Usage: render_evaluation.py reports/<batch-dir>/evaluation.json [--out RESULTS.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def render(report: dict) -> str:
    schedule = report["schedule"]
    rows = report["rows"]
    prov = schedule.get("provenance") or {}
    lines = [f"# Evaluation results: {schedule.get('label') or 'batch'} ({schedule.get('provider')})", "",
             f"Registered {schedule.get('registered_at_utc')}; finished {report.get('finished_at_utc') or 'not finished'}; complete: {report.get('complete')}; "
             f"stopped: {(report.get('budget') or {}).get('stopped') or 'no'}.",
             f"Systems {schedule.get('systems')}, {len(schedule.get('tasks') or [])} tasks, {schedule.get('attempts_per_cell')} attempt(s) per cell, "
             f"{len(schedule.get('cells') or [])} cells scheduled, {sum(1 for r in rows if r.get('status') == 'completed')} completed, "
             f"{sum(1 for r in rows if r.get('status') == 'not_run')} not run.",
             f"Provenance: commit `{prov.get('source_git_commit') or 'none'}`, package `{(prov.get('attest_revision') or {}).get('digest', '')[:16]}`, "
             f"harness `{(prov.get('eval_script_sha256') or '')[:16]}`, examples `{((prov.get('examples_digest') or {}).get('digest') or '')[:16]}`; "
             f"snapshot intact at end: {(report.get('provenance_check') or {}).get('snapshot_intact_at_end')}; invalid comparisons: "
             f"{(report.get('provenance_check') or {}).get('invalid_tasks') or 'none'}.",
             f"Budget: committed ${(report.get('budget') or {}).get('committed_usd')} of an approved {(report.get('budget') or {}).get('approve_usd')} (per-run cap ${(report.get('budget') or {}).get('per_run_cap_usd')}).", ""]
    lines += ["## Every scheduled cell", "", "| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in sorted(rows, key=lambda x: x["scheduled_index"]):
        judge = {True: "correct", False: "not correct", None: "not judged"}.get(r.get("held_out_correct"), "?")
        lines.append(f"| {r['scheduled_index']} | {r['task']} | {r['system']} | {r.get('attempt')} | {r.get('status')} | {r.get('verdict') or '-'} | {judge} | {r.get('confusion', '-')} | "
                     f"{r.get('model_calls') if r.get('model_calls') is not None else '-'} | {r.get('cost_committed_usd') if r.get('cost_committed_usd') is not None else '-'} | "
                     f"{str(r.get('wall_s')) + ' s' if r.get('wall_s') is not None else '-'} | {(r.get('revision_digest') or '-')[:8]} |")
    lines += ["", "## Summary per system", "", "| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | Infra error | Not run | Needs human | USD committed | Mean wall |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for system, s in (report.get("summary") or {}).items():
        c = s["confusion"]
        lines.append(f"| {system} | {s['scheduled']} | {s['completed']} | {c['true_accept']} | {c['false_accept']} | {c['false_reject']} | {c['true_reject']} | {c['infra_error']} | {c['not_run']} | "
                     f"{s['needs_human']} | {s['total_cost_committed_usd']} | {s['mean_wall_s']} s |")
    reasons = [(r["scheduled_index"], r["task"], r["system"], r.get("reasons") or []) for r in rows if r.get("status") == "completed" and r.get("verdict") not in ("VERIFIED", "BASELINE")]
    if reasons:
        lines += ["", "## Reasons recorded for every non-accepted cell", ""]
        for index, task, system, rs in reasons:
            lines.append(f"- cell {index} ({task}, {system}): " + ("; ".join(x[:220] for x in rs[:3]) if rs else "no reason recorded"))
    pacing = report.get("pacing") or {}
    if pacing:
        lines += ["", f"Pacing: {pacing.get('policy_source')}; rejections {pacing.get('rejections_seen')}; waits {len(pacing.get('waits') or [])}."]
    lines += ["", "Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). "
              "Infrastructure errors and not-run cells stay in the table; nothing was merged or selected."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evaluation")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    report = json.loads(Path(args.evaluation).read_text(encoding="utf-8"))
    text = render(report)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("wrote", args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
