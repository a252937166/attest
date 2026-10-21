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
git clone <publication repository> attest-eval && cd attest-eval && git checkout 948385c055852739ce98613240b01fef13c5c601
# the same tree as review-repository commit 6b786a2e51bba634d63cc8b4ee75bb215c168fa7; see "Publication repository (revision 9)"
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
git clone <publication repository> attest-eval && cd attest-eval && git checkout d258ecfd0a75746e17c2978874c8dd0e87f45a92
# the same tree as review-repository commit 4437b29a233603bf8a0523a6c0092493a92d2aa3; see "Publication repository (revision 9)"
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
git clone <publication repository> attest-eval && cd attest-eval && git checkout ef9efd17bc0fdfdc5f47046b819439f68a397255
# the same tree as review-repository commit 320651d3bd4011538fe2f6d240a1e5769b019051; see "Publication repository (revision 9)"
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
git clone <publication repository> attest-eval && cd attest-eval && git checkout 2dec76668f89ad2b288c01366a16c1f17f1400c5
# the same tree as review-repository commit da00f41a5542a1c114c2ba1a57a6f0ee7e7ff906; see "Publication repository (revision 9)"
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
git clone <publication repository> attest-eval && cd attest-eval && git checkout 179a949bc2e2ec30faa3f5c68e65aa9461c9b37f
# the same tree as review-repository commit a95e2614d643bc057a1877f81b5ebe774fabaf7e; see "Publication repository (revision 9)"
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
| Repository commit (code) | `459fe8dd97bb1f719edff42921c04fa43bb50196` on branch `main` of the review repository, version 0.8.3 (the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 37 files) | `35b264adcd0805b91c71c7742518c55af794d742bb93c0b6a3a22a0b10d548f5` (differs from 0.8.0's `ed41f4c95bd1…`, 0.8.1's `3c0cbfcaa9d6…` and 0.8.2's `ed1ac3bad3ec…` only by the version string in `attest/__init__.py`) |
| Harness `scripts/run_evaluation.py` sha256 | `9f9e4bc2ebfee8ec6fbf2504d510fdaf71b137197fbf192dd20be16a9cb70c0f` (changed: the reconciliation list, the per-service record and the peak memory) |
| `examples/` tree digest | `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` (unchanged) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged) |
| Guest programs | unchanged: supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/3` `db8e2a76834b83ac…` (equal to the revision-7 registration) |
| Evidence protocol and witness language | version 4 and `attest-witness/1`, unchanged; manifest version 2 |
| Effective provider configuration, proposed paid run (`reports/attest-revision7-repairs-2026-10-19/nemotron-effective-profile.json`, computed offline from the pinned package with a placeholder key and blocked sockets) | the compared profile is identical to revision 7's (provider `nebius_tokenfactory`; roles spec, audit, arbitrate `nvidia/Nemotron-3-Ultra-550b-a55b`, seal, implement, break `nvidia/nemotron-3-super-120b-a12b`, summary `nvidia/Nemotron-3_5-Lightning`; reasoning effort break low, implement medium, seal low, summary low; temperature 0.2; max_tokens 16000; no thinking flag; per-run USD cap 0.50; per-run call cap 22); the provider's description adds the transport retry policy |
| Effective provider configuration, development batches (registered in each `schedule.json` of `reports/attest-revision7-repairs-2026-10-19/evaluation-codex*/`) | unchanged from revision 7 (`base_url_sha256` `68e25b464500800e`) |
| Limits | revision-7 limits; deployment memory limit 200M (memory and memory plus swap) |
| Offline suite on the final tree | **402 tests, 0 failures, 0 errors, 0 skips** on a clean checkout (`git worktree`) of the pinned commit `459fe8d` (`reports/attest-revision7-repairs-2026-10-19/corpus/final-tree-suite-10-clean-459fe8d.log`); the private working tree passes the same 402 |

History of this pin (19 Oct 2026, before any deployment of revision 8): the pin first named commit `35248d0` (package
`68e9de49df5b…`, pin record `6eca557`; 397 tests on clean checkouts of both). A review of the transport paths then found that the
sealing stage took an uncertain call as an unusable attempt and sent its next attempt with the same prompt, and that three later
stages went on to further calls after an uncertain one; `5177cf4` stops the run at the first uncertain call in every stage. The pin
names `5177cf4`; the harness, examples, suite, method, guest programs and the compared provider profiles are unchanged.
`5177cf4` (0.8.0, package `ed41f4c95bd1…`) was deployed on 19 Oct at 20:42 UTC (`reports/attest-deployment-2026-10-19e/`). The
browser checks of the deployed console then found five console defects at narrow desktop widths and in two error states; `d15046a`
(0.8.1) repairs them in the console's static files and bumps the version, so the package digest changes through
`attest/__init__.py` alone: the pipeline, the providers, the harness and everything else in this table are unchanged. The pin
names `d15046a` from 19 Oct, before 0.8.1 was deployed. 0.8.1 was deployed at 22:18 UTC
(`reports/attest-deployment-2026-10-19f/`). While the video was prepared, the home page's replay of a 17 Oct bundle was found to
claim "offline check 24 of 24 OK", a figure from an earlier checker; the current checker passes that bundle as a historical bundle
(0 errors, 2 warnings). `4d37dbb` (0.8.2) corrects the claim in the console's static files and bumps the version; the pin names
`4d37dbb` from 19 Oct, before 0.8.2 was deployed. 0.8.2 was deployed at 23:11 UTC (`reports/attest-deployment-2026-10-19g/`);
watched to its end, its replay showed the longer badge squeezing the title beside it into a mid-word break, and `459fe8d` (0.8.3)
shortens the badge to "attest check: OK, partial"; the pin names `459fe8d` from 19 Oct, before 0.8.3 was deployed. 0.8.3 was
deployed at 23:55 UTC (`reports/attest-deployment-2026-10-19h/`).

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
git clone <publication repository> attest-eval && cd attest-eval && git checkout 74b6bc9d673c7daec239a38bec3e72335bbe22c7
# the same tree as review-repository commit 459fe8dd97bb1f719edff42921c04fa43bb50196; see "Publication repository (revision 9)"
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

## What changed (revision 8 to revision 9, 20 Oct 2026, version 0.9.0)

`reports/attest-revision9-repairs-2026-10-20/README.md` records the six repairs: a run stops at the first operation whose outcome is
uncertain at every stage, sandbox operations as well as model calls (revision 8 stopped only model calls; the breaker turned an
uncertain sandbox operation into a plain model error and went on to the drift audit); ambiguous HTTP answers are classified once (4xx
refused, 5xx uncertain; reads retried, bounded); sandbox operations are journaled durably as PENDING before the spawn and with their
accepted id before the first poll, and a journal failure stops the run; a cut HTTP error body keeps its status; the offline suite runs
without credentials, private configuration or network; and the review history is replayed into a separate publishable repository.
Evidence protocol 5 adds the bundle's reconciliation record. Every code path that sends a request changed (the providers, the sandbox
client, the transport, the pipeline, the console worker, the harness), so the pin is new; the guest programs, the examples, the task
suite, the method, the models and the sampling are unchanged, and the effective Nemotron profile computed from the pinned package equals
the revision-7 registration.

## The pin (revision 9)

| Item | Value |
| --- | --- |
| Repository commit (code) | `67518471b1a56e95379a789b0f0e2dc0d77db8b5` on branch `main` of the review repository, version 0.9.0 (the package and the harness of `7664742`, with the tests of the home-directory fix); in the publication repository `e91e8db2a1f40102331b403b820f9e7b1ff698dd` (the same tree; the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 37 files) | `ab5b1705ae2b921141d01d77e4728f4e63c5233bcc629e93636809e32039e3c1`, the same for `7664742` and `6751847` (`808137c`, `58d2520` and `697d0e7` share `2449ab27262c…`; `7664742` changes how a stopped run names its stage; `6751847` changes tests only) |
| Harness `scripts/run_evaluation.py` sha256 | `bc515984ccc65746846e368898b0abe393841d815a6ba584fe10c432affe5176` (changed: every cell's ledger registered with the batch, a halted cell halts every other cell in flight and is not judged, the judge's own journal, reconciliation items from the records, `--reconciled`) |
| `examples/` tree digest | unchanged: `e95a28aa363366160062107128950e9ff4c1888d52dccfdf578299e14e341b78` from a clean checkout (`6db7a2e9…` in the working and exported trees, see revision 5) |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged) |
| Guest programs | unchanged: supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/3` `db8e2a76834b83ac…` |
| Evidence protocol and witness language | version 5 (the reconciliation record) and `attest-witness/1`; manifest version 2 |
| Effective provider configuration, proposed paid run | computed offline from the pinned package (placeholder key, outbound network denied): equal to the revision-7 registration; the provider's description adds its answer and journal policies |
| Limits | revision-8 limits; deployment memory limit 200M (memory and memory plus swap) |
| Offline suite on the final tree | **459 tests, 0 failures, 0 errors, 0 skips** on a clean checkout of `6751847` with no credential, no private configuration, HOME at a directory created for the run (still empty afterwards; the suite moves HOME to a new directory of its own and checks that no test left anything there) and outbound network denied by the operating system except to the loopback interface (macOS `sandbox-exec`; the suite's own guard also refuses this machine's proxy and every loopback port listening before it started): `reports/attest-revision9-repairs-2026-10-20/suites/final-tree-suite-18-clean-6751847-macos-no-network.log`; and **459 tests, 0 failures, 0 errors, 26 skipped** on a clean `git archive` of `6751847` in a Linux container whose only network interface is the loopback one (Alpine 3.24, Python 3.12.15, uid 65534, all capabilities dropped; the 26 skips are the tests that need bash, git or node, which the image lacks): `final-tree-suite-19-clean-6751847-linux-no-network.log` (458 tests with the same results for `7664742` and `697d0e7`: suites 12 to 15) |

