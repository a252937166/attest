# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-attest-a1-20261019T042013134893Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:20:13.135866+00:00, finished 2026-10-19T04:31:35.239182+00:00.

**Accept this patch.** All 18 sealed tests pass on the candidate in a fresh sandbox, and 15 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 18 of 18 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 18 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 15 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 3 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 15 of 18 failed on the unmodified base; 18 of 18 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `26b3fdf0-e597-4d9f-a16d-a83b37177405`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement brackets.is_balanced(s) in brackets/core.py to return a bool indicating whether all parentheses, square brackets, and braces in a string are correctly paired and nested. Ignore all other characters, treat the empty string as balanced, and raise TypeError for non-string inputs. Preserve is_bracket, package imports, and existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept a str instance, including subclasses. Consider only the six characters ()[]{}. Each closing bracket must match the most recent opening bracket that has n | TypeError: s is not an instance of str, including None, bytes, numbers, and containers. Do not coerce non-string inputs to strings. Exception message is unspeci |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True exactly when c is a str instance of length one and is one of ()[]{}; return False otherwise. |  |

Acceptance criteria:
AC1. 1. from brackets import is_balanced and from brackets import is_bracket continue to work.
AC2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}', and '([{}])'.
AC3. 3. is_balanced returns True for nested and adjacent pairs, including '((()))', '[[]]', '{{}}', and '([]){}[()]'.
AC4. 4. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
AC5. 5. Strings containing no bracket characters, including ordinary text, whitespace, and Unicode text, return True.
AC6. 6. Inserting or removing non-bracket characters anywhere does not change the result. Quotation marks and backslashes do not suppress bracket recognition.
AC7. 7. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}', and '())'.
AC8. 8. Unmatched opening brackets of every kind return False, including '[', '{', and '([]'.
AC9. 9. Unmatched closing brackets of every kind return False, including ']', '}', ')(', '[]]', and '{}('.
AC10. 10. Every result for a string input has type bool, including both balanced and unbalanced cases.
AC11. 11. Non-string inputs raise TypeError, including None, True, 0, 1.5, b'()', [], (), {}, and set().
AC12. 12. Instances of a str subclass are accepted and evaluated using the same bracket rules.
AC13. 13. Repeated calls are independent: calling with an unbalanced string does not affect a subsequent balanced result.
AC14. 14. is_bracket remains unchanged and returns True for each of the six bracket characters and False for 'a', '', '((', and 1.
AC15. 15. Existing test files remain unchanged and their tests continue to pass.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by implementing is_balanced with a string type check and a local stack for bracket matching. No changes to is_bracket, constants, package exports, or existing tests are required. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `c87fe9493dae3e573ca3c6cf053a1fa48d34373b60f4917fab67fe542f6798d9`, 18 test methods, sealed at 2026-10-19T04:27:16.409778+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 18 methods: ERROR 15): 15 of 18 methods failing, 3 passing; operation `01a15269-e458-7764-b803-66aea0d4e03f`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestBalanced.test_adjacent_and_nested_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_calls_do_not_share_bracket_state | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_crossed_and_mismatched_pairs_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_extra_opening_bracket_after_a_pair_is_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_inserting_or_removing_other_characters_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_interspersed_text_is_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_non_string_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_public_package_exports | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_quotes_and_backslashes_do_not_hide_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_repeated_same_kind_nesting_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_string_results_are_actual_bools | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_string_subclasses_follow_the_same_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_text_without_brackets_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_unmatched_closing_brackets_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_unmatched_opening_brackets_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBracketHelper.test_each_bracket_character_is_recognized | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBracketHelper.test_other_values_are_not_recognized | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,15 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("s must be a string")
+
+    stack = []
+    for character in s:
+        if character in OPEN:
+            stack.append(character)
+        elif character in CLOSE:
+            if not stack or stack.pop() != PAIRS[character]:
+                return False
+
+    return not stack
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (18 of 18 methods, each in its own process). Operation `01a1526c-089e-716c-b2c7-2c6b709d0fb8`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a1526c-2ac9-7320-a5c1-0d71bb6f8912`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 9 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (8 of 8 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-1186a0e444 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-3924-7353-b23f-6f5e75b16b3d |
| m02-fdb0425458 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestBalanced.test_non_string_inputs_raise_type_error | 01a1526c-38e0-72d1-82d2-2e0126011d9c |
| m03-5bec38f1de | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-38f3-7464-ade0-e91f50fa334b |
| m04-991d05b2b7 | brackets/core.py | 21 | In -> NotIn | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-391e-73b9-ab69-a42ece50fced |
| m05-32da8a64d1 | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-38d9-772e-9942-88d1f746ec8d |
| m06-c934d1c725 | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-38f6-7334-b1a4-b2ea2c791735 |
| m07-ff959fc3ed | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-3905-750d-9e33-9f387194a7db |
| m08-226d16dc14 | brackets/core.py | 23 | False -> True | killed | test_sealed.TestBalanced.test_quotes_and_backslashes_do_not_hide_brackets, test_sealed.TestBalanced.test_crossed_and_mis | 01a1526c-38fc-7314-8b79-58cc3c109435 |
| m09-cd18452441 | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestBalanced.test_empty_and_simple_pairs_are_balanced, test_sealed.TestBalanced.test_repeated_same_kind_nest | 01a1526c-52b8-75ca-b7ef-ab76f7a71b22 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `c3456e688de525187e14d9ab9c0bc97bf1bd5324a0beb3a140348093bb184330`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a1526d-6f28-77c9-b7ab-b72f0043f12c`. Notes: Targets exhaustive short bracket sequences, mixed nesting, deep stacks, Unicode lookalikes, and additional type boundaries.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fulfills the contract: `isinstance(s, str)` accepts strings and subclasses while rejecting other inputs, the local stack and `stack.pop() != PAIRS[character]` enforce matching and nesting, and `return not stack` returns a bool while non-bracket characters are ignored. Only is_balanced changes, preserving constants, exports, is_bracket, and tests; the observed test run supports the claim that existing tests pass (2 passed).

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10118 | 823 | 0 | - | 147.7s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 10963 | 92 | 0 | - | 152.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10341 | 2308 | 7168 | - | 106.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10307 | 94 | 0 | - | 25.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10502 | 203 | 0 | - | 41.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10713 | 72 | 7168 | - | 39.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10846 | 134 | 7168 | - | 21.9s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10401 | 1689 | 0 | - | 66.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10763 | 151 | 0 | - | 29.4s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 94954/5566/21504; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15263-9893-72d9-a851-845664c7b6f0 | SUCCESS | 0 | 0.814s | retained | off | 0.0028448699999999998 |
| red-1 | 01a15269-e458-7764-b803-66aea0d4e03f | SUCCESS | 0 | 4.209s | disposable | off | 0.03479711 |
| impl-tests-3 | 01a1526b-a5e1-71b7-bb03-647719e206d4 | SUCCESS | 0 | 0.769s | disposable | off | 0.00285343 |
| verify | 01a1526c-089e-716c-b2c7-2c6b709d0fb8 | SUCCESS | 0 | 4.25s | disposable | off | 0.034931870000000004 |
| existing | 01a1526c-2ac9-7320-a5c1-0d71bb6f8912 | SUCCESS | 0 | 1.424s | disposable | off | 0.0088673 |
| mutant-m02-fdb0425458 | 01a1526c-38e0-72d1-82d2-2e0126011d9c | SUCCESS | 0 | 3.931s | disposable | off | 0.03157367 |
| mutant-m01-1186a0e444 | 01a1526c-3924-7353-b23f-6f5e75b16b3d | SUCCESS | 0 | 3.954s | disposable | off | 0.031666070000000004 |
| mutant-m03-5bec38f1de | 01a1526c-38f3-7464-ade0-e91f50fa334b | SUCCESS | 0 | 3.941s | disposable | off | 0.03162132 |
| mutant-m05-32da8a64d1 | 01a1526c-38d9-772e-9942-88d1f746ec8d | SUCCESS | 0 | 3.955s | disposable | off | 0.031672019999999995 |
| mutant-m04-991d05b2b7 | 01a1526c-391e-73b9-ab69-a42ece50fced | SUCCESS | 0 | 3.941s | disposable | off | 0.03161621 |
| mutant-m06-c934d1c725 | 01a1526c-38f6-7334-b1a4-b2ea2c791735 | SUCCESS | 0 | 3.954s | disposable | off | 0.03164849 |
| mutant-m08-226d16dc14 | 01a1526c-38fc-7314-8b79-58cc3c109435 | SUCCESS | 0 | 3.955s | disposable | off | 0.03164612 |
| mutant-m07-ff959fc3ed | 01a1526c-3905-750d-9e33-9f387194a7db | SUCCESS | 0 | 3.954s | disposable | off | 0.03134405 |
| mutant-m09-cd18452441 | 01a1526c-52b8-75ca-b7ef-ab76f7a71b22 | SUCCESS | 0 | 3.848s | disposable | off | 0.03137366 |
| breaker-tests | 01a1526d-6f28-77c9-b7ab-b72f0043f12c | SUCCESS | 0 | 2.476s | disposable | off | 0.01858925 |

Sandbox operations: 15, total guest duration 49.375s, retained images ['26b3fdf0-e597-4d9f-a16d-a83b37177405'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion is never overridden. The classification itself remains a model judgement.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
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
