# Evaluation results: m5-final (nebius)

Registered 2026-10-17T17:15:49.413714+00:00; finished 2026-10-17T18:10:41.987473+00:00; complete: True; stopped: no.
Systems ['baseline', 'attest'], 8 tasks, 2 attempt(s) per cell, 32 cells scheduled, 32 completed, 0 not run.
Provenance: commit `6b786a2e51bba634d63cc8b4ee75bb215c168fa7`, package `166cdcbd46a74cd0`, harness `3214d2b3a1fd1fbc`, examples `e95a28aa36336616`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $1.0896 of an approved 9.0 (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | baseline | 1 | completed | BASELINE | correct | true_accept | 7 | 0.006939 | 52.2 s | 166cdcbd |
| 1 | roman-to-numeral | baseline | 2 | completed | BASELINE | correct | true_accept | 8 | 0.007761 | 58.2 s | 166cdcbd |
| 2 | roman-to-numeral | attest | 1 | completed | ERROR | not judged | infra_error | 2 | 0.008862 | 29.2 s | 166cdcbd |
| 3 | roman-to-numeral | attest | 2 | completed | VERIFIED | correct | true_accept | 12 | 0.033121 | 236.1 s | 166cdcbd |
| 4 | rle-encode | baseline | 1 | completed | BASELINE | not correct | false_accept | 6 | 0.005022 | 34.1 s | 166cdcbd |
| 5 | rle-encode | baseline | 2 | completed | BASELINE | not correct | false_accept | 7 | 0.00517 | 34.3 s | 166cdcbd |
| 6 | rle-encode | attest | 1 | completed | VERIFIED | not correct | false_accept | 12 | 0.02682 | 198.6 s | 166cdcbd |
| 7 | rle-encode | attest | 2 | completed | VERIFIED | not correct | false_accept | 13 | 0.02724 | 168.6 s | 166cdcbd |
| 8 | balanced-brackets | baseline | 1 | completed | BASELINE | correct | true_accept | 8 | 0.009318 | 61.6 s | 166cdcbd |
| 9 | balanced-brackets | baseline | 2 | completed | BASELINE | correct | true_accept | 7 | 0.005409 | 40.1 s | 166cdcbd |
| 10 | balanced-brackets | attest | 1 | completed | VERIFIED | correct | true_accept | 11 | 0.020901 | 107.6 s | 166cdcbd |
| 11 | balanced-brackets | attest | 2 | completed | ERROR | not judged | infra_error | 10 | 0.032 | 230.2 s | 166cdcbd |
| 12 | durationkit-units-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 9 | 0.015828 | 93.1 s | 166cdcbd |
| 13 | durationkit-units-001 | baseline | 2 | completed | ERROR | not correct | infra_error | 10 | 0.031148 | 177.0 s | 166cdcbd |
| 14 | durationkit-units-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 12 | 0.042683 | 199.6 s | 166cdcbd |
| 15 | durationkit-units-001 | attest | 2 | completed | NEEDS HUMAN | correct | false_reject | 15 | 0.083016 | 321.7 s | 166cdcbd |
| 16 | semver-is-compatible-pr368-v2 | baseline | 1 | completed | BASELINE | correct | true_accept | 4 | 0.008062 | 76.9 s | 166cdcbd |
| 17 | semver-is-compatible-pr368-v2 | baseline | 2 | completed | BASELINE | correct | true_accept | 10 | 0.020159 | 89.5 s | 166cdcbd |
| 18 | semver-is-compatible-pr368-v2 | attest | 1 | completed | NEEDS HUMAN | correct | false_reject | 9 | 0.070617 | 201.2 s | 166cdcbd |
| 19 | semver-is-compatible-pr368-v2 | attest | 2 | completed | NEEDS HUMAN | correct | false_reject | 19 | 0.13646 | 556.8 s | 166cdcbd |
| 20 | slugkit-regression-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 7 | 0.007982 | 72.7 s | 166cdcbd |
| 21 | slugkit-regression-001 | baseline | 2 | completed | BASELINE | correct | true_accept | 5 | 0.005221 | 46.6 s | 166cdcbd |
| 22 | slugkit-regression-001 | attest | 1 | completed | ERROR | not judged | infra_error | 9 | 0.025667 | 142.7 s | 166cdcbd |
| 23 | slugkit-regression-001 | attest | 2 | completed | VERIFIED | correct | true_accept | 13 | 0.031105 | 116.3 s | 166cdcbd |
| 24 | kvparse-refactor-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 4 | 0.003929 | 25.2 s | 166cdcbd |
| 25 | kvparse-refactor-001 | baseline | 2 | completed | ERROR | not correct | infra_error | 3 | 0.01735 | 93.5 s | 166cdcbd |
| 26 | kvparse-refactor-001 | attest | 1 | completed | NEEDS HUMAN | correct | false_reject | 12 | 0.037703 | 159.0 s | 166cdcbd |
| 27 | kvparse-refactor-001 | attest | 2 | completed | NEEDS HUMAN | correct | false_reject | 8 | 0.071187 | 84.8 s | 166cdcbd |
| 28 | semver-long-prerelease-pr488 | baseline | 1 | completed | BASELINE | not correct | true_reject | 12 | 0.060715 | 432.8 s | 166cdcbd |
| 29 | semver-long-prerelease-pr488 | baseline | 2 | completed | ERROR | not correct | infra_error | 1 | 0.015859 | 98.7 s | 166cdcbd |
| 30 | semver-long-prerelease-pr488 | attest | 1 | completed | NO CHANGE | not correct | true_reject | 14 | 0.10234 | 272.7 s | 166cdcbd |
| 31 | semver-long-prerelease-pr488 | attest | 2 | completed | NO CHANGE | not correct | true_reject | 14 | 0.114001 | 179.8 s | 166cdcbd |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 16 | 16 | 10 | 2 | 0 | 1 | 3 | 0 | 0 | 0.2259 | 92.9 s |
| attest | 16 | 16 | 4 | 2 | 5 | 2 | 3 | 0 | 7 | 0.8637 | 200.3 s |

## Reasons recorded for every non-accepted cell

- cell 2 (roman-to-numeral, attest): SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay
- cell 11 (balanced-brackets, attest): SandboxError: spawn outcome uncertain (TimeoutError: The read operation timed out); inspect account operations, do not replay
- cell 13 (durationkit-units-001, baseline): model provider: inference outcome uncertain (SSLError: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac (_ssl.c:2559)); not retried
- cell 15 (durationkit-units-001, attest): adversarial suite binding failed: child process nonzero exit: test_mixed_whitespace_between_components exit 1; model-written adversarial tests failed: 1 of 13 (test_breaker.TestBreakerParseDuration.test_mixed_whitespace_between_components); each failure is a bug or a contract disagreement to resolve
- cell 18 (semver-is-compatible-pr368-v2, attest): adversarial suite binding failed: child process nonzero exit: test_major_positive_minor_equal_patch_any exit 1; model-written adversarial tests failed: 1 of 7 (test_breaker.TestIsCompatibleBreaker.test_major_positive_minor_equal_patch_any); each failure is a bug or a contract disagreement to resolve
- cell 19 (semver-is-compatible-pr368-v2, attest): adversarial suite binding failed: child process nonzero exit: test_subclass_both_directions exit 1; model-written adversarial tests failed: 1 of 8 (test_breaker.TestIsCompatibleBreaker.test_subclass_both_directions); each failure is a bug or a contract disagreement to resolve
- cell 22 (slugkit-regression-001, attest): SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay
- cell 25 (kvparse-refactor-001, baseline): model provider: inference outcome uncertain (SSLError: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac (_ssl.c:2559)); not retried
- cell 26 (kvparse-refactor-001, attest): model-written adversarial tests could not be produced: the module has a syntax error: expected '(' (test_breaker.py, line 19); rerun the breaker stage or review manually
- cell 27 (kvparse-refactor-001, attest): child process nonzero exit: test_parse_line_quote_only exit 1; drift audit unavailable: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried
- cell 29 (semver-long-prerelease-pr488, baseline): model provider: inference outcome uncertain (SSLError: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac (_ssl.c:2559)); not retried
- cell 30 (semver-long-prerelease-pr488, attest): turn budget exhausted without changes
- cell 31 (semver-long-prerelease-pr488, attest): turn budget exhausted without changes

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