History of this pin (20 Oct 2026, before the deployment of revision 9): the code of the repairs is `808137c`; `58d2520` and `697d0e7`
tighten the offline suite's own guard (the machine's configured proxy, then every loopback port listening before the suite started)
and let the three export tests that need git skip without it, as the bash and node ones do (the same package digest for all three).
The record first named `697d0e7`, whose clean checkout passed both offline set-ups. A browser check of a held run's case file then read
"At stage reconciliation" for a run stopped at `breaker-tests`: recording the stop relabelled the bundle's stage. `7664742` names the
stage of the operation from the halt record (decision header, exhibit E7, PROOF.md) and asserts it in the tests; its clean checkout
passed both offline set-ups again, and the pin names it. A live development run of `697d0e7` on the team's gateway (one task, 11
gateway calls, 15 Sandboxes operations, no Nebius inference, no Tavily) ended VERIFIED under evidence protocol 5 with every operation
journaled PENDING, ACCEPTED and SUCCESS (`reports/attest-revision9-repairs-2026-10-20/live-codex/`); `7664742` does not change any request path.
0.9.0, built from a clean checkout of the pin record `65d81f7`, was deployed on 20 Oct at 08:22 UTC (`reports/attest-deployment-2026-10-20/`).
After the deployment a clean run of the records commit `5229e14` showed that the HOME given to the macOS runs had not been empty from
the second run on: one test kept its dummy key's pacing state there (`reports/attest-revision9-repairs-2026-10-20/README.md`,
"Correction: the suite's home directory"). `6751847` gives every run of the suite its own empty home directory and fails if a test
leaves anything there; it changes tests only, so the package, harness, METHOD and example digests are those of `7664742`. Its clean
checkout passed both offline set-ups, and the pin names it. The deployed package is the pinned package (digest `ab5b1705…`); the
deployed tree carries the earlier tests, which the service never runs.

