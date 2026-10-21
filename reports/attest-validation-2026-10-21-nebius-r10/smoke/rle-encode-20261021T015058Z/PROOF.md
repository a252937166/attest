# Attest Proof Bundle: rle-encode

**Verdict: NEEDS HUMAN**  
Run `rle-encode-20261021T015058Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T01:50:58.583392+00:00, finished 2026-10-21T01:53:04.532529+00:00.

**Hold this patch.** 2 of the 9 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request. The arbiter classified 2 of them as implementation bugs (E6).

Key evidence (E1): test_round_trip_property: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc' != 'a1b2c3' (the test's first argument against its second)



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: child process nonzero exit: test_round_trip_property exit 1, test_encode_then_decode_matches_original_for_special_chars exit 1
Warnings: arbitration (validated corrections re-run their gates): 2 failing test(s) indicate a real implementation bug; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 2 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- The held-out tests (tests/test_heldout.py), which the implementer never saw, pass on the candidate (E4).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 9 of 9 failed on the unmodified base; 7 of 9 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | pass | bound | 7 of 7 pass (tests/test_heldout.py) |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | 2 failing test(s) indicate a real implementation bug; human review required |

## 1. Frozen task and provenance
Task `rle-encode`, spec digest `46f6d840c3b61a78e676dd7851d6347660ad71b9f5558f7e34b5411691f148af`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6bbabdb3-f817-47ab-b9d2-0a604e264462`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. Implement the encode function in the rle package to perform run-length encoding on a string. Each maximal run of a character becomes that character followed by its decimal count (always written, even for count 1). The function must return a string, raise TypeError for non-string inputs, and satisfy the round-trip property decode(encode(x)) == x for all strings x. The existing decode function and tests must not be modified.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| encode | encode(s: str) -> str | Run-length encodes the input string. For each maximal contiguous run of identical characters, outputs the character followed by the decimal representation of th | TypeError if s is not a string |
| decode | decode(s: str) -> str | Decodes a run-length encoded string. Expects a sequence of (character, one-or-more-digits) pairs. Returns the expanded string. Empty input returns empty string. | TypeError if s is not a string; ValueError if a character is not followed by at least one digit |

