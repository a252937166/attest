# Evaluation results: newtasks-codex (codex)

Registered 2026-10-17T15:17:05.976881+00:00; finished 2026-10-17T15:42:49.857159+00:00; complete: True; stopped: no.
Systems ['baseline', 'attest'], 3 tasks, 1 attempt(s) per cell, 6 cells scheduled, 6 completed, 0 not run.
Provenance: commit `06553c83911582186f298d42ecc8b9b283dcca1e`, package `36369c7b57230897`, harness `8bbe13805a324b06`, examples `d0d903a99e953345`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | slugkit-regression-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 5 | 0.0 | 203.9 s | 36369c7b |
| 1 | slugkit-regression-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 8 | 0.0 | 337.9 s | 36369c7b |
| 2 | kvparse-refactor-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 7 | 0.0 | 382.4 s | 36369c7b |
| 3 | kvparse-refactor-001 | attest | 1 | completed | NEEDS HUMAN | correct | false_reject | 11 | 0.0 | 756.9 s | 36369c7b |
| 4 | semver-long-prerelease-pr488 | baseline | 1 | completed | BASELINE | correct | true_accept | 9 | 0.0 | 272.3 s | 36369c7b |
| 5 | semver-long-prerelease-pr488 | attest | 1 | completed | NEEDS HUMAN | correct | false_reject | 16 | 0.0 | 658.1 s | 36369c7b |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 286.2 s |
| attest | 3 | 3 | 1 | 0 | 2 | 0 | 0 | 0 | 2 | 0.0 | 584.3 s |

## Reasons recorded for every non-accepted cell

- cell 3 (kvparse-refactor-001, attest): adversarial suite binding failed: child process nonzero exit: test_integer_keyed_mapping_preserves_indexed_input exit 1, test_mapping_insertion_order_does_not_change_indexed_input exit 1, test_mapping_missing_zero_preser; model-written adversarial tests failed: 4 of 8 (test_breaker.BreakerTests.test_integer_keyed_mapping_preserves_indexed_input, test_breaker.BreakerTests.test_mapping_insertion_order_does_not_change_indexed_input, test_bre
- cell 5 (semver-long-prerelease-pr488, attest): child process nonzero exit: test_core_precedence_skips_bad_prerelease_conversion exit 1

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
