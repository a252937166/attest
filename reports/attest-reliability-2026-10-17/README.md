# Reliability round (17 Oct 2026): the three held candidates, Codex pacing, provenance of the executed code

Scope: the three items the owner asked for before M4 and M5, in order. Everything here ran on the Codex development
gateway (team allowance), Nebius Sandboxes (no model inference) and offline fixtures. **No Nebius inference was spent.**
Nothing was published or redeployed by this round; deployment is reported separately in `reports/attest-deployment-2026-10-17/`.
Historical run directories are untouched; every rerun below is a new directory or a new file next to the original.

Files in this folder: `holds/` (the recorded breaker modules, the corrected modules, the replay records
`replay-*-local.json` and `replay-*-sandbox.json` with sandbox operation ids and logs), `evaluation-paced-codex/` (the
paced 10-cell dry run from an immutable snapshot, its `schedule.json`, `evaluation.json` and `snapshot/`),
`evaluation-paced-codex.log`.

## 1. The three holds

In the 17 Oct Codex dry run (`reports/attest-m1-2026-10-16/evaluation-dryrun-codex-3/`) Attest held three candidates that
the independent held-out judge accepted. Each hold was replayed with `scripts/replay_holds.py`: the candidate is
reconstructed from the recorded `candidate.patch` and checked against the recorded file digests, the base repository is
checked against the frozen task, and the original and the corrected breaker module run on both sides through the real
sealed-suite supervisor, locally and in Nebius Sandboxes (bound, with operation ids). The classification below separates
incorrect generated tests, excessive workloads, ambiguous requirements and genuine implementation defects, as asked.

| Hold | Failing generated test(s) | Root cause | Class | Resolution |
| --- | --- | --- | --- | --- |
| balanced-brackets (cell 5) | `test_exhaustive_short_bracket_streams`, 9,331 subtests, recorded `TIMEOUT` (killed by signal 9 after 60 s) | **Verifier defect.** The per-test child wrote one event per subtest into its result pipe (about 560 KB); supervisor v5 read that pipe only after the child had exited, so the child blocked on the full 64 KiB pipe buffer until the per-test timeout killed it. The same test runs in 0.02 s with plain unittest and in 0.07 s under supervisor v6. The arbiter's label `test_defect` ("excessive workload") was wrong too. | neither test defect nor workload: verifier defect | **Supervisor v6**: the result pipe is drained by a thread while the child runs, and the child keeps a bounded event log (complete per-outcome counts, at most a few hundred labelled events). Regression tests: `tests/test_reliability.py::SupervisorPipeDrain` (reproduces the v5 deadlock with a 600 KB pipe write and runs a 20,000-subtest test under v6). The original, unmodified test module now passes on the candidate and fails on the base, locally and in the sandbox. |
| durationkit-units-001 (cell 7) | `test_mixed_unicode_decimal_scripts`: `'١२h３４m'` expected 58440.0 | **Incorrect generated test** (wrong expected value: 12 h 34 m is 45240.0; the arbiter corrected it) on top of an **ambiguous requirement** (the statement never said whether non-ASCII decimal digits are digits). | wrong expectation + contract gap | Contract clarified in `examples/durationkit-task/task.json` (`contract_resolution` field): numbers are written with ASCII digits 0-9; acceptance or rejection of other Unicode decimal digits is unspecified and must not be tested; non-digit characters raise ValueError. Corrected module `holds/durationkit_breaker_corrected.py` replaces the test with multi-digit ASCII cases: passes on the candidate (10 of 10), 6 of 10 fail on the base. The arbiter's own corrected module (`holds/durationkit_breaker_arbiter_corrected.py`) is kept and also passes on the candidate and fails on the base. |
| roman-to-numeral (cell 1) | `test_int_subclass_with_overridden_arithmetic`, `..._comparisons`, `test_out_of_range_subclass_with_misleading_comparisons` | **Ambiguous requirement.** The tests drove `to_roman` through int subclasses whose `__floordiv__`, `__mod__`, `__ge__` and `__le__` sabotage the implementation; the statement was silent on such subclasses, its bool clause was garbled, and the specification stage wrote "an ordinary int subclass follows the same rules", which the arbiter read as covering hostile subclasses (`implementation_bug`). The candidate is correct for every int and for every subclass that does not override operators. | contract gap; the arbiter's `implementation_bug` label was wrong | Contract clarified in `examples/eval/roman-to-numeral/task.json`: conversion is by integer value; subclasses that override arithmetic or comparison operators are out of scope and must not be tested; whether bool is rejected is unspecified. Corrected module `holds/roman_breaker_corrected.py` replaces the three tests with value-based subclass tests (`PlainInt(49)`, out-of-range `PlainInt` values, large magnitudes): passes on the candidate (9 of 9), 7 of 9 fail on the base. |

