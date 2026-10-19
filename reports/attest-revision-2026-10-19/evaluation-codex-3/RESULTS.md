# Evaluation results: revision4-codex-3 (codex)

Registered 2026-10-19T05:12:33.828323+00:00; finished 2026-10-19T05:52:59.467421+00:00; complete: True; stopped: no.
Systems ['attest'], 8 tasks, 1 attempt(s) per cell, 8 cells scheduled, 8 completed, 0 not run.
Provenance: commit `none`, package `b27a1c070a852ae2`, harness `0b7056a05512f569`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 487.8 s | b27a1c07 |
| 1 | rle-encode | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 2 | 0.0 | 103.3 s | b27a1c07 |
| 2 | balanced-brackets | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 503.4 s | b27a1c07 |
| 3 | durationkit-units-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 646.4 s | b27a1c07 |
| 4 | semver-is-compatible-pr368-v2 | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 537.2 s | b27a1c07 |
| 5 | slugkit-regression-001 | attest | 1 | completed | ERROR | not judged | infra_error | 6 | 0.0 | 310.3 s | b27a1c07 |
| 6 | kvparse-refactor-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 12 | 0.0 | 486.6 s | b27a1c07 |
| 7 | semver-long-prerelease-pr488 | attest | 1 | completed | VERIFIED | correct | true_accept | 11 | 0.0 | 723.4 s | b27a1c07 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 8 | 8 | 6 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0.0 | 474.8 s |

## Reasons recorded for every non-accepted cell

- cell 1 (rle-encode, attest): contract contradiction demonstrated by an executed witness (requirements AC9, AC10, AC11): For input 'a1', the mandated encoding is 'a111', which the unchanged decoder turns into 111 copies of 'a', violating the required
- cell 5 (slugkit-regression-001, attest): SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
