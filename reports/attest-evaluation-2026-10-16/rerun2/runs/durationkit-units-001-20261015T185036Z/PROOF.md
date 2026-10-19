# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261015T185036Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:50:36.356939+00:00, finished 2026-10-15T18:54:40.887833+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `52d1936e-6c5b-4055-be1a-dda135dee646`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms) in strictly descending order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings, raise ValueError for all malformed inputs (empty, negative, fractional, unknown unit, repeated unit, out-of-order, missing number, etc.), and raise TypeError for non-string input.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts either a plain non-negative integer (seconds) or a sequence of components.  | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only.; ValueError: if any component has a negative integer.; ValueError: if any  |

Acceptance criteria:
1. 1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. 2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. 3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. 4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. 5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. 6. ValueError for empty string '' and whitespace-only '   '.
7. 7. ValueError for negative numbers: '-1h'.
8. 8. ValueError for fractional numbers: '1.5h'.
9. 9. ValueError for unknown units: '1x'.
10. 10. ValueError for repeated units: '1h1h'.
11. 11. ValueError for components out of descending order: '30m1h'.
12. 12. ValueError for unit without a number: 'h'.
13. 13. ValueError for number without a unit when other components have units (i.e., trailing number): '1h30'.
14. 14. ValueError for completely invalid text: 'abc'.
15. 14. TypeError for non-string input such as 90 or None.
16. 15. The return type is float for every accepted input.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `c32b4773bc167ebbd23a5b51b5b7efc8ef0c36c17e4dcc3f105d9fec6ef60ec9`, 23 test methods, sealed at 2026-10-15T18:51:50.191647+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (10 of 23 methods: ERROR 10): 10 of 23 methods failing, 13 passing; operation `01a140e7-f570-73df-8c08-59e3810c3803`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationSealed.test_combined_components_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_empty_string_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_fractional_number_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_invalid_text_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_negative_number_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_non_string_input_raises_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_number_without_unit_after_other_components_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_out_of_order_units_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_with_surrounding_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_without_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_repeated_unit_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_all_valid_inputs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_day_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_hour_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_millisecond_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_minute_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_second_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_unit_without_number_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_unknown_unit_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_around_string_allowed | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_between_components_allowed | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_only_string_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_zero_and_zero_seconds_component | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,78 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts either a plain non-negative integer (seconds) or a sequence of
+    components. A component is a non-negative integer immediately followed by a
+    unit suffix: 'd' (days), 'h' (hours), 'm' (minutes), 's' (seconds), or
+    'ms' (milliseconds). Components must appear in descending unit order (d >
+    h > m > s > ms), each unit at most once. Whitespace is allowed around the
+    entire string and between components, but not between a number and its unit.
+    The function computes the total seconds (1d = 86400s, 1h = 3600s, 1m = 60s,
+    1s = 1s, 1ms = 0.001s) and returns the sum as a float.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
-    stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    s = text.strip()
+    if not s:
+        raise ValueError("empty duration")
+    # Plain integer seconds (existing behavior)
+    if s.isdigit():
+        return float(s)
+    i = 0
+    total = 0.0
+    seen_units = set()
+    prev_rank = -1
+    # rank mapping for order checking
+    rank = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    multipliers = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
+    while i < len(s):
+        # skip whitespace between components
+        while i < len(s) and s[i].isspace():
+            i += 1
+        if i >= len(s):
+            break  # trailing whitespace (should not happen after strip)
+        # parse number
+        start_num = i
+        while i < len(s) and s[i].isdigit():
+            i += 1
+        if start_num == i:
+            raise ValueError("missing number in duration")
+        num_str = s[start_num:i]
+        # disallow fractional numbers: if next char is '.' it's invalid
+        if i < len(s) and s[i] == '.':
+            raise ValueError("fractional number not allowed")
+        if i >= len(s):
+            raise ValueError("missing unit after number")
+        # parse unit
+        unit = None
+        if s[i] == 'm' and i + 1 < len(s) and s[i + 1] == 's':
+            unit = 'ms'
+            i += 2
+        elif s[i] in 'dhms':
+            unit = s[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit '{s[i]}'")
+        # ensure no whitespace between number and unit (we didn't skip any)
+        # convert number
+        try:
+            num = int(num_str)
+        except ValueError:
+            raise ValueError("invalid number")
+        if num < 0:
+            raise ValueError("negative number")
+        # accumulate seconds
+        total += num * multipliers[unit]
+        # check unit repetition and order
+        r = rank[unit]
+        if unit in seen_units:
+            raise ValueError("repeated unit")
+        if r <= prev_rank:
+            raise ValueError("units out of order")
+        seen_units.add(unit)
+        prev_rank = r
+    # after processing, ensure we consumed the whole string
+    # (any trailing whitespace would have been skipped in loop)
+    if i != len(s):
+        raise ValueError("invalid duration format")
+    return total
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a140e9-8a42-74af-94fb-cba2123444e2`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
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
| mutation | pass | score 0.583 on 12 mutants |
| adversarial_tests | pass | OK (12 of 12 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 7 killed, 5 survived, 0 unknown; mutation score 0.583 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-5734e88582 | durationkit/parse.py | 19 | remove `not` | killed | test_sealed.TestParseDurationSealed.test_plain_integer_without_whitespace, test_sealed.TestParseDurationSealed.test_plai | 01a140e9-b0af-70ad-a23a-34b74c288ad7 |
| m02-6839646b22 | durationkit/parse.py | 29 | 0 -> 1 | killed | test_sealed.TestParseDurationSealed.test_combined_components_descending, test_sealed.TestParseDurationSealed.test_whites | 01a140e9-b03f-7624-bd40-c15cc1aa6f48 |
| m03-6e0a1492a4 | durationkit/parse.py | 29 | 4 -> 5 | survived |  | 01a140e9-b0a3-72eb-97d5-5dacaf4a2fd0 |
| m04-e2a0c80626 | durationkit/parse.py | 31 | Lt -> LtE | survived |  | 01a140e9-b02a-77fd-bb63-f197062660bc |
| m05-1574d64bab | durationkit/parse.py | 35 | GtE -> Gt | survived |  | 01a140e9-b047-770e-b4c2-ca4fe82f6c6d |
| m06-1b388b8a16 | durationkit/parse.py | 41 | Eq -> NotEq | killed | test_sealed.TestParseDurationSealed.test_zero_and_zero_seconds_component, test_sealed.TestParseDurationSealed.test_singl | 01a140e9-b0a8-7347-85f3-5247bc672a35 |
| m07-644506b09f | durationkit/parse.py | 46 | raise -> pass | survived |  | 01a140e9-b0ae-7482-9734-c54bb6af1449 |
| m08-f3c017cdf7 | durationkit/parse.py | 51 | 1 -> 2 | killed | test_sealed.TestParseDurationSealed.test_single_millisecond_component, test_sealed.TestParseDurationSealed.test_combined | 01a140e9-b507-71a8-b264-eada810da712 |
| m09-c9d1a7ee93 | durationkit/parse.py | 51 | Add -> Sub | killed | test_sealed.TestParseDurationSealed.test_single_millisecond_component, test_sealed.TestParseDurationSealed.test_combined | 01a140e9-ce7f-709f-8785-a63fbed5d761 |
| m10-0c4a6b34b8 | durationkit/parse.py | 56 | 1 -> 2 | killed | test_sealed.TestParseDurationSealed.test_zero_and_zero_seconds_component, test_sealed.TestParseDurationSealed.test_singl | 01a140e9-d1ff-77be-b192-29e7350aa5e1 |
| m11-83b60638b2 | durationkit/parse.py | 65 | Lt -> LtE | killed | test_sealed.TestParseDurationSealed.test_zero_and_zero_seconds_component, test_sealed.TestParseDurationSealed.test_retur | 01a140e9-d5dd-7281-8420-7ca1961012eb |
| m12-0aa3e38252 | durationkit/parse.py | 72 | raise -> pass | survived |  | 01a140e9-d6f9-70bf-a67d-eb07426ed0a0 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `0e383f40b1645f138801840f9847e0f7ef5b4065eaad46a322684e2467e3ea80`): OK (12 of 12 methods, each in its own process); binding ok; operation `01a140ea-5331-73bf-b821-b17e32e39f02`. Notes: Tests target edge cases not covered: leading plus, embedded spaces, whitespace between number and unit, multiple internal whitespace, zero-valued components, repeated units with whitespace, out-of-order with whitespace, ms unit exactness, fractional without unit, large number return type, uppercase unit, stray invalid characters.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements all required functionality for parsing duration strings with multiple components, preserving existing behavior for plain integers and raising appropriate errors for malformed inputs. All acceptance criteria are satisfied and existing tests pass.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 1569 | 0 | 0.006329 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1949 | 12128 | 0 | 0.011500 | 54.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1845 | 86 | 0 | 0.000631 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1938 | 93 | 0 | 0.000665 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2142 | 3928 | 0 | 0.004178 | 18.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 3339 | 95 | 0 | 0.001087 | 9.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3602 | 1776 | 0 | 0.002679 | 8.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 5598 | 932 | 0 | 0.002518 | 11.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 6216 | 134 | 0 | 0.001985 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 6477 | 229 | 0 | 0.002149 | 7.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 2716 | 5035 | 0 | 0.005346 | 22.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3204 | 4092 | 0 | 0.015480 | 17.9s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 40648/30097/0; USD: 0.054547.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140e6-fd39-73fa-8f71-672ba56ec7b0 | SUCCESS | 0 | 0.763s | retained | off | 0.00275114 |
| red-1 | 01a140e7-f570-73df-8c08-59e3810c3803 | SUCCESS | 0 | 4.614s | disposable | off | 0.039105 |
| impl-tests-4 | 01a140e8-9758-7341-b28f-16334af61061 | SUCCESS | 0 | 0.748s | disposable | off | 0.00278528 |
| impl-python-5 | 01a140e8-cd7d-742a-931e-c9832ad9dfa8 | SUCCESS | 0 | 0.563s | disposable | off | 0.00113579 |
| impl-python-6 | 01a140e9-0e1a-7311-9abc-1da3457876f1 | SUCCESS | 0 | 0.542s | disposable | off | 0.00113375 |
| impl-tests-7 | 01a140e9-4f3c-70a6-9665-d1821f2bf0d8 | SUCCESS | 0 | 0.779s | disposable | off | 0.0028353199999999997 |
| verify | 01a140e9-8a42-74af-94fb-cba2123444e2 | SUCCESS | 0 | 4.799s | disposable | off | 0.04081532 |
| mutant-m01-5734e88582 | 01a140e9-b0af-70ad-a23a-34b74c288ad7 | SUCCESS | 0 | 4.792s | disposable | off | 0.03985629 |
| mutant-m03-6e0a1492a4 | 01a140e9-b0a3-72eb-97d5-5dacaf4a2fd0 | SUCCESS | 0 | 4.706s | disposable | off | 0.03958471 |
| mutant-m02-6839646b22 | 01a140e9-b03f-7624-bd40-c15cc1aa6f48 | SUCCESS | 0 | 4.792s | disposable | off | 0.0398641 |
| mutant-m04-e2a0c80626 | 01a140e9-b02a-77fd-bb63-f197062660bc | SUCCESS | 0 | 4.862s | disposable | off | 0.04007951 |
| mutant-m05-1574d64bab | 01a140e9-b047-770e-b4c2-ca4fe82f6c6d | SUCCESS | 0 | 4.706s | disposable | off | 0.03936844 |
| mutant-m06-1b388b8a16 | 01a140e9-b0a8-7347-85f3-5247bc672a35 | SUCCESS | 0 | 4.703s | disposable | off | 0.03946206 |
| mutant-m07-644506b09f | 01a140e9-b0ae-7482-9734-c54bb6af1449 | SUCCESS | 0 | 4.727s | disposable | off | 0.03945219 |
| mutant-m08-f3c017cdf7 | 01a140e9-b507-71a8-b264-eada810da712 | SUCCESS | 0 | 4.71s | disposable | off | 0.03959409 |
| mutant-m09-c9d1a7ee93 | 01a140e9-ce7f-709f-8785-a63fbed5d761 | SUCCESS | 0 | 4.557s | disposable | off | 0.03893366 |
| mutant-m10-0c4a6b34b8 | 01a140e9-d1ff-77be-b192-29e7350aa5e1 | SUCCESS | 0 | 4.615s | disposable | off | 0.039293669999999996 |
| mutant-m11-83b60638b2 | 01a140e9-d5dd-7281-8420-7ca1961012eb | SUCCESS | 0 | 4.668s | disposable | off | 0.03942655 |
| mutant-m12-0aa3e38252 | 01a140e9-d6f9-70bf-a67d-eb07426ed0a0 | SUCCESS | 0 | 4.664s | disposable | off | 0.03941649 |
| breaker-tests | 01a140ea-5331-73bf-b821-b17e32e39f02 | SUCCESS | 0 | 2.775s | disposable | off | 0.021591620000000002 |

Sandbox operations: 20, total guest duration 72.085s, retained images ['52d1936e-6c5b-4055-be1a-dda135dee646'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
