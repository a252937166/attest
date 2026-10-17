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
