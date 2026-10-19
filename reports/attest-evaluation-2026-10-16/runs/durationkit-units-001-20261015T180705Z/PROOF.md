# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261015T180705Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:07:05.413221+00:00, finished 2026-10-15T18:12:56.412628+00:00.

Reasons: child process nonzero exit: test_empty_string_raises_ValueError exit 1, test_whitespace_only_string_raises_ValueError exit 1, test_duplicate_unit_raises_ValueError exit 1, test_units_not_descending_order_raises_ValueError exit 1


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `b79e2178-51e3-421b-85c3-55d6bf0f477c`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms), in descending unit order, with optional whitespace around the whole string and between components. The function returns total seconds as a float. It must preserve existing behavior for plain integer strings, reject malformed inputs with ValueError, and reject non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts either a plain non-negative integer (seconds) or a sequence of components i | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only.; ValueError: if any component has a negative number.; ValueError: if any c |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. TypeError for non-string input such as 90 or None.
8. The return type is float for every accepted input.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `5b0896fb52d8d1f7f72eb0f8fd2df262d957b7ecd4fe4584f1d19fd832bc546f`, 28 test methods, sealed at 2026-10-15T18:10:26.899911+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 28 methods: ERROR 13): 13 of 28 methods failing, 15 passing; operation `01a140c2-0628-7689-860e-f82e148bdf6b`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationSealed.test_all_five_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_duplicate_unit_raises_ValueError | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_empty_string_raises_ValueError | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_fractional_number_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_negative_number_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_non_string_raises_TypeError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_number_without_unit_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_plain_integer_with_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_random_string_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_return_type_is_float_for_new_cases | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_returns_float_existing | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_two_components_days_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_two_components_hours_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_two_components_minutes_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_two_components_seconds_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_unit_without_preceding_number_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_units_not_descending_order_raises_ValueError | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_unknown_unit_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_between_number_and_unit_raises_ValueError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_whitespace_only_string_raises_ValueError | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealed.test_zero_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_zero_with_s_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 12 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,56 @@
 """Duration parsing."""
+
+import re
 
 
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts either a plain non-negative integer (seconds) or a sequence of components in descending unit order (days, hours, minutes, seconds, milliseconds).
+    Each component is a non-negative integer immediately followed by its unit (d, h, m, s, ms).
+    Whitespace is allowed around the entire string and between components, but not between a number and its unit.
+    Each unit may appear at most once.
+    Returns the sum of all components converted to seconds (1d=86400, 1h=3600, 1m=60, 1s=1, 1ms=0.001).
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
+        raise ValueError("duration string is empty or only whitespace")
+
+    # Pattern for a single component: number followed by unit, then optional whitespace (to be consumed after)
+    component_pattern = re.compile(r'(\d+)(d|h|ms|m|s)\s*')
+    pos = 0
+    components = []
+    seen_units = set()
+    # Order: d > h > m > s -> ms -> assign increasing indices for ease of checking increasing sequence
+    order_index = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    prev_index = -1  # so that first unit's index must be >=0 and > prev_index
+
+    while pos < len(stripped):
+        match = component_pattern.match(stripped, pos)
+        if not match:
+            break
+        number = int(match.group(1))
+        unit = match.group(2)
+        if unit in seen_units:
+            raise ValueError(f"duplicate unit: {unit}")
+        seen_units.add(unit)
+        cur_index = order_index[unit]
+        if cur_index <= prev_index:
+            raise ValueError(f"units out of order: {unit}")
+        prev_index = cur_index
+        components.append((number, unit))
+        pos = match.end()
+
+    if pos == len(stripped) and components:
+        # Successfully parsed as component format
+        multipliers = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
+        total = sum(number * multipliers[unit] for number, unit in components)
+        return float(total)
+
+    # Fallback to plain integer seconds
+    if stripped.isdigit():
+        return float(stripped)
+    else:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: FAILED (4 of 28 methods: FAIL 4). Operation `01a140c4-18e6-7704-aeb8-8d2abb26205c`, networking disabled, disposable branch from the checkpoint.

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
| sealed_binding | FAIL | child process nonzero exit: test_empty_string_raises_ValueError exit 1, test_whitespace_only_string_raises_ValueError exit 1, test_duplicate_unit_raises_ValueError exit 1, test_units_not_descending_order_raises_ValueError exit 1 |
| mutation | FAIL | not run: verification did not pass |
| adversarial_tests | FAIL | not run: verification did not pass |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The implementation correctly extends parse_duration to handle component-based duration strings with all required validation, preserves existing integer-only behavior, and passes all existing and new acceptance tests. No deviations from the task requirements were observed.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 16000 | 0 | 0.049622 | 37.2s | malformed |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec-repair | default | 1704 | 1069 | 0 | 0.004911 | 4.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1729 | 16000 | 0 | 0.014919 | 76.4s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1-repair | default | 1794 | 12934 | 0 | 0.012179 | 61.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1601 | 103 | 0 | 0.000573 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1695 | 96 | 0 | 0.000595 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1896 | 134 | 0 | 0.000689 | 3.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2100 | 7785 | 0 | 0.007637 | 39.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2282 | 99 | 0 | 0.000774 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2977 | 1177 | 0 | 0.001952 | 8.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3033 | 991 | 0 | 0.001802 | 6.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 3995 | 146 | 0 | 0.001330 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 4694 | 1195 | 0 | 0.002484 | 8.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 4588 | 1018 | 0 | 0.002293 | 14.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 5324 | 340 | 0 | 0.001903 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 5385 | 186 | 0 | 0.001783 | 3.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2897 | 5185 | 0 | 0.018452 | 16.1s | ok |

Model calls: 17 (2 failed, 2 malformed); tokens in/out/cached 49316/64458/0; USD: 0.123898.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140bf-26bb-73d1-9863-911586995486 | SUCCESS | 0 | 0.805s | retained | off | 0.00279902 |
| red-1 | 01a140c2-0628-7689-860e-f82e148bdf6b | SUCCESS | 0 | 6.068s | disposable | off | 0.04861412 |
| impl-tests-6 | 01a140c3-1e27-7314-acf5-a46ee94fd597 | SUCCESS | 0 | 0.877s | disposable | off | 0.0029228999999999995 |
| impl-python-7 | 01a140c3-5815-73f7-a2d2-abed1b5895f7 | SUCCESS | 0 | 0.76s | disposable | off | 0.00154026 |
| impl-python-10 | 01a140c3-ddb4-72b4-9f78-bf2767a1e495 | SUCCESS | 0 | 0.693s | disposable | off | 0.00152841 |
| impl-tests-11 | 01a140c3-fa88-7731-b017-c9d02e48589d | SUCCESS | 0 | 0.822s | disposable | off | 0.0027927 |
| verify | 01a140c4-18e6-7704-aeb8-8d2abb26205c | SUCCESS | 0 | 5.816s | disposable | off | 0.04941541 |

Sandbox operations: 7, total guest duration 15.841s, retained images ['b79e2178-51e3-421b-85c3-55d6bf0f477c'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
