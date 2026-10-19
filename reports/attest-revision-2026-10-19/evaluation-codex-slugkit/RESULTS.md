# Evaluation results: revision4-codex-slugkit (codex)

Registered 2026-10-19T05:40:52.319820+00:00; finished 2026-10-19T05:50:57.814886+00:00; complete: True; stopped: no.
Systems ['attest'], 1 tasks, 1 attempt(s) per cell, 1 cells scheduled, 1 completed, 0 not run.
Provenance: commit `none`, package `b27a1c070a852ae2`, harness `0b7056a05512f569`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | slugkit-regression-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 598.4 s | b27a1c07 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 598.4 s |

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
