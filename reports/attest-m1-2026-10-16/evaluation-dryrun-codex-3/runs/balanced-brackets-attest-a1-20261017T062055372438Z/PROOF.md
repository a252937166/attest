# Attest Proof Bundle: balanced-brackets

**Verdict: NEEDS HUMAN**  
Run `balanced-brackets-attest-a1-20261017T062055372438Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T06:20:55.373009+00:00, finished 2026-10-17T06:31:11.472791+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter; the corrected tests pass on the candidate and still fail on the unmodified base. Arbitration is advisory, so the hold stands until a human confirms.

Key evidence (E6): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests



What to do: Check the arbiter's corrections in E6 (original and corrected tests are both kept). If you agree, accept the patch on that basis or re-run with arbitration in apply mode.

Reasons: adversarial suite binding failed: child process nonzero exit: test_exhaustive_short_bracket_streams exit None; child process killed by signal: test_exhaustive_short_bracket_streams sig 9; child process timed out: test_exhaustive_short_bracket_streams; model-written adversarial tests failed: 1 of 9 (test_breaker.BreakerTests.test_exhaustive_short_bracket_streams); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 17 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 6 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 17 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 8 of 9 pass; 1 failing: test_exhaustive_short_bracket_streams; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `fbba44e5-d011-4f4b-bb5b-4f0ddc1a0067`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.2.0 revision `17360d66f6044ce7` (33 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/5` sha256 `8511520ba75a7690`, per-test child `fb466d37f748f9ef`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement brackets.is_balanced(s) in brackets/core.py to validate matching and nesting of the ASCII bracket pairs (), [], and {} while ignoring all other characters. Return a bool for every string, including True for empty strings and strings without brackets, and raise TypeError for non-string inputs. Preserve is_bracket, package exports, and existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept str instances, including str subclasses. Scan brackets in their original order: each closing bracket must match the most recent unmatched opening bracket | TypeError: s is not an instance of str; do not coerce inputs to strings or accept bytes or other iterables as strings.; TypeError: the call omits required argum |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation unchanged: return True exactly when c is a str instance of length one containing one of the six ASCII bracket characters; o | TypeError: the call omits required argument c or supplies unsupported arguments, as dictated by the signature. |