What was **not** changed: the gates. A failing adversarial test still holds the verdict; arbitration stays advisory; the
recorded dry-run bundles and their verdicts stand as recorded. No assertion was weakened to obtain VERIFIED: in two cases
the contract was made explicit where it had been silent and the tests were rewritten to follow from the explicit
contract; in the third the test was right and the verifier was wrong.

Replay evidence (`holds/replay-*-sandbox.json`, supervisor v6 in Nebius Sandboxes, one checkpoint and one disposable
networking-off branch per module and side; local results identical):

| Run | Module | Base | Candidate | Sandbox operation (candidate) |
| --- | --- | --- | --- | --- |
| balanced-brackets | original (9,331-subtest test included) | FAILED 8 of 9 (ERROR) | OK 9 of 9 in 7.2 s | `01a1493d-…` (see file) |
| balanced-brackets | arbiter's reduced module | FAILED 8 of 9 | OK 9 of 9 | |
| roman-to-numeral | original | FAILED 7 of 9 | FAILED 3 of 9 (the hostile-subclass tests) | |
| roman-to-numeral | corrected | FAILED 7 of 9 | OK 9 of 9 | `01a1493e-5ceb-…` |
| durationkit | original | FAILED 6 of 10 | FAILED 1 of 10 (`45240.0 != 58440.0`) | |
| durationkit | arbiter-corrected and contract-corrected | FAILED 6 of 10 | OK 10 of 10 | |

Changes that make the next hold cheaper to resolve:

- The breaker prompt now states the per-test time budget and asks for bounded work, forbids tests of behaviour the
  contract marks unspecified, and forbids operator-overriding subclasses or wrapper objects as inputs (test by value).
- The arbiter prompt distinguishes a wrong expectation, unspecified behaviour, excessive workload and a Python
  incompatibility (`defect_kind`, optional in the schema), sees the failure traceback and the timeout duration, and is
  told that a TIMEOUT is not a failed assertion. A corrected adversarial module is now also re-run on the base (it must
  still fail there), as the sealed module already was.
- The exhibits gained the reason class `adversarial_timeout` (an unarbitrated timeout is "not a demonstrated defect"), the
  E3 summary counts timeouts, and the decision copy for arbitrated defects names the defect kinds. Per-test durations are
  recorded in every summary.

Live confirmation: in the paced dry run of section 4, run from a snapshot that includes these changes, the Attest cells of
roman-to-numeral, balanced-brackets and durationkit all ended **VERIFIED** and judged correct; rle-encode ended
`INFEASIBLE` as before (its contract is unsatisfiable; METHOD.md scores a hold as the right outcome).

## 2. Codex rate-limit handling

Observed before this round (ledgers of every recorded run): on 16 Oct and on 17 Oct the gateway accepted exactly 60
requests for this key inside an hour and answered `HTTP 429 hourly limit reached for this key` to the next ones,
regardless of tokens (628k and 718k tokens; 1.17M tokens within one hour had passed on 15 Oct). Both dry runs lost their
last cells to it.

Implemented (`attest/models/pacing.py`, `attest/models/codex_gateway.py`, `scripts/run_evaluation.py`,
`attest/http.py`, `attest/ledger.py`; tests `tests/test_reliability.py::Governor`, `::GovernorPolicy`, `::CodexClientPacing`):

- **One governor per key per process.** Every request of every role and every worker thread takes a slot; a state file
  shared between processes on the same machine (`~/.cache/attest/codex-pacing-<key id>.json`, advisory lock) counts
  attempts across processes, so a harness batch, a console run and a CLI run on the same machine draw from one window.
- **Declared policy first.** Before the first request the client reads `GET /v1/status`; if the gateway declares
  `limits.hourly_requests_enforced: false` there is no hourly window (concurrency and 429 handling remain); a declared
  hourly count sets the budget at 90% of it; an unreadable status keeps the conservative default of 60 per rolling hour
  (54 planned). The source of the policy is recorded in every bundle's provenance.
- **Concurrency.** At most two requests in flight per key (the gateway executes one at a time and queues the rest).
- **Bounded, visible waiting.** When the window is full the caller waits until the oldest attempt ages out, in 30 s
  steps, announcing the wait through the pipeline log, the console's event stream or the harness output; past the bound
  (default 3,900 s) the call fails with `ModelError(rate_limited=True)` and the run ends `ERROR`, reported as an
  infrastructure error. The harness also waits for a cell's estimated headroom before starting it.
