# Frozen evaluation version (M5), 17 Oct 2026

This file pins what the M5 comparison runs. The paid run has not started; it starts only after the owner approves the
budget below, and it runs from a clean checkout of the pinned commit, never from a working tree.

| Item | Value |
| --- | --- |
| Repository commit (code) | `06553c83911582186f298d42ecc8b9b283dcca1e` on branch `main` of the review repository |
| `attest/` package digest (sha256 over path and content of every source) | `36369c7b572308977852cf61ce218f356f19d954f47319397dfa0d700b44301a` |
| Harness `scripts/run_evaluation.py` sha256 | `8bbe13805a324b06800f562b42a9d5c61cda79df329a507c80cc40587968624f` |
| `examples/` tree digest (tasks, repositories, held-out suites) | `d0d903a99e953345579ea226567071736e404dc69a770010c39315b651f4da7c` |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` |
| Method `METHOD.md` sha256 | `89926dd10e63c7aec0254d77b89734ca7b8aafebc6330df768ef064f05e85844` |
| Guest programs | supervisor `attest-sealed-supervisor/6`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/2` `80999537285bacaf…` |
| Models (Nebius Token Factory) | spec, audit, arbitrate: `nvidia/Nemotron-3-Ultra-550b-a55b`; seal, implement, break: `nvidia/nemotron-3-super-120b-a12b`; summary: `nvidia/Nemotron-3_5-Lightning`; baseline implements with Super |
| Sampling | temperature 0.2, max_tokens 16000, strict JSON schema output |
| Limits | 14 implementer turns (12 for the imported repository task), 12 mutants, mutation threshold 0.5, drift threshold 0.6, 180 s per suite (60 s per test), per-run cap $0.50 reserved before the run, at most 20 model calls per run |
| Schedule | 8 tasks x 2 systems x 2 attempts = 32 cells, pre-registered, every cell reported, no merge |
| Batch controls | `--approve-usd 9.00`, concurrency 2, stop on cap, on 3 consecutive infrastructure errors, on any transport-uncertain operation; no Codex involvement, no fallback in either direction |

## The exact command

From a clean checkout of the pinned commit (the harness snapshots the tree into the report directory and re-executes from
the snapshot in a fresh process; the schedule records the digests above and the commit):

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout 06553c83911582186f298d42ecc8b9b283dcca1e
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 20 --max-turns 14 --approve-usd 9.00 --label m5-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-m5
```

Proof that the command does what it says: the same command with `--register-only` was run from that checkout on 17 Oct 2026
15:16 UTC (`reports/attest-freeze-2026-10-17/register-only-m5/schedule.json` in the private evidence tree): 32 cells, 8 tasks,
systems baseline and attest, 2 attempts, the digests above, `register_only: true`, nothing started. The first attempt of
that proof failed because registration loaded the external task with the default per-file bound; the fix is in the pinned
commit and `tests/test_budget.py::RegisterOnly` guards it.

## Budget (for approval; nothing paid runs before it)

| Budget line | Maximum | Expected | Calls | Stop rules |
| --- | --- | --- | --- | --- |
| Evaluation (32 cells) | $9.00 (`--approve-usd`; $0.50 reserved per run before it starts) | $2.50 to $3.50 (recorded Nemotron runs cost $0.025 to $0.072 per Attest run and less per baseline; the two python-semver tasks are the largest) | about 320 (baseline 4 to 6, Attest 9 to 15 per cell; hard cap 20 per run) | batch cap; 3 consecutive infrastructure errors; any transport-uncertain operation |
| Smoke test before the batch (1 Nemotron run of `durationkit-units-001` through the CLI from the pinned checkout) | $0.50 | about $0.06 | at most 20 | the run's own cap |
| Demo runs on the public console for the video (3 judge-style runs) | $1.50 ($0.50 each under the existing $2.00 daily cap) | about $0.30 | at most 20 each | the console's per-run and daily caps |
| **Total** | **$11.00** | **about $3.00 to $4.50** | | |

Verified so far: committed Nebius spend to date is $1.62 across 46 unique local runs (`scripts/usage_report.py`, computed from
the public price table), about $1.80 including the three server-only runs; the Token Factory console showed about $26 of
credit on 15 Oct 2026. The console balance has not been re-read programmatically (the Token Factory API documents no balance
endpoint); the owner's confirmation of the current figure is part of the approval.

## Validation of the frozen suite on the development profile (17 Oct 2026, 15:17 to 15:42 UTC)

`evaluation-newtasks-codex/`: the three tasks that had never run through the harness (`slugkit-regression-001`,
`kvparse-refactor-001`, `semver-long-prerelease-pr488`), both systems, one attempt, from the frozen clone at commit
`06553c83…` (revision `36369c7b…` in every row, snapshot intact, working tree unchanged, 62 Codex requests, no pacing wait,
policy "hourly request counting not enforced" adopted from the gateway). This is method validation, not an evaluation result.

| Cell | Task | System | Verdict | Judge | Label | Calls | Wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | slugkit-regression-001 | baseline | BASELINE | correct | true accept | 5 | 204 s |
| 1 | slugkit-regression-001 | attest | VERIFIED | correct | true accept | 8 | 338 s |
| 2 | kvparse-refactor-001 | baseline | BASELINE | correct | true accept | 7 | 382 s |
| 3 | kvparse-refactor-001 | attest | NEEDS HUMAN | correct | false reject | 11 | 757 s |
| 4 | semver-long-prerelease-pr488 | baseline | BASELINE | correct | true accept | 9 | 272 s |
| 5 | semver-long-prerelease-pr488 | attest | NEEDS HUMAN | correct | false reject | 16 | 658 s |

Both holds were examined before the suite is used for anything:

- **kvparse (cell 3): a contract defect, found by the breaker.** Four adversarial tests called `parse_line` with integer-keyed
  dicts (`{0: 'a', 1: '=', 2: 'b'}`), which the index-loop baseline happened to accept; the refactored candidate (which even
  kept a fallback for non-string sequences) raises `ValueError` for them. The arbiter classified them as implementation bugs,
  citing the statement's "byte-for-byte identical for every input", and it was right about the text: the statement required
  both identical behaviour for every input and the use of `str.partition`, which cannot preserve non-string behaviour. The
  contract is now scoped to `str` inputs and says that `parse_line` with a non-string argument is unspecified
  (`contract_resolution` in the task). The held-out suite only ever used strings, so the judge's verdict is unchanged.
- **semver (cell 5): a defective sealed test.** `test_core_precedence_skips_bad_prerelease_conversion` unpacked a six-element
  tuple into two names and raised `ValueError` before any assertion, on the base (where it counted as red) and on the
  candidate (where it held the verdict). The arbiter classified it `test_defect`, corrected it, and the corrected module passed
  on the candidate (20 of 20) and failed on the base (8 errors), yet the headline read "could not be cleared", because the
  sealed failure had skipped the mutation check and clearing requires a mutation score. Fixed: the headline and the decision
  copy now say exactly that; and the red check sends a sealed test back to the sealer when its red failure is an error raised
  inside the test body itself (unpacking errors, name errors; never an exception raised by the repository's code or an
  `AttributeError` for a missing API), so such a test does not get sealed in the first place
  (`tests/test_reliability.py::SealerSelfErrors`). The candidate itself passed the upstream pull request's tests again.

Consequence: the frozen version moves to the commit that carries these two changes (see the top of this file for the new
pin); this validation run and its holds stay recorded as they happened.
