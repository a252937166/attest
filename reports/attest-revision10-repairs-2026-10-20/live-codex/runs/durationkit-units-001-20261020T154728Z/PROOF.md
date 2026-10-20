# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261020T154728Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-20T15:47:28.627802+00:00, finished 2026-10-20T15:57:16.769991+00:00.

**Hold this patch.** 1 of the 18 sealed acceptance tests fail on the candidate because the candidate's behaviour contradicts the test written before the patch (an assertion failed or an exception was raised; neither the exception's type nor its frame tells the test from the candidate). The arbiter classified the failing test(s) as defective and its corrected tests pass on the candidate and still fail on the unmodified base. A sealed test is the pre-registered acceptance criterion, so Attest never overrides it on a model's judgement: the hold stands and the arbiter's view, the original test and the corrected test are all recorded for you (E6).

Key evidence (E6): 1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded)



What to do: Compare the original sealed test with the arbiter's correction and the contract; decide which encodes the requirement. If the correction is right, accept the patch on that basis and tighten the task statement so the next sealer reads it the same way.

Reasons: child process nonzero exit: test_whitespace_between_complete_components exit 1
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; arbitration (validated corrections re-run their gates): 1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded)

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 1 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 6 of 18 failed on the unmodified base; 17 of 18 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | 1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `7236aa7b-1100-430f-8d53-3fb5eae59b1f`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 775248c2f87d66e5fe4f3802b1caf85024f62a49). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/r10/wt-775248c/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; a request that was never sent (its connection, proxy tunnel or TLS handshake failed before any byte of it was written) sent again at most 2 times after 2/6 s, each attempt recorded; transport-uncertain failures (the request was written) never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 6, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer count of seconds or one or more integer-and-unit components using d, h, m, s and ms. Components must have distinct units in strictly descending duration order, with whitespace allowed only around the input and between complete components. Return total seconds as a float, preserve the public import and existing tests, and reject invalid inputs with the specified exception types.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also defined in durationkit.parse. Require a string, then ignore surrounding whitespace. Accept either an uninterrupted non-negative integer representing second | TypeError: input is not a string, including integers, floats, bytes and None.; ValueError: input is empty or contains only whitespace.; ValueError: any number i |

