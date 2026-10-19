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
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` in the exported tree, where `docs/make.bat` of the python-semver checkout keeps its CRLF line endings; a clean git clone normalises that one file to LF and computes `e95a28aa363366160062107128950e9ff4c1888d52dccfdf578299e14e341b78`, the digest the M5 registration recorded (the batch snapshots of 19 Oct show the CRLF value because they were taken from the working tree). The file is protected documentation, never executed; no task, repository source or held-out suite differs |
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

This revision-4 pin was superseded the same day by revision 5 (next section) before any paid run; it is kept as history,
including the inconsistency the audit noted (its command said 20 calls per run while its proposal said 22).

# Repaired version (revision 5, 19 Oct 2026): the version proposed for the next paid validation

Revision 5 repairs the 35 findings of the independent audit of revision 4 (`reports/attest-audit-2026-10-19/README.md`;
repairs and acceptance evidence in `reports/attest-audit-repairs-2026-10-19/README.md`). The M5 pin at the top of this file is
history and stays as it is; the revision-4 pin above was never run on Nemotron. No paid Nebius call runs before the owner
approves the proposal at the end of this file.

## What changed in the method (revision 4 to revision 5)

| Stage | Revision 4 | Revision 5 |
| --- | --- | --- |
| Evidence protocol | none; `attest check` ran whatever checks the records allowed | every bundle declares `evidence_protocol.version 2`; a current bundle must carry the complete evidence for its verdict (every gate with raw results, every evaluated mutant's raw result, base and mutant evidence of corrections, the executed witness of INFEASIBLE, isolation recorded active, complete manifest) or the check fails; older bundles are historical and never `EVIDENCE COMPLETE` |
| Mutation | a mutant was killed by any non-ok outcome, including an incomplete or forged run | killed only by an authentic child failure (exit 1, FAIL/ERROR report bound to the nonce) under a structurally sound run; incomplete, non-isolated, forged, crashed or timed-out runs are unknown; policy recorded; `attest check` reclassifies every mutant |
| Correction discrimination | any non-ok outcome on the base or a mutant counted, a lost result counted as red | only authentic red results under structurally sound base and mutant re-runs count; lost or forged evidence leaves the correction unvalidated; untrusted original failures are never arbitrated; raw results kept and recomputed offline |
| Sealed oracle | a sealed ERROR whose innermost frame was in the test file, of an allowlisted exception type, could be corrected | a sealed test that failed by assertion or by any exception is never overridden; only a test the supervisor killed at its timeout may be corrected |
| Correction scope | only the failing methods' AST compared; imports ignored; classification ids unchecked | whole-module AST compared with the failing bodies placeholdered (class bases, decorators, signatures, helpers, setUp, module code must be identical); additive non-colliding imports only; exactly one classification per failing test id |
| Supervisor | v6: the direct child was killed at the timeout; pipe draining unbounded | v7: one session and process group per test child; the group is killed, cleanup bounded (5 s grace), escaped descendants swept through `/proc`, cleanup recorded; `supervisor_cleanup_complete` is a binding check |
| Manifest | v1: unlisted files a warning; the badge followed the digests | v2: complete listing, unique contained paths, correct count and total, no symbolic links; `manifest_verified` needs digests and completeness |
| Contract audit | marker line plus exit code 3 | plus: the conflict must name existing acceptance criteria (otherwise the witness is not executed) and the marker line must name a claimed one |
| Accounting | journal best effort; a 200 without usage settled as known $0; resume could drop a recovered reservation or change the provider | reservation durably journaled before dispatch (failure stops dispatch); missing usage keeps the reservation and halts paid calls; resume restores the registered configuration and recovers every interrupted or unreported run's spend once; the console preserves committed cost on import and counts a run against every UTC day it touched |
| Console | see the audit | trusted-proxy identity, atomic admission, materialised reads, public response models, complete or refused downloads with containment, bounded retention of failed runs, no admission without a worker, sanitized errors, authoritative queue positions, team runs private |
| Host and release | see the audit | literal search with a bounded `re:` mode, snapshots never follow links, streaming archive limits, bounded guest output, strict export allowlist with fail-closed scan, no overlapping export destination, real version rollback, transactional installer, release manifest |

Per-run call cap: the revision-4 proposal said 22 while its command said 20; revision 5 uses **22** everywhere (the harness
default for the Nebius provider, the schedule, the command below and the proposal), because the contract audit adds one call
and the escalated breaker attempt may add another.

## The pin (revision 5)

| Item | Value |
| --- | --- |
| Repository commit (code) | `320651d3bd4011538fe2f6d240a1e5769b019051` on branch `main` of the review repository (the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 35 files) | `1e12d46217fb6b8a27a08b4463f42f361e7309257b211103c08777c91cb10ce5` |
| Harness `scripts/run_evaluation.py` sha256 | `2aa28413a1ccfe425c400a085a18e3e3625aa11f7170b3f655de7bab53e8816c` (the two development-gateway batches below ran `6e77617bcc8a66cc…`, which differs only in the confusion labels: it had no `false_refusal` label for an INFEASIBLE verdict on a satisfiable task; execution, budget and resume logic are identical) |
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` in the working tree and the exported tree (the python-semver `docs/make.bat` keeps CRLF line endings there; a clean git clone normalises it and computes `e95a28aa363366160062107128950e9ff4c1888d52dccfdf578299e14e341b78`, the M5 value; no task, repository source or held-out suite differs) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged: the frozen M5 method; its 20-call cap is historical, the revision-5 schedule uses 22) |
| Guest programs | supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…` (unchanged); canary `9cdc57c1348fae5c…` (unchanged); sandbox runner `attest-guest/3` `db8e2a76834b83ac…` |
| Evidence protocol | version 2 (`attest.core.verdict.EVIDENCE_PROTOCOL_VERSION`); manifest version 2 |
| Models and sampling (Nebius Token Factory) | unchanged from the M5 pin (spec, audit, arbitrate: Nemotron 3 Ultra; seal, implement, break: Nemotron 3 Super; summary: Nemotron 3.5 Lightning; temperature 0.2, max_tokens 16000, `reasoning_effort` low for seal, break and summary, medium for implement, model default for the Ultra roles; one low-effort retry of a length runaway) |
| Limits | M5 limits plus revision 4's (`max_corrected_tests 3`, `max_mutants_for_discrimination 3`, `max_breaker_attempts 3`, `max_witnesses 3`, `witness_timeout_s 60`); supervisor cleanup grace 5 s; per-run call cap **22**; a successful answer without usage halts the run's paid calls; a reservation that cannot be journaled is never dispatched |
| Offline suite | 314 tests (`reports/attest-audit-repairs-2026-10-19/offline-suite.log`) |

Development-gateway reliability batches of this revision (Attest only, one attempt per task, no paid call):
`reports/attest-audit-repairs-2026-10-19/evaluation-codex/` (5 cells; package digest `722cd6dd1a217c6d…`, which differs from
the pinned digest only in the human-readable result line of `attest check`: `format_report` now reads `OK, EVIDENCE COMPLETE
for verdict ...` instead of `FULLY VERIFIED`, so that an ERROR bundle with complete evidence is not misread) and
`evaluation-codex-2/` (2 cells; the pinned digest). Outcomes: `durationkit-units-001` VERIFIED, `semver-long-prerelease-pr488`
VERIFIED (held-out 450 passed), `balanced-brackets` VERIFIED (after a gateway capacity error in the first batch),
`rle-encode` INFEASIBLE on an executed witness (the unsatisfiable task), `kvparse-refactor-001` INFEASIBLE on an executed
witness after a gateway capacity error in the first batch: a wrong refusal of a satisfiable task, the specification's own
restatement being contradictory (`evaluation-codex-2/CORRECTIONS.md`) [correction of 19 Oct 2026, revision 6, pin values
untouched: the "every str input" quantifier is the task's own sentence, and the witness disproves one implementation rather
than every allowed one; see the correction section of `evaluation-codex-2/CORRECTIONS.md` and the revision-6 section below]. All seven bundles pass `attest check` with complete
evidence under protocol 2; the mutation runs recorded no unknown mutant; no arbitration correction was needed in these runs,
so the correction path is covered by the offline acceptance tests only.

## The exact command (revision 5)

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout 320651d3bd4011538fe2f6d240a1e5769b019051
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r5-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r5
```

