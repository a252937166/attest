# Attest Proof Bundle: rle-encode

**Verdict: VERIFIED**  
Run `rle-encode-attest-a1-20261017T172313657652Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:23:13.657861+00:00, finished 2026-10-17T17:26:32.256628+00:00.

**Accept this patch.** All 10 sealed tests pass on the candidate in a fresh sandbox, and 10 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 10 of 10 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: drift audit: score 0.00, widened 0, unsupported claims 1

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 10 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 10 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 11 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 10 of 10 failed on the unmodified base; 10 of 10 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 11 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `rle-encode`, spec digest `e64da208acc97bfcb964f579c1a5687bc6340ce7531452982870487fe1231c41`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `0d525222-5934-47c0-bf01-8e90945e7eb6`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. Implement the `encode` function in the `rle` package to perform run-length encoding on a string. The function must convert each maximal run of identical characters into the character followed by the decimal count of the run (always including the count, even for runs of length 1). The function must return a string, raise `TypeError` for non-string inputs, and satisfy the round-trip property `decode(encode(x)) == x` for all strings `x`. The existing `decode` function and tests must not be modified.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| encode | encode(s: str) -> str | Returns the run-length encoding of the input string `s`. Each maximal run of a single character is replaced by that character followed by the decimal representa | TypeError: raised when `s` is not a string. |

Acceptance criteria:
1. encode('aaabbc') == 'a3b2c1'
2. encode('a') == 'a1'
3. encode('') == ''
4. encode('abc') == 'a1b1c1' (count written even when 1)
5. encode('x' * 12) == 'x12' (multi-digit counts)
6. decode(encode(x)) == x for every string x (round-trip property)
7. encode returns a str instance
8. encode raises TypeError when the argument is not a string

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `1dfbb27cbc9e5d34ebad35bc51025a5dd0f1b8dddd4266ed2be6d9dc4df4c790`, 10 test methods, sealed at 2026-10-17T17:24:21.586771+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (10 of 10 methods: ERROR 10): 10 of 10 methods failing, 0 passing; operation `01a14ae4-a4f9-741c-b0f1-25479d3a76ae`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestEncode.test_encode_aaabbc | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_all_one_counts | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_empty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_long_run | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_mixed_runs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_multi_digit_count | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_returns_str | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_single_char | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_type_error_non_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_round_trip_property | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

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

Sealed suite: OK (10 of 10 methods, each in its own process). Operation `01a14ae5-ac4a-77ab-b39a-60a9701c66f3`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14ae6-0ac6-7637-b21c-533f16586574`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 11 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 11 generated, 11 evaluated: 11 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-8ec8ddc94d | rle/core.py | 23 | remove `not` | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae6-2849-717b-8fc3-8cbe885509eb |
| m02-d577c0fd83 | rle/core.py | 24 | raise -> pass | killed | test_sealed.TestEncode.test_encode_type_error_non_string | 01a14ae6-2828-7785-8022-6233751b5f44 |
| m03-d71b8e165a | rle/core.py | 25 | remove `not` | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae6-283e-707c-8dfb-3e41120136bf |
| m04-4041d1d761 | rle/core.py | 28 | 0 -> 1 | killed | test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_encode_all_one_counts, test_sealed.TestEncod | 01a14ae6-284d-72c8-a226-90ad0ccfe83b |
| m05-697d3a6162 | rle/core.py | 29 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae6-2810-7082-8248-4b10727311f0 |
| m06-d95fbb9afb | rle/core.py | 30 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_all_one_counts, test_sealed.TestEncode.tes | 01a14ae6-2848-7040-b4f8-fd3c2d1f1366 |
| m07-4d9f698d3f | rle/core.py | 31 | Eq -> NotEq | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_all_one_counts, test_sealed.TestEncode.tes | 01a14ae6-2829-754f-99f9-741ae52d4cdf |
| m08-368674d77d | rle/core.py | 32 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_multi_digit_count, test_sealed.TestEncode. | 01a14ae6-2845-7422-9e0c-48e74b0609a7 |
| m09-f40ccb6538 | rle/core.py | 34 | Add -> Sub | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_all_one_counts, test_sealed.TestEncode.tes | 01a14ae6-4365-74e1-870d-a9803de16a5a |
| m10-1e99faa709 | rle/core.py | 36 | 1 -> 2 | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_all_one_counts, test_sealed.TestEncode.tes | 01a14ae6-42b4-740c-8460-5b6abf015bcd |
| m11-164ff607ed | rle/core.py | 37 | Add -> Sub | killed | test_sealed.TestEncode.test_encode_aaabbc, test_sealed.TestEncode.test_encode_single_char, test_sealed.TestEncode.test_e | 01a14ae6-42e4-773a-a658-fb121ae5af39 |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `e373ad62aa223bb17776ec2fdd4cd08ec98b5170c92719921a397fdc417ac000`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a14ae6-7826-75df-8603-051bc93b3482`. Notes: Targeted edge cases: Unicode, null bytes, very long runs, alternating patterns, mixed scripts, subclass handling, no leading zeros, exhaustive small lengths.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements encode correctly, satisfying all contract requirements including TypeError for non-strings, proper run-length encoding with counts, and round-trip with decode. The implementer's assertion that the existing test suite verifies encode is unsupported because the suite only contains decode tests.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: Run test suite to verify encode implementation.

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1133 | 1526 | 0 | 0.005711 | 5.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1219 | 472 | 0 | 0.000790 | 4.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1162 | 93 | 0 | 0.000432 | 12.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1256 | 93 | 0 | 0.000460 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1501 | 1078 | 0 | 0.001420 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1747 | 250 | 0 | 0.000749 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 1888 | 388 | 0 | 0.000916 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2191 | 868 | 0 | 0.001438 | 5.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2453 | 172 | 0 | 0.000891 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 2596 | 207 | 0 | 0.000965 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1234 | 859 | 0 | 0.001143 | 7.0s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1546 | 3453 | 0 | 0.011905 | 11.0s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 19926/9459/0; USD: 0.02682.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ae4-73b8-7037-a841-b25997e9d879 | SUCCESS | 0 | 1.101s | retained | off | 0.0028459699999999997 |
| red-1 | 01a14ae4-a4f9-741c-b0f1-25479d3a76ae | SUCCESS | 0 | 3.999s | disposable | off | 0.02187196 |
| impl-tests-4 | 01a14ae5-31c6-75d6-a150-3c9417ceb25e | SUCCESS | 0 | 0.761s | disposable | off | 0.00285353 |
| impl-python-5 | 01a14ae5-4e59-7707-8de6-0a5f4877d62c | SUCCESS | 0 | 0.615s | disposable | off | 0.0012209 |
| impl-python-6 | 01a14ae5-7a60-7769-a609-60cb7d8e3a93 | SUCCESS | 0 | 0.622s | disposable | off | 0.00177645 |
| impl-tests-7 | 01a14ae5-9151-7340-bb1e-268737085bd3 | SUCCESS | 0 | 0.791s | disposable | off | 0.00286655 |
| verify | 01a14ae5-ac4a-77ab-b39a-60a9701c66f3 | SUCCESS | 0 | 3.026s | disposable | off | 0.02180712 |
| existing | 01a14ae6-0ac6-7637-b21c-533f16586574 | SUCCESS | 0 | 1.408s | disposable | off | 0.00878648 |
| mutant-m01-8ec8ddc94d | 01a14ae6-2849-717b-8fc3-8cbe885509eb | SUCCESS | 0 | 2.56s | disposable | off | 0.01853513 |
| mutant-m02-d577c0fd83 | 01a14ae6-2828-7785-8022-6233751b5f44 | SUCCESS | 0 | 2.529s | disposable | off | 0.01858595 |
| mutant-m03-d71b8e165a | 01a14ae6-283e-707c-8dfb-3e41120136bf | SUCCESS | 0 | 2.55s | disposable | off | 0.01846917 |
| mutant-m04-4041d1d761 | 01a14ae6-284d-72c8-a226-90ad0ccfe83b | SUCCESS | 0 | 2.53s | disposable | off | 0.018461039999999998 |
| mutant-m05-697d3a6162 | 01a14ae6-2810-7082-8248-4b10727311f0 | SUCCESS | 0 | 2.492s | disposable | off | 0.018541989999999998 |
| mutant-m06-d95fbb9afb | 01a14ae6-2848-7040-b4f8-fd3c2d1f1366 | SUCCESS | 0 | 2.518s | disposable | off | 0.01856246 |
| mutant-m07-4d9f698d3f | 01a14ae6-2829-754f-99f9-741ae52d4cdf | SUCCESS | 0 | 2.503s | disposable | off | 0.01861713 |
| mutant-m08-368674d77d | 01a14ae6-2845-7422-9e0c-48e74b0609a7 | SUCCESS | 0 | 2.519s | disposable | off | 0.01836547 |
| mutant-m09-f40ccb6538 | 01a14ae6-4365-74e1-870d-a9803de16a5a | SUCCESS | 0 | 2.466s | disposable | off | 0.018625970000000002 |
| mutant-m10-1e99faa709 | 01a14ae6-42b4-740c-8460-5b6abf015bcd | SUCCESS | 0 | 2.473s | disposable | off | 0.01848354 |
| mutant-m11-164ff607ed | 01a14ae6-42e4-773a-a658-fb121ae5af39 | SUCCESS | 0 | 2.482s | disposable | off | 0.01858322 |
| breaker-tests | 01a14ae6-7826-75df-8603-051bc93b3482 | SUCCESS | 0 | 2.806s | disposable | off | 0.02187216 |

Sandbox operations: 20, total guest duration 42.751s, retained images ['0d525222-5934-47c0-bf01-8e90945e7eb6'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
