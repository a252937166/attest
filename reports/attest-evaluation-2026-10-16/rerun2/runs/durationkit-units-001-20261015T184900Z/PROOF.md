# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: BASELINE**  
Run `durationkit-units-001-20261015T184900Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:49:00.082707+00:00, finished 2026-10-15T18:50:33.115752+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `4a38cb5c-f0b7-492e-ac8e-4b46a17cb019`; test runner `unittest`; install: `none` (checkpoint networking off).

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
1 changed path(s); scope check passed; 11 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,101 @@
-"""Duration parsing."""
+'''Duration parsing.'''
 
 
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer number of seconds (e.g. "90") or
+    one or more components made of a non-negative integer followed by a unit:
+    d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds).
+    Components must appear in descending unit order (e.g. "2d4h", "1h30m"),
+    each unit may appear at most once, and whitespace is allowed around the
+    whole string and between components (but not between a number and its unit).
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
+        raise ValueError(f"empty duration: {text!r}")
+
+    # Plain integer seconds (existing behavior)
+    if s.isdigit():
+        return float(s)
+
+    # Parse components
+    i = 0
+    n = len(s)
+    total = 0.0
+    # unit order: d > h > m > s > ms
+    order = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    seen = set()
+    last_order = -1  # nothing seen yet
+
+    while i < n:
+        # skip whitespace between components
+        while i < n and s[i].isspace():
+            i += 1
+        if i >= n:
+            break  # trailing whitespace
+
+        # parse number
+        start_num = i
+        while i < n and s[i].isdigit():
+            i += 1
+        if start_num == i:
+            raise ValueError(f"missing number in duration: {text!r}")
+        num_str = s[start_num:i]
+        # Leading zeros are okay; int conversion works.
+        try:
+            value = int(num_str)
+        except ValueError:
+            raise ValueError(f"invalid number in duration: {text!r}")
+        if value < 0:
+            raise ValueError(f"negative number in duration: {text!r}")
+
+        # parse unit
+        if i >= n:
+            raise ValueError(f"missing unit in duration: {text!r}")
+        # check for ms first because it's two chars
+        if s[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif s[i] in 'dhms':
+            unit = s[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit in duration: {text!r}")
+
+        # check repetition
+        if unit in seen:
+            raise ValueError(f"repeated unit '{unit}' in duration: {text!r}")
+        seen.add(unit)
+
+        # check order
+        cur_order = order[unit]
+        if cur_order <= last_order:
+            raise ValueError(f"units out of descending order in duration: {text!r}")
+        last_order = cur_order
+
+        # add to total
+        if unit == 'd':
+            total += value * 86400.0
+        elif unit == 'h':
+            total += value * 3600.0
+        elif unit == 'm':
+            total += value * 60.0
+        elif unit == 's':
+            total += value * 1.0
+        elif unit == 'ms':
+            total += value * 0.001
+        else:
+            # shouldn't happen
+            raise ValueError(f"unsupported unit: {unit}")
+
+    # after loop, skip any trailing whitespace
+    while i < n and s[i].isspace():
+        i += 1
+    if i != n:
+        raise ValueError(f"unexpected characters in duration: {text!r}")
+
+    return float(total)
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1361 | 108 | 0 | 0.000505 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1559 | 1788 | 0 | 0.002077 | 10.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1766 | 3210 | 0 | 0.003419 | 15.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1950 | 148 | 0 | 0.000718 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2890 | 1126 | 0 | 0.001880 | 6.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2718 | 244 | 0 | 0.001035 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3656 | 1487 | 0 | 0.002435 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 4458 | 1496 | 0 | 0.002684 | 9.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 4716 | 367 | 0 | 0.001745 | 4.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 5461 | 1621 | 0 | 0.003097 | 8.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 6095 | 496 | 0 | 0.002275 | 4.3s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 36630/12091/0; USD: 0.02187.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140e5-851d-754b-a584-7277df3d4938 | SUCCESS | 0 | 0.758s | retained | off | 0.0027703999999999997 |
| impl-tests-5 | 01a140e6-2573-7719-ae3e-ae2208424a5f | SUCCESS | 0 | 0.782s | disposable | off | 0.00274315 |
| impl-python-7 | 01a140e6-5e26-72eb-bb47-5ffdc298c564 | SUCCESS | 0 | 0.568s | disposable | off | 0.00122918 |
| impl-tests-8 | 01a140e6-8e53-748a-aaff-a2589b1c5139 | SUCCESS | 0 | 0.714s | disposable | off | 0.00276823 |
| impl-python-10 | 01a140e6-cd76-751f-a689-115612a44404 | SUCCESS | 0 | 0.537s | disposable | off | 0.00112741 |

Sandbox operations: 5, total guest duration 3.359s, retained images ['4a38cb5c-f0b7-492e-ac8e-4b46a17cb019'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
