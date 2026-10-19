# Attest Proof Bundle: rle-encode

**Verdict: VERIFIED**  
Run `rle-encode-attest-a2-20261017T172313815697Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:23:13.815874+00:00, finished 2026-10-17T17:26:02.381272+00:00.

**Accept this patch.** All 14 sealed tests pass on the candidate in a fresh sandbox, and 14 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 14 of 14 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 14 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 14 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 11 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 7 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 14 of 14 failed on the unmodified base; 14 of 14 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 11 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 7 of 7 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `rle-encode`, spec digest `e64da208acc97bfcb964f579c1a5687bc6340ce7531452982870487fe1231c41`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d2076b4f-e611-4f16-bb54-bb3094a73db5`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. Implement the `encode` function in the `rle` package to perform run-length encoding on a string. The function must convert each maximal run of identical characters into the character followed by the decimal count of the run (always including the count, even for runs of length 1). The function must return a string, raise `TypeError` for non-string inputs, and satisfy the round-trip property `decode(encode(x)) == x` for all strings `x`, where `decode` is the existing decoding function.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| encode | encode(s: str) -> str | Returns the run-length encoding of the input string `s`. Each maximal run of a single character is represented by that character followed by the decimal represe | TypeError: raised if `s` is not a string. |
| decode | decode(s: str) -> str | Decodes a run-length encoded string `s` back to the original string. The encoded string must consist of sequences of a single character followed by one or more  | TypeError: raised if `s` is not a string.; ValueError: raised if a character is not followed by at least one digit (missing count). |

Acceptance criteria:
1. encode('aaabbc') returns 'a3b2c1'.
2. encode('a') returns 'a1'.
3. encode('') returns ''.
4. encode('abc') returns 'a1b1c1'.
5. encode('x' * 12) returns 'x12' (multi-digit count).
6. For any string x, decode(encode(x)) == x (round-trip property).
7. encode returns an instance of str.
8. encode raises TypeError when the argument is not a string (e.g., encode(123) raises TypeError).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `9f3f106a1af5dda11125d10582ea415037cd87e2c1646388d4e855e3636f55d0`, 14 test methods, sealed at 2026-10-17T17:23:41.636491+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (14 of 14 methods: ERROR 14): 14 of 14 methods failing, 0 passing; operation `01a14ae4-08d5-719b-b821-0cdf32086526`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestEncode.test_encode_aaabbc | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_abc | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_counts_no_leading_zero | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_empty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_long_run_multi_digit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_mixed_runs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_returns_str | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_single_char | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_type_error_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_type_error_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_round_trip_complex | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_round_trip_simple1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_round_trip_simple2 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_round_trip_simple3 | ERROR (1 ev) | ok (1 ev) |

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

