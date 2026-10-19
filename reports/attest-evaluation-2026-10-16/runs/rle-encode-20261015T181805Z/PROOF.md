# Attest Proof Bundle: rle-encode

**Verdict: NEEDS HUMAN**  
Run `rle-encode-20261015T181805Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:18:05.316701+00:00, finished 2026-10-15T18:20:23.247197+00:00.

Reasons: child process nonzero exit: test_round_trip_property exit 1
Warnings: arbitration (advisory): 1 failing test(s) indicate a real implementation bug; human review required

## 1. Frozen task
Task `rle-encode`, spec digest `46f6d840c3b61a78e676dd7851d6347660ad71b9f5558f7e34b5411691f148af`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `adc2cb1d-0bbd-4d20-b23b-9f77bca07b4c`; test runner `unittest`; install: `none` (checkpoint networking off).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. Implement the `encode` function in the `rle` package to perform run-length encoding on a string. Each maximal run of identical characters is replaced by the character followed by its decimal count (always written, even for a count of 1). The function must return a string, raise `TypeError` for non-string inputs, and satisfy the round-trip property `decode(encode(x)) == x` for all strings `x`. The existing `decode` function and tests must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| encode | encode(s: str) -> str | Returns the run-length encoding of the input string `s`. Each maximal run of a single character is represented as that character followed by the decimal count o | TypeError: raised when `s` is not a string. |
| decode | decode(s: str) -> str | Decodes a run-length encoded string `s` back to the original string. The input must consist of a character followed by one or more digits for each run. For exam | TypeError: raised when `s` is not a string.; ValueError: raised when a character is not followed by at least one digit (missing count). |

Acceptance criteria:
1. encode('aaabbc') == 'a3b2c1'
2. encode('a') == 'a1'
3. encode('') == ''
4. encode('abc') == 'a1b1c1' (count written even when 1)
5. encode('x' * 12) == 'x12' (multi-digit counts)
6. decode(encode(x)) == x for every string x (round-trip property)
7. encode returns a str instance
8. encode raises TypeError when the argument is not a string (e.g., encode(123) raises TypeError)
9. The existing decode function behavior is unchanged: decode('a3b1') == 'aaab', decode('') == '', and decode(123) raises TypeError
10. encode handles strings with multiple runs of the same character separated by other characters (e.g., encode('aaabba') == 'a3b2a1')

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `76aeccd40192e5d5fad60ef470aa4d1ffc72a891a1e9e876b0c539f39114b0f1`, 12 test methods, sealed at 2026-10-15T18:18:48.392012+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 12 methods: ERROR 9): 9 of 12 methods failing, 3 passing; operation `01a140c9-ae44-70e1-a904-9716a22239e5`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestDecodeUnchanged.test_decode_a3b1 | ok (1 ev) | ok (1 ev) |
| test_sealed.TestDecodeUnchanged.test_decode_empty | ok (1 ev) | ok (1 ev) |
| test_sealed.TestDecodeUnchanged.test_decode_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_aaabbc | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_each_char_one | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_empty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_multi_digit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_returns_str | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_single_char | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAdditional.test_encode_multiple_runs_separated | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAdditional.test_round_trip_property | ERROR (1 ev) | FAIL (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 9 implementer turn(s).

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
Existing suite: OK (2 passed of 2). Sealed suite: FAILED (1 of 12 methods: FAIL 1). Operation `01a140ca-b5f7-7059-8f34-d27c76f03da6`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| static_ids_match_red | pass |
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |

Held-out suite (tests/test_heldout.py): OK (9 passed of 9); operation `01a140ca-d609-72ce-805f-2444b4701c7b`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | FAIL | child process nonzero exit: test_round_trip_property exit 1 |
| heldout_suite | pass | OK |
| mutation | FAIL | not run: verification did not pass |
| adversarial_tests | FAIL | not run: verification did not pass |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The implementation of encode in rle/core.py meets all specified requirements, including run-length encoding, TypeError for non-strings, and round-trip compatibility with decode. All tests pass and no unauthorized changes were made.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
1 failing test(s) indicate a real implementation bug; human review required (mode: advisory). Classifications: {'implementation_bug': 1, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale |
| --- | --- | --- |
| test_round_trip_property | implementation_bug | The round-trip test fails, meaning the candidate's encode function does not satisfy the required property decode(encode(x)) == x for all tes |

- `sealed` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1133 | 2974 | 0 | 0.010055 | 11.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1412 | 3109 | 0 | 0.003222 | 14.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1433 | 76 | 0 | 0.000498 | 2.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1524 | 113 | 0 | 0.000559 | 2.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1770 | 689 | 0 | 0.001151 | 4.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2013 | 90 | 0 | 0.000685 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2157 | 233 | 0 | 0.000857 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2317 | 450 | 0 | 0.001100 | 3.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 2596 | 235 | 0 | 0.000990 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 2768 | 131 | 0 | 0.000948 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 2913 | 215 | 0 | 0.001067 | 3.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1856 | 1518 | 0 | 0.006410 | 6.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-sealed | default | 2195 | 4531 | 0 | 0.015788 | 20.3s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 26087/14364/0; USD: 0.04333.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140c9-3a1d-719f-8919-fa0113616865 | SUCCESS | 0 | 0.867s | retained | off | 0.00275826 |
| red-1 | 01a140c9-ae44-70e1-a904-9716a22239e5 | SUCCESS | 0 | 2.849s | disposable | off | 0.02188963 |
| impl-tests-4 | 01a140ca-06ef-72a3-af9d-14adf6f9560c | SUCCESS | 0 | 0.822s | disposable | off | 0.00276963 |
| impl-python-6 | 01a140ca-319e-7381-abc1-4358d1f828e5 | SUCCESS | 0 | 0.548s | disposable | off | 0.0011412299999999998 |
| impl-python-7 | 01a140ca-4b9b-742f-9b39-c8a4f45e50a9 | SUCCESS | 0 | 0.575s | disposable | off | 0.00112093 |
| impl-tests-8 | 01a140ca-66a3-77be-acb8-631c89bf1ffa | SUCCESS | 0 | 0.832s | disposable | off | 0.00280818 |
| verify | 01a140ca-b5f7-7059-8f34-d27c76f03da6 | SUCCESS | 0 | 2.976s | disposable | off | 0.023133260000000003 |
| heldout | 01a140ca-d609-72ce-805f-2444b4701c7b | SUCCESS | 0 | 0.778s | disposable | off | 0.00280088 |

Sandbox operations: 8, total guest duration 10.247s, retained images ['adc2cb1d-0bbd-4d20-b23b-9f77bca07b4c'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
