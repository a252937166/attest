# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-attest-a1-20261019T051423353770Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:14:23.354219+00:00, finished 2026-10-19T05:22:46.771553+00:00.

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
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
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
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e145001c-b939-4647-ac58-40b24afe8f1d`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the existing is_balanced(s) stub in brackets/core.py, retaining its availability through from brackets import is_balanced. For string inputs, determine whether all ASCII parentheses, square brackets, and braces match by kind and are properly nested, ignoring every other character. Return an actual bool, treat empty strings and strings without brackets as balanced, and raise TypeError for non-string inputs. Preserve is_bracket and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept str instances, including subclasses. Process the six characters ()[]{} in their string order, ignoring all other characters. Each closing bracket must ma | TypeError: s is not an instance of str, including bytes, None, numbers, lists, and other iterables. Do not coerce inputs to strings. Exception message is unspec |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True exactly when c is a str instance of length one containing one of ()[]{}; return False otherwise, including for |  |

Acceptance criteria:
AC1. 1. from brackets import is_balanced and from brackets import is_bracket both succeed.
AC2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}', and '([{}])'.
AC3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
AC4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}', and '())'.
AC5. 5. Unmatched openings of every kind are rejected: '[', '{', '(()', and '([]' return False.
AC6. 6. Unmatched or premature closings of every kind are rejected: ']', '}', ')(', '][', and '}{' return False.
AC7. 7. Arbitrary valid nesting and concatenation are supported; '((()))', '[[]]', '{{}}', and '([]){}[()]' return True.
AC8. 8. Every character outside ()[]{} is ignored, including whitespace, newlines, Unicode characters, quotes, and backslashes. Removing all such characters from any input does not change its result; there is no quoting or escaping syntax.
AC9. 9. Strings without any of the six bracket characters, including 'abc', ' \t\n', and '你好（）', return True.
AC10. 10. For every string input, type(is_balanced(s)) is bool, including inputs producing False.
AC11. 11. is_balanced raises TypeError for None, True, 0, 1.5, b'()', [], (), {}, and iter(['(', ')']), rather than returning a result or coercing the input.
AC12. 12. Instances of a str subclass with ordinary inherited string behavior are accepted and evaluated by the same matching rules.
AC13. 13. Repeated calls are independent: evaluating '(', then '()', then ')', then '' returns False, True, False, True.
AC14. 14. is_bracket remains unchanged: each character in '()[]{}' returns True; 'a', '', '((', and 1 return False; all existing tests continue to pass.
AC15. 15. Existing test files remain unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by implementing only is_balanced in brackets/core.py with a string type check and a local stack. Existing exports, is_bracket, bracket definitions, and tests can remain unchanged. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d6a86a5084bf7a386e612b87ea25c67349d2e3b6ffcfadaff738b6a71013d147`, 18 test methods, sealed at 2026-10-19T05:17:41.625565+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 18 methods: ERROR 15): 15 of 18 methods failing, 3 passing; operation `01a15298-0e34-742a-97d2-fbcb971091ea`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestBalanced.test_deep_nesting_and_concatenation_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_each_simple_pair_and_concatenation_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_empty_string_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_mismatched_and_extra_brackets_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_mixed_nesting_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_non_string_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_ordinary_text_between_brackets_is_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_premature_closings_of_each_kind_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_public_exports_are_callable | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_quotes_and_backslashes_do_not_change_bracket_meaning | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_removing_ignored_characters_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_repeated_calls_are_independent | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_result_type_is_bool_for_true_and_false_cases | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_str_subclass_uses_the_same_matching_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_strings_without_ascii_brackets_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_unmatched_openings_of_each_kind_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBracketHelper.test_each_ascii_bracket_is_recognized | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBracketHelper.test_original_non_bracket_examples_are_rejected | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

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
+    for c in s:
+        if c in OPEN:
+            stack.append(c)
+        elif c in CLOSE:
+            if not stack or stack.pop() != PAIRS[c]:
+                return False
+
+    return not stack
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (18 of 18 methods, each in its own process). Operation `01a1529a-c097-7490-9c91-3cebed7b510f`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a1529a-d951-7339-adc9-9adea5510ba7`, bound through the supervisor: 1 module(s), binding ok.

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

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-17781654c1 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestBalanced.test_empty_string_is_balanced, test_sealed.TestBalanced.test_each_simple_pair_and_concatenation | 01a1529a-e76d-75a8-8bf2-1a157836eee4 |
| m02-1d8db31cc8 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestBalanced.test_non_string_inputs_raise_type_error | 01a1529a-e7c3-71f7-ad8b-0fe5ba08003f |
| m03-3ed9a3293a | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestBalanced.test_each_simple_pair_and_concatenation_are_balanced, test_sealed.TestBalanced.test_mixed_nesti | 01a1529a-e768-7479-a3d9-11dbac0d81df |
| m04-be9c0a1c38 | brackets/core.py | 21 | In -> NotIn | killed | test_sealed.TestBalanced.test_each_simple_pair_and_concatenation_are_balanced, test_sealed.TestBalanced.test_mixed_nesti | 01a1529a-e7ca-723a-9be9-b58a14ee6993 |
| m05-34fe0c49e2 | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestBalanced.test_each_simple_pair_and_concatenation_are_balanced, test_sealed.TestBalanced.test_mixed_nesti | 01a1529a-e754-7157-98a4-24127dcfc244 |
| m06-49e34e734e | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestBalanced.test_each_simple_pair_and_concatenation_are_balanced, test_sealed.TestBalanced.test_mixed_nesti | 01a1529a-e7af-77b0-8459-37a6516a62e9 |
| m07-fdc74f1cd4 | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestBalanced.test_each_simple_pair_and_concatenation_are_balanced, test_sealed.TestBalanced.test_mixed_nesti | 01a1529a-e754-7646-a2c2-ff7fd373c944 |
| m08-4867ef55fc | brackets/core.py | 23 | False -> True | killed | test_sealed.TestBalanced.test_mismatched_and_extra_brackets_are_rejected, test_sealed.TestBalanced.test_premature_closin | 01a1529a-e756-7769-ad93-ee414f8115a1 |
| m09-d543026f6d | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestBalanced.test_empty_string_is_balanced, test_sealed.TestBalanced.test_each_simple_pair_and_concatenation | 01a1529b-045e-770a-a48c-e161703742ae |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `3a06b8d9895239906cad1903b0ab15ba68ce4a1bc1360000d7e6e004b6c60846`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a1529b-f4a4-77af-8db2-2120a7af2177`. Notes: Targets exhaustive short bracket sequences, crossed pairs, deep nesting, ignored characters, additional invalid input types, and ASCII is_bracket behavior.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `if not isinstance(s, str)` rejects non-strings while accepting str subclasses, and `stack.pop() != PAIRS[c]` enforces matching and nesting; other characters are ignored, and `return not stack` returns a bool and rejects leftover openings. Only is_balanced changes, preserving is_bracket, constants, exports, and tests; observed outputs support the reported successful existing tests and contract checks.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10118 | 889 | 0 | - | 75.5s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11034 | 88 | 0 | - | 27.9s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10408 | 2753 | 7168 | - | 78.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10383 | 97 | 7168 | - | 24.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10576 | 210 | 7168 | - | 35.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10789 | 78 | 7168 | - | 26.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10925 | 484 | 7168 | - | 19.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11407 | 103 | 7168 | - | 54.8s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10487 | 1939 | 0 | - | 55.2s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10893 | 132 | 0 | - | 52.0s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 107020/6773/43008; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15295-2fb0-7087-a561-8efbc61f9287 | SUCCESS | 0 | 0.811s | retained | off | 0.00285556 |
| red-1 | 01a15298-0e34-742a-97d2-fbcb971091ea | SUCCESS | 0 | 4.215s | disposable | off | 0.03482402 |
| impl-tests-3 | 01a15299-81fa-777f-bce6-2d772a49deba | SUCCESS | 0 | 0.777s | disposable | off | 0.00294626 |
| impl-python-4 | 01a15299-dc5f-729d-9446-9d5b19e1a6fa | SUCCESS | 0 | 0.551s | disposable | off | 0.00124047 |
| verify | 01a1529a-c097-7490-9c91-3cebed7b510f | SUCCESS | 0 | 4.21s | disposable | off | 0.03482048 |
| existing | 01a1529a-d951-7339-adc9-9adea5510ba7 | SUCCESS | 0 | 1.424s | disposable | off | 0.00876159 |
| mutant-m02-1d8db31cc8 | 01a1529a-e7c3-71f7-ad8b-0fe5ba08003f | SUCCESS | 0 | 3.948s | disposable | off | 0.03176681 |
| mutant-m03-3ed9a3293a | 01a1529a-e768-7479-a3d9-11dbac0d81df | SUCCESS | 0 | 4.006s | disposable | off | 0.032189129999999996 |
| mutant-m01-17781654c1 | 01a1529a-e76d-75a8-8bf2-1a157836eee4 | SUCCESS | 0 | 3.948s | disposable | off | 0.0319788 |
| mutant-m04-be9c0a1c38 | 01a1529a-e7ca-723a-9be9-b58a14ee6993 | SUCCESS | 0 | 3.874s | disposable | off | 0.03135107 |
| mutant-m07-fdc74f1cd4 | 01a1529a-e754-7646-a2c2-ff7fd373c944 | SUCCESS | 0 | 3.887s | disposable | off | 0.03178215 |
| mutant-m05-34fe0c49e2 | 01a1529a-e754-7157-98a4-24127dcfc244 | SUCCESS | 0 | 3.927s | disposable | off | 0.03162231 |
| mutant-m06-49e34e734e | 01a1529a-e7af-77b0-8459-37a6516a62e9 | SUCCESS | 0 | 3.834s | disposable | off | 0.03110769 |
| mutant-m08-4867ef55fc | 01a1529a-e756-7769-ad93-ee414f8115a1 | SUCCESS | 0 | 4.054s | disposable | off | 0.03264461 |
| mutant-m09-d543026f6d | 01a1529b-045e-770a-a48c-e161703742ae | SUCCESS | 0 | 3.841s | disposable | off | 0.0317568 |
| breaker-tests | 01a1529b-f4a4-77af-8db2-2120a7af2177 | SUCCESS | 0 | 2.639s | disposable | off | 0.02026226 |

Sandbox operations: 16, total guest duration 49.946s, retained images ['e145001c-b939-4647-ac58-40b24afe8f1d'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception raised in the code under test is never overridden (only a test-internal crash or a timeout may be corrected). The classification itself remains a model judgement.
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
