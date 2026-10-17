# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261015T092142Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T09:21:42.692588+00:00, finished 2026-10-15T09:23:23.820857+00:00.

Reasons: all gates passed

## 1. Frozen task
Task `durationkit-units-001`, spec digest `e51653cf1b317948395923522095ddf1b6d11db0574120e38c3472448f457b8c`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `9dc49965-9210-4ec4-a7a8-e772ce72e8ab`.

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms) in strict descending order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. Preserve existing behavior for plain integer seconds. Reject malformed input with ValueError and non-string input with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parse a duration string and return the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (optional surrounding whitespace) | TypeError: if text is not a string; ValueError: if text is empty or whitespace-only after stripping; ValueError: if any component has a negative integer (e.g.,  |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
3. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
4. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
5. '0s' and '0' return 0.0.
6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. TypeError for non-string input such as 90 or None.
8. The return type is float for every accepted input.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `7252c8cdb25c610a55ad81a78e1b037ea9108081dd85bc27ef98e4b350fecf49`, 28 tests, sealed at 2026-10-15T09:22:12.616117+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint: FAILED (errors=13) (13 failing of 28 ran; operation `01a13ede-869f-7344-a943-d50274461d2c`).

| Sealed test | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationExtended.test_combined_1d1h1m1s1ms | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_combined_1h30m | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_combined_1m1s | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_combined_1s500ms | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_combined_2d4h | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_plain_integer_seconds_with_whitespace | ok | ok |
| test_sealed.TestParseDurationExtended.test_return_type_is_float | ok | ok |
| test_sealed.TestParseDurationExtended.test_single_component_days | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_single_component_hours | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_single_component_milliseconds | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_single_component_minutes | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_single_component_seconds | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_type_error_non_string | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_duplicate_unit | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_empty | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_fractional | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_missing_number | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_negative | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_number_without_unit | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_other_malformed | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_unknown_unit | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_whitespace_between_number_and_unit | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_whitespace_only | ok | ok |
| test_sealed.TestParseDurationExtended.test_value_error_wrong_order | ok | ok |
| test_sealed.TestParseDurationExtended.test_whitespace_around_string | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_whitespace_between_components | ERROR | ok |
| test_sealed.TestParseDurationExtended.test_zero_plain | ok | ok |
| test_sealed.TestParseDurationExtended.test_zero_with_units | ERROR | ok |

## 4. Candidate patch
1 changed path(s); scope check passed; 10 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,99 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts two forms:
+    1. A plain non-negative integer (optional surrounding whitespace) representing seconds.
+    2. A sequence of components, each a non-negative integer immediately followed by a unit
+       (d, h, m, s, ms), components in descending unit order (d > h > m > s > ms),
+       each unit at most once, optional whitespace between components and around the whole string.
+
+    Conversion factors: 1d = 86400s, 1h = 3600s, 1m = 60s, 1s = 1s, 1ms = 0.001s.
+    The result is the sum of all components as a float.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+    
+    # Remove outer whitespace
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("empty duration string")
+    
+    # Plain integer seconds case (existing behavior)
+    if stripped.isdigit():
+        return float(stripped)
+    
+    # Otherwise parse components
+    i = 0
+    n = len(stripped)
+    total = 0.0
+    seen_units = set()
+    # order ranking: higher means larger unit
+    rank = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    prev_rank = None
+    
+    while i < n:
+        # skip whitespace between components
+        while i < n and stripped[i].isspace():
+            i += 1
+        if i >= n:
+            break  # trailing whitespace
+        
+        # parse number (one or more digits)
+        start_num = i
+        while i < n and stripped[i].isdigit():
+            i += 1
+        if start_num == i:
+            # no digits where we expected a number
+            raise ValueError(f"missing number in duration at position {start_num}")
+        num_str = stripped[start_num:i]
+        # leading zeros are fine
+        value = int(num_str)
+        
+        # after number, must have a unit directly (no whitespace)
+        if i >= n:
+            raise ValueError(f"missing unit after number '{num_str}'")
+        
+        # try to match unit; check longer first ('ms') then single letters
+        unit = None
+        if i + 1 < n and stripped[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        else:
+            ch = stripped[i]
+            if ch in ('d', 'h', 'm', 's'):
+                unit = ch
+                i += 1
+            else:
+                raise ValueError(f"unknown unit after number '{num_str}' at position {i}")
+        
+        # duplicate unit check
+        if unit in seen_units:
+            raise ValueError(f"duplicate unit '{unit}'")
+        seen_units.add(unit)
+        
+        # order check
+        curr_rank = rank[unit]
+        if prev_rank is not None and curr_rank >= prev_rank:
+            raise ValueError(f"units out of order: '{unit}' after previous unit with rank {prev_rank}")
+        prev_rank = curr_rank
+        
+        # convert to seconds and add
+        factor = {
+            'd': 86400,
+            'h': 3600,
+            'm': 60,
+            's': 1,
+            'ms': 0.001
+        }[unit]
+        total += value * factor
+        
+        # after unit, loop continues (whitespace will be skipped at top)
+    
+    # After loop, ensure we consumed all characters (any leftover non-whitespace would have caused error)
+    # but we can double-check that there is no leftover non-whitespace
+    while i < n:
+        if not stripped[i].isspace():
+            raise ValueError(f"unexpected character '{stripped[i]}' at position {i}")
+        i += 1
+    
+    return total
```

## 5. Fresh-branch verification
Existing suite: OK (6 passed of 6). Sealed suite: OK (28 passed of 28). Operation `01a13edf-9d6b-755e-91f0-21b62d07f4b8`, networking disabled, disposable branch from the checkpoint.

## 6. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1537 | 1973 | 0 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1689 | 2222 | 0 | 12.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1420 | 67 | 0 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1492 | 79 | 0 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1668 | 98 | 0 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1916 | 2096 | 0 | 11.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2076 | 170 | 0 | 3.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3041 | 89 | 0 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3282 | 841 | 0 | 6.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 4300 | 2583 | 0 | 13.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 6720 | 103 | 0 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 6891 | 166 | 0 | 3.4s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 36032/10487/0; USD: 0.025468.

| Sandbox op | Operation | Status | Exit | Duration | Image | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13ede-28bb-750a-bb58-c16869789977 | SUCCESS | 0 | 0.775s | retained | 0.00278851 |
| red-1 | 01a13ede-869f-7344-a943-d50274461d2c | SUCCESS | 0 | 0.776s | disposable | 0.00281459 |
| impl-tests-6 | 01a13ede-fea0-76e9-a298-90f951be33b8 | SUCCESS | 0 | 0.751s | disposable | 0.0028104400000000004 |
| impl-python-7 | 01a13edf-27b6-7538-a12a-3f2a0c27ab8c | SUCCESS | 0 | 0.543s | disposable | 0.00115944 |
| impl-python-8 | 01a13edf-69b5-73c9-acf6-55dc266b3526 | SUCCESS | 0 | 0.553s | disposable | 0.00116339 |
| impl-tests-9 | 01a13edf-8030-73d2-8f0a-a0d9e4a78a06 | SUCCESS | 0 | 0.735s | disposable | 0.0027588400000000003 |
| verify | 01a13edf-9d6b-755e-91f0-21b62d07f4b8 | SUCCESS | 0 | 0.937s | disposable | 0.004483890000000001 |

Sandbox operations: 7, total guest duration 5.07s, retained images ['9dc49965-9210-4ec4-a7a8-e772ce72e8ab'].

## 7. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- First slice: single candidate, no breaker/mutation pass, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- Sandbox CPU/RAM quotas are not configurable through the public REST schema; only max_layer_bytes, a timeout and networking=off are enforced per operation.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge.
- The retained checkpoint image stays on the service (no documented delete endpoint) and is listed in the ledger.
