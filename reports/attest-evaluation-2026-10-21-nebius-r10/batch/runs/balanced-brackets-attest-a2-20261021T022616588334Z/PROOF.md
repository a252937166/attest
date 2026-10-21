# Attest Proof Bundle: balanced-brackets

**Verdict: NEEDS HUMAN**  
Run `balanced-brackets-attest-a2-20261021T022616588334Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T02:26:16.592240+00:00, finished 2026-10-21T02:28:26.242456+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter. The correction did not pass the mechanical validation (correction rejected whole: tests that were not failing were altered: test_breaker.TestIsBalancedBreaker.test_escape_sequences_in_string_literal), so the gate was not re-run and the hold stands. Defect kinds: wrong expected value.

Key evidence (E6): generated-test failures could not be cleared by arbitration; human review required



What to do: Check the arbiter's classifications and the correction in E6 (original and corrected tests are both kept). If you agree with the arbiter, accept the patch on that basis; otherwise treat the failing test as a finding.

Reasons: adversarial suite binding failed: child process nonzero exit: test_bracket_like_characters_not_brackets exit 1; model-written adversarial tests failed: 1 of 10 (test_breaker.TestIsBalancedBreaker.test_bracket_like_characters_not_brackets); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (validated corrections re-run their gates): generated-test failures could not be cleared by arbitration; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 13 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 13 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 13 of 13 failed on the unmodified base; 13 of 13 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 9 of 10 pass; 1 failing: test_bracket_like_characters_not_brackets; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | generated-test failures could not be cleared by arbitration; human review required |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `2e7ae4e1-b025-49cd-ba06-ef45557526af`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the is_balanced(s) function in brackets/core.py so that it returns True when the three bracket types (), [], {} in the string s are correctly matched and nested, ignoring non-bracket characters. The empty string is balanced. The function must return a bool and raise TypeError if s is not a string. The existing is_bracket helper and the test suite must not be modified.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_balanced | is_balanced(s: str) -> bool | Returns True if the string s contains correctly matched and nested brackets of types (), [], {}. Non-bracket characters are ignored. The empty string is conside | TypeError: raised when s is not a string. |
| is_bracket | is_bracket(c: str) -> bool | Returns True if c is a single character string that is one of the six bracket characters '(', ')', '[', ']', '{', '}'. Returns False otherwise. |  |

Acceptance criteria:
AC1. 1. The empty string '', '()', '[]', '{}', '()[]{}', '([{}])' are all balanced (return True).
AC2. 2. Nested mixed brackets with other characters are balanced: '(a[b]{c})', 'f(x[0], y[1])' return True.
AC3. 3. Unbalanced strings '(', ')', '([)]', '(]', '{[}', '())' return False.
AC4. 4. Non-bracket characters are ignored (they do not affect balancing).
AC5. 5. is_balanced returns a bool (True or False).
AC6. 6. TypeError is raised when s is not a string.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract is satisfiable. The existing is_bracket helper correctly identifies the six bracket characters and can be used to filter input. The standard stack-based bracket matching algorithm can be implemented in is_balanced using the module's PAIRS, OPEN, and CLOSE constants without modifying is_bracket or any tests. All acceptance criteria (TC1-TC6) are mutually compatible and achievable. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `2544e3c53fec1f242becb96f24e44c49d382fd8b9f7d5289b3b19379c6a1375c`, 13 test methods, sealed at 2026-10-21T02:26:56.508093+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 13 methods: ERROR 13): 13 of 13 methods failing, 0 passing; operation `01a15c48-71af-7722-bd38-018d19b293d6`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_empty_string_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_extra_closing | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_types | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_multiple_pairs_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_with_other_chars | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_non_bracket_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_return_type_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_simple_pairs_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_non_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unbalanced_single_close | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unbalanced_single_open | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_wrong_order | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,15 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("s must be a string")
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

Sealed suite: OK (13 of 13 methods, each in its own process). Operation `01a15c49-3557-73e9-a6eb-16efc564b0d8`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15c49-4f01-7416-9691-6b336561abb0`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 9 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 10 methods: FAIL 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-49f17f1c46 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_simple_pairs_balanced, test_se | 01a15c49-67c3-731a-bef4-081de7a85b66 |
| m02-13cd7c4660 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestIsBalanced.test_type_error_non_string | 01a15c49-67e7-71ab-8d57-e9d0a04e9fd3 |
| m03-6bf6dacb10 | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_simple_pairs_balanced, test_sealed.TestIsBalanced.test_multiple_pairs_balanced, test_sea | 01a15c49-67f4-7278-9e19-a5405c161c9d |
| m04-56a9992acf | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestIsBalanced.test_simple_pairs_balanced, test_sealed.TestIsBalanced.test_multiple_pairs_balanced, test_sea | 01a15c49-67c2-7180-8226-81ebffa459ec |
| m05-ff54fc2cdd | brackets/core.py | 22 | 1 -> 2 | killed | test_sealed.TestIsBalanced.test_simple_pairs_balanced, test_sealed.TestIsBalanced.test_multiple_pairs_balanced, test_sea | 01a15c49-6983-716c-9388-c76d87b2286a |
| m06-648bfa5727 | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_simple_pairs_balanced, test_sealed.TestIsBalanced.test_multiple_pairs_balanced, test_sea | 01a15c49-67d8-70cd-9d77-86076824ed82 |
| m07-aaa321b790 | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestIsBalanced.test_unbalanced_single_close, test_sealed.TestIsBalanced.test_wrong_order, test_sealed.TestIs | 01a15c49-67ba-75b9-a808-9ec2225769ad |
| m08-30c6179cf9 | brackets/core.py | 23 | False -> True | killed | test_sealed.TestIsBalanced.test_unbalanced_single_close, test_sealed.TestIsBalanced.test_wrong_order, test_sealed.TestIs | 01a15c49-67ae-7671-8ece-d7098061f5bb |
| m09-d06fca2f72 | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_simple_pairs_balanced, test_se | 01a15c49-7ffe-7401-b73b-6c96f209be3e |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `686ca947cd74967681fdb7f56ce94ca06d54e773786b2a8f8266656295155783`): FAILED (1 of 10 methods: FAIL 1); binding FAILED; operation `01a15c49-b96c-7120-8311-2660a28893cb`. Notes: Targeted boundaries, large inputs, unicode, non-bracket only, subclass acceptance.

