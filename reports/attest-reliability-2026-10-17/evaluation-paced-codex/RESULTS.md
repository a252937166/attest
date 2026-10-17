# Evaluation results: pacing-dryrun (codex)

Registered 2026-10-17T12:11:44.973658+00:00; finished 2026-10-17T13:24:34.894958+00:00; complete: True; stopped: no.
Systems ['baseline', 'attest'], 5 tasks, 1 attempt(s) per cell, 10 cells scheduled, 10 completed, 0 not run.
Provenance: commit `none`, package `b7fdd9eb0b71d237`, harness `676b02f665754f7e`, examples `b83c8a78c5315725`; snapshot intact at end: True; invalid comparisons: none.
Budget: committed $0.0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | baseline | 1 | completed | BASELINE | correct | true_accept | 5 | 0.0 | 217.3 s | b7fdd9eb |
| 1 | roman-to-numeral | attest | 1 | completed | VERIFIED | correct | true_accept | 9 | 0.0 | 388.5 s | b7fdd9eb |
| 2 | rle-encode | baseline | 1 | completed | BASELINE | correct | true_accept | 4 | 0.0 | 147.3 s | b7fdd9eb |
| 3 | rle-encode | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 1 | 0.0 | 49.7 s | b7fdd9eb |
| 4 | balanced-brackets | baseline | 1 | completed | BASELINE | correct | true_accept | 4 | 0.0 | 179.2 s | b7fdd9eb |
| 5 | balanced-brackets | attest | 1 | completed | VERIFIED | correct | true_accept | 9 | 0.0 | 440.8 s | b7fdd9eb |
| 6 | durationkit-units-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 5 | 0.0 | 144.6 s | b7fdd9eb |
| 7 | durationkit-units-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 9 | 0.0 | 548.5 s | b7fdd9eb |
| 8 | semver-is-compatible-pr368-v2 | baseline | 1 | completed | BASELINE | correct | true_accept | 5 | 0.0 | 205.5 s | b7fdd9eb |
| 9 | semver-is-compatible-pr368-v2 | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 558.8 s | b7fdd9eb |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 178.8 s |
| attest | 5 | 5 | 4 | 0 | 0 | 1 | 0 | 0 | 1 | 0.0 | 397.3 s |

## Reasons recorded for every non-accepted cell

- cell 3 (rle-encode, attest): The required encoding format contradicts universal round-tripping with the unchanged decode. For x='a1', maximal-run encoding must produce 'a111' ('a1' followed by '11'), but decode('a111') returns 'a' repeated 111 times

Pacing: None; rejections 0; waits 1.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