Acceptance criteria:
AC1. 1. Preserve the import from durationkit import parse_duration and its signature parse_duration(text: str) -> float.
AC2. 2. All existing tests in tests/ pass without modification.
AC3. 3. Plain integers remain seconds: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0 and '0007' returns 7.0.
AC4. 4. Single components return the correct seconds: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0 and '500ms' -> 0.5.
AC5. 5. Descending combinations work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5 and '1d1h1m1s1ms' -> 90061.001. Compare non-integral results with an appropriate floating-point tolerance.
AC6. 6. Surrounding and inter-component whitespace, including spaces, tabs and newlines, is accepted: ' 1h 30m ' and '\t1h\n30m\r' each return 5400.0.
AC7. 7. Zero and leading-zero components are accepted: '0s' returns 0.0, '0d0h0m0s0ms' returns 0.0 and '01h003m' returns 3780.0.
AC8. 8. Component values have no clock-field limits: '90m' returns 5400.0 and '1500ms' returns 1.5.
AC9. 9. Every accepted input returns a float, including zero and whole-second results.
AC10. 10. Empty and whitespace-only strings raise ValueError, including '', '   ' and '\t\n'.
AC11. 11. Invalid numeric forms raise ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s' and '1_000s'.
AC12. 12. Unknown or incorrectly cased units and missing numbers raise ValueError, including '1x', '1H', '1MS', 'h', 'ms' and 'abc'.
AC13. 13. Repeated units raise ValueError, including '1h1h', '1ms2ms' and '0s0s'.
AC14. 14. Ascending or otherwise out-of-order components raise ValueError, including '30m1h', '1ms1s', '1s1m' and '0ms0s'.
AC15. 15. Whitespace inside a component or number raises ValueError, including '1 h', '1\tms', '1 0s' and '9 0'.
AC16. 16. Mixed bare integers and components, separators and trailing junk raise ValueError, including '1h30', '90 1s', '1h,30m', '1h30m!', '1mss' and '1h garbage'.
AC17. 17. Non-decimal numeric characters raise ValueError in both bare and component forms, including 'Ⅳ', 'Ⅳh', '½', '½s', '①' and '①m'.
AC18. 18. Non-string inputs raise TypeError, including 90, 1.5, None, True, b'90' and an empty list.
AC19. 19. Tests impose no acceptance or rejection requirement on non-ASCII Unicode decimal digits, including Arabic-Indic and fullwidth digits.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable within durationkit/**. The existing tests and fixed public import are compatible with the required parsing rules, error cases, and float results. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `4ad9fec6e65ada0efe92e24a65cb7fb3b093275606189435c7c62bf489a8e75a`, 18 test methods, sealed at 2026-10-20T15:51:29.388415+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (6 of 18 methods: ERROR 6): 6 of 18 methods failing, 12 passing; operation `01a15a02-9820-76b4-9b83-9eb30288957d`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_accepted_results_are_floats | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_have_no_clock_limits | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_descending_adjacent_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_or_whitespace_only_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_invalid_numeric_forms_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_mixed_bare_integers_and_components_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_decimal_numeric_characters_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_public_signature_and_import | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_separators_and_trailing_junk_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_unit_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_cased_or_numberless_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_complete_components | ERROR (1 ev) | FAIL (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_numbers_or_components_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_and_leading_zero_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,39 @@
 """Duration parsing."""
+
+import re
+
+
+_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")
+_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_ORDER = {unit: index for index, unit in enumerate(_UNITS)}
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse integer seconds or descending integer-and-unit components."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("duration must not be empty")
+    if re.fullmatch(r"[0-9]+", stripped):
+        return float(stripped)
+
+    total = 0.0
+    position = 0
+    previous_order = -1
+    while position < len(stripped):
+        match = _COMPONENT.match(stripped, position)
+        if match is None:
+            raise ValueError(f"unsupported duration: {text!r}")
+        number, unit = match.groups()
+        order = _ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"duration units are repeated or out of order: {text!r}")
+        total += int(number) * _UNITS[unit]
+        previous_order = order
+        position = match.end()
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (32 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| durationkit/parse.py | 6 | dynamic code or decoded payload | _COMPONENT = re.compile(r"([0-9]+)(ms\|[dhms])") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (1 of 18 methods: FAIL 1). Operation `01a15a05-9346-73fc-be78-b4c07a9abf91`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| supervisor_cleanup_complete | pass |
| nonce_matches | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a15a06-2603-70ef-b9b3-b94174347b04`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_whitespace_between_complete_components exit 1 |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
- E1 `test_whitespace_between_complete_components`: FAIL; AssertionError: 93780.0 != 90180.0; first `93780.0` vs second `90180.0` (the test's argument order decides which is the actual value); arbiter: Defective test, by the arbiter; contract basis: The contract defines d=86400, h=3600 and m=60 seconds and permits Python str.isspace() whitespace around inputs and between complete components.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")` parses supported components, `order <= previous_order` rejects repeated or unordered units, and `isspace()` permits inter-component whitespace while preserving type checks and float results. Existing tests were unchanged; observed outputs report six passing tests and successful contract examples, supporting the implementer's summary.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded) (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_whitespace_between_complete_components | test_defect | The whitespace-delimited input contains 1 day, 2 hours and 3 minutes, totaling 86400 + 7200 + 180 = 93780 seconds. The test incorrectly expe | The contract defines d=86400, h=3600 and m=60 seconds and permits Python str.isspace() whitespace around inputs and between complete compone |

- `sealed` corrected re-run: candidate OK (18 of 18 methods, each in its own process); base FAILED (6 of 18 methods: ERROR 6); validated=False; sealed assertion or exception failure: never overridden, the hold stands

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | - | - | - | - | 5.0s | not sent |
| codex_gateway:gpt-6-astra | spec | spec | low | 11129 | 1441 | 0 | - | 59.5s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13432 | 83 | 0 | - | 21.6s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11108 | 3082 | 0 | - | 65.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10967 | 85 | 0 | - | 16.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22566 | 678 | 11008 | - | 38.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11385 | 108 | 0 | - | 40.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11624 | 115 | 0 | - | 32.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12035 | 635 | 0 | - | 25.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12611 | 147 | 7168 | - | 20.3s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12429 | 141 | 0 | - | 24.7s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-sealed | medium | 14293 | 1709 | 0 | - | 58.6s | ok |

Model calls: 12 (1 failed, 0 malformed); tokens in/out/cached 143579/8224/18176; Inference USD: n/a (development gateway allowance, not billed in USD); 1 attempt(s) were never sent (the connection failed first) and cost nothing.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a159ff-3869-7317-9b71-38d718d0c6ef | SUCCESS | 0 | 34.981s | retained | off | 0.00285333 |
| red-1 | 01a15a02-9820-76b4-9b83-9eb30288957d | SUCCESS | 0 | 11.607s | disposable | off | 0.037246879999999996 |
| impl-tests-3 | 01a15a04-44e7-7543-b83f-8ba82120c65b | SUCCESS | 0 | 0.837s | disposable | off | 0.00287794 |
| impl-python-5 | 01a15a05-360d-71d5-a050-fd3da2855327 | SUCCESS | 0 | 0.665s | disposable | off | 0.0016135000000000001 |
| verify | 01a15a05-9346-73fc-be78-b4c07a9abf91 | SUCCESS | 0 | 4.524s | disposable | off | 0.03762967 |
| existing | 01a15a06-2603-70ef-b9b3-b94174347b04 | SUCCESS | 0 | 2.179s | disposable | off | 0.015213130000000002 |
| arbitrate-sealed-candidate | 01a15a07-8564-74a0-b815-bd1384535665 | SUCCESS | 0 | 4.512s | disposable | off | 0.03741116 |
| arbitrate-sealed-base | 01a15a08-0029-70c8-a616-6965085667d5 | SUCCESS | 0 | 4.61s | disposable | off | 0.03745912 |

Sandbox operations: 8, total guest duration 63.915s, retained images ['7236aa7b-1100-430f-8d53-3fb5eae59b1f'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