## The exact command (revision 9)

```bash
git clone <publication repository> attest-eval && cd attest-eval && git checkout 1c3a8c14ddf6f0cbbb02bb70d46a90621210e92b
# the same tree as review-repository commit 67518471b1a56e95379a789b0f0e2dc0d77db8b5
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r9-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r9
```

## Publication repository (revision 9)

The review repository (`dist/public`, private) keeps the record as it was written. Its commits from before revision 8 carry the
development gateway's host in 125 historical REDACTION.json files and 16 versions of the export script, and two early EXPORT.json files
carry a local home directory, so its history is not published. `scripts/build_publication_history.py` replays that history, commit by
commit with the same authors, dates and messages, into a separate repository (`dist/publication`, not pushed): only the 143 blobs that
hold a private string change (through the export's own redaction) and the 324 derived manifests that list one of them get that entry's
digest and size recomputed; every other file, the package, the harness, the examples and the evidence included, is byte-identical.
`--verify` found the publication history clean (every object, every spelling, including escaped, base64 and compressed forms), every
commit differing from its review commit only by those rewrites, every pinned digest below equal in both, and the 849 run copies whose
manifest changed passing `attest check` at the commits where they changed
(`reports/attest-revision9-repairs-2026-10-20/publication/`). The replay is deterministic, so a review commit always maps to the same
publication commit (the builds up to `697d0e7`, `7664742` and `6751847` agree on every commit they share);
`publication-map-to-6751847.json` lists every one. Historical records cite review-repository commit ids; this table
translates the pinned ones (the `git checkout` lines of every pin above now name the publication commits):

| Pin | Review repository | Publication repository |
| --- | --- | --- |
| M5 evaluation (17 Oct) | `6b786a2e51bba634d63cc8b4ee75bb215c168fa7` | `550568285af7d572b70a48d4a2de729f570f94c3` |
| Revision 4 | `4437b29a233603bf8a0523a6c0092493a92d2aa3` | `f4bf5f48eb698ccd1b7bb5d2c7c1c450de993ca7` |
| Revision 5 | `320651d3bd4011538fe2f6d240a1e5769b019051` | `ad2f633c555898a8a6e47e7e410aff0ddb15e1b7` |
| Revision 6 | `da00f41a5542a1c114c2ba1a57a6f0ee7e7ff906` | `0dd0b425b8aa6ea9fe03160a8eb6aef82dbf21e8` |
| Revision 7 | `a95e2614d643bc057a1877f81b5ebe774fabaf7e` | `00a3e2a76b1fa5b24b5e96cb1387d5bf7de381af` |
| Revision 8 (0.8.3) | `459fe8dd97bb1f719edff42921c04fa43bb50196` | `84d3d8b774b3e4a1aa5cef77cecc17e67e5d4b89` |
| Revision 9 (0.9.0), the deployed code | `7664742309216676c7a0bc9188df0aac932fe35b` | `12a541dc6da91e55955b561e6ac9d64465028d33` |
| Revision 9 (0.9.0), the pin (tests of the home-directory fix) | `67518471b1a56e95379a789b0f0e2dc0d77db8b5` | `e91e8db2a1f40102331b403b820f9e7b1ff698dd` |

For every row the publication commit reproduces the recorded `attest/` package digest and harness digest exactly (for example
`166cdcbd46a74cd0…` and `3214d2b3a1fd1fbc…` for the M5 pin). Who may publish the publication repository, and under which author identity,
is the owner's decision; nothing has been pushed.

## Proposed paid work (revision 9; awaiting the owner's approval; nothing runs before it)

Unchanged in scope and budget, re-pinned to revision 9: the two-run Nemotron smoke test through the CLI (about $0.15, at most $1.00) and
the revised 32-cell evaluation with the command above (about $3.00 to $4.00, at most $9.00 through `--approve-usd`). Total maximum
**$10.00**, stop rules as before plus the revision-9 rule: any operation of uncertain outcome stops its run and the batch, every cell in
flight included. No paid Nebius call was made in revision 9.

# Revision 10 (20 Oct 2026, version 0.10.0): the version proposed for the next paid validation

## What changed (revision 9 to revision 10)

`reports/attest-revision10-repairs-2026-10-20/README.md` records the four repairs: the console's restart recovery reads a run's proof bundle
and its journal before it settles the row, so a held run keeps its hold however far the process got; the held state and its hold are one
transaction (one hold per run, ever), a failure fails the service closed, start-up repairs a missing hold and never reopens a cleared one;
a resumed batch starts nothing while any item of its rows, bundles or run and judge journals is unresolved, and an acknowledgement must
name the item ids and is kept across restarts; and every upstream answer is decoded and checked before use, an unreadable one stopping the
run with what is known (UNCERTAIN, ACCEPTED_UNREAD with its id, an uncertain call). The package, the harness and the console page changed;
the guest programs, the examples, the task suite, the method, the models, the sampling and the evidence protocol (5) did not, and the
effective Nemotron profile computed from the pinned package equals the revision-7 registration. The two VERIFIED development runs of 17 Oct
that went on after an uncertain spawn were reconciled read-only: both spawns executed, both mutants were killed, both verdicts stand.

## The pin (revision 10)

| Item | Value |
| --- | --- |
| Repository commit (code) | `c0ddb486f8c91f061678a2b6239cbbdbddd21f87` on branch `main` of the review repository, version 0.10.0 (the package and the harness of `775248c`, with the recorded-corpus inventory that knows revision 10's live run); in the publication repository `953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a` (the same tree; the documentation commits that follow carry this record with an identical `attest/` digest) |
| `attest/` package digest (sha256 over path and content of every source, 37 files) | `7e72364f135c45c8a69a3a59c9cba5c954ebbb843cc7752b76c8303550548cb6`, the same for `775248c`, `f0c28c2` and `c0ddb48` (`c0ddb48` changes one test only) |
| Harness `scripts/run_evaluation.py` sha256 | `243ab12f3879ffc6d7a0eef5c08c147141a13915457fb7ff1b8e02aa7e0e4ac7` (changed: the resume gate over every row, bundle and run or judge journal, acknowledgements tied to item ids in `reconciliations.jsonl`, the refusal of a batch whose gateway status answer cannot be read) |
| `examples/` tree digest | unchanged: `e95a28aa363366160062107128950e9ff4c1888d52dccfdf578299e14e341b78` from a clean checkout |
| Task suite `examples/eval/SUITE-M5.json` sha256 | `a43da6c3ee74d713e6d8dc9764f6775f8e89f8986fd6b0317d64335a54bf5d39` (unchanged since M5) |
| Method `METHOD.md` sha256 | `ec415afcf1649040a219968d49a469553058d8299a1dfd3ad557bafe71c138dc` (unchanged) |
| Guest programs | unchanged: supervisor `attest-sealed-supervisor/7` `97d3d47d1d5b4fed…`; per-test child `e4e7b0b294a2004c…`; canary `9cdc57c1348fae5c…`; sandbox runner `attest-guest/3` `db8e2a76834b83ac…` |
| Evidence protocol and witness language | version 5 and `attest-witness/1` (unchanged); manifest version 2 |
| Effective provider configuration, proposed paid run | computed offline from the pinned package (placeholder key, outbound network denied): equal to the revision-7 registration (`reports/attest-revision10-repairs-2026-10-20/checker/nemotron-effective-profile-775248c.json`) |
| Limits | revision-8 limits; deployment memory limit 200M (memory and memory plus swap) |
| Offline suite on the final tree | **491 tests, 0 failures, 0 errors, 0 skips** on a clean checkout of `c0ddb48` with no credential, no private configuration, HOME at a new empty directory (still empty afterwards) and outbound network denied by the operating system except to the loopback interface (`reports/attest-revision10-repairs-2026-10-20/suites/suite-4-clean-c0ddb48-macos.log`); **491 tests, 26 skipped** (no bash, git or node in the image) in a container with no network interface (`suite-5-clean-c0ddb48-linux.log`); `775248c` passed both set-ups the same way (`suite-1`, `suite-2`) |

History of this pin (20 Oct 2026): the code of the repairs is `775248c`; its clean checkout passed both offline set-ups and the reproduction
(63 of 63), and a live development run of it on the team's gateway read every real answer through the new checks (12 gateway calls, 8
Sandboxes operations, no Nebius inference, no Tavily; NEEDS HUMAN on its own evidence). 0.10.0, built from a clean checkout of the pin
record `f0c28c2`, was deployed on 20 Oct at 16:02 UTC (`reports/attest-deployment-2026-10-20b/`); the deployed package is the pinned package
(digest `7e72364f…`). A clean checkout of that pin record, run after the deployment, then failed one test of 491
(`suite-3-clean-f0c28c2-macos-one-failure.log`): `RecordedCorpusInventory` requires every recorded run directory to be classified, and the
record had added the live run's directory without classifying it. `c0ddb48` adds it to the modern corpus under protocol 5 (tests only, the
package, harness, METHOD and example digests of `775248c`); its clean checkout passed both offline set-ups, and the pin names it. The deployed
tree carries the earlier test file, which the service never runs.