Acceptance criteria:
1. 1. from brackets import is_balanced and from brackets import is_bracket both continue to work.
2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}', and '([{}])'.
3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}', and '())'.
5. 5. Every closing bracket must match the most recent unmatched opening bracket: '[)', '{]', and '[(])' return False, while '([]{})' returns True.
6. 6. Unmatched brackets at either boundary or within the input cause False: '[', '{', ']', '}', '(()', '[](', and ')(' return False.
7. 7. Removing all characters other than the six ASCII bracket characters does not change a string's result. Strings containing only ordinary text, whitespace, Unicode letters, or non-ASCII bracket lookalikes return True.
8. 8. Quotes and backslashes do not suppress bracket processing: a string consisting of a double quote, an opening parenthesis, and a double quote returns False; a backslash followed by an opening parenthesis also returns False.
9. 9. For every accepted string input, the result has type bool, including both balanced and unbalanced cases.
10. 10. Non-string inputs raise TypeError, including None, True, integers, floats, bytes, lists, tuples, dictionaries, and sets, even when empty.
11. 11. Instances of str subclasses are accepted and evaluated under the same bracket-matching rules.
12. 12. Repeated calls are independent: calling with an unbalanced string does not affect the result of a subsequent call with a balanced string.
13. 13. is_bracket remains unchanged and returns True for each character in '()[]{}', and False for 'a', '', '((', and 1. Existing tests remain unchanged and pass.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `76bdafe7ae0a899c81c98584ff74f05d70f1957374e8ace48c9be612fdef3691`, 23 test methods, sealed at 2026-10-17T06:22:57.556591+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (17 of 23 methods: ERROR 17): 17 of 23 methods failing, 6 passing; operation `01a14887-0eef-71ce-a04c-41d10fcab015`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestBalancedBrackets.test_adjacent_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_backslashes_do_not_escape_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_calls_do_not_share_bracket_state | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_closing_brackets_without_openers_are_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_crossed_nesting_is_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_empty_string_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_is_balanced_rejects_unsupported_arguments | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_is_balanced_requires_its_argument | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_mismatched_closing_brackets_are_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_nested_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_non_bracket_characters_inside_pairs_are_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_non_string_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_opening_brackets_left_unmatched_are_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_quotes_do_not_hide_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_removing_non_bracket_characters_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_results_have_exact_bool_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_simple_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_string_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalancedBrackets.test_text_without_ascii_brackets_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracketExport.test_ascii_bracket_characters_are_recognized | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracketExport.test_is_bracket_rejects_unsupported_arguments | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracketExport.test_is_bracket_requires_its_argument | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracketExport.test_other_values_are_not_brackets | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,15 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("s must be a str instance")
+
+    stack = []
+    for char in s:
+        if char in OPEN:
+            stack.append(char)
+        elif char in CLOSE:
+            if not stack or stack.pop() != PAIRS[char]:
+                return False
+
+    return not stack
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a14889-5d76-72b0-9007-2c49720159d5`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14889-8273-70dc-a25d-0c5ed15bca38`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 9 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 9 methods: TIMEOUT 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-12a76d2694 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestBalancedBrackets.test_empty_string_is_balanced, test_sealed.TestBalancedBrackets.test_simple_pairs_are_b | 01a14889-93a9-75db-969e-917f0976a657 |
| m02-e621c52120 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestBalancedBrackets.test_non_string_inputs_raise_type_error | 01a14889-93a4-7525-b9d8-3304af45e63e |
| m03-7d2b12e684 | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestBalancedBrackets.test_simple_pairs_are_balanced, test_sealed.TestBalancedBrackets.test_adjacent_pairs_ar | 01a14889-93f7-7102-a6ae-9d0b5c97bc35 |
| m04-5948415dfb | brackets/core.py | 21 | In -> NotIn | killed | test_sealed.TestBalancedBrackets.test_simple_pairs_are_balanced, test_sealed.TestBalancedBrackets.test_adjacent_pairs_ar | 01a14889-9370-7605-93f4-8ba7ff81ed4c |
| m05-2e4bdfd5ef | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestBalancedBrackets.test_simple_pairs_are_balanced, test_sealed.TestBalancedBrackets.test_adjacent_pairs_ar | 01a14889-93ad-74a7-b81f-8a7d4878e6e2 |
| m06-e77585491e | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestBalancedBrackets.test_simple_pairs_are_balanced, test_sealed.TestBalancedBrackets.test_adjacent_pairs_ar | 01a14889-93df-742e-a050-f71493acacea |
| m07-2716a419ce | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestBalancedBrackets.test_simple_pairs_are_balanced, test_sealed.TestBalancedBrackets.test_adjacent_pairs_ar | 01a14889-93dc-77d2-a435-06ec889a7ca6 |
| m08-273a5a1e83 | brackets/core.py | 23 | False -> True | killed | test_sealed.TestBalancedBrackets.test_closing_brackets_without_openers_are_unbalanced, test_sealed.TestBalancedBrackets. | 01a14889-93b7-774a-ae1f-568e4be6f9b3 |
| m09-84907a78f7 | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestBalancedBrackets.test_empty_string_is_balanced, test_sealed.TestBalancedBrackets.test_simple_pairs_are_b | 01a14889-af65-7103-ba1a-e033448112d9 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `281d039ed5adfbad2944c45f37c714b362db1e77746786fc5fbfd60e683b2883`): FAILED (1 of 9 methods: TIMEOUT 1); binding FAILED; operation `01a1488a-83cc-7040-b4aa-a99c520b44f3`. Notes: Targets exhaustive short sequences, deep and late errors, ignored Unicode and controls, string subclass coercion, and string-like non-string inputs.

| Failing adversarial test | Outcome |
| --- | --- |
| test_exhaustive_short_bracket_streams | TIMEOUT |

### Counterexamples
- E3 `test_exhaustive_short_bracket_streams`: TIMEOUT; arbiter: Defective test, by the arbiter; contract basis: The contract requires correct matching, nesting, and bool results for strings; it does not require completing exhaustive enumeration within a test runner's deadline.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `if not isinstance(s, str)` rejects non-strings, the stack enforces ordered matching through `stack.pop() != PAIRS[char]`, and `return not stack` returns a bool while non-bracket characters are ignored. Only is_balanced changes, preserving constants, exports, is_bracket, and tests; observed outputs support the reported passing existing tests and contract checks, although the additional check code is not shown.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_exhaustive_short_bracket_streams | test_defect | The reduction oracle correctly checks bracket matching, but the reported failure is a timeout, not a wrong result. The test performs 9,331 s | The contract requires correct matching, nesting, and bool results for strings; it does not require completing exhaustive enumeration within  |

