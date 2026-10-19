# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: ERROR**  
Run `durationkit-units-001-attest-a1-20261019T142607972621Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T14:26:07.974126+00:00, finished 2026-10-19T14:31:43.592156+00:00.

**This run did not complete.** The sandbox executor failed at stage implement. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): sandbox executor error after 6 model call(s): a sandbox operation's outcome is uncertain; it was not replayed [ref 9236e245]



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: a sandbox operation's outcome is uncertain; it was not replayed [ref 9236e245]


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 8 of 22 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the sandbox executor at stage implement; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 8 of 22 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage implement: a sandbox operation's outcome is uncertain; it was not replayed [ref 9236e245] |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6df49ea6-b73a-408a-a128-5d86563ca814`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.7.0 revision `f836cfd0154faa87` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision6-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer representing seconds or a sequence of non-negative integer components with lowercase units d, h, m, s, and ms. Unit components must occur at most once each and in strictly descending order, with optional whitespace around the input and between components but none between a number and its unit. Return total seconds as a float, preserve existing valid behavior and tests, and reject invalid strings with ValueError and non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Remain available through `from durationkit import parse_duration` and defined in durationkit.parse. After removing surrounding whitespace, accept either one uns | TypeError: text is not a string, including integers, floats, None, bytes, and containers.; ValueError: input is empty or consists only of whitespace.; ValueErro |

Acceptance criteria:
AC1. 1. All existing tests in tests/ pass unchanged using `python -m unittest discover -s tests -t . -v`; the public import `from durationkit import parse_duration` continues to work.
AC2. 2. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0, and '0007' returns 7.0.
AC3. 3. Each individual unit works: '2d' returns 172800.0, '3h' returns 10800.0, '15m' returns 900.0, '45s' returns 45.0, and '500ms' returns 0.5.
AC4. 4. Descending combinations work: '1h30m' returns 5400.0, '2d4h' returns 187200.0, '1m1s' returns 61.0, '1s500ms' returns 1.5, and '1d1h1m1s1ms' returns approximately 90061.001. Non-integral results may be checked with an absolute tolerance of 1e-9 for these examples.
AC5. 5. Units may be skipped: '1d1s' returns 86401.0 and '1h1ms' returns approximately 3600.001.
AC6. 6. Zero and leading-zero components are accepted: '0s', '0ms', and '0d0h0m0s0ms' return 0.0; '01h030m' returns 5400.0.
AC7. 7. Component values are not restricted to conventional clock ranges: '90m' returns 5400.0 and '1500ms' returns 1.5.
AC8. 8. Surrounding and inter-component whitespace is accepted: ' 1h 30m ' and '\t1h\n30m\r' return 5400.0. Python whitespace such as U+00A0 is also accepted in these positions.
AC9. 9. Every accepted input returns a float, including zero, plain integers, whole-second unit expressions, and millisecond expressions.
AC10. 10. Empty and whitespace-only strings, including '', '   ', and '\t\n', raise ValueError.
AC11. 11. Invalid numeric syntax raises ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s', and '1_000s'.
AC12. 12. Unknown, incorrectly cased, or missing-number units raise ValueError, including '1x', '1H', '1MS', 'h', 'ms', and 'abc'.
AC13. 13. Repeated or out-of-order units raise ValueError, including '1h1h', '1ms1ms', '30m1h', '1ms1s', '0s0h', and '0h0h'.
AC14. 14. Incomplete components, mixed forms, internal numeric whitespace, and extra text raise ValueError, including '1h30', '1 30m', '1 h', '1 m s', '1 0s', '1h,30m', and '1s!'.
AC15. 15. Non-string inputs including 90, 1.5, None, b'90', [], and {} raise TypeError.
AC16. 16. Non-decimal numeric characters raise ValueError both alone and as component numbers; examples include 'Ⅻ', 'Ⅻh', '½s', '①s', and '²s'. Tests must not depend on acceptance or rejection of non-ASCII Unicode decimal digits such as Arabic-Indic or fullwidth digits.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are mutually compatible and can be satisfied by changes confined to durationkit/**. The unchanged tests and public export impose no conflicting behavior; Unicode decimal-digit handling and numeric magnitude limits remain explicitly unspecified. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `09818549a1791ebc8532aef4325f7935dbecb8657c6ee07c001b72dbecf2f8af`, 22 test methods, sealed at 2026-10-19T14:29:50.568683+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (8 of 22 methods: ERROR 8): 8 of 22 methods failing, 14 passing; operation `01a15491-91ea-768e-b000-7997c847c718`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_have_no_clock_range | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_descending_unit_combinations | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_each_individual_unit | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_extra_text_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_fraction_exponent_and_separator_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_incomplete_or_mixed_components_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zero_components | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_non_decimal_numeric_characters_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_rejected_even_with_zero | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_public_import_parses_existing_example | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_skipped_units | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_and_uppercase_units_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_around_and_between_components | ERROR (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_numbers_or_before_units_rejected | ok (1 ev) | - |
| test_sealed.ParseDurationAcceptanceTests.test_zero_valued_components | ERROR (1 ev) | - |


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
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10756 | 1515 | 0 | - | 103.0s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13130 | 90 | 0 | - | 38.5s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11181 | 2648 | 0 | - | 62.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11035 | 101 | 7168 | - | 29.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22771 | 727 | 11008 | - | 47.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11478 | 93 | 7168 | - | 31.0s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 80351/5174/25344; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1548e-5659-70f2-94cd-0d5fe02f083e | SUCCESS | 0 | 0.804s | retained | off | 0.00288119 |
| red-1 | 01a15491-91ea-768e-b000-7997c847c718 | SUCCESS | 0 | 4.998s | disposable | off | 0.04185871 |
| impl-tests-3 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 3, total guest duration 5.802s, retained images ['6df49ea6-b73a-408a-a128-5d86563ca814'].

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
Component: sandbox executor; stage: implement; model calls 6 (0 failed); sandbox operations 3; committed cost USD 0.0; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- a sandbox operation's outcome is uncertain; it was not replayed [ref 9236e245]

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
