# Attest Proof Bundle: rle-encode

**Verdict: BASELINE**  
Run `rle-encode-20261016T192806Z` · profile `eval-baseline-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:28:06.836688+00:00, finished 2026-10-16T19:32:07.115126+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `rle-encode`, spec digest `e64da208acc97bfcb964f579c1a5687bc6340ce7531452982870487fe1231c41`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `34edbc35-cbbd-4174-9626-dc211deb49d6`; test runner `unittest`; install: `none` (checkpoint networking off).

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
@@ -20,4 +20,21 @@
 
 
 def encode(s):
-    raise NotImplementedError("encode is not implemented yet")
+    """Encode each maximal run as its character followed by its count."""
+    if not isinstance(s, str):
+        raise TypeError("encode expects a string")
+    if not s:
+        return ""
+
+    out = []
+    ch = s[0]
+    count = 1
+    for next_ch in s[1:]:
+        if next_ch == ch:
+            count += 1
+        else:
+            out.append(ch + str(count))
+            ch = next_ch
+            count = 1
+    out.append(ch + str(count))
+    return "".join(out)
```




## 5. Fresh-branch verification (bound to the sealed suite)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

Held-out suite: none configured.

## 6. Gates
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

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
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 9669 | 89 | 0 | - | 16.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 20260 | 663 | 9728 | - | 85.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10171 | 305 | 0 | - | 65.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10314 | 676 | 0 | - | 28.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 10517 | 583 | 0 | - | 28.6s | ok |

Model calls: 5 (0 failed, 0 malformed); tokens in/out/cached 60931/2316/9728; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1462f-b3c9-71f7-bba6-ecc906b03483 | SUCCESS | 0 | 0.815s | retained | off | 0.0027928899999999997 |
| impl-tests-3 | 01a14632-5e1b-7557-b194-e0335fd83aad | SUCCESS | 0 | 0.713s | disposable | off | 0.00279394 |
| impl-python-4 | 01a14632-da4b-7215-bd41-8fbfd787cbf8 | SUCCESS | 0 | 0.525s | disposable | off | 0.0011407300000000002 |

Sandbox operations: 3, total guest duration 2.053s, retained images ['34edbc35-cbbd-4174-9626-dc211deb49d6'].

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