## The exact command (revision 10)

```bash
git clone <publication repository> attest-eval && cd attest-eval && git checkout a72fdf247a927b111b0ee17f5c5602c299118e5d
# the same tree as review-repository commit c0ddb486f8c91f061678a2b6239cbbdbddd21f87
export NEBIUS_API_KEY=... NEBIUS_PROJECT_ID=...
python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
    --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r10-final \
    --out reports/attest-evaluation-2026-10-XX-nebius-r10
```

## Publication repository (revision 10)

The replays of the review history up to `775248c` and up to `c0ddb48` (`reports/attest-revision10-repairs-2026-10-20/publication/`) found the
publication history clean (every object, every spelling), every commit differing from its review commit only by the known rewrites, the pinned
digests equal in both (nine, then ten), and the 849 rewritten run copies passing `attest check`; every commit they share with each other and
with the revision-9 builds maps to the same publication commit. Revision 10 adds two rows to the table of revision 9:

| Pin | Review repository | Publication repository |
| --- | --- | --- |
| Revision 10 (0.10.0), the code of the repairs | `775248c2f87d66e5fe4f3802b1caf85024f62a49` | `fe88f405ae3bd684f7c089ebfdab135cd7ae7d0c` |
| Revision 10 (0.10.0), the pin (the corrected inventory) | `c0ddb486f8c91f061678a2b6239cbbdbddd21f87` | `953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a` |

