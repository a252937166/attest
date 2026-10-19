# Attest Proof Bundle: balanced-brackets

**Verdict: BASELINE**  
Run `balanced-brackets-20261015T183344Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:33:44.214686+00:00, finished 2026-10-15T18:34:18.233852+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `balanced-brackets`, spec digest `b4b1ed357cf1c1bd54b85a7c1e9d3157d00ec207969b2cf0547512c4dbe167c8`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ae33bc84-1268-4b4e-846b-487a8b5d81f0`; test runner `unittest`; install: `none` (checkpoint networking off).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

(none)

Acceptance criteria:
1. '', '()', '[]', '{}', '()[]{}', '([{}])' are all balanced (True)
2. nested mixed brackets with other characters are balanced: '(a[b]{c})', 'f(x[0], y[1])'
3. '(', ')', '([)]', '(]', '{[}', '())' are not balanced (False)
4. non-bracket characters are ignored
5. is_balanced returns a bool
6. TypeError when s is not a string

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,14 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("Input must be a string")
+    stack = []
+    for ch in s:
+        if ch in OPEN:
+            stack.append(ch)
+        elif ch in PAIRS:
+            if not stack or stack[-1] != PAIRS[ch]:
+                return False
+            stack.pop()
+    return not stack
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 974 | 113 | 0 | 0.000394 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1164 | 180 | 0 | 0.000511 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1358 | 1464 | 0 | 0.001725 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1579 | 98 | 0 | 0.000562 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 1720 | 283 | 0 | 0.000771 | 3.4s | ok |

Model calls: 5 (0 failed, 0 malformed); tokens in/out/cached 6795/2138/0; USD: 0.003963.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140d7-a4b7-7194-86ae-e9cba62bc554 | SUCCESS | 0 | 0.79s | retained | off | 0.00274367 |
| impl-tests-4 | 01a140d7-f058-72b3-934f-fb2e13bc0ba6 | SUCCESS | 0 | 0.847s | disposable | off | 0.00275917 |

Sandbox operations: 2, total guest duration 1.637s, retained images ['ae33bc84-1268-4b4e-846b-487a8b5d81f0'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
