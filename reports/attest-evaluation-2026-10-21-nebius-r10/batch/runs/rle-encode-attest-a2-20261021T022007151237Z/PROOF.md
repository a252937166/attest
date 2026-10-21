# Attest Proof Bundle: rle-encode

**Verdict: NEEDS HUMAN**  
Run `rle-encode-attest-a2-20261021T022007151237Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T02:20:07.151903+00:00, finished 2026-10-21T02:22:36.330225+00:00.

**Hold this patch.** 1 of the 12 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request. The arbiter classified 1 of them as implementation bugs (E6).

Key evidence (E1): test_encode_roundtrip_property: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc' != 'a1b2c3' (the test's first argument against its second)



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: child process nonzero exit: test_encode_roundtrip_property exit 1
Warnings: arbitration (validated corrections re-run their gates): 1 failing test(s) indicate a real implementation bug; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 1 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 12 of 12 failed on the unmodified base; 11 of 12 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | 1 failing test(s) indicate a real implementation bug; human review required |

## 1. Frozen task and provenance
Task `rle-encode`, spec digest `e64da208acc97bfcb964f579c1a5687bc6340ce7531452982870487fe1231c41`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ad6d111e-1a72-4c7e-b8fe-69994a453720`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: True. Implement the `encode` function in the `rle` package to perform run-length encoding on a string. The function must take a string `s` and return a string where each maximal run of identical characters is represented by the character followed by its run length in decimal (always including the count, even for runs of length 1). The function must raise `TypeError` if the input is not a string. The encoding must be the exact inverse of the existing `decode` function, ensuring `decode(encode(x)) == x` for all strings `x`.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| decode | decode(s: str) -> str | Decodes a run-length encoded string `s` back to the original string. The encoded string consists of a character followed by one or more decimal digits represent | TypeError if `s` is not a string; ValueError if the encoded string is malformed (e.g., missing count after a character) |
| encode | encode(s: str) -> str | Encodes a string `s` using run-length encoding. Each maximal run of identical characters is replaced by the character followed by the decimal representation of  | TypeError if `s` is not a string |

Acceptance criteria:
AC1. encode('aaabbc') returns 'a3b2c1'
AC2. encode('a') returns 'a1'
AC3. encode('') returns ''
AC4. encode('abc') returns 'a1b1c1' (count written even when 1)
AC5. encode('x' * 12) returns 'x12' (multi-digit counts)
AC6. For every string x, decode(encode(x)) == x (round-trip property)
AC7. encode returns a value of type str
AC8. encode raises TypeError when the argument is not a string (e.g., int, list, None)

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract is satisfiable: the existing decode function expects a character followed by one or more digits, which matches exactly the output format required for encode. The round-trip property holds for all strings because the encoding is the exact inverse of the decoding algorithm. No conflicts among the authoritative criteria (TC1-TC7) or with the fixed decode implementation. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `798e2e59c23d60d65966894c0cc07fca3e77e3e44b8aa79a8f3eaa7b81672050`, 12 test methods, sealed at 2026-10-21T02:20:53.221744+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 12 methods: ERROR 12): 12 of 12 methods failing, 0 passing; operation `01a15c42-e412-7769-acdb-66131fb4b93f`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestEncodeSealed.test_encode_aaabbc_returns_a3b2c1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_distinct_chars_each_with_count1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_empty_string_returns_empty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_handles_unicode_characters | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_mixed_runs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_multi_digit_count | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_returns_str_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_roundtrip_property | ERROR (1 ev) | FAIL (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_single_char_returns_char1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_type_error_on_nonstring_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_type_error_on_nonstring_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestEncodeSealed.test_encode_type_error_on_nonstring_none | ERROR (1 ev) | ok (1 ev) |


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

Sealed suite: FAILED (1 of 12 methods: FAIL 1). Operation `01a15c43-e976-7081-b639-b0e34c7d5fee`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15c44-0284-70f8-8286-f83558405660`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_encode_roundtrip_property exit 1 |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
- E1 `test_encode_roundtrip_property`: FAIL; AssertionError: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc' != 'a1b2c3'; first `'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[317 chars]cccc'` vs second `'a1b2c3'` (the test's argument order decides which is the actual value); arbiter: Implementation bug, by the arbiter; contract basis: The contract states: 'The encoding must be the exact inverse of the existing `decode` function, ensuring `decode(encode(x)) == x` for every string x.' The test directly verifies this requirement.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements encode exactly as specified: it validates input type, handles empty strings, performs run-length encoding with counts always written (including 1), supports multi-digit counts, and returns a string. The existing test suite passes and the implementer's sanity checks report success, indicating the round-trip property holds for the tested cases. No required behavior was omitted and no extra behavior was added.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
1 failing test(s) indicate a real implementation bug; human review required (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 1, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_encode_roundtrip_property | implementation_bug | The test checks the round-trip property for all strings, as required by the contract. The candidate's encode function produces ambiguous out | The contract states: 'The encoding must be the exact inverse of the existing `decode` function, ensuring `decode(encode(x)) == x` for every  |

- `sealed` corrected re-run: candidate n/a; base n/a; validated=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1133 | 2527 | 0 | 0.008714 | 8.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 2619 | 4307 | 0 | 0.015540 | 13.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1507 | 825 | 0 | 0.001195 | 7.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1467 | 108 | 0 | 0.000537 | 2.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1556 | 261 | 0 | 0.000702 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1664 | 115 | 0 | 0.000603 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1806 | 138 | 0 | 0.000666 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2043 | 832 | 0 | 0.001362 | 11.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2226 | 269 | 0 | 0.000910 | 4.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2370 | 600 | 0 | 0.001251 | 7.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 2793 | 465 | 0 | 0.001256 | 14.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1632 | 3814 | 0 | 0.013074 | 12.4s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-sealed | default | 3067 | 7142 | 0 | 0.024493 | 21.6s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 25883/21403/0; Inference USD: 0.070303.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c42-636e-769d-8e6f-14ef937558be | SUCCESS | 0 | 0.993s | retained | off | 0.00286877 |
| red-1 | 01a15c42-e412-7769-acdb-66131fb4b93f | SUCCESS | 0 | 3.508s | disposable | off | 0.025332720000000003 |
| impl-tests-6 | 01a15c43-7329-74b8-974f-fecb17b9644c | SUCCESS | 0 | 1.728s | disposable | off | 0.00283283 |
| impl-python-7 | 01a15c43-a50b-7247-a218-a886caa5747b | SUCCESS | 0 | 1.227s | disposable | off | 0.0012798800000000002 |
| verify | 01a15c43-e976-7081-b639-b0e34c7d5fee | SUCCESS | 0 | 3.319s | disposable | off | 0.02552844 |
| existing | 01a15c44-0284-70f8-8286-f83558405660 | SUCCESS | 0 | 1.499s | disposable | off | 0.00892354 |

Sandbox operations: 6, total guest duration 12.274s, retained images ['ad6d111e-1a72-4c7e-b8fe-69994a453720'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