## Proposed paid work (revision 10; awaiting the owner's approval; nothing runs before it)

Unchanged in scope and budget, re-pinned to revision 10: the two-run Nemotron smoke test through the CLI (about $0.15, at most $1.00) and
the revised 32-cell evaluation with the command above (about $3.00 to $4.00, at most $9.00 through `--approve-usd`). Total maximum
**$10.00**, stop rules as before plus revision 10's: a malformed upstream answer stops its run and the batch, and a resumed batch starts
nothing while an item is unresolved. No paid Nebius call was made in revision 10.

# Revision 10 validated on Nemotron (21 Oct 2026), and the console release 0.10.1

## The paid work, as approved

The owner approved the proposed paid work on 21 Oct 2026. It ran from a fresh clone of publication commit
`953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a` (review `c0ddb486`), whose package, harness, examples, suite and METHOD digests were checked
against the pin above before the first call. The smoke test (both runs NEEDS HUMAN with complete protocol-5 evidence) cost $0.116153 of
inference against the $1.00 maximum; the evaluation, with the exact command above (label `r10-final`), cost $1.3871 against the $9.00
approval. Total paid Nebius inference for revision 10: $1.503253 of the $10.00 maximum. Tavily: no call. Sandboxes: 16 smoke operations,
141 evaluation operations and 22 judge operations (163 in all; the rendered RESULTS.md counts the judge operations twice). Records: `reports/attest-validation-2026-10-21-nebius-r10/` (smoke test, every stop's
read-only reconciliation, the operator loop) and `reports/attest-evaluation-2026-10-21-nebius-r10/` (README, RESULTS.md, the batch).

