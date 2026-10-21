# Attest Proof Bundle: balanced-brackets

**Verdict: NEEDS HUMAN**  
Run `balanced-brackets-attest-a1-20261021T022451789152Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T02:24:51.792298+00:00, finished 2026-10-21T02:29:05.713157+00:00.

**Hold this patch.** The implementer ran out of turns before declaring the work finished, so the candidate is a partial attempt even where tests pass.

Key evidence (gates): implementer did not finish within 14 turns



What to do: Treat the patch as a draft; run again with a larger turn budget or a narrower task.

Reasons: implementer did not finish within 14 turns


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 18 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 18 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 18 of 18 failed on the unmodified base; 18 of 18 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ed9f8250-64c6-4bdf-8a0b-267e73df742b`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the `is_balanced(s)` function in `brackets/core.py` to determine whether a string `s` contains properly matched and nested brackets of three types: parentheses `()`, square brackets `[]`, and curly braces `{}`. Non-bracket characters are ignored. The function must return `True` for balanced strings (including the empty string) and `False` otherwise. It must raise `TypeError` if the input `s` is not a string. The existing helper `is_bracket` and the constants `PAIRS`, `OPEN`, `CLOSE` are available and must not be modified.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_balanced | def is_balanced(s) -> bool: | Checks if the brackets in the string `s` are correctly matched and nested. Iterates over each character in `s`; if the character is a bracket (as determined by  | Raise TypeError if `s` is not a string. |

Acceptance criteria:
AC1. is_balanced("") returns True.
AC2. is_balanced("()") returns True.
AC3. is_balanced("[]") returns True.
AC4. is_balanced("{}") returns True.
AC5. is_balanced("()[]{}") returns True.
AC6. is_balanced("([{}])") returns True.
AC7. is_balanced("(a[b]{c})") returns True.
AC8. is_balanced("f(x[0], y[1])") returns True.
AC9. is_balanced("(") returns False.
AC10. is_balanced(")") returns False.
AC11. is_balanced("([)]") returns False.
AC12. is_balanced("(]") returns False.
AC13. is_balanced("{[}") returns False.
AC14. is_balanced("())") returns False.
AC15. is_balanced returns a bool for all string inputs.
AC16. is_balanced raises TypeError when s is not a string (e.g., None, 123, []).

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract is satisfiable. The requirements describe a standard bracket matching problem solvable with a stack-based algorithm. All authoritative criteria (TC1-TC6) are mutually consistent: they specify correct behavior for balanced strings, unbalanced strings, non-bracket characters, return type, and error handling. The existing helper is_bracket and constants PAIRS, OPEN, CLOSE are correctly defined and support the implementation. No conflicts exist between requirements or with the frozen code. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `c4953c648844d3dd2ae71516be470ea0beff6db0b386af4768fc4aaa7eae892f`, 18 test methods, sealed at 2026-10-21T02:25:28.357661+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 18 methods: ERROR 18): 18 of 18 methods failing, 0 passing; operation `01a15c47-1d1e-739f-88b9-83503d77e844`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_balanced_function_call_like | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_balanced_with_other_characters | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_curly_braces_only_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_curly_open_square_close_curly_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_empty_string_returns_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_extra_close_parenthesis_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_order_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mixed_types_balanced_sequence | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_open_parenthesis_close_square_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_parentheses_only_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_return_type_is_bool_for_strings | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_single_close_parenthesis_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_single_open_parenthesis_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_square_brackets_only_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_on_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_on_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_on_none | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 14 implementer turn(s).

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
+            else:  # ch is a closing bracket
+                if not stack or stack.pop() != PAIRS[ch]:
+                    return False
+    return len(stack) == 0
+
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (18 of 18 methods, each in its own process). Operation `01a15c49-c954-7227-a301-45ea8625a404`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15c49-ec00-758b-93cf-e0a105be7ae6`, bound through the supervisor: 1 module(s), binding ok.

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

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: implementer did not finish.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-3cafca6a46 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_returns_true, test_sealed.TestIsBalanced.test_parentheses_only_balanced, te | 01a15c4a-0586-73aa-b48b-a8e951e4c883 |
| m02-69b9809a8c | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestIsBalanced.test_type_error_on_list | 01a15c4a-05fa-76be-9bca-1c3e6294b189 |
| m03-4739522edc | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_parentheses_only_balanced, test_sealed.TestIsBalanced.test_square_brackets_only_balanced | 01a15c4a-0573-74fa-84fe-4d8f98b0c465 |
| m04-79b03b486a | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestIsBalanced.test_parentheses_only_balanced, test_sealed.TestIsBalanced.test_square_brackets_only_balanced | 01a15c4a-05d6-719d-bac6-a25f28730a1e |
| m05-a6550a9dc1 | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_parentheses_only_balanced, test_sealed.TestIsBalanced.test_square_brackets_only_balanced | 01a15c4a-05c2-7211-b1cd-80cd7af8cab2 |
| m06-7e7fc66ad7 | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestIsBalanced.test_parentheses_only_balanced, test_sealed.TestIsBalanced.test_square_brackets_only_balanced | 01a15c4a-0589-7671-a31f-8ca2a4acbe4b |
| m07-5ede625652 | brackets/core.py | 23 | False -> True | killed | test_sealed.TestIsBalanced.test_single_close_parenthesis_returns_false, test_sealed.TestIsBalanced.test_mismatched_order | 01a15c4a-057a-733d-b8ba-048e983a6b84 |
| m08-73d38d359d | brackets/core.py | 24 | 0 -> 1 | killed | test_sealed.TestIsBalanced.test_empty_string_returns_true, test_sealed.TestIsBalanced.test_parentheses_only_balanced, te | 01a15c4a-0598-7168-b996-665d45304330 |
| m09-a3ae309408 | brackets/core.py | 24 | Eq -> NotEq | killed | test_sealed.TestIsBalanced.test_empty_string_returns_true, test_sealed.TestIsBalanced.test_parentheses_only_balanced, te | 01a15c4a-2778-7374-a893-4818d97fa46d |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `8338cddf9f2b9ecf5278dff1ed5448815145294a088721f984043b03ddc797de`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a15c4a-5e29-76d8-a035-def5e0a73813`. Notes: Added tests for non‑bracket only strings, deep nesting, large inputs, additional non‑string types, and return‑type verification.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds a type guard raising TypeError for non-strings, then iterates over characters using is_bracket to push openings onto a stack and pop for closings with PAIRS mapping, returning True only when the stack is empty. This matches the contract and all acceptance criteria without modifying is_bracket or the constants.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1046 | 1878 | 0 | 0.006680 | 6.0s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 2589 | 651 | 0 | 0.004542 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1514 | 1008 | 0 | 0.001361 | 13.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1527 | 105 | 0 | 0.000553 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1724 | 555 | 0 | 0.001017 | 7.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1823 | 383 | 0 | 0.000892 | 6.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2072 | 917 | 0 | 0.001447 | 10.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2314 | 1282 | 0 | 0.001848 | 16.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2424 | 1128 | 0 | 0.001742 | 9.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2711 | 744 | 0 | 0.001483 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 2837 | 464 | 0 | 0.001269 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 2943 | 1526 | 0 | 0.002256 | 18.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 2927 | 1902 | 0 | 0.002590 | 17.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 2968 | 3757 | 0 | 0.004272 | 26.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 3019 | 315 | 0 | 0.001189 | 4.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | medium | 2931 | 2330 | 0 | 0.002976 | 17.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-14 | medium | 3119 | 1788 | 0 | 0.002545 | 16.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1570 | 720 | 0 | 0.001119 | 7.4s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2108 | 2161 | 0 | 0.008591 | 6.7s | ok |

