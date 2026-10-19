# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: BASELINE**  
Run `durationkit-units-001-20261015T183630Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:36:30.500094+00:00, finished 2026-10-15T18:37:58.344677+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6a379539-fcb2-4e10-8cd0-0fe69120eb13`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

(none)

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
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,70 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    The string can be a plain non-negative integer representing seconds,
+    or a sequence of components with units d (days), h (hours), m (minutes),
+    s (seconds), ms (milliseconds). Components must be in descending order
+    of units and each unit may appear at most once. Whitespace is allowed
+    around the string and between components.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError(f"empty duration: {text!r}")
+
+    # If it's just a plain number of seconds (old format)
+    if stripped.isdigit():
+        return float(stripped)
+
+    # Otherwise parse the new format
+    total = 0.0
+    i = 0
+    n = len(stripped)
+    seen_units = set()
+    # order index: d=0, h=1, m=2, s=3, ms=4
+    order_index = {'d':0, 'h':1, 'm':2, 's':3, 'ms':4}
+    last_index = -1  # to ensure descending order
+
+    while i < n:
+        # Parse number (must be at least one digit)
+        if not stripped[i].isdigit():
+            raise ValueError(f"invalid duration: {text!r}")
+        start = i
+        while i < n and stripped[i].isdigit():
+            i += 1
+        num_str = stripped[start:i]
+        # After number, we must have a unit
+        if i >= n:
+            raise ValueError(f"missing unit in duration: {text!r}")
+        # Check for two-letter unit 'ms'
+        if stripped[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif stripped[i] in 'dhms':
+            unit = stripped[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit in duration: {text!r}")
+
+        # Check for repeated unit
+        if unit in seen_units:
+            raise ValueError(f"repeated unit in duration: {text!r}")
+        seen_units.add(unit)
+
+        # Check descending order
+        cur_index = order_index[unit]
+        if cur_index <= last_index:
+            raise ValueError(f"units out of order in duration: {text!r}")
+        last_index = cur_index
+
+        # Convert number to float and add
+        value = int(num_str)
+        factors = {'d':86400, 'h':3600, 'm':60, 's':1, 'ms':0.001}
+        total += value * factors[unit]
+
+        # Skip any whitespace after unit (allowed between components)
+        while i < n and stripped[i].isspace():
+            i += 1
+
+    return total
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: n/a (0 passed of 0). Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint.

(none)

Held-out suite: none configured.

## 6. Gates
(none)

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Drift audit not run.



## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1361 | 87 | 0 | 0.000487 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1454 | 118 | 0 | 0.000542 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1655 | 130 | 0 | 0.000614 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1861 | 2493 | 0 | 0.002802 | 13.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2076 | 6227 | 0 | 0.006227 | 28.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3043 | 110 | 0 | 0.001012 | 6.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3306 | 1150 | 0 | 0.002027 | 6.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 4234 | 270 | 0 | 0.001513 | 8.3s | ok |

Model calls: 8 (0 failed, 0 malformed); tokens in/out/cached 18990/10585/0; USD: 0.015224.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140da-2009-779d-a5d0-71b45defe8e5 | SUCCESS | 0 | 0.723s | retained | off | 0.00275846 |
| impl-tests-6 | 01a140db-0e06-71f3-97ca-68c5988d5b6b | SUCCESS | 0 | 0.759s | disposable | off | 0.0027462299999999997 |
| impl-python-7 | 01a140db-377b-7208-b02a-5a76725cd0a2 | SUCCESS | 0 | 0.539s | disposable | off | 0.0011352200000000002 |

Sandbox operations: 3, total guest duration 2.021s, retained images ['6a379539-fcb2-4e10-8cd0-0fe69120eb13'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