## Results (16 cells per system)

| | Plain agent | Attest |
| --- | --- | --- |
| Correct patch accepted | 8 | 2 |
| Broken patch shipped | 2 | 0 |
| Correct patch held for a human | 1 | 2 |
| Correct refusal (the task that cannot be satisfied) | 0 | 2 |
| Hold without a patch on a satisfiable task, or unfinished | 1 | 4 |
| Sandboxes error after the request was sent, never replayed | 4 | 6 |
| Committed inference | $0.3448 | $1.0423 |

Six spawns were answered HTTP 500 by `POST /sandboxes/v1/instances` after they were sent; each stopped the batch with every cell in flight,
read-only checks (at least ten minutes after the request) found that none had executed, and each item was acknowledged by id before the
batch resumed. The method, the models and the sampling were not changed during the batch.

## 0.10.1: the console release that publishes these results

The evaluated package is 0.10.0 (`7e72364f…`). The release deployed after it, 0.10.1, changes nothing the evaluation measured: the version
string (`attest/__init__.py`, `pyproject.toml`), the console's evaluation section (`attest/app/static/index.html`: the 21 Oct table first,
the 17 Oct table kept below it, and the sentence that said the re-evaluation had not been run replaced), and the service's import list
(`deploy/yungou/attest.service`: the evaluation's runs and the two smoke runs are imported read-only, as `requester=import`, which
revision 10 never holds; a local console with that list opened 0 holds). Its pin record, digests and deployment are recorded below when
they exist.

