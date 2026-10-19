# Frozen evaluation version (M5), 17 Oct 2026

This file pins what the M5 comparison runs. The paid run has not started; it starts only after the owner approves the
budget below, and it runs from a clean checkout of the pinned commit, never from a working tree.

| Item | Value |
| --- | --- |
| Repository commit (code) | `6b786a2e51bba634d63cc8b4ee75bb215c168fa7` on branch `main` of the review repository (the following documentation commit carries this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source) | `166cdcbd46a74cd0c666a19e111762eea64cd973c80396dfad724c1d47791b4e` |
| Harness `scripts/run_evaluation.py` sha256 | `3214d2b3a1fd1fbc7aac74db0ce8e06752fe4c373db9a872219ee10ac6cdc720` |
| `examples/` tree digest (tasks, repositories, held-out suites) | `e95a28aa363366160062107128950e9ff4c1888d52dccfdf578299e14e341b78` |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` |
| Guest programs | supervisor `attest-sealed-supervisor/6`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/2` `80999537285bacaf…` |
| Models (Nebius Token Factory) | spec, audit, arbitrate: `nvidia/Nemotron-3-Ultra-550b-a55b`; seal, implement, break: `nvidia/nemotron-3-super-120b-a12b`; summary: `nvidia/Nemotron-3_5-Lightning`; baseline implements with Super |
| Sampling | temperature 0.2, max_tokens 16000, strict JSON schema output; `reasoning_effort` low for seal and break, medium for implement, low for summary (Super and Lightning roles), model default for the Ultra roles spec, audit and arbitrate; an answer that spends the whole completion budget on reasoning (finish_reason length, no content) is retried once at low effort, both attempts recorded (set after the 17 Oct smoke tests; see the freeze report) |
| Limits | 14 implementer turns (12 for the imported repository task), 12 mutants, mutation threshold 0.5, drift threshold 0.6, 180 s per suite (60 s per test), per-run cap $0.50 reserved before the run, at most 20 model calls per run |
| Schedule | 8 tasks x 2 systems x 2 attempts = 32 cells, pre-registered, every cell reported, no merge |
| Batch controls | `--approve-usd 9.00`, concurrency 2, stop on cap, on 3 consecutive infrastructure errors, on any transport-uncertain operation; no Codex involvement, no fallback in either direction |

## The exact command

