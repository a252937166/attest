# Attest Proof Bundle: rle-encode

**Verdict: BASELINE**  
Run `rle-encode-20261015T180150Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:01:50.760963+00:00, finished 2026-10-15T18:02:22.797891+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `rle-encode`, spec digest `46f6d840c3b61a78e676dd7851d6347660ad71b9f5558f7e34b5411691f148af`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e38dda71-7b13-49df-817b-7b546a5674f2`; test runner `unittest`; install: `none` (checkpoint networking off).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

(none)

Acceptance criteria:
1. encode('aaabbc')=='a3b2c1' and encode('a')=='a1'
2. encode('')==''
3. encode('abc')=='a1b1c1' (count written even when 1)
4. encode('x'*12)=='x12' (multi-digit counts)
5. decode(encode(x))==x for every string x
6. encode returns a str
7. TypeError when s is not a string

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/rle/core.py
+++ b/rle/core.py
@@ -20,4 +20,19 @@
 
 
 def encode(s):
-    raise NotImplementedError("encode is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("encode expects a string")
+    if not s:
+        return ""
+    result = []
+    count = 1
+    prev = s[0]
+    for ch in s[1:]:
+        if ch == prev:
+            count += 1
+        else:
+            result.append(prev + str(count))
+            prev = ch
+            count = 1
+    result.append(prev + str(count))
+    return "".join(result)
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1011 | 139 | 0 | 0.000428 | 3.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1250 | 146 | 0 | 0.000506 | 3.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1500 | 516 | 0 | 0.000914 | 4.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1743 | 96 | 0 | 0.000609 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 1889 | 585 | 0 | 0.001093 | 5.6s | ok |

Model calls: 5 (0 failed, 0 malformed); tokens in/out/cached 7393/1482/0; USD: 0.00355.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140ba-622d-7247-8667-b55025ee2680 | SUCCESS | 0 | 0.74s | retained | off | 0.00275734 |
| impl-tests-4 | 01a140ba-aba4-7509-bc2e-81c4d300b005 | SUCCESS | 0 | 0.768s | disposable | off | 0.002738 |

Sandbox operations: 2, total guest duration 1.508s, retained images ['e38dda71-7b13-49df-817b-7b546a5674f2'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