## Proposed paid work (awaiting the owner's approval; nothing runs before it)

| Budget line | Purpose | Models | Expected | Maximum | Calls | Stop rules |
| --- | --- | --- | --- | --- | --- | --- |
| Smoke test | one Nemotron run of `durationkit-units-001` and one of `rle-encode` through the CLI from the revision-5 pinned checkout, to see the contract audit and the arbitration path on Nemotron output before a batch | Ultra (spec, contract audit, drift, arbitrate), Super (seal, implement, break), Lightning (summary) | about $0.15 | $1.00 | at most 22 per run | the run's own cap; a missing usage record halts the run's paid calls |
| Revised evaluation (32 cells, same suite, same method otherwise) | measure revision 5 against the M5 result: false accepts on rle-encode, false holds, the external task | as above; concurrency 2 | $3.00 to $4.00 (M5 cost $1.09 for 32 cells; the audit adds one Ultra call and up to three sandbox branches per Attest cell, the arbitration re-runs add branches on holds) | $9.00 (`--approve-usd`) | at most 22 per run | batch cap; 3 consecutive infrastructure errors; any transport-uncertain operation (never replayed); a reservation that cannot be journaled stops dispatch |
| Total | | | about $3.50 | **$10.00** | | |

Credit: the last verified reading of the Token Factory billing page is $25.00 at 16:55 UTC on 17 Oct 2026; committed spend
since then is about $1.49 (plus at most $0.03 unrecorded). Reading the current balance and its expiry needs the owner's
signed-in browser session (the debugging session was not available on 19 Oct without closing the owner's Chrome, which was
not done); the account is never recharged by the project.

