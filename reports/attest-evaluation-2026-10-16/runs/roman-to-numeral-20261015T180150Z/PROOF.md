# Attest Proof Bundle: roman-to-numeral

**Verdict: BASELINE**  
Run `roman-to-numeral-20261015T180150Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:01:50.761097+00:00, finished 2026-10-15T18:02:46.678836+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e3f14481-6710-4990-ab23-4f2887298324`; test runner `unittest`; install: `none` (checkpoint networking off).

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
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,19 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    """Convert an integer to a Roman numeral."""
+    if type(n) is not int:
+        raise TypeError("Argument must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("Argument must be between 1 and 3999 inclusive")
+    val_sym = [
+        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
+        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
+        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
+    ]
+    result = []
+    for value, symbol in val_sym:
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1102 | 115 | 0 | 0.000434 | 4.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1191 | 113 | 0 | 0.000459 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1371 | 153 | 0 | 0.000549 | 8.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1546 | 1362 | 0 | 0.001690 | 8.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 1921 | 125 | 0 | 0.000689 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2068 | 879 | 0 | 0.001411 | 5.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 2478 | 215 | 0 | 0.000937 | 3.5s | ok |

Model calls: 7 (0 failed, 0 malformed); tokens in/out/cached 11677/2962/0; USD: 0.006169.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140ba-5d29-7463-a766-b3602a651402 | SUCCESS | 0 | 0.748s | retained | off | 0.00274903 |
| impl-tests-5 | 01a140ba-ecc1-72d7-b0d9-5ad51dd14797 | SUCCESS | 0 | 0.802s | disposable | off | 0.0028136399999999996 |
| impl-python-6 | 01a140bb-1295-760f-a296-ee5a2dfa33cb | SUCCESS | 0 | 0.524s | disposable | off | 0.0011339499999999999 |

Sandbox operations: 3, total guest duration 2.074s, retained images ['e3f14481-6710-4990-ab23-4f2887298324'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