The same records commit carries the publication tooling for the owner's decisions of 21 Oct (no change to the package or the harness):
`scripts/export_public.py` rewrites a development session's scratch path, which spells the account name inside its own name, to a neutral
path and its scan flags any left; `scripts/build_publication_history.py` gains `--identity "Name <email>"` (every commit's author and
committer become that identity, dates and messages kept; `--verify` checks it); `tests/test_publication_identity.py` covers both, and the
recorded-corpus inventory classifies the two new evidence folders under protocol 5.


# The 0.10.1 pin and the published history (21 Oct 2026)

## The pin (0.10.1)

| Item | Value |
| --- | --- |
| Repository commit (code) | `2ac80fbee49e39a83d70b73b047b7d275f4daf73` on branch `main` of the review repository; in the published history `c38e9c110e2130b102ba27d73a27dddf2b759d43` |
| `attest/` package digest (37 files) | `53a9b7c39a96288e2a4f2f439874e985231ed0aa4b8ed18ff31e1579a7a69ae1` (0.10.1); against `c0ddb48` only `attest/__init__.py` (the version) and `attest/app/static/index.html` (the evaluation section) changed |
| Harness, METHOD, suite, examples | unchanged: `243ab12f3879…`, `ec415afcf164…`, `a43da6c3ee74…`, examples `e95a28aa3633…` (196 files) |
| Service unit | `deploy/yungou/attest.service` sha256 `c84e1bb107ba3877…`: the import list adds the 21 Oct evaluation's runs and the two smoke runs |
| Offline suite | **498 tests, 0 failures, 0 skips** on a clean checkout of `2ac80fb` on macOS (no credential, HOME new and empty and still empty afterwards, outbound network denied except loopback; `reports/attest-deployment-2026-10-21/suites/suite-1-clean-2ac80fb-macos.log`); **498 tests, 30 skipped** (no bash, git or node in the image) in a container with no network interface (`suite-2-clean-2ac80fb-linux.log`) |

The release is built from a clean checkout of this pin record, which carries the package of `2ac80fb` unchanged (the commits between change
the publication tooling, its tests and these records only).

```bash
git clone <publication repository> attest-0101 && cd attest-0101 && git checkout c38e9c110e2130b102ba27d73a27dddf2b759d43
# the same tree as review-repository commit 2ac80fbee49e39a83d70b73b047b7d275f4daf73
```

## The published history