# Revision 6 (19 Oct 2026): the version proposed for the next paid validation

Revision 6 closes the seven findings of the independent follow-up review of revision 5
(`reports/attest-revision5-review-2026-10-19/README.md`; repairs and acceptance evidence in
`reports/attest-revision5-repairs-2026-10-19/README.md`). The M5 pin at the top of this file is history and stays as it is; the
revision-4 and revision-5 pins above were never run on Nemotron and stay as written (one bracketed correction of the
revision-5 narrative, pin values untouched). No paid Nebius call runs before the owner approves the proposal at the end of this
section.

## What changed in the method (revision 5 to revision 6)

| Stage | Revision 5 | Revision 6 |
| --- | --- | --- |
| Infeasibility | a demonstrated witness (exit code 3 and a `CONTRADICTION` line naming existing criteria) ended the run INFEASIBLE, whichever criteria it named and whatever the witness program did | the auditor sees the task's own criteria (`TC` ids) apart from the specification's derived ones (`AC` ids); INFEASIBLE needs a conflict whose requirements are all `TC` ids and whose witness is constrained (no `def`, `class`, `lambda`, dynamic type, `exec`/`eval`/`compile`/`__import__`/`globals`/`locals`/`vars`/`setattr`/`getattr`; literal inputs of the declared domain only); a demonstrated conflict that is derived, mixed or unconstrained holds the run (`NEEDS HUMAN`, `contract_conflict_held`) |
| Evidence protocol | version 2: the checker required raw results for the stage records that were present | version 3: the mandatory records are derived from the protocol, the verdict, the frozen task and the recorded execution mode (existing-suite record, raw result and binding in bound mode; held-out evidence exactly when the task declares held-out tests; a stage record behind every recorded gate; a grounded conflict with a constrained witness behind INFEASIBLE); jointly deleting a stage record with its raw result or its gate is a named completeness error |
| Diagnostics | raw exception text in bundle reasons, stage records, progress events, call records | a fixed public vocabulary with correlation references everywhere a run speaks publicly; the raw text goes to a private sidecar outside the run directory (`<runs dir>/diagnostics/<run id>.jsonl`), excluded from exports, never in a bundle, manifest, download or event |
| Ledger journal | durable reservation before dispatch; a failed settlement append was swallowed and could leave a cut line that swallowed the next reservation on restart | every append is written, flushed, fsynced and read back; a cut tail is terminated by a `journal_repair` record before anything is appended; a reservation that cannot be journaled and verified halts paid dispatch; a failed settlement marks the ledger `journal_degraded` until a later reservation reads back intact; `read_journal` is binary-safe and reports `tail_framed` |
| Call cap | the harness supplied 22; the CLI and the console built the paid provider without a cap | `python -m attest run --max-calls` (22 by default for the Nebius provider) and `ATTEST_PER_RUN_MAX_CALLS` (22 by default) on the console; the provider refuses call 23 before dispatch and records the cap and its policy in the bundle's profile |
| Comparison validity | provider name and high-level limits compared | the effective provider profile (resolved model id and effort per role, sampling, limits, thinking flags) is registered with the schedule; a resume under an environment override is refused before any cell runs; a cell whose profile differs from the registration is not run, and a row with another implementation model invalidates the comparison |
| Harness labels | `false_refusal` for INFEASIBLE on a satisfiable task | plus: a hold before any patch (`NEEDS HUMAN`, no changed path, implementer never ran) is labelled by the ground truth: `true_reject` on an unsatisfiable task, `false_refusal` otherwise; a hold with a patch keeps the held-out judge's label |
| Console credentials | the team token travelled as `?token=` on download links and was honoured everywhere | the team token is a header only; downloads of team runs use short-lived (600 s), run-scoped, read-only tickets that authorise no POST and no other route; team downloads are `Cache-Control: no-store`; the host's access log drops the query string |

