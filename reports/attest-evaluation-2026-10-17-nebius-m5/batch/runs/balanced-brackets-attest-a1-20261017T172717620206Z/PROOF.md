# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-attest-a1-20261017T172717620206Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:27:17.620545+00:00, finished 2026-10-17T17:29:05.261214+00:00.

**Accept this patch.** All 18 sealed tests pass on the candidate in a fresh sandbox, and 18 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 18 of 18 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 18 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 18 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 18 of 18 failed on the unmodified base; 18 of 18 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `36ffdb60-ee67-48cb-b23f-2ce5de58673b`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the function `is_balanced(s)` in the `brackets` package to determine whether a string `s` contains properly matched and nested brackets of three types: parentheses `()`, square brackets `[]`, and curly braces `{}`. Non-bracket characters are ignored. The function must return `True` for balanced strings (including the empty string) and `False` otherwise. It must raise a `TypeError` if the input `s` is not a string. The existing helper `is_bracket` must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_bracket | is_bracket(c) | Returns True if `c` is a single-character string and one of the six bracket characters: '(', ')', '[', ']', '{', '}'. Returns False otherwise (including for non |  |
| is_balanced | is_balanced(s) | Returns True if all brackets in the string `s` are correctly matched and nested, ignoring any non-bracket characters. The empty string is considered balanced. R | TypeError: raised when `s` is not a string (e.g., None, int, list, etc.) |

Acceptance criteria:
1. 1. The empty string '' returns True.
2. 2. Simple balanced pairs '()', '[]', '{}' each return True.
3. 3. Concatenated balanced pairs '()[]{}' returns True.
4. 4. Nested mixed brackets '([{}])' returns True.
5. 5. Balanced brackets with non-bracket characters: '(a[b]{c})' returns True.
6. 6. Balanced brackets with non-bracket characters in a function-like string: 'f(x[0], y[1])' returns True.
7. 7. Unclosed opening bracket '(' returns False.
8. 8. Unmatched closing bracket ')' returns False.
9. 9. Incorrectly nested brackets '([)]' returns False.
10. 10. Mismatched opening and closing brackets '(]' returns False.
11. 11. Mismatched opening and closing brackets '{[}' returns False.
12. 12. Extra closing bracket '())' returns False.
13. 13. Non-bracket characters are ignored (e.g., 'abc' returns True, 'a(b)c' returns True).
14. 14. The function returns a bool (True or False) for all string inputs.
15. 15. A TypeError is raised when the input `s` is not a string (e.g., 123, None, [], {}).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `b03e09da35e0f0e496fc04d903ab1b4e8b6b78a0db1e3fe065a7043c33beadaa`, 18 test methods, sealed at 2026-10-17T17:27:45.211639+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 18 methods: ERROR 18): 18 of 18 methods failing, 0 passing; operation `01a14ae7-b5b0-74d9-b407-2e8df65d6f92`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_balanced_with_non_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_concatenated_pairs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_empty_string_returns_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_extra_closing | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_function_like_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_incorrectly_nested | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_curly_square | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_parenthesis_square | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_mixed | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_non_bracket_characters_only | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_non_bracket_interleaved | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_return_type_is_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_simple_curly | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_simple_parentheses | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_simple_square | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_on_non_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unclosed_opening | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unmatched_closing | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,15 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("Input must be a string")
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (18 of 18 methods, each in its own process). Operation `01a14ae8-687a-7600-986c-1050c5904c9f`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14ae8-8171-75ae-b5da-597539761d43`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 9 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-f803d18efa | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_returns_true, test_sealed.TestIsBalanced.test_simple_parentheses, test_seal | 01a14ae8-9022-7594-9946-391f1380f09e |
| m02-13cd7c4660 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestIsBalanced.test_type_error_on_non_string | 01a14ae8-900d-7455-8405-e070efe3f343 |
| m03-a871b8398d | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_simple_parentheses, test_sealed.TestIsBalanced.test_simple_square, test_sealed.TestIsBal | 01a14ae8-902b-7244-a6ea-17009967303f |
| m04-676b2caa85 | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestIsBalanced.test_simple_parentheses, test_sealed.TestIsBalanced.test_simple_square, test_sealed.TestIsBal | 01a14ae8-900a-760a-b2f1-e7b49c79e718 |
| m05-74309e5db8 | brackets/core.py | 22 | 1 -> 2 | killed | test_sealed.TestIsBalanced.test_simple_parentheses, test_sealed.TestIsBalanced.test_simple_square, test_sealed.TestIsBal | 01a14ae8-901c-77c1-b1bc-014d13826ae0 |
| m06-e5b958d362 | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_simple_parentheses, test_sealed.TestIsBalanced.test_simple_square, test_sealed.TestIsBal | 01a14ae8-903d-74cf-8a15-7982dff842f2 |
| m07-1d457f2df0 | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestIsBalanced.test_unmatched_closing, test_sealed.TestIsBalanced.test_incorrectly_nested, test_sealed.TestI | 01a14ae8-8fec-75f6-a580-cb9fabf5b871 |
| m08-27dbf581ca | brackets/core.py | 23 | False -> True | killed | test_sealed.TestIsBalanced.test_unmatched_closing, test_sealed.TestIsBalanced.test_incorrectly_nested, test_sealed.TestI | 01a14ae8-901f-76c7-9f0e-9f83901b47f0 |
| m09-7b4f6e6466 | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_returns_true, test_sealed.TestIsBalanced.test_simple_parentheses, test_seal | 01a14ae8-a8c9-72c9-be37-42818ed6568a |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `d165d385db8add10e6b1822d614c0933d4feb8637d622a9813243ebc094723c3`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a14ae8-dcfd-7643-a6e2-c480cc0f3db5`. Notes: Targeted deep nesting, alternating patterns, many non‑brackets, unicode, various non‑string types, return type, single chars, and large input performance.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The implementation of is_balanced correctly handles all required cases including type checking, bracket matching, nesting, and non-bracket characters. All tests pass and the verification script confirms all acceptance criteria are met.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1046 | 1675 | 0 | 0.006071 | 6.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1453 | 682 | 0 | 0.001050 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1445 | 80 | 0 | 0.000505 | 2.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1537 | 107 | 0 | 0.000557 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1730 | 820 | 0 | 0.001257 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1974 | 107 | 0 | 0.000688 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2115 | 712 | 0 | 0.001275 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2639 | 148 | 0 | 0.000925 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2789 | 95 | 0 | 0.000922 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1585 | 819 | 0 | 0.001213 | 6.8s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1701 | 1579 | 0 | 0.006438 | 6.4s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 20014/6824/0; USD: 0.020901.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ae7-731c-754e-9d4e-44a0cfd03b18 | SUCCESS | 0 | 1.272s | retained | off | 0.00287322 |
| red-1 | 01a14ae7-b5b0-74d9-b407-2e8df65d6f92 | SUCCESS | 0 | 5.279s | disposable | off | 0.03445791 |
| impl-tests-4 | 01a14ae8-0a84-77e7-8c1e-42360af58e5c | SUCCESS | 0 | 0.895s | disposable | off | 0.00287968 |
| impl-python-5 | 01a14ae8-39e8-713b-821f-1bce14fe2fc4 | SUCCESS | 0 | 0.574s | disposable | off | 0.00121109 |
| impl-tests-6 | 01a14ae8-50e9-738c-b445-884761938b53 | SUCCESS | 0 | 0.835s | disposable | off | 0.0028936899999999995 |
| verify | 01a14ae8-687a-7600-986c-1050c5904c9f | SUCCESS | 0 | 4.094s | disposable | off | 0.03447216 |
| existing | 01a14ae8-8171-75ae-b5da-597539761d43 | SUCCESS | 0 | 1.398s | disposable | off | 0.008811099999999999 |
| mutant-m01-f803d18efa | 01a14ae8-9022-7594-9946-391f1380f09e | SUCCESS | 0 | 3.966s | disposable | off | 0.03156594 |
| mutant-m02-13cd7c4660 | 01a14ae8-900d-7455-8405-e070efe3f343 | SUCCESS | 0 | 4.051s | disposable | off | 0.03189993 |
| mutant-m03-a871b8398d | 01a14ae8-902b-7244-a6ea-17009967303f | SUCCESS | 0 | 3.853s | disposable | off | 0.03120903 |
| mutant-m05-74309e5db8 | 01a14ae8-901c-77c1-b1bc-014d13826ae0 | SUCCESS | 0 | 4.056s | disposable | off | 0.03207887 |
| mutant-m04-676b2caa85 | 01a14ae8-900a-760a-b2f1-e7b49c79e718 | SUCCESS | 0 | 3.966s | disposable | off | 0.03151896 |
| mutant-m06-e5b958d362 | 01a14ae8-903d-74cf-8a15-7982dff842f2 | SUCCESS | 0 | 4.082s | disposable | off | 0.03208984 |
| mutant-m07-1d457f2df0 | 01a14ae8-8fec-75f6-a580-cb9fabf5b871 | SUCCESS | 0 | 3.955s | disposable | off | 0.03106351 |
| mutant-m08-27dbf581ca | 01a14ae8-901f-76c7-9f0e-9f83901b47f0 | SUCCESS | 0 | 3.976s | disposable | off | 0.03202196 |
| mutant-m09-7b4f6e6466 | 01a14ae8-a8c9-72c9-be37-42818ed6568a | SUCCESS | 0 | 3.868s | disposable | off | 0.03163852 |
| breaker-tests | 01a14ae8-dcfd-7643-a6e2-c480cc0f3db5 | SUCCESS | 0 | 2.678s | disposable | off | 0.020112730000000002 |

Sandbox operations: 17, total guest duration 52.798s, retained images ['36ffdb60-ee67-48cb-b23f-2ce5de58673b'].

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
