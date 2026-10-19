# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: ERROR**  
Run `durationkit-units-001-attest-a1-20261019T145258760882Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T14:52:58.761999+00:00, finished 2026-10-19T14:55:51.288091+00:00.

**This run did not complete.** The inference provider failed at stage error. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): inference provider error after 2 model call(s): model provider: the inference outcome is uncertain (transport failure); the request was not retried [ref 1a80f2b9] (outcome uncertain; not retried)



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: model provider: the inference outcome is uncertain (transport failure); the request was not retried [ref 1a80f2b9] (outcome uncertain; not retried)


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The run failed in the inference provider at stage error; nothing was retried (E7).

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
| E7 | Failure record | FAIL | bound | inference provider failed at stage error: model provider: the inference outcome is uncertain (transport failure); the request was not retried [ref 1a80f2b9] (outcome uncertain; not retried) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `87c0821b-c60a-4bb4-8f21-3822df636c56`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.7.0 revision `f836cfd0154faa87` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision6-repairs-2026-10-19/evaluation-codex-4/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer number of seconds or a sequence of integer-and-unit components using d, h, m, s and ms. Require unique units in strictly descending order, allow whitespace around the input and between complete components, and return total seconds as a float. Preserve the existing public import and tests, reject malformed strings with ValueError, and reject non-string arguments with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration (implemented in durationkit.parse) | parse_duration(text: str) -> float | Accept a string after removing surrounding whitespace. The entire remaining string must be either an unsigned integer interpreted as seconds, or one or more com | TypeError: text is not a string.; ValueError: text is empty or contains only whitespace.; ValueError: a number has a sign, decimal point, exponent, separator, o |

Acceptance criteria:
AC1. 1. Preserve the public import `from durationkit import parse_duration` and the exact callable signature `parse_duration(text: str) -> float`.
AC2. 2. All existing tests in tests/ pass without modification.
AC3. 3. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0, and '0007' returns 7.0.
AC4. 4. Single components return the expected seconds: '2d' → 172800.0, '3h' → 10800.0, '15m' → 900.0, '45s' → 45.0, and '500ms' → 0.5.
AC5. 5. Ordered combinations work: '1h30m' → 5400.0, '2d4h' → 187200.0, '1m1s' → 61.0, '1s500ms' → 1.5, and '1d1h1m1s1ms' → approximately 90061.001. Use floating-point tolerance for fractional totals.
AC6. 6. Skipped units and unrestricted component magnitudes are accepted: '1d1s' returns 86401.0, '90m' returns 5400.0, and '1500ms' returns 1.5.
AC7. 7. Leading zeros and zero-valued components are accepted: '001h030m' returns 5400.0, '0s' returns 0.0, and '0d0h0m0s0ms' returns 0.0.
AC8. 8. Surrounding and inter-component whitespace is accepted, including spaces, tabs and newlines: ' 1h 30m ' and '\t1h\n30m\t' each return 5400.0.
AC9. 9. Whitespace inside components is rejected with ValueError, including '1 h', '1m s', and '1 0s'.
AC10. 10. Empty and whitespace-only strings raise ValueError, including '', '   ', and '\t\n'.
AC11. 11. Signed, fractional and other numeric notation raises ValueError, including '-1', '-1h', '+1', '+1h', '1.5h', '1e3s', and '1_000s'.
AC12. 12. Unknown units, wrong case and missing numbers raise ValueError, including '1x', '1H', '1sec', 'h', and 'ms'.
AC13. 13. Repeated or out-of-order units raise ValueError, including '1h1h', '1ms1ms', '30m1h', '1ms1s', '0s0m', and '0h0h'.
AC14. 14. Mixed bare numbers and components, punctuation, and arbitrary malformed text raise ValueError, including '1h30', '30 1h', '1h,30m', and 'abc'.
AC15. 15. Non-decimal numeric characters raise ValueError, including 'Ⅳh', '½h', '①h', and '²'. Tests must not require either acceptance or rejection of non-ASCII Unicode decimal digits such as '١٢h' or '１２h'.
AC16. 16. Non-string arguments raise TypeError, including 90, None, 1.5, True, b'90', and ['90'].
AC17. 17. Every accepted input returns a float, including plain integers, zero, whole-second unit totals and millisecond totals.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10756 | 1470 | 0 | - | 57.8s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | - | - | - | - | 105.5s | error |

Model calls: 2 (1 failed, 0 malformed); tokens in/out/cached 10756/1470/0; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a154a6-e9af-73a2-a2fa-6e0e267948a3 | SUCCESS | 0 | 0.752s | retained | off | 0.0028764299999999997 |

Sandbox operations: 1, total guest duration 0.752s, retained images ['87c0821b-c60a-4bb4-8f21-3822df636c56'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: inference provider; stage: error; model calls 2 (1 failed); sandbox operations 1; committed cost USD 0.0; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- model provider: the inference outcome is uncertain (transport failure); the request was not retried [ref 1a80f2b9] (outcome uncertain; not retried)

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