Model calls: 19 (0 failed, 0 malformed); tokens in/out/cached 44166/23614/0; Inference USD: 0.048372.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c46-b56e-76b7-a677-50bb7d062052 | SUCCESS | 0 | 0.778s | retained | off | 0.00294065 |
| red-1 | 01a15c47-1d1e-739f-88b9-83503d77e844 | SUCCESS | 0 | 4.693s | disposable | off | 0.03490802 |
| verify | 01a15c49-c954-7227-a301-45ea8625a404 | SUCCESS | 0 | 4.751s | disposable | off | 0.035493949999999996 |
| existing | 01a15c49-ec00-758b-93cf-e0a105be7ae6 | SUCCESS | 0 | 1.721s | disposable | off | 0.00888265 |
| mutant-m01-3cafca6a46 | 01a15c4a-0586-73aa-b48b-a8e951e4c883 | SUCCESS | 0 | 4.671s | disposable | off | 0.03146954 |
| mutant-m02-69b9809a8c | 01a15c4a-05fa-76be-9bca-1c3e6294b189 | SUCCESS | 0 | 4.67s | disposable | off | 0.031115300000000002 |
| mutant-m03-4739522edc | 01a15c4a-0573-74fa-84fe-4d8f98b0c465 | SUCCESS | 0 | 4.273s | disposable | off | 0.03163452 |
| mutant-m04-79b03b486a | 01a15c4a-05d6-719d-bac6-a25f28730a1e | SUCCESS | 0 | 4.67s | disposable | off | 0.03185879 |
| mutant-m05-a6550a9dc1 | 01a15c4a-05c2-7211-b1cd-80cd7af8cab2 | SUCCESS | 0 | 4.647s | disposable | off | 0.03157317 |
| mutant-m06-7e7fc66ad7 | 01a15c4a-0589-7671-a31f-8ca2a4acbe4b | SUCCESS | 0 | 4.671s | disposable | off | 0.03152099 |
| mutant-m08-73d38d359d | 01a15c4a-0598-7168-b996-665d45304330 | SUCCESS | 0 | 4.671s | disposable | off | 0.03147399 |
| mutant-m07-5ede625652 | 01a15c4a-057a-733d-b8ba-048e983a6b84 | SUCCESS | 0 | 4.672s | disposable | off | 0.03150482 |
| mutant-m09-a3ae309408 | 01a15c4a-2778-7374-a893-4818d97fa46d | SUCCESS | 0 | 4.353s | disposable | off | 0.03126599 |
| breaker-tests | 01a15c4a-5e29-76d8-a035-def5e0a73813 | SUCCESS | 0 | 2.529s | disposable | off | 0.01880149 |

Sandbox operations: 14, total guest duration 55.77s, retained images ['ed9f8250-64c6-4bdf-8a0b-267e73df742b'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