## The pin (revision 6)

| Item | Value |
| --- | --- |
| Repository commit (code) | `da00f41a5542a1c114c2ba1a57a6f0ee7e7ff906` on branch `main` of the review repository (the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 36 files) | `b11ec0658845e54d8917ac7a1cdbb32dddd1d16232fa0f377b08971a711837e9` |
| Harness `scripts/run_evaluation.py` sha256 | `5af2b4989b2b93db7a9c37b4e1d654cb1e8b703bba47c8cfcf3a0e0c36bec5a3` (registers the effective provider profile; labels a hold before any patch by the ground truth) |
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` in the working tree and the exported tree (unchanged since revision 5; a clean git clone normalises the python-semver `docs/make.bat` line endings and computes `e95a28aa…`, the M5 value) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged: the frozen M5 method; its 20-call cap is historical, revisions 5 and 6 use 22) |
| Guest programs | unchanged from revision 5: supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/3` `db8e2a76834b83ac…` |
| Evidence protocol | version 3 (`attest.core.verdict.EVIDENCE_PROTOCOL_VERSION`); manifest version 2 |
| Models and sampling (Nebius Token Factory) | unchanged from the M5 pin (spec, audit, arbitrate: Nemotron 3 Ultra; seal, implement, break: Nemotron 3 Super; summary: Nemotron 3.5 Lightning; temperature 0.2, max_tokens 16000, `reasoning_effort` low for seal, break and summary, medium for implement, model default for the Ultra roles); the effective profile is now registered in every schedule and compared on resume |
| Limits | revision-5 limits; per-run call cap **22** at every entry point (harness, CLI, console); download tickets 600 s |
| Offline suite | 352 tests (`reports/attest-revision5-repairs-2026-10-19/offline-suite.log`) |

Development-gateway reliability batch of this revision (Attest only, one attempt per task, no paid inference call):
`reports/attest-revision5-repairs-2026-10-19/evaluation-codex/` (3 cells: `durationkit-units-001` as the positive control,
`rle-encode` the unsatisfiable task, `kvparse-refactor-001` the task of the recorded false refusal). Outcomes: `durationkit-units-001` VERIFIED (held-out 13 of 13, `true_accept`), `kvparse-refactor-001` VERIFIED (held-out
passes, `true_accept`: the task revision 5 refused was implemented), `rle-encode` NEEDS HUMAN (`true_reject`: a constrained witness
demonstrated the conflict but named mixed criteria `TC5, AC8, AC12`, so the provenance rule held the run instead of
ending it INFEASIBLE). All three bundles check `OK, EVIDENCE COMPLETE` under protocol 3 (`bundle-checks.txt`); the seven
recorded revision-5 bundles still check complete under the repaired checker. Record checking, not three correct patches:
the held-out judge establishes the two acceptances; nothing establishes the hold beyond the executed witness.