Static tamper scan of the added lines: no suspicious constructs on the added lines (16 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (14 of 14 methods, each in its own process). Operation `01a14ae5-2c2d-71fc-90a5-9081550821ff`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14ae5-4528-7064-b791-3f1088e70c2b`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 11 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (7 of 7 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 11 generated, 11 evaluated: 11 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-8ec8ddc94d | rle/core.py | 23 | remove `not` | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae5-5411-7472-a031-74704d0589ee |
| m02-d577c0fd83 | rle/core.py | 24 | raise -> pass | killed | test_sealed.TestEncode.test_encode_type_error_list | 01a14ae5-542f-727a-b7ac-baa338e94377 |
| m03-d71b8e165a | rle/core.py | 25 | remove `not` | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae5-5494-7656-bd46-258b00a6cae1 |
| m04-4041d1d761 | rle/core.py | 28 | 0 -> 1 | killed | test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_encode_abc, test_sealed.TestEncode.test_roun | 01a14ae5-5425-739a-a819-f3bbd407353b |
| m05-697d3a6162 | rle/core.py | 29 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae5-5440-73d6-8043-647ac78caa17 |
| m06-d95fbb9afb | rle/core.py | 30 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_abc, test_sealed.TestEncode.test_encode_lo | 01a14ae5-5442-70a5-9541-adbfd8bd1179 |
| m07-4d9f698d3f | rle/core.py | 31 | Eq -> NotEq | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_abc, test_sealed.TestEncode.test_encode_lo | 01a14ae5-5520-779a-a2f6-2e8f59591061 |
| m08-368674d77d | rle/core.py | 32 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_long_run_multi_digit, test_sealed.TestEnco | 01a14ae5-5486-71ad-a577-e7e94fbe58be |
| m09-f40ccb6538 | rle/core.py | 34 | Add -> Sub | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_abc, test_sealed.TestEncode.test_encode_re | 01a14ae5-6d43-712c-8f8a-2a6637331318 |
| m10-1e99faa709 | rle/core.py | 36 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_abc, test_sealed.TestEncode.test_round_tri | 01a14ae5-6d85-768a-8a4b-c3ad7e72bf01 |
| m11-164ff607ed | rle/core.py | 37 | Add -> Sub | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae5-eaba-7694-96ce-88bec5984128 |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `5a195d1cd18f8243ae02fca254508c57b2e09336be74e56a76c682337130a242`): OK (7 of 7 methods, each in its own process); binding ok; operation `01a14ae6-1b06-719b-bfd8-ea9ad8b78f05`. Notes: Targeted Unicode, long runs, alternating patterns, non‑string inputs, newline/tab handling, and instance identity.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements encode exactly as specified, handling all acceptance criteria including TypeError for non-strings, empty string, multi-digit counts, and round-trip property. All tests pass and no out-of-scope changes were made.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1133 | 2484 | 0 | 0.008585 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1352 | 942 | 0 | 0.001253 | 8.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1301 | 82 | 0 | 0.000464 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1392 | 101 | 0 | 0.000509 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1637 | 1018 | 0 | 0.001407 | 7.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1893 | 92 | 0 | 0.000651 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2036 | 400 | 0 | 0.000971 | 4.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2389 | 1868 | 0 | 0.002398 | 11.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2825 | 1918 | 0 | 0.002574 | 10.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 3130 | 159 | 0 | 0.001082 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 3278 | 98 | 0 | 0.001072 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1407 | 602 | 0 | 0.000964 | 5.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1719 | 1197 | 0 | 0.005310 | 4.8s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 25492/10961/0; USD: 0.02724.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ae3-bb4e-7191-8631-f86dbb6c2e7d | SUCCESS | 0 | 0.748s | retained | off | 0.00283 |
| red-1 | 01a14ae4-08d5-719b-b821-0cdf32086526 | SUCCESS | 0 | 3.524s | disposable | off | 0.028463489999999998 |
| impl-tests-4 | 01a14ae4-6058-7650-8c83-8a135f7edc45 | SUCCESS | 0 | 0.965s | disposable | off | 0.00281517 |
| impl-python-5 | 01a14ae4-7d14-77eb-8c51-27da1e6286eb | SUCCESS | 0 | 0.723s | disposable | off | 0.0012415400000000002 |
| impl-python-6 | 01a14ae4-b5a3-727a-9fb1-5e73bf9de7f3 | SUCCESS | 0 | 0.601s | disposable | off | 0.00119711 |
| impl-python-7 | 01a14ae4-eb47-748b-9155-48ad6453cd2c | SUCCESS | 0 | 0.557s | disposable | off | 0.00120978 |
| impl-tests-8 | 01a14ae5-0352-7297-a31d-a458df0ba3c9 | SUCCESS | 0 | 0.818s | disposable | off | 0.00284835 |
| verify | 01a14ae5-2c2d-71fc-90a5-9081550821ff | SUCCESS | 0 | 3.368s | disposable | off | 0.02794821 |
| existing | 01a14ae5-4528-7064-b791-3f1088e70c2b | SUCCESS | 0 | 1.401s | disposable | off | 0.00871271 |
| mutant-m01-8ec8ddc94d | 01a14ae5-5411-7472-a031-74704d0589ee | SUCCESS | 0 | 3.157s | disposable | off | 0.02497073 |
| mutant-m02-d577c0fd83 | 01a14ae5-542f-727a-b7ac-baa338e94377 | SUCCESS | 0 | 3.159s | disposable | off | 0.0252275 |
| mutant-m03-d71b8e165a | 01a14ae5-5494-7656-bd46-258b00a6cae1 | SUCCESS | 0 | 3.234s | disposable | off | 0.02514298 |
| mutant-m04-4041d1d761 | 01a14ae5-5425-739a-a819-f3bbd407353b | SUCCESS | 0 | 3.155s | disposable | off | 0.02499607 |
| mutant-m05-697d3a6162 | 01a14ae5-5440-73d6-8043-647ac78caa17 | SUCCESS | 0 | 3.156s | disposable | off | 0.02496914 |
| mutant-m06-d95fbb9afb | 01a14ae5-5442-70a5-9541-adbfd8bd1179 | SUCCESS | 0 | 3.185s | disposable | off | 0.024998069999999997 |
| mutant-m07-4d9f698d3f | 01a14ae5-5520-779a-a2f6-2e8f59591061 | SUCCESS | 0 | 3.133s | disposable | off | 0.02503639 |
| mutant-m08-368674d77d | 01a14ae5-5486-71ad-a577-e7e94fbe58be | SUCCESS | 0 | 3.235s | disposable | off | 0.02519123 |
| mutant-m09-f40ccb6538 | 01a14ae5-6d43-712c-8f8a-2a6637331318 | SUCCESS | 0 | 3.064s | disposable | off | 0.0247497 |
| mutant-m10-1e99faa709 | 01a14ae5-6d85-768a-8a4b-c3ad7e72bf01 | SUCCESS | 0 | 3.114s | disposable | off | 0.024923749999999998 |
| mutant-m11-164ff607ed | 01a14ae5-eaba-7694-96ce-88bec5984128 | SUCCESS | 0 | 3.128s | disposable | off | 0.024981839999999998 |
| breaker-tests | 01a14ae6-1b06-719b-bfd8-ea9ad8b78f05 | SUCCESS | 0 | 2.281s | disposable | off | 0.0168698 |

Sandbox operations: 21, total guest duration 49.706s, retained images ['d2076b4f-e611-4f16-bb54-bb3094a73db5'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 13. Artifacts
Every file of the run directory is listed in `manifest.json` with its sha256 and size (written last, so it covers this file and proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from `verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.

| Artifact | Purpose |
| --- | --- |
| proof_bundle.json | The Proof Bundle: every stage record, gate and the verdict |
| PROOF.md | Human-readable rendering of the Proof Bundle |
| manifest.json | sha256 and size of every artifact (this file) |
| task.frozen.json | Frozen task: statement, policy and repository digests |
| spec.json | Specification and contract written before any code |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
