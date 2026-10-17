# Evaluation results: revalidation-codex (codex)

Registered 2026-10-17T15:47:50.156328+00:00; finished 2026-10-17T15:57:13.085834+00:00; complete: True; stopped: a transport-uncertain operation occurred; the batch stopped without replaying anything.
Systems ['baseline', 'attest'], 2 tasks, 1 attempt(s) per cell, 4 cells scheduled, 4 completed, 0 not run.
Provenance: commit `5242c1fcb967cf1f6bb0cad0b88d8506ec7301b7`, package `bd896d025d3ab872`, harness `8bbe13805a324b06`, examples `e95a28aa36336616`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | kvparse-refactor-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 5 | 0.0 | 258.4 s | bd896d02 |
| 1 | kvparse-refactor-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 555.0 s | bd896d02 |
| 2 | semver-long-prerelease-pr488 | baseline | 1 | completed | BASELINE | correct | true_accept | 5 | 0.0 | 153.2 s | bd896d02 |
| 3 | semver-long-prerelease-pr488 | attest | 1 | completed | ERROR | not correct | infra_error | 1 | 0.0 | 29.1 s | bd896d02 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 205.8 s |
| attest | 2 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0.0 | 292.1 s |

## Reasons recorded for every non-accepted cell

- cell 3 (semver-long-prerelease-pr488, attest): model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not retried)

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