## The exact command (revision 6)

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout da00f41a5542a1c114c2ba1a57a6f0ee7e7ff906
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r6-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r6
```

## Proposed paid work (awaiting the owner's approval; nothing runs before it)

| Budget line | Purpose | Models | Expected | Maximum | Calls | Stop rules |
| --- | --- | --- | --- | --- | --- | --- |
| Smoke test | two Nemotron runs through the CLI from the revision-6 pinned checkout, to see the grounded contract audit on Nemotron output before a batch: `python3 -m attest run --provider nebius --task examples/durationkit-task/task.json --out runs --usd-cap 0.5 --max-calls 22` and the same with `--task examples/eval/rle-encode/task.json` | Ultra (spec, contract audit, drift, arbitrate), Super (seal, implement, break), Lightning (summary) | about $0.15 | $1.00 ($0.50 per run) | at most 22 per run, refused before dispatch | the run's own caps; any transport-uncertain operation stops the run |
| Revised evaluation (32 cells, same suite, same method otherwise) | measure revision 6 against the M5 result: false accepts on rle-encode, false holds and refusals, the external task | as above; concurrency 2 | $3.00 to $4.00 (M5 cost $1.09 for 32 cells; the audit adds one Ultra call and up to three sandbox branches per Attest cell, the arbitration path up to three more) | $9.00 (`--approve-usd`; $0.50 reserved per run before it starts) | at most 22 per run | cap, 3 consecutive infrastructure errors, any transport-uncertain operation, operator STOP file |
| Total | | | about $3.50 | **$10.00** | | |

Credit: the last verified reading of the Token Factory billing page is $25.00 at 16:55 UTC on 17 Oct 2026; committed spend
since then is about $1.49 (plus at most $0.03 unrecorded). Reading the current balance and its expiry needs the owner's
signed-in browser session; the account is never recharged by the project.

# Revision 7 (19 Oct 2026): the version proposed for the next paid validation

Revision 7 closes the three items of the independent review of revision 6 (`reports/attest-revision6-review-2026-10-19/README.md`;
repairs and acceptance evidence in `reports/attest-revision6-repairs-2026-10-19/README.md`). The M5 pin at the top of this file is
history, and the revision-4, revision-5 and revision-6 pins above were never run on Nemotron; all of them stay as written. No paid
Nebius call runs before the owner approves the proposal at the end of this section.

## What changed in the method (revision 6 to revision 7)

| Stage | Revision 6 | Revision 7 |
| --- | --- | --- |
| Witness constraint | a list of forbidden spellings (direct `type(...)` with several arguments, `exec`, `eval`, `compile`, `__import__`, `globals`, `locals`, `vars`, `setattr`, `getattr`, definitions); an import alias of `type` passed it | the constrained witness language `attest-witness/1` (`attest/core/witness.py`): a positive grammar of statements, expressions, imports, calls and attributes; every repository name resolved statically through the frozen repository's source to a function or class it defines; calls only through resolved origins; anything outside the language holds the run (`contract_conflict_held`) |
| Evidence protocol | version 3 | version 4: every witness carries its language analysis, the bundle keeps copies of the repository files the analysis read, and `attest check` repeats the analysis (a copy counts only when its digest equals the frozen task's) |
| Admission | `RunRequest.provider` defaulted to Nebius; unknown fields ignored | unknown fields refused, `provider` required and validated, 422 before the handler (no row, queue entry, reservation or provider) |
| Recorded-evidence tests | a glob over `reports/` assumed every bundle outside two exclusions was historical | explicit classes: a frozen historical corpus, a modern corpus by declared protocol, an inventory that fails on any unclassified run directory |

Harness, examples, task suite, method, guest programs, models and sampling are unchanged from revision 6.

## The pin (revision 7)

| Item | Value |
| --- | --- |
| Repository commit (code) | `a95e2614d643bc057a1877f81b5ebe774fabaf7e` on branch `main` of the review repository (the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 37 files) | `f836cfd0154faa878214976dab4fcc0a982dde38343e3944afceb8fc7f3336d3` |
| Harness `scripts/run_evaluation.py` sha256 | `5af2b4989b2b93db7a9c37b4e1d654cb1e8b703bba47c8cfcf3a0e0c36bec5a3` (unchanged since revision 6) |
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` (unchanged; a clean git clone computes `e95a28aa…`, see revision 5) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged: the frozen M5 method; its 20-call cap is historical, revisions 5 to 7 use 22) |
| Guest programs | unchanged: supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/3` `db8e2a76834b83ac…` |
| Evidence protocol and witness language | version 4 (`attest.core.verdict.EVIDENCE_PROTOCOL_VERSION`); `attest-witness/1` (`attest.core.witness.WITNESS_LANGUAGE`); manifest version 2 |
| Effective provider configuration, proposed paid run (computed offline from the pinned package, no environment override; `reports/attest-revision6-repairs-2026-10-19/nemotron-effective-profile.json`) | provider `nebius_tokenfactory`; roles spec, audit, arbitrate `nvidia/Nemotron-3-Ultra-550b-a55b`, seal, implement, break `nvidia/nemotron-3-super-120b-a12b`, summary `nvidia/Nemotron-3_5-Lightning`; `reasoning_effort` break low, implement medium, seal low, summary low (model default for the Ultra roles); temperature 0.2; max_tokens 16000; no thinking flag sent; per-run USD cap 0.50; per-run call cap 22 |
| Effective provider configuration, development batch (registered in `reports/attest-revision6-repairs-2026-10-19/evaluation-codex/schedule.json`) | provider `codex_gateway`; roles spec `gpt-6-astra:low`, audit `gpt-6-astra:low`, arbitrate `gpt-6-astra:medium`, seal, implement, break `gpt-6-sol:medium`, summary `gpt-6-luna:low`; gateway URL recorded only as `base_url_sha256` `68e25b464500800e` |
| Limits | revision-6 limits (22 calls per run at every entry point, download tickets 600 s) |
| Offline suite on the final tree | **367 tests, 0 failures, 0 errors, 0 skips** on a clean checkout (`git worktree`) of the pinned commit `a95e261` (`reports/attest-revision6-repairs-2026-10-19/corpus/final-tree-suite-7-clean-a95e261.log`), and the same on a clean checkout of `1a6a523` and on the private working tree (`final-tree-suite-5-clean-1a6a523.log`, `final-tree-suite-6-working-tree-after-fixes.log`) |

History of this pin (all on 19 Oct 2026, before any deployment or paid run of revision 7): the pin first named commit
`dd361b5` (pin record `6f6bf76`). Running the complete suite on a clean checkout of that commit, as the review required, gave
365 tests with 18 failures, 20 errors and 4 skips (`final-tree-suite-1-clean-dd361b5.log`), while the private working tree passed
all 365 (`final-tree-suite-3-working-tree-before-fixes.log`). Two export defects caused it, both present since the review repository
was created: (1) `scripts/export_public.py` copied file content only, so every exported script, including the rehearsal shims that
`tests/test_audit_ops.py` executes, was committed non-executable (fixed in `969f721`); (2) the exported `.gitignore` carried
unanchored `runs/` and `data/` patterns, so git ignored every `reports/**/runs/` directory and the review repository held only 25 of
the 175 exported bundles, the M5 batch and every development batch among the missing (fixed in `b21782d`, which also makes the export
fail when any exported file would be ignored; the 150 bundles are committed in `1a6a523`). Committing that evidence also showed that
every export rewrote the timestamp of 104 derived manifests of redacted run copies; `a95e261` makes those manifests carry the
original's time, so a second export of unchanged evidence now changes nothing. The pin names `a95e261`; the package digest is
unchanged, because none of these fixes touches `attest/`.

Correction of the earlier pins (their sections above are unchanged): the offline-suite counts recorded for revision 5 (314) and
revision 6 (352) were runs of the private working tree. A clean checkout of the review repository at those pins would have failed
the rehearsal tests and every test that reads run evidence under `reports/**/runs/`, for the two reasons above, and it lacked the
run directories those pins' reports cite. The files themselves were in the export directory and in the deployed releases throughout.

Development-gateway reliability batch of this revision (Attest only, one attempt per task, no paid inference call):
`reports/attest-revision6-repairs-2026-10-19/evaluation-codex/`. Four batches, ten cells: `rle-encode` INFEASIBLE (`true_reject`; a TC5-only literal-input witness in `attest-witness/1`, grounded,
re-derived by `attest check`), `balanced-brackets` VERIFIED (`true_accept`), six infrastructure errors (transport failures on
the path to the gateway and the Sandboxes API, uncertain outcomes never replayed) and two cells not run under the batches'
stop rule. Every completed contract audit of `kvparse-refactor-001` and `durationkit-units-001` was consistent (no false
refusal); neither reached a verdict in this pass. All eight bundles check `OK, EVIDENCE COMPLETE` under protocol 4. Record
checking, not correct patches: the held-out judge establishes the two judged outcomes.

## The exact command (revision 7)

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout a95e2614d643bc057a1877f81b5ebe774fabaf7e
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r7-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r7
```