From a clean checkout of the pinned commit (the harness snapshots the tree into the report directory and re-executes from
the snapshot in a fresh process; the schedule records the digests above and the commit):

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout 6b786a2e51bba634d63cc8b4ee75bb215c168fa7
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 20 --max-turns 14 --approve-usd 9.00 --label m5-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-m5
```

Proof that the command does what it says: the same command with `--register-only` was run from a clean clone of that commit
on 17 Oct 2026 at 17:11 UTC (`reports/attest-freeze-2026-10-17/register-only-m5/schedule.json`): 32 cells, 8 tasks, systems
baseline and attest, 2 attempts, the digests above, `register_only: true`, nothing started. History of the pin, every step recorded in `reports/attest-freeze-2026-10-17/README.md`: `ce4524be…` failed its own
proof because registration loaded the external task with the default per-file bound; `06553c83…` fixed that, and its
validation on the development profile exposed a self-contradictory contract in `kvparse-refactor-001` and a sealed test that
crashed in its own body; `5242c1fc…` carried those two fixes, and its first Nemotron smoke test saw Super spend the whole
completion budget on reasoning; `85701f5d…` switched reasoning off for Super, whose implementation quality then dropped;
`2cbaf941…` bounded reasoning with `reasoning_effort` instead, and its smoke test was held by eleven sealed tests asserting
the old implementation's error wording; `15e145c1…` makes the sealer and the breaker assert exception types only; its smoke test ran the whole pipeline but its first
sealing call still hit the token cap at medium effort, so `6b786a2e…` runs the sealer and the breaker at low effort, retries a
length runaway once at low effort and honours an operator STOP file; it is the pinned version. `tests/test_budget.py::RegisterOnly` guards the registration path.

## Budget (for approval; nothing paid runs before it)

| Budget line | Maximum | Expected | Calls | Stop rules |
| --- | --- | --- | --- | --- |
| Evaluation (32 cells) | $9.00 (`--approve-usd`; $0.50 reserved per run before it starts) | $2.50 to $3.50 (recorded Nemotron runs cost $0.025 to $0.072 per Attest run and less per baseline; the two python-semver tasks are the largest) | about 320 (baseline 4 to 6, Attest 9 to 15 per cell; hard cap 20 per run) | batch cap; 3 consecutive infrastructure errors; any transport-uncertain operation |
| Smoke test before the batch (1 Nemotron run of `durationkit-units-001` through the CLI from the pinned checkout) | $0.50 | about $0.06 | at most 20 | the run's own cap |
| Demo runs on the public console for the video (3 judge-style runs) | $1.50 ($0.50 each under the existing $2.00 daily cap) | about $0.30 | at most 20 each | the console's per-run and daily caps |
| **Total** | **$11.00** | **about $3.00 to $4.50** | | |

Verified credit: the Token Factory console's billing page read **Account balance $25.00 USD** at 16:55 UTC on 17 Oct 2026
(read through the owner's signed-in browser session with the owner's consent; only the figure is recorded). Committed Nebius
spend to date from the ledgers is $1.62 across 46 unique local runs (`scripts/usage_report.py`, public price table), about
$1.80 including the three server-only runs, plus about $0.10 of smoke tests and probes on 17 Oct. The owner approved the
$11.00 budget on 17 Oct 2026.

# Revised version (revision 4, 19 Oct 2026): pinned for the next paid validation

The M5 pin above is history and stays as it is; the results it produced are in `reports/attest-evaluation-2026-10-17-nebius-m5/`
(with `CORRECTIONS.md` for the reading of three cells). The revision below changes the pipeline; it has been validated
offline (179 tests) and on the development gateway (`reports/attest-revision-2026-10-19/README.md`), not yet on Nemotron.
No paid Nebius call runs before the owner approves the proposal at the end of this section.

## What changed in the method

| Stage | M5 (pinned above) | Revision 4 |
| --- | --- | --- |
| Infeasibility | the specification model's `feasible=false` ended the run INFEASIBLE on its word | a contract auditor must back every conflict with a witness program; Attest executes it on the unmodified checkpoint; INFEASIBLE only on exit code 3 plus a `CONTRADICTION` line; an undemonstrated claim is a hold (`infeasibility_unproven`) or a sealer hint |
| Sealing | tests only | tests plus a coverage map (criterion to test methods), checked for completeness; gaps fed back, then recorded |
| Breaker authoring | 2 attempts, same model | 3 attempts; compile error names the line; the third attempt uses the arbiter's model |
| Arbitration | advisory: classification, corrected module re-run on candidate and base, verdict unchanged | correction counts only after mechanical validation (same test methods, only failing ones changed, at most 3, passes on the candidate, every corrected sealed test fails on the base; a corrected adversarial module fails on the base or is caught by a mutant); the affected gate is re-run and the verdict re-derived; a sealed test that failed by assertion or by an exception raised in the code under test is never overridden |
| Implementer | list, read (ranges), replace, write, run_tests, run_python, undo, finish | plus `search`; def/class outline of write-scope files in the prompt and in truncated reads; closest-line hint on a failed replace; navigation warning after three read-only turns |
| NO CHANGE | one reason text for finished and unfinished | unfinished recorded (`candidate.unfinished`), own reason class and copy; harness label `no_patch` |
| Ledger | written at the end | append-only journal during the run (reservation before each request); `settlement` per call; interrupted runs reconciled from the journal (console and harness) |

Limits added to every bundle's provenance: `max_corrected_tests 3`, `max_mutants_for_discrimination 3`, `max_breaker_attempts 3`,
`max_witnesses 3`, `witness_timeout_s 60`. Unchanged: supervisor `attest-sealed-supervisor/6`, per-test child, canary and
sandbox runner (same digests as the M5 pin), the gate-to-verdict rule's structure, the never-replay rule, the per-run caps.

## The pin

| Item | Value |
| --- | --- |
| Repository commit (code) | `4437b29a233603bf8a0523a6c0092493a92d2aa3` on branch `main` of the review repository (the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest | `b27a1c070a852ae2f0f2776c59cebe09cea87307a014ca80a1c37f7e66e68b49` |
| Harness `scripts/run_evaluation.py` sha256 | `0b7056a05512f569b6c41b78a531002f5b75d73d1919c2c93b0533b77f66f423` |
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` (the M5 registration recorded `e95a28aa…` because its clean clone normalised the line endings of one Windows batch file, `docs/make.bat` of the python-semver checkout, a protected file never executed; no task, repository source or held-out suite differs) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged) |
| Models and sampling (Nebius Token Factory) | unchanged from the M5 pin; the contract auditor runs on the `audit` role (Nemotron 3 Ultra, model default effort); the escalated third breaker attempt runs on the `arbitrate` role (Ultra) |
| Limits | M5 limits plus the five above |

## The exact command (unchanged in shape; a new report directory)

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout 4437b29a233603bf8a0523a6c0092493a92d2aa3
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 20 --max-turns 14 --approve-usd 9.00 --label r4-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r4
```

## Proposed paid work (awaiting the owner's approval; nothing runs before it)

| Budget line | Purpose | Models | Expected | Maximum | Calls | Stop rules |
| --- | --- | --- | --- | --- | --- | --- |
| Smoke test | one Nemotron run of `durationkit-units-001` and one of `rle-encode` through the CLI from the pinned checkout, to see the contract audit and the arbitration path on Nemotron output before a batch | Ultra (spec, contract audit, drift, arbitrate), Super (seal, implement, break), Lightning (summary) | about $0.15 | $1.00 | at most 22 per run (the audit adds one) | the run's own cap |
| Revised evaluation (32 cells, same suite, same method otherwise) | measure the revision against the M5 result: false accepts on rle-encode, false holds, the external task | as above | $3.00 to $4.00 (M5 cost $1.09 for 32 cells; the audit adds one Ultra call and up to three sandbox branches per Attest cell, the arbitration re-runs add branches on holds) | $9.00 (`--approve-usd`) | at most 22 per run | batch cap; 3 consecutive infrastructure errors; any transport-uncertain operation (never replayed) |
| Total | | | about $3.50 | **$10.00** | | |

Credit: the last verified reading of the Token Factory billing page is $25.00 at 16:55 UTC on 17 Oct 2026; committed spend
since then is about $1.49 (plus at most $0.03 unrecorded). Reading the current balance and its expiry needs the owner's
signed-in browser session (the debugging session was not available on 19 Oct without closing the owner's Chrome, which was
not done); the account is never recharged by the project.
