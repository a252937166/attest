# Evaluation results: revision4-codex-semver (codex)

Registered 2026-10-19T04:44:26.573711+00:00; finished 2026-10-19T05:00:39.345757+00:00; complete: True; stopped: no.
Systems ['attest'], 1 tasks, 1 attempt(s) per cell, 1 cells scheduled, 1 completed, 0 not run.
Provenance: commit `none`, package `87aa03b95d6e6e33`, harness `0b7056a05512f569`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | semver-is-compatible-pr368-v2 | attest | 1 | completed | VERIFIED | correct | true_accept | 12 | 0.0 | 967.6 s | 87aa03b9 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 967.6 s |

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