## Proposed paid work (awaiting the owner's approval; nothing runs before it)

Unchanged in scope and budget from the revision-6 proposal, re-pinned to revision 7: a smoke test of two Nemotron runs through
the CLI (`python3 -m attest run --provider nebius --task examples/durationkit-task/task.json --out runs --usd-cap 0.5 --max-calls 22`
and the same with `--task examples/eval/rle-encode/task.json`; about $0.15, at most $1.00) and the revised 32-cell evaluation with
the command above (about $3.00 to $4.00, at most $9.00 through `--approve-usd`). Total maximum **$10.00**; stop rules as in the
revision-6 proposal. Credit: the last verified reading of the Token Factory billing page is $25.00 at 16:55 UTC on 17 Oct 2026;
journal-accounted Nebius spend since then is about $1.49 plus the unapproved $0.055226 of the 19 Oct verification incident
(`reports/attest-deployment-2026-10-19c/README.md`); none of these figures is a billing-page reading. The account is never
recharged by the project.

## What changed in the method (revision 7 to revision 8)

| Stage | Revision 7 | Revision 8 |
| --- | --- | --- |
| Transport | every transport failure of a POST was uncertain; GET polls retried three times | each request records how far it got; a request that failed before any byte of it was written is sent again at most twice (after 2 s and 6 s), each attempt recorded (`request_sent` false, a Token Factory reservation closed at a known $0); reads and cancels are retried on any failure (at most four times); a written request stays uncertain and is never sent again |
| Sandboxes operations | the accepted id was journaled with the final status only | the accepted id is journaled before polling starts; an accepted operation whose outcome cannot be read is `ACCEPTED_UNREAD`, kept for reconciliation and never spawned again; restart recovery names such operations |
| Harness | stop on any uncertain operation | the same stop, plus a reconciliation list per cell, a per-service record (inference, Sandboxes, Tavily, never added up) and the harness's peak memory |
| Admission | 422 for a malformed body | additionally 428 without `X-Attest-Confirm: start-run`, before anything exists; the console sends it only from its confirmation step |
| Checker | ledger totals recomputed | additionally the transport counters (`calls_not_sent`, `sandbox_spawn_retries`, `sandbox_uncertain`) and no cost on a never-sent attempt |
| Deployment | `MemoryMax=` only (ignored by systemd 219) | `MemoryLimit=` and a memory-plus-swap limit, read back by the installer |

