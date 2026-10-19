# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261015T175512Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T17:55:12.328299+00:00, finished 2026-10-15T17:57:10.350895+00:00.

Reasons: child process nonzero exit: test_whitespace_between_number_and_unit_raises exit 1, test_error_missing_unit_after_number_in_multi exit 1


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `081d48ec-51ea-474e-8294-87941a886076`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms) in descending order, with optional whitespace around the whole string and between components. The function returns total seconds as a float. It must preserve existing behavior for plain integer seconds strings, raise ValueError for malformed input (empty, negative, fractional, unknown unit, repeated unit, out-of-order, missing number, etc.), and raise TypeError for non-string input.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (optionally surrounded by white | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only after stripping.; ValueError: if any component contains a negative number ( |

Acceptance criteria:
1. 1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. 2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. 3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. 4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. 5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. 6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. 7. TypeError for non-string input such as 90 or None.
8. 8. The return type is float for every accepted input.
9. 9. Existing tests in tests/test_parse.py continue to pass without modification.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `601359c45431f213cd042a4ec77519abfa646fdd1e8021d4e8d70dc2d961481d`, 28 test methods, sealed at 2026-10-15T17:55:52.426956+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 28 methods: ERROR 13): 13 of 28 methods failing, 15 passing; operation `01a140b4-b80d-7093-81c6-16fe412250f0`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationAcceptance.test_error_empty_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_fractional_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_missing_number_before_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_missing_unit_after_number_in_multi | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_negative_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_other_malformed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_out_of_order | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_repeated_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_unknown_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_error_whitespace_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_five_component_descending_all_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_four_component_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_plain_integer_seconds_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_plain_integer_with_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_return_type_is_float_for_combined | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_return_type_is_float_for_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_return_type_is_float_for_single_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_three_component_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_two_component_descending_various | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_type_error_non_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_whitespace_around_string_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_whitespace_between_number_and_unit_raises | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_zero_plain_and_with_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,70 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts two forms:
+    1. A plain non-negative integer representing seconds (whitespace allowed around).
+    2. One or more components of a non-negative integer immediately followed by a unit
+       (d, h, m, s, ms) in strictly descending order (d > h > m > s > ms).
+       Whitespace is allowed around the entire string and between components,
+       but not between a number and its unit.
+    Returns the total number of seconds as a float.
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
+    i = 0
+    total = 0.0
+    seen_units = set()
+    order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    prev_order = float('inf')
+    while i < len(s):
+        # skip whitespace between components
+        if s[i].isspace():
+            while i < len(s) and s[i].isspace():
+                i += 1
+            continue
+        # parse number
+        start_num = i
+        while i < len(s) and s[i].isdigit():
+            i += 1
+        if start_num == i:
+            raise ValueError(f"missing number in duration: {text!r}")
+        num_str = s[start_num:i]
+        # after number, check if we are at end (plain seconds case)
+        if i == len(s):
+            # plain integer seconds
+            if 's' in seen_units:
+                raise ValueError(f"repeated unit: s")
+            seen_units.add('s')
+            total += int(num_str)
+            break
+        # parse unit
+        if s[i] == 'm' and i + 1 < len(s) and s[i + 1] == 's':
+            unit = 'ms'
+            i += 2
+        else:
+            unit = s[i]
+            i += 1
+            if unit not in ('d', 'h', 'm', 's'):
+                raise ValueError(f"unknown unit: {unit}")
+        if unit in seen_units:
+            raise ValueError(f"repeated unit: {unit}")
+        seen_units.add(unit)
+        cur_order = order[unit]
+        if cur_order > prev_order:
+            raise ValueError(f"units out of order: {unit} after previous")
+        prev_order = cur_order
+        num = int(num_str)
+        if unit == 'd':
+            total += num * 86400
+        elif unit == 'h':
+            total += num * 3600
+        elif unit == 'm':
+            total += num * 60
+        elif unit == 's':
+            total += num
+        elif unit == 'ms':
+            total += num / 1000.0
+    return total
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: FAILED (2 of 28 methods: FAIL 2). Operation `01a140b5-9f8d-72fb-b7de-e16d79d79c31`, networking disabled, disposable branch from the checkpoint.

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
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |

Held-out suite: none configured.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | FAIL | child process nonzero exit: test_whitespace_between_number_and_unit_raises exit 1, test_error_missing_unit_after_number_in_multi exit 1 |
| mutation | FAIL | not run: verification did not pass |
| adversarial_tests | FAIL | not run: verification did not pass |
| drift_audit | pass | score 0.15 (narrowed) |

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Score 0.150 (narrowed; threshold 0.6). The implementation correctly handles most new duration formats and preserves existing behavior, but fails to reject a number without a following unit in a multi-component string (e.g., '1h30'), which is explicitly required to raise ValueError. All existing tests pass, but this gap means the scope is narrowed relative to the acceptance criteria.

Scope narrowed: Missing validation for trailing number without unit in multi-component string (e.g., '1h30' should raise ValueError but is accepted as 1h30s).  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 1623 | 0 | 0.006491 | 5.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1833 | 4361 | 0 | 0.004475 | 20.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1712 | 111 | 0 | 0.000614 | 3.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1918 | 168 | 0 | 0.000727 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2131 | 2527 | 0 | 0.002914 | 14.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 3161 | 99 | 0 | 0.001037 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3425 | 1081 | 0 | 0.002000 | 7.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 4345 | 150 | 0 | 0.001438 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 4610 | 117 | 0 | 0.001488 | 3.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2834 | 5471 | 0 | 0.019247 | 17.7s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 27591/15708/0; USD: 0.040431.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140b4-45b3-7433-86ee-b61c6d109234 | SUCCESS | 0 | 0.789s | retained | off | 0.0027912699999999998 |
| red-1 | 01a140b4-b80d-7093-81c6-16fe412250f0 | SUCCESS | 0 | 5.576s | disposable | off | 0.04769473 |
| impl-tests-4 | 01a140b5-40b6-73d2-a7ba-9c7235530afa | SUCCESS | 0 | 0.805s | disposable | off | 0.00285606 |
| impl-python-5 | 01a140b5-6896-701d-ab6b-a9e5fd89b8ff | SUCCESS | 0 | 0.551s | disposable | off | 0.0011542800000000001 |
| impl-tests-6 | 01a140b5-84c5-7104-ad64-daf6793f75e3 | SUCCESS | 0 | 0.732s | disposable | off | 0.0027425799999999997 |
| verify | 01a140b5-9f8d-72fb-b7de-e16d79d79c31 | SUCCESS | 0 | 5.742s | disposable | off | 0.04897497 |

Sandbox operations: 6, total guest duration 14.195s, retained images ['081d48ec-51ea-474e-8294-87941a886076'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
