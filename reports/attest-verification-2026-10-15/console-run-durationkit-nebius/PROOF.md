# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261015T152352Z` · profile `submission` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T15:23:52.662682+00:00, finished 2026-10-15T15:28:30.257531+00:00.

Reasons: all gates passed
Warnings: adversarial tests skipped: only 0 adversarial tests were written

## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ab24e7ee-dd5a-46b0-be72-32f2bd79524a`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms), in descending unit order, with optional whitespace around the whole string and between components. The function returns total seconds as a float. It must preserve existing behavior for plain integer seconds. It must raise ValueError for malformed inputs (empty, negative, fractional, unknown units, repeated units, out-of-order units, missing number, etc.) and TypeError for non-string input.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parse a duration string and return the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (optionally surrounded by whitesp | TypeError: input is not a string.; ValueError: input is empty or whitespace-only.; ValueError: any component contains a negative integer.; ValueError: any compo |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. TypeError for non-string input such as 90 or None.
8. The return type is float for every accepted input.
9. Existing tests in tests/test_parse.py continue to pass without modification.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d4024175b7dcf59656e46f977fa656f36acf3a8e31767c933578ce896a3596f2`, 32 test methods, sealed at 2026-10-15T15:24:47.318069+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 32 methods: ERROR 15): 15 of 32 methods failing, 17 passing; operation `01a1402a-627d-76e8-9145-78a96d852c69`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationSealed.test_combined_1d1h1m1s1ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_combined_1h30m | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_combined_1m1s | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_combined_1s500ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_combined_2d4h | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_empty_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_fractional_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_missing_number_before_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_negative_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_number_without_unit_in_component_form | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_other_malformed_text | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_out_of_order_units | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_repeated_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_unknown_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_error_whitespace_only_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_seconds_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_with_surrounding_whitespace_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_combined | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_plain_integer | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_zero_with_unit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_type_error_for_non_string_input_int | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_type_error_for_non_string_input_none | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_allowed_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_between_number_and_unit_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_zero_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_zero_with_seconds_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 13 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -2,14 +2,95 @@
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
+    """Parse a duration string and return the total number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts two forms:
+      1. A plain non-negative integer (optionally surrounded by whitespace) representing seconds.
+      2. A sequence of one or more components, each consisting of a non-negative integer
+         immediately followed by a unit (d, h, m, s, ms), with components appearing in
+         descending unit order (d > h > m > s > ms). Whitespace is allowed around the
+         entire string and between components, but not between a number and its unit.
+
+    Returns the sum of all components converted to seconds as a float.
+
+    Raises:
+      TypeError: if input is not a string.
+      ValueError: for malformed inputs (empty, negative, fractional, unknown units,
+                  repeated units, out-of-order units, missing number, missing unit,
+                  whitespace between number and unit, etc.).
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("input is empty or whitespace-only")
+    # Plain integer seconds (existing behavior)
+    if stripped.isdigit():
+        return float(stripped)
+    # Component-based parsing
+    total_seconds = 0.0
+    i = 0
+    n = len(stripped)
+    # Unit order for validation: lower index means larger unit
+    unit_order = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    prev_order = -1  # order of previous unit
+    while i < n:
+        # Skip whitespace between components
+        while i < n and stripped[i].isspace():
+            i += 1
+        if i >= n:
+            break  # trailing whitespace
+        # Parse number (one or more digits)
+        start_num = i
+        while i < n and stripped[i].isdigit():
+            i += 1
+        if start_num == i:
+            raise ValueError("missing number")
+        num_str = stripped[start_num:i]
+        # Check for fractional part (dot) directly after number
+        if i < n and stripped[i] == '.':
+            raise ValueError("fractional number")
+        # Ensure no negative (already filtered by isdigit)
+        value = int(num_str)
+        if value < 0:
+            raise ValueError("negative integer")
+        # Parse unit
+        if i >= n:
+            raise ValueError("missing unit after number")
+        if stripped[i] == 'm':
+            # Could be 'ms' or 'm'
+            if i + 1 < n and stripped[i + 1] == 's':
+                unit = 'ms'
+                i += 2
+            else:
+                unit = 'm'
+                i += 1
+        elif stripped[i] in ('d', 'h', 's'):
+            unit = stripped[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit: {stripped[i]!r}")
+        # Validate unit order
+        curr_order = unit_order[unit]
+        if prev_order != -1 and curr_order <= prev_order:
+            raise ValueError("units out of order or repeated")
+        # Convert to seconds
+        if unit == 'd':
+            seconds = value * 86400
+        elif unit == 'h':
+            seconds = value * 3600
+        elif unit == 'm':
+            seconds = value * 60
+        elif unit == 's':
+            seconds = value
+        elif unit == 'ms':
+            seconds = value * 0.001
+        else:
+            # Should not happen
+            raise ValueError(f"unsupported unit: {unit}")
+        total_seconds += seconds
+        prev_order = curr_order
+    if prev_order == -1:
+        # No components parsed (should not happen due to earlier checks)
+        raise ValueError("no duration components")
+    return float(total_seconds)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: OK (32 of 32 methods, each in its own process). Operation `01a1402c-d59b-703d-9873-c1e2473bc0b6`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| static_ids_match_red | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |

Held-out suite: none configured.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | pass | all checks pass |
| mutation | pass | score 0.667 on 12 mutants |
| adversarial_tests | pass | only 0 adversarial tests were written |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 8 killed, 4 survived, 0 unknown; mutation score 0.667 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-eb5f2a39b1 | durationkit/parse.py | 25 | remove `not` | killed | test_sealed.TestParseDurationSealed.test_plain_integer_seconds_preserved, test_sealed.TestParseDurationSealed.test_plain | 01a1402d-5cc8-7453-9ebd-64082af04d9f |
| m02-aeb3837bb7 | durationkit/parse.py | 35 | 2 -> 3 | killed | test_sealed.TestParseDurationSealed.test_combined_1m1s, test_sealed.TestParseDurationSealed.test_combined_1d1h1m1s1ms | 01a1402c-fd91-746f-8277-b1e791c80c5c |
| m03-6af4f3abab | durationkit/parse.py | 39 | Lt -> LtE | survived |  | 01a1402d-0180-71bf-800b-ce79ceac584d |
| m04-4bbac5120a | durationkit/parse.py | 45 | And -> Or | killed | test_sealed.TestParseDurationSealed.test_zero_with_seconds_unit, test_sealed.TestParseDurationSealed.test_single_compone | 01a1402c-fc14-762b-a71d-00920d4fe094 |
| m05-bdc46562d1 | durationkit/parse.py | 51 | Eq -> NotEq | killed | test_sealed.TestParseDurationSealed.test_zero_with_seconds_unit, test_sealed.TestParseDurationSealed.test_single_compone | 01a1402c-fcfb-73c3-a5ee-1a42843087b3 |
| m06-2229707ac5 | durationkit/parse.py | 56 | raise -> pass | survived |  | 01a1402c-fcdc-7410-b658-25cd9e28ea5c |
| m07-ae51498613 | durationkit/parse.py | 62 | Lt -> LtE | killed | test_sealed.TestParseDurationSealed.test_single_component_minutes, test_sealed.TestParseDurationSealed.test_combined_1h3 | 01a1402c-fc8f-7585-a480-9b2fdcd5ea7a |
| m08-2e8acdbdb2 | durationkit/parse.py | 64 | 2 -> 3 | survived |  | 01a1402c-fbf4-71c4-ae10-9f2457b18b72 |
| m09-01d94820a7 | durationkit/parse.py | 75 | 1 -> 2 | survived |  | 01a1402d-2138-7082-b1f6-2d0eab5a6498 |
| m10-a93172531a | durationkit/parse.py | 78 | Eq -> NotEq | killed | test_sealed.TestParseDurationSealed.test_single_component_days, test_sealed.TestParseDurationSealed.test_single_componen | 01a1402d-2e85-769d-b69b-67b36166625f |
| m11-7eedfb5f76 | durationkit/parse.py | 81 | Mult -> Div | killed | test_sealed.TestParseDurationSealed.test_single_component_hours, test_sealed.TestParseDurationSealed.test_combined_1h30m | 01a1402d-251c-77f9-980a-135888cd035e |
| m12-5ea7d6d2c8 | durationkit/parse.py | 86 | Eq -> NotEq | killed | test_sealed.TestParseDurationSealed.test_single_component_milliseconds, test_sealed.TestParseDurationSealed.test_combine | 01a1402d-36a6-7078-8356-05949474f3f1 |

Model-written adversarial tests: skipped (only 0 adversarial tests were written)



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff extends parse_duration with a component-parsing loop that enforces descending unit order, whitespace rules, and all required ValueError cases while preserving the plain-integer seconds behavior. The final verification (turn 12) and existing test suite confirm full alignment with the acceptance criteria.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 1902 | 0 | 0.007328 | 6.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1738 | 7366 | 0 | 0.007151 | 29.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1632 | 99 | 0 | 0.000579 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1726 | 102 | 0 | 0.000610 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1928 | 2082 | 0 | 0.002452 | 11.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2144 | 6139 | 0 | 0.006168 | 26.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3358 | 114 | 0 | 0.001110 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3615 | 1372 | 0 | 0.002319 | 7.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 5374 | 1408 | 0 | 0.002879 | 8.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 5962 | 310 | 0 | 0.002068 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 6224 | 2693 | 0 | 0.004291 | 12.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 7756 | 2132 | 0 | 0.004246 | 12.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 9306 | 2946 | 0 | 0.005443 | 14.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 10524 | 1672 | 0 | 0.004662 | 8.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | default | 10801 | 239 | 0 | 0.003455 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests | default | 2674 | 1571 | 0 | 0.002216 | 15.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3659 | 3892 | 0 | 0.015335 | 12.8s | ok |

Model calls: 17 (0 failed, 0 malformed); tokens in/out/cached 80043/36039/0; USD: 0.072312.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14029-ba0a-7572-8858-cbf95468a678 | SUCCESS | 0 | 0.857s | retained | off | 0.0028065 |
| red-1 | 01a1402a-627d-76e8-9145-78a96d852c69 | SUCCESS | 0 | 6.298s | disposable | off | 0.05350891000000001 |
| impl-tests-5 | 01a1402b-3cb5-7005-85b0-49f49fcde4dc | SUCCESS | 0 | 0.799s | disposable | off | 0.0027874999999999996 |
| impl-python-6 | 01a1402b-6873-7431-b500-5750e9b3757e | SUCCESS | 0 | 0.629s | disposable | off | 0.00116798 |
| impl-python-7 | 01a1402b-9781-731a-8b4f-61057a3c81fd | SUCCESS | 0 | 0.537s | disposable | off | 0.0011488 |
| impl-tests-8 | 01a1402b-baab-7543-87af-c2341d888242 | SUCCESS | 0 | 0.812s | disposable | off | 0.00281777 |
| impl-python-9 | 01a1402b-fb09-7666-89a4-63a0813bdea1 | SUCCESS | 0 | 0.536s | disposable | off | 0.0012013 |
| impl-python-10 | 01a1402c-3ad8-7257-a3e8-a51da86096b1 | SUCCESS | 0 | 0.685s | disposable | off | 0.00119312 |
| impl-python-11 | 01a1402c-8409-7776-8aa2-c57446d2f0f3 | SUCCESS | 0 | 0.556s | disposable | off | 0.00115646 |
| impl-python-12 | 01a1402c-b8cc-7714-8d6b-c43f8176063a | SUCCESS | 0 | 0.571s | disposable | off | 0.00118122 |
| verify | 01a1402c-d59b-703d-9873-c1e2473bc0b6 | SUCCESS | 0 | 6.565s | disposable | off | 0.05624021 |
| mutant-m02-aeb3837bb7 | 01a1402c-fd91-746f-8277-b1e791c80c5c | SUCCESS | 0 | 6.278s | disposable | off | 0.05368514 |
| mutant-m01-eb5f2a39b1 | 01a1402d-5cc8-7453-9ebd-64082af04d9f | SUCCESS | 0 | 6.255s | disposable | off | 0.05386318 |
| mutant-m04-4bbac5120a | 01a1402c-fc14-762b-a71d-00920d4fe094 | SUCCESS | 0 | 6.233s | disposable | off | 0.05366578 |
| mutant-m03-6af4f3abab | 01a1402d-0180-71bf-800b-ce79ceac584d | SUCCESS | 0 | 6.34s | disposable | off | 0.054446800000000004 |
| mutant-m05-bdc46562d1 | 01a1402c-fcfb-73c3-a5ee-1a42843087b3 | SUCCESS | 0 | 6.366s | disposable | off | 0.05420354 |
| mutant-m06-2229707ac5 | 01a1402c-fcdc-7410-b658-25cd9e28ea5c | SUCCESS | 0 | 6.269s | disposable | off | 0.05387863 |
| mutant-m07-ae51498613 | 01a1402c-fc8f-7585-a480-9b2fdcd5ea7a | SUCCESS | 0 | 6.398s | disposable | off | 0.054182890000000004 |
| mutant-m08-2e8acdbdb2 | 01a1402c-fbf4-71c4-ae10-9f2457b18b72 | SUCCESS | 0 | 6.455s | disposable | off | 0.05479257 |
| mutant-m09-01d94820a7 | 01a1402d-2138-7082-b1f6-2d0eab5a6498 | SUCCESS | 0 | 6.253s | disposable | off | 0.05434186 |
| mutant-m10-a93172531a | 01a1402d-2e85-769d-b69b-67b36166625f | SUCCESS | 0 | 6.192s | disposable | off | 0.053623300000000006 |
| mutant-m11-7eedfb5f76 | 01a1402d-251c-77f9-980a-135888cd035e | SUCCESS | 0 | 6.193s | disposable | off | 0.053711800000000004 |
| mutant-m12-5ea7d6d2c8 | 01a1402d-36a6-7078-8356-05949474f3f1 | SUCCESS | 0 | 6.263s | disposable | off | 0.053606310000000004 |

Sandbox operations: 23, total guest duration 94.34s, retained images ['ab24e7ee-dd5a-46b0-be72-32f2bd79524a'].

## 11. Limitations of this bundle
- Profile 'submission': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