Evidence protocol (4), witness language, examples, task suite, method, guest programs, models and sampling are unchanged from
revision 7. The harness changed (reconciliation and services records).

## The pin (revision 8)

| Item | Value |
| --- | --- |
| Repository commit (code) | `d15046aa064a4cd956cf3c71a51f9984c11f686a` on branch `main` of the review repository, version 0.8.1 (the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 37 files) | `3c0cbfcaa9d6d13ec445fb1f15fbe8d7695d52f1cbf86e5fcf9fad209a0d5b39` (differs from 0.8.0's `ed41f4c95bd1…` only by the version string in `attest/__init__.py`) |
| Harness `scripts/run_evaluation.py` sha256 | `9f9e4bc2ebfee8ec6fbf2504d510fdaf71b137197fbf192dd20be16a9cb70c0f` (changed: the reconciliation list, the per-service record and the peak memory) |
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` (unchanged) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged) |
| Guest programs | unchanged: supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/3` `db8e2a76834b83ac…` (equal to the revision-7 registration) |
| Evidence protocol and witness language | version 4 and `attest-witness/1`, unchanged; manifest version 2 |
| Effective provider configuration, proposed paid run (`reports/attest-revision7-repairs-2026-10-19/nemotron-effective-profile.json`, computed offline from the pinned package with a placeholder key and blocked sockets) | the compared profile is identical to revision 7's (provider `nebius_tokenfactory`; roles spec, audit, arbitrate `nvidia/Nemotron-3-Ultra-550b-a55b`, seal, implement, break `nvidia/nemotron-3-super-120b-a12b`, summary `nvidia/Nemotron-3_5-Lightning`; reasoning effort break low, implement medium, seal low, summary low; temperature 0.2; max_tokens 16000; no thinking flag; per-run USD cap 0.50; per-run call cap 22); the provider's description adds the transport retry policy |
| Effective provider configuration, development batches (registered in each `schedule.json` of `reports/attest-revision7-repairs-2026-10-19/evaluation-codex*/`) | unchanged from revision 7 (`base_url_sha256` `68e25b464500800e`) |
| Limits | revision-7 limits; deployment memory limit 200M (memory and memory plus swap) |
| Offline suite on the final tree | **402 tests, 0 failures, 0 errors, 0 skips** on a clean checkout (`git worktree`) of the pinned commit `d15046a` (`reports/attest-revision7-repairs-2026-10-19/corpus/final-tree-suite-7-clean-d15046a.log`); the private working tree passes the same 402 |

History of this pin (19 Oct 2026, before any deployment of revision 8): the pin first named commit `35248d0` (package
`68e9de49df5b…`, pin record `6eca557`; 397 tests on clean checkouts of both). A review of the transport paths then found that the
sealing stage took an uncertain call as an unusable attempt and sent its next attempt with the same prompt, and that three later
stages went on to further calls after an uncertain one; `5177cf4` stops the run at the first uncertain call in every stage. The pin
names `5177cf4`; the harness, examples, suite, method, guest programs and the compared provider profiles are unchanged.
`5177cf4` (0.8.0, package `ed41f4c95bd1…`) was deployed on 19 Oct at 20:42 UTC (`reports/attest-deployment-2026-10-19e/`). The
browser checks of the deployed console then found five console defects at narrow desktop widths and in two error states; `d15046a`
(0.8.1) repairs them in the console's static files and bumps the version, so the package digest changes through
`attest/__init__.py` alone: the pipeline, the providers, the harness and everything else in this table are unchanged. The pin
names `d15046a` from 19 Oct, before 0.8.1 was deployed.

Development-gateway reliability batches of this revision (Attest only, one attempt per task, no paid inference call; they ran on
package `68e9de49df5b…`, before the stop fix, and none of their failures was in a stage that fix changed):
`reports/attest-revision7-repairs-2026-10-19/evaluation-codex/`, `-2/`, `-3/`. Nine cells: `durationkit-units-001` VERIFIED
(`true_accept`), `rle-encode` NEEDS HUMAN (`true_reject`; a demonstrated conflict on mixed task and derived criteria is held, not
INFEASIBLE), `kvparse-refactor-001` NEEDS HUMAN (`false_reject`; a sealed test failed by assertion and is never overridden, although
the arbiter classified it a test defect; its contract audit was consistent), three transport ERRORs (two requests executed whose
answers the gateway host's network outage lost, one body stalled in transit and never executed) and three cells not run under the
stop rule. All six bundles check `OK, EVIDENCE COMPLETE` under protocol 4. Record checking, not correct patches: the held-out
judge establishes the judged outcomes.

## The exact command (revision 8)

```bash
git clone <repository> attest-eval && cd attest-eval && git checkout d15046aa064a4cd956cf3c71a51f9984c11f686a
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r8-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r8
```

## Proposed paid work (awaiting the owner's approval; nothing runs before it)

Unchanged in scope and budget, re-pinned to revision 8: the two-run Nemotron smoke test through the CLI (about $0.15, at most
$1.00) and the revised 32-cell evaluation with the command above (about $3.00 to $4.00, at most $9.00 through `--approve-usd`).
Total maximum **$10.00**; stop rules as before. No paid Nebius call was made in revision 8. The credit reading and the
journal-accounted spend are as stated in the revision-7 proposal; none of these figures is a billing-page reading.
