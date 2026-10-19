# Evaluation results: audit-repairs (codex)

Registered 2026-10-19T07:58:15.573546+00:00; finished 2026-10-19T08:26:42.134403+00:00; complete: True; stopped: no.
Systems ['attest'], 5 tasks, 1 attempt(s) per cell, 5 cells scheduled, 5 completed, 0 not run.
Provenance: commit `none`, package `722cd6dd1a217c6d`, harness `6e77617bcc8a66cc`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | rle-encode | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 2 | 0.0 | 250.4 s | 722cd6dd |
| 1 | balanced-brackets | attest | 1 | completed | ERROR | not correct | infra_error | 3 | 0.0 | 252.6 s | 722cd6dd |
| 2 | durationkit-units-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 11 | 0.0 | 926.7 s | 722cd6dd |
| 3 | kvparse-refactor-001 | attest | 1 | completed | ERROR | not correct | infra_error | 3 | 0.0 | 280.3 s | 722cd6dd |
| 4 | semver-long-prerelease-pr488 | attest | 1 | completed | VERIFIED | correct | true_accept | 12 | 0.0 | 1148.1 s | 722cd6dd |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | False refusal (INFEASIBLE on a satisfiable task) | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 5 | 5 | 2 | 0 | 0 | 1 | 0 | 0 | 2 | 0 | 1 | 0.0 | 571.6 s |
Starting committed total of this process: $0 = $0 from 0 completed row(s) + $0 from 0 run director(ies) no row owns (rebuilt from disk at 2026-10-19T07:58:15.594597+00:00).


## Reasons recorded for every non-accepted cell

- cell 0 (rle-encode, attest): contract contradiction demonstrated by an executed witness (requirements AC10, AC11, AC13): For input 'a1', the required encoding is 'a111', which the unchanged decoder maps to 111 copies of 'a', violating universal roun
- cell 1 (balanced-brackets, attest): model provider: HTTP 502 from development-gateway/run: Selected model is at capacity. Please try a different model.
- cell 3 (kvparse-refactor-001, attest): model provider: HTTP 502 from development-gateway/run: Selected model is at capacity. Please try a different model.

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance); `false_refusal` marks an INFEASIBLE verdict on a task whose held-out suite is satisfiable (a wrong refusal). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
