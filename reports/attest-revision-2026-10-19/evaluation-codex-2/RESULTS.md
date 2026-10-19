# Evaluation results: revision4-codex-2 (codex)

Registered 2026-10-19T04:17:12.699390+00:00; finished 2026-10-19T05:09:32.064863+00:00; complete: True; stopped: no.
Systems ['attest'], 8 tasks, 1 attempt(s) per cell, 8 cells scheduled, 8 completed, 0 not run.
Provenance: commit `none`, package `87aa03b95d6e6e33`, harness `0b7056a05512f569`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 844.1 s | 87aa03b9 |
| 1 | rle-encode | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 2 | 0.0 | 174.1 s | 87aa03b9 |
| 2 | balanced-brackets | attest | 1 | completed | VERIFIED | correct | true_accept | 9 | 0.0 | 682.1 s | 87aa03b9 |
| 3 | durationkit-units-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 13 | 0.0 | 699.9 s | 87aa03b9 |
| 4 | semver-is-compatible-pr368-v2 | attest | 1 | completed | ERROR | not correct | infra_error | 6 | 0.0 | 537.5 s | 87aa03b9 |
| 5 | slugkit-regression-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 11 | 0.0 | 808.3 s | 87aa03b9 |
| 6 | kvparse-refactor-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 824.1 s | 87aa03b9 |
| 7 | semver-long-prerelease-pr488 | attest | 1 | completed | VERIFIED | correct | true_accept | 14 | 0.0 | 686.5 s | 87aa03b9 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 8 | 8 | 6 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0.0 | 657.1 s |

## Reasons recorded for every non-accepted cell

- cell 1 (rle-encode, attest): contract contradiction demonstrated by an executed witness (requirements AC10, AC12): For input 'a1', the mandated format produces 'a111', which the unchanged decoder interprets as 111 copies of 'a', violating the requir
- cell 4 (semver-is-compatible-pr368-v2, attest): model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not retried)

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