Acceptance criteria:
AC1. encode('aaabbc') returns 'a3b2c1'
AC2. encode('a') returns 'a1'
AC3. encode('') returns ''
AC4. encode('abc') returns 'a1b1c1' (count written even when 1)
AC5. encode('x' * 12) returns 'x12' (multi-digit counts)
AC6. For any string x, decode(encode(x)) == x (round-trip property)
AC7. encode returns a value of type str
AC8. encode raises TypeError when the argument is not a string (e.g., encode(123), encode(None), encode(['a']))

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract is consistent: the existing decode function expects a sequence of (character, one-or-more-digits) pairs, which matches exactly the output format required for encode. All acceptance criteria (TC1-TC7) can be satisfied simultaneously by a straightforward run-length encoding implementation. No conflicts exist between the requirements. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `f0d941e660199e945aa18577995a0ebbc13d90244b225392d150e7daa4fed5d1`, 9 test methods, sealed at 2026-10-21T01:51:31.961925+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 9 methods: ERROR 9): 9 of 9 methods failing, 0 passing; operation `01a15c28-1445-7424-ae88-d50be900b791`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestEncode.test_encode_aaabbc_returns_a3b2c1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_abc_returns_a1b1c1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_empty_string_returns_empty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_multi_digit_count | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_returns_str_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_single_char_returns_char1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_encode_then_decode_matches_original_for_special_chars | ERROR (1 ev) | FAIL (1 ev) |
| test_sealed.TestEncode.test_encode_type_error_nonstring | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncode.test_round_trip_property | ERROR (1 ev) | FAIL (1 ev) |


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
+    prev = s[0]
+    count = 1
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (16 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (2 of 9 methods: FAIL 2). Operation `01a15c29-0c1c-71e7-a25a-d8062bed15e6`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| supervisor_cleanup_complete | pass |
| nonce_matches | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15c29-2404-7117-8ec4-70c318858b2c`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite (evidence class `bound`; tests/test_heldout.py): OK (7 of 7 methods, each in its own process) (7 passed of 7); operation `01a15c29-3c49-768e-8bab-01d598baec23`. Gate: failures block VERIFIED.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_round_trip_property exit 1, test_encode_then_decode_matches_original_for_special_chars exit 1 |
| heldout_suite | Held-out tests | pass | bound | E4 | OK (7 of 7 methods, each in its own process) |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
- E1 `test_round_trip_property`: FAIL; AssertionError: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc' != 'a1b2c3'; first `'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc'` vs second `'a1b2c3'` (the test's argument order decides which is the actual value); arbiter: Implementation bug, by the arbiter; contract basis: Contract requires 'For any string x, decode(encode(x)) == x (round-trip property)'. The candidate's encode does not satisfy this for strings containing digits (e.g., 'a1b2c3').
- E1 `test_encode_then_decode_matches_original_for_special_chars`: FAIL; AssertionError: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc' != 'a3b1c2'; first `'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc'` vs second `'a3b1c2'` (the test's argument order decides which is the actual value); arbiter: Implementation bug, by the arbiter; contract basis: Contract requires round-trip for every string. The test is a valid instance of that requirement.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements encode exactly as specified: it validates input type, handles empty strings, emits character-count pairs for every run (including counts of 1), and returns a string. The existing test suite passes, confirming round-trip compatibility with decode. No out-of-scope files were modified.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
2 failing test(s) indicate a real implementation bug; human review required (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 2, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_round_trip_property | implementation_bug | The candidate's encode function produces an encoding that the existing decode function cannot correctly decode when the original string cont | Contract requires 'For any string x, decode(encode(x)) == x (round-trip property)'. The candidate's encode does not satisfy this for strings |
| test_encode_then_decode_matches_original_for_special_chars | implementation_bug | This test checks the round-trip property for a specific string containing digits ('a3b1c2'). The candidate's encode fails to produce an enco | Contract requires round-trip for every string. The test is a valid instance of that requirement. |

- `sealed` corrected re-run: candidate n/a; base n/a; validated=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1133 | 1525 | 0 | 0.005708 | 5.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 2558 | 2830 | 0 | 0.011048 | 9.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1455 | 792 | 0 | 0.001149 | 7.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1406 | 137 | 0 | 0.000545 | 6.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1495 | 184 | 0 | 0.000614 | 5.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1742 | 1078 | 0 | 0.001493 | 11.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1990 | 124 | 0 | 0.000709 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2135 | 497 | 0 | 0.001088 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2513 | 825 | 0 | 0.001496 | 7.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2840 | 196 | 0 | 0.001028 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 2986 | 115 | 0 | 0.000999 | 2.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1616 | 2001 | 0 | 0.007619 | 7.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-sealed | default | 3154 | 2707 | 0 | 0.011275 | 9.7s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 27023/13011/0; Inference USD: 0.044771.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c27-b10d-7585-b7da-7e560eea578d | SUCCESS | 0 | 0.864s | retained | off | 0.00287772 |
| red-1 | 01a15c28-1445-7424-ae88-d50be900b791 | SUCCESS | 0 | 2.667s | disposable | off | 0.02006751 |
| impl-tests-4 | 01a15c28-9135-76fd-9771-cb8b59c11433 | SUCCESS | 0 | 1.279s | disposable | off | 0.00284708 |
| impl-python-5 | 01a15c28-b21e-73d0-b1dc-e16ad704f9af | SUCCESS | 0 | 0.585s | disposable | off | 0.00123631 |
| impl-python-6 | 01a15c28-da0a-742b-9986-af5608bb8fec | SUCCESS | 0 | 0.598s | disposable | off | 0.0012587700000000002 |
| impl-tests-7 | 01a15c28-f38f-73cf-adce-eea6a3c0cb8d | SUCCESS | 0 | 0.817s | disposable | off | 0.0028776400000000003 |
| verify | 01a15c29-0c1c-71e7-a25a-d8062bed15e6 | SUCCESS | 0 | 3.02s | disposable | off | 0.02034891 |
| existing | 01a15c29-2404-7117-8ec4-70c318858b2c | SUCCESS | 0 | 1.836s | disposable | off | 0.0087472 |
| heldout | 01a15c29-3c49-768e-8bab-01d598baec23 | SUCCESS | 0 | 2.628s | disposable | off | 0.01691402 |

Sandbox operations: 9, total guest duration 14.294s, retained images ['6bbabdb3-f817-47ab-b9d2-0a604e264462'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
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
| contract_audit.json | Contract audit: claimed conflicts and the result of executing their witness programs |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
| ledger.jsonl | Append-only ledger journal: reservations before each request, call records as they complete |
