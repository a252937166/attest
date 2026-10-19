# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: BASELINE**  
Run `durationkit-units-001-20261015T182054Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:20:54.593465+00:00, finished 2026-10-15T18:23:02.893378+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ea2e724d-3025-4349-bc22-3abda2961984`; test runner `unittest`; install: `none` (checkpoint networking off).

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
1 changed path(s); scope check passed; 13 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,78 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer number of seconds (e.g. ``\"90\"") or
+    one or more components made of a non-negative integer followed by a unit:
+    d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds).
+    Components must appear in descending unit order (e.g. ``'2d4h'``,
+    ``'1h30m'``), each unit may appear at most once, and whitespace is allowed
+    around the whole string and between components (but not between a number
+    and its unit). The function returns the total number of seconds as a float
+    (so ``'500ms'`` is 0.5 and ``'1h30m'`` is 5400.0).
+
+    Raises:
+        TypeError: if ``text`` is not a string.
+        ValueError: for empty or whitespace-only input, negative numbers,
+            fractional numbers, unknown units, repeated units, components out
+            of descending order, a unit without a number, or any other malformed
+            text.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("empty duration")
+    # Plain integer seconds (existing behavior)
+    if stripped.isdigit():
+        return float(stripped)
+    # Extended format
+    total = 0.0
+    i = 0
+    n = len(stripped)
+    # unit to rank (lower rank = larger unit)
+    rank = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    # unit to seconds multiplier
+    mult = {
+        'd': 86400,
+        'h': 3600,
+        'm': 60,
+        's': 1,
+        'ms': 0.001,
+    }
+    seen = set()
+    prev_rank = -1
+    while i < n:
+        # skip whitespace
+        while i < n and stripped[i].isspace():
+            i += 1
+        if i >= n:
+            break
+        # parse number
+        start = i
+        while i < n and stripped[i].isdigit():
+            i += 1
+        if start == i:
+            raise ValueError(f"missing number in duration: {text!r}")
+        num = int(stripped[start:i])
+        # parse unit
+        if i >= n:
+            raise ValueError(f"missing unit in duration: {text!r}")
+        if i + 1 < n and stripped[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif stripped[i] in 'dhms':
+            unit = stripped[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit in duration: {text!r}")
+        # validation
+        if unit in seen:
+            raise ValueError(f"repeated unit in duration: {text!r}")
+        seen.add(unit)
+        r = rank[unit]
+        if r <= prev_rank:
+            raise ValueError(f"units out of order in duration: {text!r}")
+        prev_rank = r
+        total += num * mult[unit]
+    # after loop, allow trailing whitespace (already skipped at top of loop)
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1361 | 88 | 0 | 0.000487 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1455 | 98 | 0 | 0.000525 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1656 | 132 | 0 | 0.000616 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1860 | 1996 | 0 | 0.002354 | 13.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2064 | 3297 | 0 | 0.003586 | 18.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2247 | 192 | 0 | 0.000847 | 5.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3080 | 91 | 0 | 0.001006 | 7.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 2998 | 135 | 0 | 0.001021 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 3831 | 875 | 0 | 0.001937 | 5.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 4533 | 147 | 0 | 0.001492 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 5208 | 3779 | 0 | 0.004964 | 16.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 4861 | 135 | 0 | 0.001580 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | default | 4923 | 1512 | 0 | 0.002838 | 10.0s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 40077/12477/0; USD: 0.023253.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140cb-d154-74c1-968a-ddb6bfa132b6 | SUCCESS | 0 | 0.747s | retained | off | 0.00276679 |
| impl-tests-7 | 01a140cc-b6d7-7206-9f4c-e9cbe03dbee6 | SUCCESS | 0 | 0.767s | disposable | off | 0.0027616699999999995 |
| impl-python-9 | 01a140cc-f6f2-7009-bced-c3d727edb5f0 | SUCCESS | 0 | 0.592s | disposable | off | 0.0011190500000000001 |
| impl-tests-12 | 01a140cd-69a7-710e-a0fa-8e8176bdc178 | SUCCESS | 0 | 0.824s | disposable | off | 0.00274604 |

Sandbox operations: 4, total guest duration 2.93s, retained images ['ea2e724d-3025-4349-bc22-3abda2961984'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
