# Evaluation results: audit-repairs-2 (codex)

Registered 2026-10-19T08:21:12.437658+00:00; finished 2026-10-19T08:33:15.562911+00:00; complete: True; stopped: no.
Systems ['attest'], 2 tasks, 1 attempt(s) per cell, 2 cells scheduled, 2 completed, 0 not run.
Provenance: commit `none`, package `1e12d46217fb6b8a`, harness `6e77617bcc8a66cc`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | balanced-brackets | attest | 1 | completed | VERIFIED | correct | true_accept | 9 | 0.0 | 714.1 s | 1e12d462 |
| 1 | kvparse-refactor-001 | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 2 | 0.0 | 295.0 s | 1e12d462 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | False refusal (INFEASIBLE on a satisfiable task) | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 2 | 2 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 | 504.6 s |
Starting committed total of this process: $0 = $0 from 0 completed row(s) + $0 from 0 run director(ies) no row owns (rebuilt from disk at 2026-10-19T08:21:12.439035+00:00).


## Reasons recorded for every non-accepted cell

- cell 1 (kvparse-refactor-001, attest): contract contradiction demonstrated by an executed witness (requirements AC1, AC2, AC16): The universal string-input preservation requirement includes str subclasses. A subclass containing 'a=b' but overriding __len__ to

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance); `false_refusal` marks an INFEASIBLE verdict on a task whose held-out suite is satisfiable (a wrong refusal). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
