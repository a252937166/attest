# Attest Proof Bundle: roman-to-numeral

**Verdict: ERROR**  
Run `roman-to-numeral-baseline-a2-20261021T015413732689Z` · profile `eval-baseline-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T01:54:13.733151+00:00, finished 2026-10-21T01:55:20.834679+00:00.

**This run stopped for reconciliation.** At stage impl-python-6 an operation's outcome became uncertain (sandbox executor), so Attest sent nothing further, replayed nothing and certified nothing. The repository was not changed by this run.

Key evidence (E7): 1 operation(s) to reconcile: stopped for reconciliation at impl-python-6: the outcome of the impl-python-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref ...



What to do: Reconcile the listed operations against the providers' records (each item names its read-only check) before this task is run again; nothing of this run is ever sent again.

Reasons: stopped for reconciliation at impl-python-6: the outcome of the impl-python-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref b6caebc7]; it was not sent again (outcome uncertain; not retried; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The run failed in the sandbox executor at stage impl-python-6; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage impl-python-6: stopped for reconciliation at impl-python-6: the outcome of the impl-python-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was ... |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `648b990e-9dc7-403a-896f-e843dd709714`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

(none)

Acceptance criteria:
AC1. to_roman(1)=='I', to_roman(4)=='IV', to_roman(9)=='IX'
AC2. to_roman(40)=='XL', to_roman(90)=='XC', to_roman(400)=='CD', to_roman(900)=='CM'
AC3. to_roman(2024)=='MMXXIV', to_roman(3999)=='MMMCMXCIX', to_roman(1994)=='MCMXCIV'
AC4. to_roman returns a str
AC5. ValueError for ints outside 1..3999 (0, -1, 4000), including int subclass instances with such values
AC6. TypeError for non-int input ('5', 5.0, None, [1])
AC7. An int subclass instance with a value in range (for example an IntEnum member or PlainInt(49)) converts like the equal int: PlainInt(49) -> 'XLIX'
AC8. Unspecified, not to be tested: int subclasses that override arithmetic or comparison operators; whether bool is rejected

## 2b. Contract audit (executed witnesses)
Not run (bundle predates the contract audit, or the run ended before the specification).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.


(none)


## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```




## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Drift audit not run.



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1440 | 106 | 0 | 0.000527 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1611 | 842 | 0 | 0.001241 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1733 | 1164 | 0 | 0.001568 | 9.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2082 | 214 | 0 | 0.000817 | 5.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2223 | 1063 | 0 | 0.001624 | 10.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2866 | 1412 | 0 | 0.002131 | 16.9s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 11955/4801/0; Inference USD: 0.007908.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c2a-aa15-7275-afb4-31b2be48b12c | SUCCESS | 0 | 1.398s | retained | off | 0.00286366 |
| impl-tests-4 | 01a15c2b-2211-7045-9515-991a69a2ac91 | SUCCESS | 0 | 0.851s | disposable | off | 0.0028304299999999997 |
| impl-python-5 | 01a15c2b-561b-71dd-b3e0-65e996a69d4a | SUCCESS | 0 | 0.815s | disposable | off | 0.00123006 |
| impl-python-6 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 4, total guest duration 3.064s, retained images ['648b990e-9dc7-403a-896f-e843dd709714'], 1 operation(s) with an unknown outcome (never replayed).

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-baseline-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: sandbox executor; stage: impl-python-6; model calls 6 (0 failed); sandbox operations 4; committed inference USD 0.007908; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- stopped for reconciliation at impl-python-6: the outcome of the impl-python-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref b6caebc7]; it was not sent again (outcome uncertain; not retried; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it

## 12b. Reconciliation (nothing of this run is sent again)
The run stopped at stage `impl-python-6` (uncertain_operation) at 2026-10-21T01:55:20.830185+00:00: the outcome of the impl-python-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref b6caebc7]; it was not sent again. Each item below is settled by a human with the read-only check it names.

| Item | Service | Stage | Operation | State | Started | How to settle it |
| --- | --- | --- | --- | --- | --- | --- |
| sandbox_spawn | sandboxes | impl-python-6 | s4 | UNCERTAIN | 2026-10-21T01:55:19.340901+00:00 | GET /operations?kind=instance with since/until around started_at, matching image_uuid (the spawn request carries no client id); it is never sent again |

Rule: once an operation's outcome is uncertain (a request that may have been executed and whose answer is unknown, an accepted operation whose outcome was not read, an answer that could not be priced) or a record of the run could not be made durable, the run sends nothing further: no model call, no sandbox operation, no poll; it ends ERROR with every such operation listed here with the read-only check that settles it, and none of them is ever sent again

## 13. Artifacts
Every file of the run directory is listed in `manifest.json` with its sha256 and size (written last, so it covers this file and proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from `verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.

| Artifact | Purpose |
| --- | --- |
| proof_bundle.json | The Proof Bundle: every stage record, gate and the verdict |
| PROOF.md | Human-readable rendering of the Proof Bundle |
| manifest.json | sha256 and size of every artifact (this file) |
| task.frozen.json | Frozen task: statement, policy and repository digests |
| spec.json | Specification and contract written before any code |
| contract_audit.json | Contract audit: claimed conflicts and the result of executing their witness programs |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
| ledger.jsonl | Append-only ledger journal: reservations before each request, call records as they complete |
