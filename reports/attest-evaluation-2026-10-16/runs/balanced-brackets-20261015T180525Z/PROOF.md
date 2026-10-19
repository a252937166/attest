# Attest Proof Bundle: balanced-brackets

**Verdict: BASELINE**  
Run `balanced-brackets-20261015T180525Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:05:25.300112+00:00, finished 2026-10-15T18:06:00.370128+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `balanced-brackets`, spec digest `b4b1ed357cf1c1bd54b85a7c1e9d3157d00ec207969b2cf0547512c4dbe167c8`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `baa313d5-03bd-4c96-bfb2-c15e5ad9f18c`; test runner `unittest`; install: `none` (checkpoint networking off).

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
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,18 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    """Return True if brackets in s are balanced, False otherwise.
+    Raises TypeError if s is not a string.
+    """
+    if not isinstance(s, str):
+        raise TypeError("s must be a string")
+    stack = []
+    for ch in s:
+        if is_bracket(ch):
+            if ch in OPEN:
+                stack.append(ch)
+            else:  # ch in CLOSE
+                if not stack or stack[-1] != PAIRS[ch]:
+                    return False
+                stack.pop()
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 974 | 84 | 0 | 0.000368 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1066 | 110 | 0 | 0.000419 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1270 | 875 | 0 | 0.001169 | 6.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1544 | 269 | 0 | 0.000705 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 1687 | 481 | 0 | 0.000939 | 4.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2110 | 188 | 0 | 0.000802 | 3.1s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 8651/2007/0; USD: 0.004402.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140bd-9ee0-7516-a412-1b7133c13132 | SUCCESS | 0 | 0.767s | retained | off | 0.0027953199999999996 |
| impl-tests-4 | 01a140bd-e4bc-778f-82e9-5f2a8ecc33ee | SUCCESS | 0 | 0.765s | disposable | off | 0.00287816 |
| impl-python-5 | 01a140be-05ac-7732-ba45-68f24cc7b99d | SUCCESS | 0 | 0.547s | disposable | off | 0.00114797 |

Sandbox operations: 3, total guest duration 2.079s, retained images ['baa313d5-03bd-4c96-bfb2-c15e5ad9f18c'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
