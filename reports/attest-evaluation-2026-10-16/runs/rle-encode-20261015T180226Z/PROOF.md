# Attest Proof Bundle: rle-encode

**Verdict: NEEDS HUMAN**  
Run `rle-encode-20261015T180226Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:02:26.977401+00:00, finished 2026-10-15T18:05:34.226283+00:00.

Reasons: model-written adversarial tests failed: 2 of 9 (test_breaker.TestBreaker.test_roundtrip_with_digits, test_breaker.TestBreaker.test_encode_newline_and_tab); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): 1 failing test(s) indicate a real implementation bug; human review required

## 1. Frozen task
Task `rle-encode`, spec digest `46f6d840c3b61a78e676dd7851d6347660ad71b9f5558f7e34b5411691f148af`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `85e8cdd9-afa4-4492-b6a4-6bc15f6c7123`; test runner `unittest`; install: `none` (checkpoint networking off).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. Implement the encode function in the rle package to perform run-length encoding on a string. Each maximal run of a single character must be represented as that character followed by its decimal count (always written, even for a count of 1). The function must return a string, raise TypeError for non-string inputs, and satisfy the round-trip property decode(encode(x)) == x for all strings x. The existing decode function must not be altered.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| encode | encode(s: str) -> str | Run-length encodes the input string s. Each maximal run of identical characters is replaced by the character followed by the decimal representation of the run l | TypeError if s is not a string |
| decode | decode(s: str) -> str | Decodes a run-length encoded string s. Expects each character followed by a decimal count (one or more digits). Returns the expanded string. For empty input, re | TypeError if s is not a string; ValueError if a character is not followed by at least one digit (missing count) |

Acceptance criteria:
1. encode('aaabbc') returns 'a3b2c1'
2. encode('a') returns 'a1'
3. encode('') returns ''
4. encode('abc') returns 'a1b1c1'
5. encode('x'*12) returns 'x12'
6. For any string x, decode(encode(x)) == x (round-trip property). This must hold for empty string, single character, multiple runs, and runs with multi-digit counts.
7. encode returns a value of type str
8. encode raises TypeError when the input is not a string (e.g., integer, list, None)

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `bc2cdfd8aab0131a1db19f0d93a971dae2351decb9b0a7a547247ac0eaf379b0`, 13 test methods, sealed at 2026-10-15T18:03:08.524114+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 13 methods: ERROR 13): 13 of 13 methods failing, 0 passing; operation `01a140bb-6977-7684-8185-f9688ee31c7a`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_abc_returns_a1b1c1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_empty_string_returns_empty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_long_run_returns_char_and_count | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_returns_str_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_single_char_returns_char_plus_one | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_type_error_on_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_type_error_on_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_encode_type_error_on_none | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_roundtrip_empty_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_roundtrip_multi_digit_counts | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_roundtrip_multiple_runs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeAcceptance.test_roundtrip_single_character | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

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
+    current_char = s[0]
+    count = 1
+    for ch in s[1:]:
+        if ch == current_char:
+            count += 1
+        else:
+            result.append(current_char + str(count))
+            current_char = ch
+            count = 1
+    result.append(current_char + str(count))
+    return "".join(result)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (2 passed of 2). Sealed suite: OK (13 of 13 methods, each in its own process). Operation `01a140bc-0f67-710b-ac04-0fe1108fda33`, networking disabled, disposable branch from the checkpoint.

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
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |

Held-out suite (tests/test_heldout.py): OK (9 passed of 9); operation `01a140bc-27d2-7017-8f65-9090515a2bee`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | OK |
| mutation | pass | score 1.0 on 11 mutants |
| adversarial_tests | FAIL | FAILED (2 of 9 methods: FAIL 2) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 11 generated, 11 evaluated: 11 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-8ec8ddc94d | rle/core.py | 23 | remove `not` | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_single_ | 01a140bc-35f0-76c8-a67e-5de12df064f2 |
| m02-d577c0fd83 | rle/core.py | 24 | raise -> pass | killed | test_sealed.TestEncodeAcceptance.test_encode_type_error_on_none | 01a140bc-39fd-7603-a7ee-0fc6d687d13f |
| m03-d71b8e165a | rle/core.py | 25 | remove `not` | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_single_ | 01a140bc-35f3-72ff-93e2-08bee08e1c92 |
| m04-4041d1d761 | rle/core.py | 28 | 0 -> 1 | killed | test_sealed.TestEncodeAcceptance.test_encode_single_char_returns_char_plus_one, test_sealed.TestEncodeAcceptance.test_en | 01a140bc-35fa-72a5-82e2-40a48668bc88 |
| m05-697d3a6162 | rle/core.py | 29 | 1 -> 2 | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_single_ | 01a140bc-35ed-7022-b549-f590a7994771 |
| m06-d95fbb9afb | rle/core.py | 30 | 1 -> 2 | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_abc_ret | 01a140bc-3a8f-734c-b3b4-fe516323cb62 |
| m07-4d9f698d3f | rle/core.py | 31 | Eq -> NotEq | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_abc_ret | 01a140bc-35ad-7177-84a6-8cc9ceced576 |
| m08-368674d77d | rle/core.py | 32 | 1 -> 2 | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_long_ru | 01a140bc-472b-7120-b3d9-41a123794078 |
| m09-f40ccb6538 | rle/core.py | 34 | Add -> Sub | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_abc_ret | 01a140bc-504b-7491-8063-7b5d620d7598 |
| m10-1e99faa709 | rle/core.py | 36 | 1 -> 2 | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_abc_ret | 01a140bc-4fe9-75da-bbb0-b6cd128bdb62 |
| m11-164ff607ed | rle/core.py | 37 | Add -> Sub | killed | test_sealed.TestEncodeAcceptance.test_encode_aaabbc_returns_a3b2c1, test_sealed.TestEncodeAcceptance.test_encode_single_ | 01a140bc-5442-7257-a723-552b70f65ad2 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `d93a288c3b82a4dc5c9a44ebc59f48bdfac3408b6db9af032c4cc20d03bcd47c`): FAILED (2 of 9 methods: FAIL 2); binding FAILED; operation `01a140bd-02aa-77e3-be68-acbae39719df`. Notes: Targets edge cases with digits, unicode, whitespace, large runs, and type variants.

| Failing adversarial test | Outcome |
| --- | --- |
| test_roundtrip_with_digits | FAIL |
| test_encode_newline_and_tab | FAIL |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements encode exactly as specified: it validates input type, handles empty strings, produces character-count pairs for every run (including count 1), and returns a string. The existing test suite passes and custom round-trip tests pass, confirming the round-trip property with decode. No required behavior was omitted and no extra behavior was added.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
1 failing test(s) indicate a real implementation bug; human review required (mode: advisory). Classifications: {'implementation_bug': 1, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale |
| --- | --- | --- |
| test_roundtrip_with_digits | implementation_bug | The contract requires the round-trip property decode(encode(x)) == x for every string x. The candidate's encode produces 'a111' for input 'a |
| test_encode_newline_and_tab | test_defect | The test uses string literals '\\n\\n\\t' and '\\n2\\t1', which in Python source represent literal backslash-n sequences (six characters), n |

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1133 | 2083 | 0 | 0.007382 | 13.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1259 | 3000 | 0 | 0.003078 | 14.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1257 | 115 | 0 | 0.000481 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1348 | 98 | 0 | 0.000493 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1592 | 1278 | 0 | 0.001628 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1844 | 281 | 0 | 0.000806 | 3.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 1988 | 475 | 0 | 0.001024 | 7.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2316 | 126 | 0 | 0.000808 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 1212 | 6594 | 0 | 0.006298 | 34.4s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1512 | 1289 | 0 | 0.005379 | 5.3s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 2008 | 11475 | 0 | 0.036433 | 36.3s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 17469/26814/0; USD: 0.06381.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140ba-ea4d-71a0-86ae-e2ad74216cc7 | SUCCESS | 0 | 0.739s | retained | off | 0.0027539099999999996 |
| red-1 | 01a140bb-6977-7684-8185-f9688ee31c7a | SUCCESS | 0 | 2.948s | disposable | off | 0.023179490000000004 |
| impl-tests-4 | 01a140bb-c853-75f2-8492-6462f2f7f464 | SUCCESS | 0 | 0.734s | disposable | off | 0.0027432100000000003 |
| impl-python-5 | 01a140bb-f870-736e-9a69-59741dcdc903 | SUCCESS | 0 | 0.507s | disposable | off | 0.00112821 |
| verify | 01a140bc-0f67-710b-ac04-0fe1108fda33 | SUCCESS | 0 | 3.102s | disposable | off | 0.024866350000000002 |
| heldout | 01a140bc-27d2-7017-8f65-9090515a2bee | SUCCESS | 0 | 0.734s | disposable | off | 0.0027517699999999997 |
| mutant-m01-8ec8ddc94d | 01a140bc-35f0-76c8-a67e-5de12df064f2 | SUCCESS | 0 | 3.023s | disposable | off | 0.023370340000000003 |
| mutant-m02-d577c0fd83 | 01a140bc-39fd-7603-a7ee-0fc6d687d13f | SUCCESS | 0 | 2.945s | disposable | off | 0.02331816 |
| mutant-m03-d71b8e165a | 01a140bc-35f3-72ff-93e2-08bee08e1c92 | SUCCESS | 0 | 2.984s | disposable | off | 0.02324655 |
| mutant-m04-4041d1d761 | 01a140bc-35fa-72a5-82e2-40a48668bc88 | SUCCESS | 0 | 2.966s | disposable | off | 0.02308759 |
| mutant-m05-697d3a6162 | 01a140bc-35ed-7022-b549-f590a7994771 | SUCCESS | 0 | 2.966s | disposable | off | 0.02293103 |
| mutant-m06-d95fbb9afb | 01a140bc-3a8f-734c-b3b4-fe516323cb62 | SUCCESS | 0 | 2.994s | disposable | off | 0.023336250000000003 |
| mutant-m07-4d9f698d3f | 01a140bc-35ad-7177-84a6-8cc9ceced576 | SUCCESS | 0 | 2.933s | disposable | off | 0.02307965 |
| mutant-m08-368674d77d | 01a140bc-472b-7120-b3d9-41a123794078 | SUCCESS | 0 | 2.97s | disposable | off | 0.02305199 |
| mutant-m09-f40ccb6538 | 01a140bc-504b-7491-8063-7b5d620d7598 | SUCCESS | 0 | 2.993s | disposable | off | 0.02327651 |
| mutant-m10-1e99faa709 | 01a140bc-4fe9-75da-bbb0-b6cd128bdb62 | SUCCESS | 0 | 2.975s | disposable | off | 0.02308464 |
| mutant-m11-164ff607ed | 01a140bc-5442-7257-a723-552b70f65ad2 | SUCCESS | 0 | 2.965s | disposable | off | 0.02340363 |
| breaker-tests | 01a140bd-02aa-77e3-be68-acbae39719df | SUCCESS | 0 | 2.26s | disposable | off | 0.016629900000000003 |

Sandbox operations: 18, total guest duration 43.738s, retained images ['85e8cdd9-afa4-4492-b6a4-6bc15f6c7123'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
