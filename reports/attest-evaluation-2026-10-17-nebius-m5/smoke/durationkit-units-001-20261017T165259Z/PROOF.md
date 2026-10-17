# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261017T165259Z` · profile `submission-smoke` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T16:52:59.556378+00:00, finished 2026-10-17T16:58:33.309264+00:00.

**Hold this patch.** 11 of the 24 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request. The arbiter classified every failing sealed test as defective, and the corrected tests pass on the candidate and still fail on the base; the hold stands because the sealed failure also skipped the mutation check (E6).

Key evidence (E1): test_whitespace_between_number_and_unit_is_rejected: AssertionError: 'unsupported duration' not found in "unknown unit: ' '"



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: child process nonzero exit: test_whitespace_between_number_and_unit_is_rejected exit 1, test_empty_string_raises_value_error exit 1, test_whitespace_only_string_raises_value_error exit 1, test_negative_number_raises_value_error exit 1, test_fractional_number_raises_value_error exit 1, test_unknown_unit_raises_value_error exit 
Warnings: arbitration (advisory): all 11 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base, but the sealed failure skipped the mutation check, so there is no mutation score and the verdict is not cleared; a rerun seals fresh tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 11 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 9 of 24 failed on the unmodified base; 13 of 24 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 11 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base, but the sealed failure skipped the mutation check, so there is no mutation score and the verdict is not cleared; a rerun seals fresh tests |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `c7ff3a24-1487-49e0-be4a-e9b3f3f259b9`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `21bd3fa853041909` (35 package sources; git commit 2cbaf9413d709d973408ca41e06253bdca66892c). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/attest-eval-frozen/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms) in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings, reject malformed input with ValueError, and reject non-string input with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (ASCII digits) representing sec | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only.; ValueError: if any component contains a negative number (leading '-').; V |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. Return type is float for every accepted input.
7. ValueError for empty string '' and whitespace-only '   '.
8. ValueError for negative numbers: '-1h'.
9. ValueError for fractional numbers: '1.5h'.
10. ValueError for unknown units: '1x'.
11. ValueError for repeated units: '1h1h'.
12. ValueError for components out of descending order: '30m1h'.
13. ValueError for unit without a number: 'h'.
14. ValueError for number without a unit when other components have units (i.e., trailing number): '1h30'.
15. ValueError for completely malformed text: 'abc'.
16. TypeError for non-string input such as 90 or None.
17. Existing tests in tests/test_parse.py must continue to pass without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d287d9db561860f08667385451985e236f2dc4e8dccb33826a8bb87986be5194`, 24 test methods, sealed at 2026-10-17T16:54:40.741197+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 24 methods: ERROR 9): 9 of 24 methods failing, 15 passing; operation `01a14ac9-6d63-75c2-afbb-db351394d7e2`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationSealed.test_combined_components_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_completely_malformed_text_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_components_out_of_descending_order_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_empty_string_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_fractional_number_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_negative_number_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_non_string_input_raises_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_none_input_raises_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_number_without_unit_when_other_components_have_units_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_with_surrounding_whitespace_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_repeated_unit_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_various_inputs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_unit_without_preceding_number_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_unknown_unit_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_allowed_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_between_number_and_unit_is_rejected | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_only_string_raises_value_error | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_zero_and_zero_seconds_component | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,72 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer (ASCII digits) representing seconds, with optional surrounding whitespace.
+    Also accepts one or more components, each a non-negative integer immediately followed by a unit suffix (d, h, m, s, ms),
+    components ordered from largest to smallest unit (d > h > m > s > ms), each unit used at most once,
+    with optional whitespace around the whole string and between components.
+    Returns the sum of each component converted to seconds (1d=86400, 1h=3600, 1m=60, 1s=1, 1ms=0.001).
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("duration string is empty")
+    if stripped.isdigit():
+        return float(stripped)
+    i = 0
+    total = 0.0
+    seen_units = set()
+    last_order = float('inf')
+    order_map = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    while i < len(stripped):
+        # Skip whitespace between components
+        while i < len(stripped) and stripped[i].isspace():
+            i += 1
+        if i >= len(stripped):
+            break
+        # Parse number
+        if not stripped[i].isdigit():
+            raise ValueError("expected number at start of component")
+        start = i
+        while i < len(stripped) and stripped[i].isdigit():
+            i += 1
+        num_str = stripped[start:i]
+        num = int(num_str)
+        # Expect unit directly after number (no whitespace allowed)
+        if i >= len(stripped):
+            raise ValueError("missing unit after number")
+        # Parse unit
+        if stripped[i] == 'm':
+            # Check for 'ms'
+            if i + 1 < len(stripped) and stripped[i + 1] == 's':
+                unit = 'ms'
+                i += 2
+            else:
+                unit = 'm'
+                i += 1
+        elif stripped[i] in 'dhms':
+            unit = stripped[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit: {stripped[i]!r}")
+        # Process component
+        if unit in seen_units:
+            raise ValueError(f"repeated unit: {unit}")
+        seen_units.add(unit)
+        curr_order = order_map[unit]
+        if curr_order >= last_order:
+            raise ValueError("units not in strictly descending order")
+        last_order = curr_order
+        # Convert to seconds
+        if unit == 'd':
+            total += num * 86400
+        elif unit == 'h':
+            total += num * 3600
+        elif unit == 'm':
+            total += num * 60
+        elif unit == 's':
+            total += num
+        elif unit == 'ms':
+            total += num * 0.001
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (65 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (11 of 24 methods: FAIL 11). Operation `01a14acc-1a32-7584-b2e3-39d146bf9588`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14acc-3d8e-7745-8867-c88d134fee11`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_whitespace_between_number_and_unit_is_rejected exit 1, test_empty_string_raises_value_error exit 1, test_whitespace_only_string_raises_value_error exit 1, test_negative_number_raises_value_error exit 1, test_fractional_number_raises_value_error exit 1, test_unknown_unit_raises_value_error exit  |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
- E1 `test_whitespace_between_number_and_unit_is_rejected`: FAIL; AssertionError: 'unsupported duration' not found in "unknown unit: ' '"; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: ... whitespace is allowed around the whole string and between components (but not between a number and its unit).' No message wording is specified.
- E1 `test_empty_string_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'duration string is empty'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: empty or whitespace-only input.' No message wording is specified.
- E1 `test_whitespace_only_string_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'duration string is empty'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: empty or whitespace-only input.' No message wording is specified.
- E1 `test_negative_number_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'expected number at start of component'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: negative numbers (leading '-').' No message wording is specified.
- E1 `test_fractional_number_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in "unknown unit: '.'"; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: fractional numbers (decimal point).' No message wording is specified.
- E1 `test_unknown_unit_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in "unknown unit: 'x'"; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: unknown units.' No message wording is specified.
- E1 `test_repeated_unit_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'repeated unit: h'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: repeated units.' No message wording is specified.
- E1 `test_components_out_of_descending_order_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'units not in strictly descending order'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: components out of descending order.' No message wording is specified.
- E1 `test_unit_without_preceding_number_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'expected number at start of component'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: a unit without a number.' No message wording is specified.
- E1 `test_number_without_unit_when_other_components_have_units_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'missing unit after number'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: number without a unit when other components have units (i.e., trailing number).' No message wording is specified.
- E1 `test_completely_malformed_text_raises_value_error`: FAIL; AssertionError: 'unsupported duration' not found in 'expected number at start of component'; arbiter: Defective test, by the arbiter; contract basis: Contract says: 'Reject with ValueError: any other malformed text.' No message wording is specified.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff extends parse_duration to handle compound durations with units d, h, m, s, ms in strictly descending order, preserves the existing plain-integer fast path, and rejects all specified malformed inputs with ValueError (e.g., empty string, negative numbers, unknown units, repeated units, out-of-order units, missing numbers, whitespace between number and unit). The implementation passes all existing tests (6/6) and adds no public API changes.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 11 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base, but the sealed failure skipped the mutation check, so there is no mutation score and the verdict is not cleared; a rerun seals fresh tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 11, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_whitespace_between_number_and_unit_is_rejected | test_defect | The test asserts that the ValueError message contains 'unsupported duration', but the contract only requires a ValueError be raised for whit | Contract says: 'Reject with ValueError: ... whitespace is allowed around the whole string and between components (but not between a number a |
| test_empty_string_raises_value_error | test_defect | The test expects the ValueError message to contain 'unsupported duration', but the contract only requires a ValueError for empty or whitespa | Contract says: 'Reject with ValueError: empty or whitespace-only input.' No message wording is specified. |
| test_whitespace_only_string_raises_value_error | test_defect | Same as empty string: the test checks for a specific message not required by the contract. | Contract says: 'Reject with ValueError: empty or whitespace-only input.' No message wording is specified. |
| test_negative_number_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for negative numbers. The candidate rais | Contract says: 'Reject with ValueError: negative numbers (leading '-').' No message wording is specified. |
| test_fractional_number_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for fractional numbers. The candidate ra | Contract says: 'Reject with ValueError: fractional numbers (decimal point).' No message wording is specified. |
| test_unknown_unit_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for unknown units. The candidate raises  | Contract says: 'Reject with ValueError: unknown units.' No message wording is specified. |
| test_repeated_unit_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for repeated units. The candidate raises | Contract says: 'Reject with ValueError: repeated units.' No message wording is specified. |
| test_components_out_of_descending_order_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for components out of descending order.  | Contract says: 'Reject with ValueError: components out of descending order.' No message wording is specified. |
| test_unit_without_preceding_number_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for a unit without a number. The candida | Contract says: 'Reject with ValueError: a unit without a number.' No message wording is specified. |
| test_number_without_unit_when_other_components_have_units_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for a trailing number without a unit. Th | Contract says: 'Reject with ValueError: number without a unit when other components have units (i.e., trailing number).' No message wording  |
| test_completely_malformed_text_raises_value_error | test_defect | The test expects 'unsupported duration' in the message, but the contract only requires a ValueError for any other malformed text. The candid | Contract says: 'Reject with ValueError: any other malformed text.' No message wording is specified. |

- `sealed` corrected re-run: candidate OK (24 of 24 methods, each in its own process); base FAILED (9 of 24 methods: ERROR 9); cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 1662 | 0 | 0.006723 | 6.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1888 | 6745 | 0 | 0.006637 | 63.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1790 | 103 | 0 | 0.000630 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1884 | 90 | 0 | 0.000646 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2085 | 115 | 0 | 0.000729 | 3.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2289 | 7787 | 0 | 0.007695 | 57.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2492 | 13158 | 0 | 0.012590 | 83.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3555 | 187 | 0 | 0.001235 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3813 | 979 | 0 | 0.002025 | 9.4s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2986 | 5212 | 0 | 0.018622 | 15.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-sealed | default | 5551 | 4747 | 0 | 0.019792 | 12.9s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 30070/40785/0; USD: 0.077324.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ac8-13f0-7790-bc8e-02f9023033ee | SUCCESS | 0 | 0.797s | retained | off | 0.0028287499999999997 |
| red-1 | 01a14ac9-6d63-75c2-afbb-db351394d7e2 | SUCCESS | 0 | 5.218s | disposable | off | 0.04456137 |
| impl-tests-6 | 01a14acb-e7ec-7603-b41c-33da351e55fd | SUCCESS | 0 | 0.777s | disposable | off | 0.00286009 |
| verify | 01a14acc-1a32-7584-b2e3-39d146bf9588 | SUCCESS | 0 | 5.244s | disposable | off | 0.04450779 |
| existing | 01a14acc-3d8e-7745-8867-c88d134fee11 | SUCCESS | 0 | 2.105s | disposable | off | 0.01521955 |
| arbitrate-sealed-candidate | 01a14acc-d48a-73ae-ac7c-f00eaede5ce1 | SUCCESS | 0 | 5.251s | disposable | off | 0.04467095 |
| arbitrate-sealed-base | 01a14acc-fa10-70ef-8ebb-9ff857cada5a | SUCCESS | 0 | 5.149s | disposable | off | 0.044288900000000006 |

Sandbox operations: 7, total guest duration 24.541s, retained images ['c7ff3a24-1487-49e0-be4a-e9b3f3f259b9'].

## 11. Limitations of this bundle
- Profile 'submission-smoke': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
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
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
