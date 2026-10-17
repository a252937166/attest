# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261017T170038Z` · profile `submission-smoke` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:00:38.162842+00:00, finished 2026-10-17T17:07:23.748863+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter; the corrected tests pass on the candidate and still fail on the unmodified base. Arbitration is advisory, so the hold stands until a human confirms. Defect kinds: wrong expected value.

Key evidence (E6): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests



What to do: Check the arbiter's corrections in E6 (original and corrected tests are both kept). If you agree, accept the patch on that basis or re-run with arbitration in apply mode.

Reasons: adversarial suite binding failed: child process nonzero exit: test_space_between_number_and_unit_multiple_rejected exit 1; model-written adversarial tests failed: 1 of 12 (test_breaker.TestParseDurationBreaker.test_space_between_number_and_unit_multiple_rejected); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 29 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 12 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 17 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 3 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 12 of 29 failed on the unmodified base; 29 of 29 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 12 one-line mutants caught, 3 survived, 0 unknown; score 0.75 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 11 of 12 pass; 1 failing: test_space_between_number_and_unit_multiple_rejected; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `172364e3-f8cc-4863-a24e-c419dc4950a5`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `d34d3830d3267ef8` (35 package sources; git commit 15e145c13578f4da19c2111e86b85b6e55900602). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/attest-eval-frozen/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non‑negative integer followed by a unit (d, h, m, s, ms), in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings, reject malformed input with ValueError, and reject non‑string input with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non‑negative integer (ASCII digits only) optionally  | TypeError: if text is not a string.; ValueError: if text is empty or whitespace‑only after stripping.; ValueError: if any component contains a negative number ( |

Acceptance criteria:
1. 1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. 2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. 3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. 4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. 5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. 6. The return type is float for every accepted input.
7. 7. ValueError is raised for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
8. 8. TypeError is raised for non‑string input such as 90 or None.
9. 9. Existing tests in tests/test_parse.py must continue to pass without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `ebcfb23c9004b64c9b1ffe81a4df6fcd7e5e569580a0140d1d5326c92b80924d`, 29 test methods, sealed at 2026-10-17T17:03:30.453739+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 29 methods: ERROR 12): 12 of 29 methods failing, 17 passing; operation `01a14ad1-7c59-71ac-89ef-9d674280d590`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationExtended.test_combined_1d1h1m1s1ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_combined_1h30m | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_combined_1m1s | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_combined_1s500ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_combined_2d4h | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_whitespace_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_return_type_float | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_type_error_non_string_int | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_type_error_non_string_none | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_duplicate_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_empty_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_fractional_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_missing_number_before_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_negative_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_non_ascii_or_other_chars | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_trailing_number_without_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_units_not_descending | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_unknown_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_value_error_whitespace_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_around_and_between_allowed | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_between_number_and_unit_not_allowed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_zero_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_zero_with_unit_seconds | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,84 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer (as seconds) or a sequence of
+    components like ``'1h30m'`` with units d, h, m, s, ms in descending order.
+    Whitespace is allowed around the string and between components.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
-    stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    s = text.strip()
+    if not s:
+        raise ValueError(f"empty duration: {text!r}")
+
+    # Plain integer case (only digits)
+    if s.isdigit():
+        return float(s)
+
+    # Mapping of unit to seconds and order for descending check
+    unit_to_seconds = {
+        'd': 86400.0,
+        'h': 3600.0,
+        'm': 60.0,
+        's': 1.0,
+        'ms': 0.001,
+    }
+    unit_order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+
+    total = 0.0
+    seen_units = set()
+    prev_order = 5  # larger than any unit order
+    i = 0
+    n = len(s)
+
+    while i < n:
+        # Skip whitespace between components
+        if s[i].isspace():
+            i += 1
+            continue
+
+        # Parse number (one or more digits)
+        if not s[i].isdigit():
+            raise ValueError(f"invalid duration format at position {i}: {text!r}")
+        start = i
+        while i < n and s[i].isdigit():
+            i += 1
+        number_str = s[start:i]
+        # Leading zeros are fine; convert to int
+        try:
+            number = int(number_str)
+        except ValueError:
+            raise ValueError(f"invalid number in duration: {text!r}")
+
+        # Parse unit
+        if i >= n:
+            raise ValueError(f"missing unit after number in duration: {text!r}")
+        # Check for 'ms' first (two chars)
+        if s[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif s[i] in unit_to_seconds:
+            unit = s[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit in duration: {text!r}")
+
+        # Validate no whitespace between number and unit (already ensured because we didn't skip whitespace)
+        # But we already skipped whitespace before number; after number we went straight to unit.
+        # If there was whitespace, the unit wouldn't match.
+
+        # Check unit duplication
+        if unit in seen_units:
+            raise ValueError(f"duplicate unit '{unit}' in duration: {text!r}")
+        seen_units.add(unit)
+
+        # Check descending order
+        cur_order = unit_order[unit]
+        if cur_order >= prev_order:
+            raise ValueError(f"units not in descending order in duration: {text!r}")
+        prev_order = cur_order
+
+        # Add to total
+        total += number * unit_to_seconds[unit]
+
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (78 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (29 of 29 methods, each in its own process). Operation `01a14ad2-fef9-73cb-84eb-f7672063af4f`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14ad3-225a-712a-8223-e972468bda0d`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.75 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 12 methods: FAIL 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 9 killed, 3 survived, 0 unknown; mutation score 0.750 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-e24672cfa1 | durationkit/parse.py | 14 | remove `not` | killed | test_sealed.TestParseDurationExtended.test_plain_integer_value, test_sealed.TestParseDurationExtended.test_plain_integer | 01a14ad3-3c3a-77fb-ace6-5606132b6f93 |
| m02-f30929e892 | durationkit/parse.py | 29 | 4 -> 5 | killed | test_sealed.TestParseDurationExtended.test_single_component_days, test_sealed.TestParseDurationExtended.test_combined_2d | 01a14ad3-3c7d-7673-8134-6b9ba95a1bed |
| m03-d62ce0684d | durationkit/parse.py | 29 | 1 -> 2 | killed | test_sealed.TestParseDurationExtended.test_combined_1m1s, test_sealed.TestParseDurationExtended.test_combined_1d1h1m1s1m | 01a14ad3-3c82-703f-ba60-f6382718f133 |
| m04-7ddd9e093c | durationkit/parse.py | 33 | 5 -> 6 | survived |  | 01a14ad3-3d5d-72d2-8805-7de131321a31 |
| m05-1c7adbf18e | durationkit/parse.py | 40 | 1 -> 2 | killed | test_sealed.TestParseDurationExtended.test_whitespace_around_and_between_allowed | 01a14ad3-3c87-7491-bed3-eedc6a0181a7 |
| m06-408bf96b93 | durationkit/parse.py | 45 | raise -> pass | survived |  | 01a14ad3-3c34-7310-8f18-e5bed75e0c12 |
| m07-752250b412 | durationkit/parse.py | 48 | 1 -> 2 | killed | test_sealed.TestParseDurationExtended.test_zero_with_unit_seconds, test_sealed.TestParseDurationExtended.test_single_com | 01a14ad3-3c3c-7400-8302-13a14db25e6b |
| m08-ba00aa780f | durationkit/parse.py | 58 | raise -> pass | killed | test_sealed.TestParseDurationExtended.test_value_error_trailing_number_without_unit | 01a14ad3-3c8b-75fd-9d68-51a6883a09dc |
| m09-c815d9b385 | durationkit/parse.py | 60 | Add -> Sub | killed | test_sealed.TestParseDurationExtended.test_single_component_milliseconds, test_sealed.TestParseDurationExtended.test_com | 01a14ad3-6094-767c-a083-eb68f2fcbae0 |
| m10-c3a5ab96bf | durationkit/parse.py | 63 | In -> NotIn | killed | test_sealed.TestParseDurationExtended.test_zero_with_unit_seconds, test_sealed.TestParseDurationExtended.test_single_com | 01a14ad3-618d-742a-9f2c-aeaf260a8616 |
| m11-51bd35ec07 | durationkit/parse.py | 67 | raise -> pass | killed | test_sealed.TestParseDurationExtended.test_whitespace_between_number_and_unit_not_allowed, test_sealed.TestParseDuration | 01a14ad3-6200-71ce-8454-323e84463562 |
| m12-044e77bdf2 | durationkit/parse.py | 80 | GtE -> Gt | survived |  | 01a14ad3-6204-710e-aca8-68fca57d84b8 |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `5b90a6e71cc120bbcdf336676ce16dcf1b3a50e0310aa62116bc4a7de70aa674`): FAILED (1 of 12 methods: FAIL 1); binding FAILED; operation `01a14ad4-7701-7741-b0dd-e99a976ef991`. Notes: Targeted edge cases: plus sign, leading zeros, multiple/tabs whitespace, skipped units, zero values, duplicate zero units, large numbers, ms fractions, spaces between number and unit, trailing numbers, non-string types.

| Failing adversarial test | Outcome |
| --- | --- |
| test_space_between_number_and_unit_multiple_rejected | FAIL |

### Counterexamples
- E3 `test_space_between_number_and_unit_multiple_rejected`: FAIL; AssertionError: ValueError not raised; arbiter: Defective test, by the arbiter; contract basis: whitespace is allowed around the whole string and between components (but not between a number and its unit).

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff extends parse_duration to accept multi-component duration strings with units d, h, m, s, ms in descending order, while preserving the existing plain-integer behavior. All acceptance criteria are satisfied, existing tests pass, and no scope deviations are observed.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_space_between_number_and_unit_multiple_rejected | test_defect | The test expects ValueError for strings with multiple spaces between components (e.g., '1h  30m'), but the contract explicitly allows whites | whitespace is allowed around the whole string and between components (but not between a number and its unit). |

- `adversarial` corrected re-run: candidate OK (12 of 12 methods, each in its own process); base FAILED (6 of 12 methods: ERROR 6); cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 1709 | 0 | 0.006864 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1905 | 16000 | 0 | 0.014972 | 109.1s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1-repair | default | 1970 | 6111 | 0 | 0.006091 | 41.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1816 | 86 | 0 | 0.000622 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1910 | 95 | 0 | 0.000658 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2114 | 2887 | 0 | 0.003233 | 22.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2330 | 4622 | 0 | 0.004859 | 27.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3365 | 831 | 0 | 0.001757 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3626 | 960 | 0 | 0.001952 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 4345 | 137 | 0 | 0.001427 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 4606 | 136 | 0 | 0.001504 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 2721 | 8143 | 0 | 0.008145 | 61.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3085 | 5485 | 0 | 0.019540 | 16.3s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 4413 | 4273 | 0 | 0.017232 | 13.2s | ok |

Model calls: 14 (1 failed, 1 malformed); tokens in/out/cached 39943/51475/0; USD: 0.088856.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14acf-0bad-7423-a704-00375e432cb8 | SUCCESS | 0 | 0.824s | retained | off | 0.0028778399999999996 |
| red-1 | 01a14ad1-7c59-71ac-89ef-9d674280d590 | SUCCESS | 0 | 6.033s | disposable | off | 0.05238465 |
| impl-tests-5 | 01a14ad2-a328-706b-90de-606a6898fddb | SUCCESS | 0 | 0.769s | disposable | off | 0.0028485 |
| impl-python-6 | 01a14ad2-cd99-7049-a971-19e98ed54849 | SUCCESS | 0 | 0.561s | disposable | off | 0.00124118 |
| impl-tests-7 | 01a14ad2-e602-73df-82ad-9750cd81f2e7 | SUCCESS | 0 | 0.768s | disposable | off | 0.0028252999999999998 |
| verify | 01a14ad2-fef9-73cb-84eb-f7672063af4f | SUCCESS | 0 | 6.039s | disposable | off | 0.05240802000000001 |
| existing | 01a14ad3-225a-712a-8223-e972468bda0d | SUCCESS | 0 | 2.113s | disposable | off | 0.01525232 |
| mutant-m01-e24672cfa1 | 01a14ad3-3c3a-77fb-ace6-5606132b6f93 | SUCCESS | 0 | 5.826s | disposable | off | 0.04950009 |
| mutant-m02-f30929e892 | 01a14ad3-3c7d-7673-8134-6b9ba95a1bed | SUCCESS | 0 | 5.824s | disposable | off | 0.0492575 |
| mutant-m03-d62ce0684d | 01a14ad3-3c82-703f-ba60-f6382718f133 | SUCCESS | 0 | 5.734s | disposable | off | 0.04894149 |
| mutant-m05-1c7adbf18e | 01a14ad3-3c87-7491-bed3-eedc6a0181a7 | SUCCESS | 0 | 5.865s | disposable | off | 0.04954063 |
| mutant-m06-408bf96b93 | 01a14ad3-3c34-7310-8f18-e5bed75e0c12 | SUCCESS | 0 | 5.717s | disposable | off | 0.049803860000000005 |
| mutant-m04-7ddd9e093c | 01a14ad3-3d5d-72d2-8805-7de131321a31 | SUCCESS | 0 | 5.733s | disposable | off | 0.04897167 |
| mutant-m07-752250b412 | 01a14ad3-3c3c-7400-8302-13a14db25e6b | SUCCESS | 0 | 5.942s | disposable | off | 0.050210370000000004 |
| mutant-m08-ba00aa780f | 01a14ad3-3c8b-75fd-9d68-51a6883a09dc | SUCCESS | 0 | 5.81s | disposable | off | 0.04905205 |
| mutant-m09-c815d9b385 | 01a14ad3-6094-767c-a083-eb68f2fcbae0 | SUCCESS | 0 | 5.759s | disposable | off | 0.04923377000000001 |
| mutant-m10-c3a5ab96bf | 01a14ad3-618d-742a-9f2c-aeaf260a8616 | SUCCESS | 0 | 5.72s | disposable | off | 0.04912991 |
| mutant-m11-51bd35ec07 | 01a14ad3-6200-71ce-8454-323e84463562 | SUCCESS | 0 | 5.731s | disposable | off | 0.04924649 |
| mutant-m12-044e77bdf2 | 01a14ad3-6204-710e-aca8-68fca57d84b8 | SUCCESS | 0 | 5.85s | disposable | off | 0.04958969 |
| breaker-tests | 01a14ad4-7701-7741-b0dd-e99a976ef991 | SUCCESS | 0 | 3.154s | disposable | off | 0.02506102 |
| arbitrate-adversarial-candidate | 01a14ad5-03ce-706e-b03a-d5eb915af7e3 | SUCCESS | 0 | 3.167s | disposable | off | 0.025061450000000002 |
| arbitrate-adversarial-base | 01a14ad5-1ce4-7306-8e79-73809cbabb8d | SUCCESS | 0 | 3.163s | disposable | off | 0.02519828 |

Sandbox operations: 22, total guest duration 96.102s, retained images ['172364e3-f8cc-4863-a24e-c419dc4950a5'].

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
