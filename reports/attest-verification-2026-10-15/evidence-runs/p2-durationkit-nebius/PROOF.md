# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261015T154756Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T15:47:56.507208+00:00, finished 2026-10-15T15:52:55.490376+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d04ed85f-8624-4626-a69c-106c5c697e0c`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms), in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns total seconds as a float. It must preserve existing behavior for plain integer strings (e.g., '90' -> 90.0) and continue to raise TypeError for non-string input and ValueError for malformed input (empty, negative, fractional, unknown unit, repeated unit, out-of-order units, missing number, number without unit, whitespace between number and unit).

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (optionally surrounded by white | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only after stripping.; ValueError: if any component contains a negative integer  |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. parse_duration('  42 ') == 42.0 (existing behavior preserved).
4. parse_duration('7') returns a float (existing behavior preserved).
5. parse_duration('') raises ValueError (existing behavior preserved).
6. parse_duration(90) raises TypeError (existing behavior preserved).
7. parse_duration(None) raises TypeError.
8. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
9. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
10. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0.
11. Whitespace between number and unit raises ValueError: '1 h' raises ValueError.
12. ValueError for empty or whitespace-only input: '' and '   ' raise ValueError.
13. ValueError for negative numbers: '-1h' raises ValueError.
14. ValueError for fractional numbers: '1.5h' raises ValueError.
15. ValueError for unknown units: '1x' raises ValueError.
16. ValueError for repeated units: '1h1h' raises ValueError.
17. ValueError for components out of descending order: '30m1h' raises ValueError.
18. ValueError for unit without a number: 'h' raises ValueError.
19. ValueError for number without a unit in multi-component string: '1h30' raises ValueError.
20. ValueError for other malformed text: 'abc' raises ValueError.
21. The return type is float for every accepted input.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `4a634ae46515b66dca7301c809b07203aece04b3db928578c04b97f650ee2e48`, 29 test methods, sealed at 2026-10-15T15:48:50.516617+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 29 methods: ERROR 12): 12 of 29 methods failing, 17 passing; operation `01a14040-6ab5-7118-99f0-cd4cb5c80069`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_combined_1d1h1m1s1ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_1h30m | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_1m1s | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_1s500ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_2d4h | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_string_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_number_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_negative_number_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_int_raises_TypeError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_none_raises_TypeError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_number_without_unit_in_multi_component_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_other_malformed_text_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_no_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_with_surrounding_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_unit_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_return_type_is_float_for_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_component_d | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_component_h | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_component_m | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_component_ms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_component_s | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unit_without_number_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_unit_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_number_and_unit_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_only_string_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_with_s_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 11 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,68 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts two forms: (1) a plain non-negative integer (optionally surrounded by whitespace)
+    representing seconds; (2) one or more components of the form <non-negative integer><unit>
+    where unit is one of 'd', 'h', 'm', 's', 'ms'. Components must appear in descending unit
+    order (d > h > m > s > ms), each unit at most once. Whitespace is allowed around the
+    entire string and between components, but not between a number and its unit. The function
+    computes the total seconds: 1d = 86400s, 1h = 3600s, 1m = 60s, 1s = 1s, 1ms = 0.001s.
+    Returns the sum as a float.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("duration string is empty or only whitespace")
+    # Check for plain integer (only digits) after stripping
+    if stripped.isdigit():
+        return float(stripped)
+    # Parse components
+    i = 0
+    n = len(stripped)
+    total = 0.0
+    seen = set()
+    prev_rank = float('inf')
+    unit_order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    unit_factor = {'d': 86400.0, 'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
+    while i < n:
+        # Skip whitespace
+        while i < n and stripped[i].isspace():
+            i += 1
+        if i >= n:
+            break  # trailing whitespace
+        # Parse number
+        start = i
+        while i < n and stripped[i].isdigit():
+            i += 1
+        if start == i:
+            raise ValueError(f"missing number in duration at position {start}")
+        number_str = stripped[start:i]
+        # Parse unit
+        if i >= n:
+            raise ValueError(f"missing unit after number {number_str!r}")
+        # Check for 'ms' first
+        if stripped[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif stripped[i] in 'dhms':
+            unit = stripped[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit after number {number_str!r}")
+        # Validate number
+        try:
+            value = int(number_str)
+        except ValueError:
+            raise ValueError(f"invalid number {number_str!r}")
+        # Check unit repetition and order
+        if unit in seen:
+            raise ValueError(f"repeated unit {unit}")
+        rank = unit_order[unit]
+        if rank >= prev_rank:
+            raise ValueError(f"unit {unit} out of order")
+        seen.add(unit)
+        prev_rank = rank
+        total += value * unit_factor[unit]
+        # After unit, loop continues (will skip whitespace before next number)
+    return total
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: OK (29 of 29 methods, each in its own process). Operation `01a14042-4f91-76ca-ac49-4b399196313f`, networking disabled, disposable branch from the checkpoint.

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
| mutation | pass | score 0.75 on 12 mutants |
| adversarial_tests | pass | OK (12 of 12 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 9 killed, 3 survived, 0 unknown; mutation score 0.750 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-b5d3a5d45f | durationkit/parse.py | 18 | remove `not` | killed | test_sealed.ParseDurationAcceptanceTests.test_plain_integer_no_whitespace, test_sealed.ParseDurationAcceptanceTests.test | 01a14042-7620-778e-b327-7e06d1284b7f |
| m02-63fb8e931a | durationkit/parse.py | 24 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_zero_with_s_unit, test_sealed.ParseDurationAcceptanceTests.test_single_com | 01a14042-757a-7023-8751-119019819b35 |
| m03-9efe362cd3 | durationkit/parse.py | 29 | 2 -> 3 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_1h30m, test_sealed.ParseDurationAcceptanceTests.test_combined_1d1 | 01a14042-764e-7688-9e75-b9a364ca1cdb |
| m04-8fad39f7fe | durationkit/parse.py | 31 | Lt -> LtE | survived |  | 01a14042-7622-7522-8672-91a2cff81900 |
| m05-a2a1e6c10d | durationkit/parse.py | 34 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_whitespace_around_and_between_components | 01a14042-760f-75ee-8d6b-dd8670909c8a |
| m06-f273bfe973 | durationkit/parse.py | 39 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_number_without_unit_in_multi_component_raises_ValueError | 01a14042-75b3-7685-9411-44caad3059ec |
| m07-95bc9dbc0f | durationkit/parse.py | 41 | Eq -> NotEq | killed | test_sealed.ParseDurationAcceptanceTests.test_zero_with_s_unit, test_sealed.ParseDurationAcceptanceTests.test_single_com | 01a14042-761a-72b4-838d-cd8b77a6f232 |
| m08-bc0ddcc4a3 | durationkit/parse.py | 46 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_number_without_unit_in_multi_component_raises_ValueError | 01a14042-75ca-702b-a9ce-2e0fd325b36b |
| m09-5d4c8571c6 | durationkit/parse.py | 48 | Eq -> NotEq | killed | test_sealed.ParseDurationAcceptanceTests.test_single_component_d, test_sealed.ParseDurationAcceptanceTests.test_single_c | 01a14042-9d6d-74e0-8e0d-ff38d040db89 |
| m10-3fcdd28551 | durationkit/parse.py | 51 | In -> NotIn | killed | test_sealed.ParseDurationAcceptanceTests.test_zero_with_s_unit, test_sealed.ParseDurationAcceptanceTests.test_single_com | 01a14042-9c5e-777d-ae37-1f73b7f90cbc |
| m11-7fe7c4e9fd | durationkit/parse.py | 60 | raise -> pass | survived |  | 01a14042-9c80-75eb-9fdc-6a08ae56f120 |
| m12-2347a4c2f1 | durationkit/parse.py | 65 | GtE -> Gt | survived |  | 01a14042-9e05-769a-9e8d-8c6300359596 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `2092557172037457ca29fe4c71c75c01f2165e6b9861b87d6c0b9a32bf45cac7`): OK (12 of 12 methods, each in its own process); binding ok; operation `01a14043-eaf4-757f-9a90-9043ef3020cd`. Notes: Targeted edge cases: leading zeros, various whitespace chars (tab, cr, lf), missing number/unit in multi-component, repeated units/out-of-order with whitespace, unknown unit variants, negative/plus sign with space, large numbers, skipping units, return type always float.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fully implements the required extension: parse_duration now accepts component-based duration strings with units d, h, m, s, ms in descending order, allows whitespace around the string and between components, rejects malformed input with ValueError, preserves plain-integer behavior, and keeps raising TypeError for non-strings. All existing tests pass and the comprehensive acceptance test reports success. No required features were omitted, no extra features were added, and all implementer claims are backed by the observed tool outputs.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 1532 | 0 | 0.006218 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 2010 | 6318 | 0 | 0.006289 | 26.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1872 | 106 | 0 | 0.000657 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1966 | 90 | 0 | 0.000671 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2168 | 1508 | 0 | 0.002008 | 9.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2384 | 3282 | 0 | 0.003669 | 15.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3393 | 2649 | 0 | 0.003402 | 14.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3660 | 1146 | 0 | 0.002129 | 6.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 5054 | 4194 | 0 | 0.005291 | 26.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 6739 | 83 | 0 | 0.002096 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 7000 | 1616 | 0 | 0.003554 | 8.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 8683 | 147 | 0 | 0.002737 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 8741 | 113 | 0 | 0.002724 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 2773 | 15700 | 0 | 0.014962 | 72.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3435 | 5152 | 0 | 0.018891 | 18.1s | ok |

Model calls: 15 (0 failed, 0 malformed); tokens in/out/cached 61500/43636/0; USD: 0.075298.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1403f-d635-7274-9056-93838c560c17 | SUCCESS | 0 | 0.826s | retained | off | 0.0028011299999999998 |
| red-1 | 01a14040-6ab5-7118-99f0-cd4cb5c80069 | SUCCESS | 0 | 5.79s | disposable | off | 0.04884697 |
| impl-tests-5 | 01a14041-3dd6-7254-9728-91d2042fd822 | SUCCESS | 0 | 0.734s | disposable | off | 0.0027895800000000003 |
| impl-python-6 | 01a14041-6915-7452-bdbc-334f27374533 | SUCCESS | 0 | 0.526s | disposable | off | 0.00117832 |
| impl-tests-8 | 01a14041-e8ee-72c2-89ea-0bc108558e23 | SUCCESS | 0 | 0.749s | disposable | off | 0.00279649 |
| impl-python-9 | 01a14042-1af1-72d5-b200-156e7288bddb | SUCCESS | 0 | 0.534s | disposable | off | 0.0011691100000000001 |
| impl-tests-10 | 01a14042-34df-771b-971d-0935c3992a7c | SUCCESS | 0 | 0.715s | disposable | off | 0.00279031 |
| verify | 01a14042-4f91-76ca-ac49-4b399196313f | SUCCESS | 0 | 5.951s | disposable | off | 0.050563290000000004 |
| mutant-m01-b5d3a5d45f | 01a14042-7620-778e-b327-7e06d1284b7f | SUCCESS | 0 | 5.794s | disposable | off | 0.04921649 |
| mutant-m04-8fad39f7fe | 01a14042-7622-7522-8672-91a2cff81900 | SUCCESS | 0 | 5.771s | disposable | off | 0.048969359999999997 |
| mutant-m03-9efe362cd3 | 01a14042-764e-7688-9e75-b9a364ca1cdb | SUCCESS | 0 | 5.673s | disposable | off | 0.04871633000000001 |
| mutant-m05-a2a1e6c10d | 01a14042-760f-75ee-8d6b-dd8670909c8a | SUCCESS | 0 | 5.795s | disposable | off | 0.04919569000000001 |
| mutant-m02-63fb8e931a | 01a14042-757a-7023-8751-119019819b35 | SUCCESS | 0 | 5.79s | disposable | off | 0.04900182000000001 |
| mutant-m06-f273bfe973 | 01a14042-75b3-7685-9411-44caad3059ec | SUCCESS | 0 | 5.791s | disposable | off | 0.04936454 |
| mutant-m07-95bc9dbc0f | 01a14042-761a-72b4-838d-cd8b77a6f232 | SUCCESS | 0 | 5.864s | disposable | off | 0.05007028000000001 |
| mutant-m08-bc0ddcc4a3 | 01a14042-75ca-702b-a9ce-2e0fd325b36b | SUCCESS | 0 | 5.792s | disposable | off | 0.04901528 |
| mutant-m09-5d4c8571c6 | 01a14042-9d6d-74e0-8e0d-ff38d040db89 | SUCCESS | 0 | 5.763s | disposable | off | 0.04925537 |
| mutant-m10-3fcdd28551 | 01a14042-9c5e-777d-ae37-1f73b7f90cbc | SUCCESS | 0 | 5.828s | disposable | off | 0.04911581 |
| mutant-m11-7fe7c4e9fd | 01a14042-9c80-75eb-9fdc-6a08ae56f120 | SUCCESS | 0 | 5.827s | disposable | off | 0.0487668 |
| mutant-m12-2347a4c2f1 | 01a14042-9e05-769a-9e8d-8c6300359596 | SUCCESS | 0 | 5.782s | disposable | off | 0.04921194 |
| breaker-tests | 01a14043-eaf4-757f-9a90-9043ef3020cd | SUCCESS | 0 | 2.739s | disposable | off | 0.02142882 |

Sandbox operations: 21, total guest duration 88.034s, retained images ['d04ed85f-8624-4626-a69c-106c5c697e0c'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
