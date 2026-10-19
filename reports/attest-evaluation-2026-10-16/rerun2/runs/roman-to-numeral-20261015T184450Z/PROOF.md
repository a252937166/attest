# Attest Proof Bundle: roman-to-numeral

**Verdict: BASELINE**  
Run `roman-to-numeral-20261015T184450Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:44:50.561920+00:00, finished 2026-10-15T18:45:46.585712+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `566e3c04-83e4-46fe-8211-60bf7879b473`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

(none)

Acceptance criteria:
1. to_roman(1)=='I', to_roman(4)=='IV', to_roman(9)=='IX'
2. to_roman(40)=='XL', to_roman(90)=='XC', to_roman(400)=='CD', to_roman(900)=='CM'
3. to_roman(2024)=='MMXXIV', to_roman(3999)=='MMMCMXCIX', to_roman(1994)=='MCMXCIV'
4. to_roman returns a str
5. ValueError for ints outside 1..3999 (0, -1, 4000)
6. TypeError for non-int input ('5', 5.0, None, [1])

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,19 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    if not isinstance(n, int):
+        raise TypeError("Argument must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("Argument must be between 1 and 3999 inclusive")
+    roman_numerals = [
+        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
+        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
+        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'),
+        (1, 'I')
+    ]
+    result = []
+    for value, symbol in roman_numerals:
+        while n >= value:
+            result.append(symbol)
+            n -= value
+    return ''.join(result)
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1102 | 79 | 0 | 0.000402 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1191 | 95 | 0 | 0.000443 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1369 | 1788 | 0 | 0.002020 | 10.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1722 | 122 | 0 | 0.000626 | 5.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 1864 | 544 | 0 | 0.001049 | 4.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2267 | 218 | 0 | 0.000876 | 2.9s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 9515/2846/0; USD: 0.005416.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140e1-c7a3-7001-99c1-5a50757f95aa | SUCCESS | 0 | 0.776s | retained | off | 0.00276146 |
| impl-tests-4 | 01a140e2-47bf-77b6-b8bd-41ae73081b31 | SUCCESS | 0 | 0.753s | disposable | off | 0.00274277 |
| impl-python-5 | 01a140e2-739a-721e-86c4-cf7bc5c022d9 | SUCCESS | 0 | 0.555s | disposable | off | 0.0011435999999999998 |

Sandbox operations: 3, total guest duration 2.084s, retained images ['566e3c04-83e4-46fe-8211-60bf7879b473'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