- **429 is a definite rejection, never uncertain.** The rejected attempt is recorded in the ledger as a failed call
  (`rate_limited_calls` in the totals), the key is blocked for `Retry-After` or until the window reopens, and the same
  request is retried after the bounded wait (at most two retries). Transport-uncertain failures are still never retried.
- **Resumption.** `run_evaluation.py --resume DIR` continues a batch from its own snapshot, running only the cells that
  never executed, after verifying the snapshot digests; completed rows are kept verbatim.
- **No fallback.** Neither module imports or names the paid provider (asserted by a test); exhaustion is reported.

On 17 Oct at 09:37 UTC the gateway operator removed the hourly counter (`reports/codex-gateway-hourly-limit-removal-2026-10-17/`);
`GET /v1/status` now declares `hourly_requests_enforced: false`, and the governor adopts that. The paced dry run of section 4
started at 12:11 UTC from a snapshot that still assumed 60 per hour, so it shows the mechanism under the stricter model.

## 3. Version provenance

- **Immutable snapshot, fresh process.** `scripts/run_evaluation.py` copies `attest/`, itself and `examples/` into
  `<report>/snapshot/`, records `SNAPSHOT.json` (package digest, harness digest, examples digest, working-tree digest at
  launch) and re-executes itself from the copy with `PYTHONPATH` cleared; the snapshot process refuses to run if the
  imported package is not the snapshot's. `schedule.json` records the revision, the harness digest, the examples digest,
  the guest-program digests (supervisor, child, canary, sandbox runner), Python and platform.
- **Detection.** Every row records the revision its bundle carries; at the end (and after every cell) the report
  recomputes the snapshot digests and the working tree's digest. A task whose cells did not all run the registered
  revision, or whose snapshot changed, is listed under `provenance_check.invalid_tasks`; the summary counts its cells.
  Edits to the working tree during a batch are reported (`working_tree_changed_since_launch`) and cannot affect the batch.