Owner decisions of 21 Oct 2026 for the public repository: every commit's author and committer are `Mr.ooo
<16303294+a252937166@users.noreply.github.com>` (dates and messages kept), and the account name a development session's scratch path spells
is rewritten to a neutral path in every published copy (the originals stay private and unchanged). The identity enters every commit, so
every publication commit id changed with this rebuild. The `git checkout` lines above now name the published commits; the publication ids
quoted elsewhere in this file before 21 Oct name the local builds of that time (none was ever pushed). The rebuilt history up to
`30c93fc` replays 77 commits; its verification: scan clean (7,170 objects), 0 unexpected differences, the identity on every commit, the
package, harness and METHOD digests of all 11 pins equal, 1,141 rewritten bundle copies passing `attest check`.

| Pin (review commit) | Local build before 21 Oct | Published history |
| --- | --- | --- |
| `6b786a2e51bba634d63cc8b4ee75bb215c168fa7` | `550568285af7` | `948385c055852739ce98613240b01fef13c5c601` |
| `4437b29a233603bf8a0523a6c0092493a92d2aa3` | `f4bf5f48eb69` | `d258ecfd0a75746e17c2978874c8dd0e87f45a92` |
| `320651d3bd4011538fe2f6d240a1e5769b019051` | `ad2f633c5558` | `ef9efd17bc0fdfdc5f47046b819439f68a397255` |
| `da00f41a5542a1c114c2ba1a57a6f0ee7e7ff906` | `0dd0b425b8aa` | `2dec76668f89ad2b288c01366a16c1f17f1400c5` |
| `a95e2614d643bc057a1877f81b5ebe774fabaf7e` | `00a3e2a76b1f` | `179a949bc2e2ec30faa3f5c68e65aa9461c9b37f` |
| `459fe8dd97bb1f719edff42921c04fa43bb50196` | `84d3d8b774b3` | `74b6bc9d673c7daec239a38bec3e72335bbe22c7` |
| `7664742309216676c7a0bc9188df0aac932fe35b` | `12a541dc6da9` | `a2058694ce8b35051973ec2574b4641d337be77a` |
| `67518471b1a56e95379a789b0f0e2dc0d77db8b5` | `e91e8db2a1f4` | `1c3a8c14ddf6f0cbbb02bb70d46a90621210e92b` |
| `775248c2f87d66e5fe4f3802b1caf85024f62a49` | `fe88f405ae3b` | `1a97df7fbcf8d13f12e758ac08cc562b712aacef` |
| `c0ddb486f8c91f061678a2b6239cbbdbddd21f87` | `953ae59b8c8e` | `a72fdf247a927b111b0ee17f5c5602c299118e5d` |
| `2ac80fbee49e39a83d70b73b047b7d275f4daf73` | `(new)` | `c38e9c110e2130b102ba27d73a27dddf2b759d43` |


# The 0.10.1 deployment, a correction, and release 0.10.2 (21 Oct 2026)

0.10.1 was deployed to yungou at 03:56 UTC from a clean worktree of the pin record `73abb06` (release `0.10.1-53a9b7c39a96`;
`reports/attest-deployment-2026-10-21/README.md`). The one-hour reconciliation sweep at 04:19 UTC found that none of the six uncertain
spawns had executed (`reports/attest-validation-2026-10-21-nebius-r10/README.md`).

Correction to "The paid work, as approved" above: the evaluation's committed inference is $1.387089 (quoted rounded as $1.3871), so the
total paid Nebius inference for revision 10 is $1.503242 ($1.387089 + $0.116153), not $1.503253; that figure added the rounded
evaluation total. The production store agrees: the 34 imported runs carry $1.503242 committed.

0.10.2 corrects two statements on the console page. The package changes only in its version and that page:
- The page named Nemotron 3.5 Lightning as the summary model, but no recorded run called it (`METHOD.md` lists the summary role as not
  used). The page now names Nemotron 3 Ultra and Super only. The architecture diagram now also lists Ultra's contract audit, as the
  narrow-screen list already did.
- The architecture said `attest_revision 166cdcbd` was recorded in every bundle of "the frozen evaluation". Since 0.10.1 the page shows
  the 21 Oct evaluation first, so that reads as the wrong batch. It now names both: `7e72364f` (21 Oct) and `166cdcbd` (17 Oct).

The same commit makes four console tests independent of the host's free disk space. On a volume below the worker's 7 % threshold they
failed, because the worker paused new runs; this was seen on the development machine at 6.9 % free. They now pass zero thresholds, and
the whole suite passes with `shutil.disk_usage` patched to report 1 % free. The Devpost draft drops the same Lightning claim. The 0.10.2
pin is recorded below once its suites have run.

Also in 0.10.2, in the next commit: the home page counted only the newest 50 runs, the list API's default page, so production's ticker
read "50 recorded runs" while the store held 74. The page now requests up to the server's cap of 200 rows, and says "latest" if a list
ever fills it. The asset stamp moves to `20261021a`, so browsers fetch the new script. The server is unchanged: it already accepted
`limit` up to 200.