| Failing adversarial test | Outcome |
| --- | --- |
| test_bracket_like_characters_not_brackets | FAIL |

Adversarial authoring: 1 attempt(s).

### Counterexamples
- E3 `test_bracket_like_characters_not_brackets`: FAIL; AssertionError: True is not false; arbiter: Defective test, by the arbiter; contract basis: Contract: 'Characters that are not brackets are ignored.' The brackets are only '(', ')', '[', ']', '{', '}'. The string '<>{}' contains non-bracket characters '<' and '>' which must be ignored, leaving balanced '{}'.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements is_balanced exactly as specified: it validates string input, uses a stack with the existing PAIRS/OPEN/CLOSE constants and the is_bracket helper, ignores non-bracket characters, and returns a bool. All acceptance criteria are satisfied and the existing test suite passes, with no extra changes or omissions.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
generated-test failures could not be cleared by arbitration; human review required (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_bracket_like_characters_not_brackets | test_defect | The test expects is_balanced('<>{}') to return False, but the contract states that non-bracket characters are ignored. Since '<' and '>' are | Contract: 'Characters that are not brackets are ignored.' The brackets are only '(', ')', '[', ']', '{', '}'. The string '<>{}' contains non |

- `adversarial` corrected re-run: candidate n/a; base n/a; validated=False; not applied: correction rejected whole: tests that were not failing were altered: test_breaker.TestIsBalancedBreaker.test_escape_sequences_in_string_literal

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1046 | 1565 | 0 | 0.005741 | 5.6s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 2432 | 1469 | 0 | 0.006839 | 5.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1373 | 1462 | 0 | 0.001728 | 11.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1363 | 148 | 0 | 0.000542 | 3.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1483 | 171 | 0 | 0.000599 | 4.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1688 | 783 | 0 | 0.001211 | 7.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1934 | 194 | 0 | 0.000755 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2077 | 959 | 0 | 0.001486 | 8.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2666 | 150 | 0 | 0.000935 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1339 | 554 | 0 | 0.000900 | 8.3s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1479 | 1007 | 0 | 0.004500 | 4.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 2576 | 1242 | 0 | 0.006302 | 4.6s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 21456/9704/0; Inference USD: 0.031538.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c48-0236-75c3-92b2-8bd41d0d10c8 | SUCCESS | 0 | 1.267s | retained | off | 0.0028235699999999996 |
| red-1 | 01a15c48-71af-7722-bd38-018d19b293d6 | SUCCESS | 0 | 4.412s | disposable | off | 0.026791300000000004 |
| impl-tests-4 | 01a15c48-e5a8-76ea-b72e-438fcd214a6f | SUCCESS | 0 | 1.714s | disposable | off | 0.0029212599999999997 |
| impl-python-5 | 01a15c49-1de7-7214-9778-edbd471d4ba3 | SUCCESS | 0 | 0.819s | disposable | off | 0.00121193 |
| verify | 01a15c49-3557-73e9-a6eb-16efc564b0d8 | SUCCESS | 0 | 3.823s | disposable | off | 0.02662455 |
| existing | 01a15c49-4f01-7416-9691-6b336561abb0 | SUCCESS | 0 | 1.547s | disposable | off | 0.00880919 |
| mutant-m04-56a9992acf | 01a15c49-67c2-7180-8226-81ebffa459ec | SUCCESS | 0 | 3.237s | disposable | off | 0.023216700000000003 |
| mutant-m01-49f17f1c46 | 01a15c49-67c3-731a-bef4-081de7a85b66 | SUCCESS | 0 | 3.226s | disposable | off | 0.023299910000000004 |
| mutant-m02-13cd7c4660 | 01a15c49-67e7-71ab-8d57-e9d0a04e9fd3 | SUCCESS | 0 | 3.235s | disposable | off | 0.02321564 |
| mutant-m05-ff54fc2cdd | 01a15c49-6983-716c-9388-c76d87b2286a | SUCCESS | 0 | 3.14s | disposable | off | 0.023257550000000002 |
| mutant-m03-6bf6dacb10 | 01a15c49-67f4-7278-9e19-a5405c161c9d | SUCCESS | 0 | 3.236s | disposable | off | 0.023253940000000004 |
| mutant-m06-648bfa5727 | 01a15c49-67d8-70cd-9d77-86076824ed82 | SUCCESS | 0 | 3.255s | disposable | off | 0.023142239999999998 |
| mutant-m07-aaa321b790 | 01a15c49-67ba-75b9-a808-9ec2225769ad | SUCCESS | 0 | 3.223s | disposable | off | 0.02313189 |
| mutant-m08-30c6179cf9 | 01a15c49-67ae-7671-8ece-d7098061f5bb | SUCCESS | 0 | 3.27s | disposable | off | 0.02338623 |
| mutant-m09-d06fca2f72 | 01a15c49-7ffe-7401-b73b-6c96f209be3e | SUCCESS | 0 | 3.394s | disposable | off | 0.023550520000000002 |
| breaker-tests | 01a15c49-b96c-7120-8311-2660a28893cb | SUCCESS | 0 | 3.377s | disposable | off | 0.022070149999999997 |

Sandbox operations: 16, total guest duration 46.175s, retained images ['2e7ae4e1-b025-49cd-ba06-ef45557526af'].

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