- **Bundles.** `provenance` now also records `runtime` (Python, platform, the package directory the process executed),
  `pacing` (the governor's policy) and `retry_policy`; PROOF.md section 1 prints them.
- **Retroactive note.** The dry run of 17 Oct 06:11 UTC (`evaluation-dryrun-codex-3`) ran five different package
  revisions across its cells because the sources were edited while the harness process kept its imported code. Under
  today's rule those comparisons are invalid; they were never quoted as results and are not quoted now
  (`reports/attest-m2-2026-10-17/README.md` section 5 records the digests).
- **Terminology.** `attest check`, the console, the docs and the two milestone reports no longer say "signed" or
  "unsigned": a SHA-256 manifest is an integrity and internal-consistency check, not a digital signature and not
  independent proof of execution. The checker reports `manifest verified`, `manifest MISMATCH` or `no manifest:
  integrity not checkable`; the console API field is `recorded`.

## 4. Live validation on the Codex gateway: paced 10-cell dry run from a snapshot

Started 12:11 UTC 17 Oct 2026: `python3 scripts/run_evaluation.py --provider codex --workers 2 --label pacing-dryrun --out
reports/attest-reliability-2026-10-17/evaluation-paced-codex` (log `evaluation-paced-codex.log`). The launcher wrote the
snapshot (package revision `b7fdd9eb0b71`, 34 sources; harness `676b02f66575`; examples `b83c8a78c531`, 61 files) and
re-executed the harness from it. Finished 13:24 UTC; `complete: true`, `stopped: null`, committed USD 0.0, 61 Codex calls.
This is a method and mechanism validation on the development profile, not an evaluation result.

| Cell | Task | System | Verdict | Judge | Label | Calls | Wall | Pacing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | baseline | BASELINE | correct | true_accept | 5 | 217.3 s | none |
| 1 | roman-to-numeral | attest | VERIFIED | correct | true_accept | 9 | 388.5 s | none |
| 2 | rle-encode | baseline | BASELINE | correct | true_accept | 4 | 147.3 s | none |
| 3 | rle-encode | attest | INFEASIBLE | not correct | true_reject | 1 | 49.7 s | none |
| 4 | balanced-brackets | baseline | BASELINE | correct | true_accept | 4 | 179.2 s | none |
| 5 | balanced-brackets | attest | VERIFIED | correct | true_accept | 9 | 440.8 s | none |
| 6 | durationkit-units-001 | baseline | BASELINE | correct | true_accept | 5 | 144.6 s | none |
| 7 | durationkit-units-001 | attest | VERIFIED | correct | true_accept | 9 | 548.5 s | none |
| 8 | semver-is-compatible-pr368-v2 | baseline | BASELINE | correct | true_accept | 5 | 205.5 s | none |
| 9 | semver-is-compatible-pr368-v2 | attest | VERIFIED | correct | true_accept | 10 | 558.8 s | waited 2707.7 s before start, 13.3 s in calls |

- **Provenance.** Every cell's bundle records revision `b7fdd9eb0b71…`, the registered one; `snapshot_intact_at_end: true`;
  `working_tree_changed_since_launch: true` (the sources were edited throughout the batch, which is exactly the situation
  that invalidated the 06:11 dry run) and `invalid_tasks: []`, because the batch never saw those edits. `attest check` passes
  on all 10 bundles with the manifest verified.
- **Pacing.** No HTTP 429. One wait: the harness held the last Attest cell for 2,708 s before starting it because the shared
  window (which also counted the external-task run of M4 and the pilot dry run on the same machine) had no headroom for the
  15 requests the cell might need; inside that cell the governor waited another 13 s once. The snapshot still modelled the
  limit as 60 per hour; the gateway had stopped enforcing it at 09:37 UTC, so this wait was unnecessary in hindsight but shows
  the mechanism (bounded, announced, cross-process) working. With the adopted policy the current code would not have waited.
- **Holds.** The three tasks held on 17 Oct 06:11 (roman-to-numeral, balanced-brackets, durationkit) are VERIFIED here with
  judge-correct candidates; rle-encode is INFEASIBLE at the specification stage as before; python-semver is VERIFIED.
  Five of five baseline cells judged correct. These ten rows are the development profile and say nothing about Nemotron.

## 5. Offline tests

`python3 -m unittest discover -s tests -t .`: 129 tests pass (94 before this round; `tests/test_reliability.py` 25 new:
supervisor pipe drain and 20,000-subtest run, breaker and arbiter prompts, adversarial base re-run, timeout reason class,
governor window, bounded wait, rejection blocking, shared state file, concurrency permits, declared policy, Codex client 429
retry and visible failure, transport still uncertain, harness snapshot, comparison validity, launcher refusals;
`tests/test_external.py` 10 new, see the M4 report).

## 6. Weaknesses that remain

- The pacing model is inferred from two observations and the gateway's declared status; a change of policy on the gateway
  side is picked up only through `GET /v1/status` (refreshed every 15 minutes) or through the 429 handling.
- The state file coordinates processes on one machine; the console on yungou and a developer machine do not share a window
  (the console's development-profile runs are rare and started by hand).
- Provenance records a package digest, not a commit, until the public repository is published and development moves into
  it; the review repository created today in `dist/public` is the first step.
- The gateway returned one truncated JSON body and one TLS EOF during the external-task run of M4 (both treated as uncertain,
  never retried); the cause is on the gateway side and is reported to its operator, not worked around here.

## 7. Budget proposal for the paid Nebius run (not started; needs the owner's explicit approval)

| | Proposal |
| --- | --- |
| Purpose | M5.1 frozen comparison (`METHOD.md`, `examples/eval/SUITE-M5.json`): plain agent vs Attest; one public demo run for the video; nothing else |
| Models | Attest: Nemotron 3 Ultra (spec, audit, arbitration), Nemotron 3 Super (seal, implement, break), Nemotron 3.5 Lightning (summary); baseline: Super for implement |
| Tasks and attempts | 8 tasks x 2 systems x 2 attempts = 32 cells, pre-registered, every cell reported |
| Expected calls and tokens | about 320 model calls (baseline 4 to 6 per cell, Attest 9 to 15 per cell on the dry runs); about 4 M tokens in total, mostly input (the dry runs averaged 12k tokens per call) |
| Expected cost | about $2.50 to $3.50 for the 32 cells (recorded Nemotron runs: $0.025 to $0.072 per Attest run, less for baselines; the two python-semver tasks are the largest) |
| Hard cap | `--approve-usd 9.00` for the batch (reservation of the $0.50 per-run cap before each run, at most 20 calls per run), plus a demo allocation of 3 console runs under the existing $0.50 per-run and $2.00 daily caps (about $0.30 expected) |
| Concurrency | 2 cells at a time |
| Stop conditions | batch cap reached; 3 consecutive infrastructure errors; any transport-uncertain operation (never replayed); Codex is not involved and nothing falls back to it or from it |
| Balance basis | $1.62 committed locally to date across 46 unique Nemotron runs (`scripts/usage_report.py`), about $1.80 with the three server-only runs, against the $26 credit seen on 15 Oct; please confirm the console figure before approving |