- `adversarial` corrected re-run: candidate OK (9 of 9 methods, each in its own process); base n/a; cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10118 | 897 | 0 | - | 58.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10221 | 1474 | 0 | - | 46.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10247 | 128 | 7168 | - | 32.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10442 | 202 | 7168 | - | 16.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10659 | 85 | 7168 | - | 33.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10798 | 466 | 7168 | - | 23.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11227 | 111 | 7168 | - | 26.9s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10320 | 2080 | 0 | - | 44.2s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10910 | 136 | 0 | - | 92.8s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 11828 | 1292 | 0 | - | 107.5s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 106770/6871/35840; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14885-5da7-76de-8ce5-332ff11c894f | SUCCESS | 0 | 0.762s | retained | off | 0.0027727499999999996 |
| red-1 | 01a14887-0eef-71ce-a04c-41d10fcab015 | SUCCESS | 0 | 5.157s | disposable | off | 0.04294904 |
| impl-tests-3 | 01a14888-7832-7680-8065-c34367b15ea7 | SUCCESS | 0 | 0.768s | disposable | off | 0.00279513 |
| impl-python-4 | 01a14888-e08c-75ac-b14c-db9ca4cfb14d | SUCCESS | 0 | 0.546s | disposable | off | 0.00115074 |
| verify | 01a14889-5d76-72b0-9007-2c49720159d5 | SUCCESS | 0 | 4.957s | disposable | off | 0.04280697 |
| existing | 01a14889-8273-70dc-a25d-0c5ed15bca38 | SUCCESS | 0 | 1.408s | disposable | off | 0.008716080000000001 |
| mutant-m02-e621c52120 | 01a14889-93a4-7525-b9d8-3304af45e63e | SUCCESS | 0 | 5.001s | disposable | off | 0.03954058 |
| mutant-m03-7d2b12e684 | 01a14889-93f7-7102-a6ae-9d0b5c97bc35 | SUCCESS | 0 | 5.0s | disposable | off | 0.0392826 |
| mutant-m04-5948415dfb | 01a14889-9370-7605-93f4-8ba7ff81ed4c | SUCCESS | 0 | 4.733s | disposable | off | 0.03964109 |
| mutant-m05-2e4bdfd5ef | 01a14889-93ad-74a7-b81f-8a7d4878e6e2 | SUCCESS | 0 | 4.979s | disposable | off | 0.03940992 |
| mutant-m01-12a76d2694 | 01a14889-93a9-75db-969e-917f0976a657 | SUCCESS | 0 | 5.001s | disposable | off | 0.03957109 |
| mutant-m06-e77585491e | 01a14889-93df-742e-a050-f71493acacea | SUCCESS | 0 | 5.002s | disposable | off | 0.03941038 |
| mutant-m07-2716a419ce | 01a14889-93dc-77d2-a435-06ec889a7ca6 | SUCCESS | 0 | 4.98s | disposable | off | 0.03934989 |
| mutant-m08-273a5a1e83 | 01a14889-93b7-774a-ae1f-568e4be6f9b3 | SUCCESS | 0 | 4.981s | disposable | off | 0.03924116 |
| mutant-m09-84907a78f7 | 01a14889-af65-7103-ba1a-e033448112d9 | SUCCESS | 0 | 5.114s | disposable | off | 0.03943322 |
| breaker-tests | 01a1488a-83cc-7040-b4aa-a99c520b44f3 | SUCCESS | 0 | 63.168s | disposable | off | 0.020578500000000003 |
| arbitrate-adversarial-candidate | 01a1488e-a438-7373-a8e9-3f7faddc5ce6 | SUCCESS | 0 | 2.692s | disposable | off | 0.02023938 |

Sandbox operations: 17, total guest duration 124.249s, retained images ['fbba44e5-d011-4f4b-bb5b-4f0ddc1a0067'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
