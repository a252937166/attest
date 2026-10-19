# Attest Proof Bundle: balanced-brackets

**Verdict: NEEDS HUMAN**  
Run `balanced-brackets-20261016T193830Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:38:30.200710+00:00, finished 2026-10-16T19:45:45.948528+00:00.

Reasons: adversarial suite binding failed: child process nonzero exit: test_str_subclass_uses_its_string_contents exit 1; model-written adversarial tests failed: 1 of 8 (test_breaker.TestBreaker.test_str_subclass_uses_its_string_contents); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): 1 failing test(s) indicate a real implementation bug; human review required

## 1. Frozen task
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `4689fcc9-71de-4e7f-baa8-a06974a31551`; test runner `unittest`; install: `none` (checkpoint networking off).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement brackets.core.is_balanced(s), available through from brackets import is_balanced, to return a bool indicating whether all ASCII parentheses, square brackets and curly braces in a string are matched in the correct order and nesting. Ignore every other character, treat the empty string as balanced, and raise TypeError for non-string inputs. Preserve is_bracket and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept a str, including str subclasses. Read bracket characters in order, ignoring all other characters. Each closing bracket must match the most recent unmatch | TypeError: s is not an instance of str; do not coerce other values to strings. |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True exactly when c is an instance of str of length one and is one of '(', ')', '[', ']', '{', or '}'. Return False |  |

Acceptance criteria:
1. 1. from brackets import is_balanced and from brackets import is_bracket continue to succeed.
2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}', and '([{}])'.
3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}', and '())'.
5. 5. Unmatched opening brackets of every kind produce False, including '[', '{', and '([]'.
6. 6. Unmatched closing brackets of every kind produce False, including ']', '}', and ')('. Equal numbers of opening and closing brackets alone do not imply balance.
7. 7. Matching requires the correct nesting order at every depth; '([]{})' is True and '{(})' is False.
8. 8. All characters outside the six ASCII bracket characters are ignored. Strings containing only letters, digits, whitespace, punctuation or non-ASCII characters return True, and removing non-bracket characters from any string does not change its result.
9. 9. Quotes and backslashes do not suppress bracket recognition: a string containing a double quote, an opening parenthesis and a double quote returns False, as does a string containing a backslash followed by an opening parenthesis.
10. 10. For every string input, type(is_balanced(s)) is bool, whether the result is True or False.
11. 11. Non-string inputs raise TypeError, including None, True, 0, 1.5, b'()', [], (), {}, and an arbitrary object. Empty non-string values also raise TypeError. No particular exception message is required.
12. 12. Instances of str subclasses are accepted and evaluated using the same bracket-matching rules.
13. 13. Successive calls are independent: calling with '(', then '()', then '' returns False, True, and True.
14. 14. is_bracket remains unchanged: it returns True for each character in '()[]{}' and False for 'a', '', '((', and 1. Existing tests remain unchanged and pass.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `007f38dcb5f1496f0d3f1e499e2fbfede906a623493fb710188bbadaeb1a07d0`, 20 test methods, sealed at 2026-10-16T19:40:41.084311+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 20 methods: ERROR 18): 18 of 20 methods failing, 2 passing; operation `01a1463b-1333-76b7-9b8c-70fd34d55182`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_adjacent_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_backslashes_do_not_suppress_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_closing_before_opening_is_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_empty_string_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_every_string_result_has_bool_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_bracket_types_are_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nonbracket_characters_inside_pairs_are_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nonstring_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_quotes_do_not_suppress_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_removing_nonbracket_characters_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_str_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_strings_without_ascii_brackets_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_successive_calls_are_independent | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unmatched_closings_are_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unmatched_openings_are_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_wrong_nesting_order_is_unbalanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracket.test_other_inputs_are_not_brackets | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracket.test_six_ascii_bracket_characters_are_recognized | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,15 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    """Return whether the ASCII brackets in s are correctly nested."""
+    if not isinstance(s, str):
+        raise TypeError("s must be a string")
+
+    stack = []
+    for char in s:
+        if char in OPEN:
+            stack.append(char)
+        elif char in CLOSE:
+            if not stack or stack.pop() != PAIRS[char]:
+                return False
+    return not stack
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (bound to the sealed suite)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (20 of 20 methods, each in its own process). Operation `01a1463d-8811-7431-8e9c-5867a9418e5e`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a1463d-a308-71f5-b92c-faf822e4f616`, bound through the supervisor: 1 module(s), binding ok.

Held-out suite: none configured.

## 6. Gates
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Result | Evidence | Detail |
| --- | --- | --- | --- |
| existing_suite | pass | bound | OK (2 of 2 methods, each in its own process) |
| sealed_binding | pass | bound | all checks pass |
| mutation | pass | bound | score 1.0 on 9 mutants |
| adversarial_tests | FAIL | bound | FAILED (1 of 8 methods: FAIL 1) |
| drift_audit | pass | model | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ba8452d645 | brackets/core.py | 15 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced,  | 01a1463d-b63e-7595-b8fb-91cb65ec3fd7 |
| m02-57f6af0214 | brackets/core.py | 16 | raise -> pass | killed | test_sealed.TestIsBalanced.test_nonstring_inputs_raise_type_error | 01a1463d-b682-7080-950d-30d47ed57899 |
| m03-1b3e7f0d7f | brackets/core.py | 20 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a1463d-b62b-7136-b3d3-e9b65e3fb93b |
| m04-e3b6a1be86 | brackets/core.py | 22 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a1463d-b65e-77a2-8ecc-baec10d150c7 |
| m05-3ae1c5083c | brackets/core.py | 23 | remove `not` | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a1463d-b635-7325-a908-577bf0a4fa0f |
| m06-9753e0bb65 | brackets/core.py | 23 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a1463d-b652-762c-8789-f1a37e120565 |
| m07-bf026b8432 | brackets/core.py | 23 | Or -> And | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a1463d-b67e-75b7-97dd-8bb1830669e2 |
| m08-647ebba621 | brackets/core.py | 24 | False -> True | killed | test_sealed.TestIsBalanced.test_unmatched_closings_are_unbalanced, test_sealed.TestIsBalanced.test_closing_before_openin | 01a1463d-b6c2-709d-8c38-defe30fb04ff |
| m09-380b5ed00e | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced,  | 01a1463d-d594-73ae-a24f-8acc331cf25c |

Model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `28beb2f5d67738c8700aed195002a586b842305a6c8eac63bdaf13ac82d597f1`): FAILED (1 of 8 methods: FAIL 1); binding FAILED; operation `01a1463e-96af-722f-9364-3971a6d65119`. Notes: Targets deep inputs, late errors, Unicode lookalikes, coercion, and str subclasses whose iteration differs from their string contents.

| Failing adversarial test | Outcome |
| --- | --- |
| test_str_subclass_uses_its_string_contents | FAIL |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(s, str)` validates inputs while accepting str subclasses, the local stack and `stack.pop() != PAIRS[char]` enforce matching and nesting, and `return not stack` returns a bool while handling empty strings and unmatched openings; other characters are ignored. Only is_balanced changes, preserving constants, exports, is_bracket and tests, and the observed test output supports the implementer's claim that existing tests pass (2/2).

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
1 failing test(s) indicate a real implementation bug; human review required (mode: advisory). Classifications: {'implementation_bug': 1, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale |
| --- | --- | --- |
| test_str_subclass_uses_its_string_contents | implementation_bug | The subclass instances contain '(' and '()', respectively, so their required results are False and True. The candidate instead processes the |

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10118 | 919 | 0 | - | 48.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10228 | 1389 | 0 | - | 66.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10270 | 140 | 7168 | - | 49.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10451 | 227 | 7168 | - | 56.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10678 | 93 | 7168 | - | 28.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10818 | 147 | 0 | - | 16.3s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10300 | 1583 | 0 | - | 42.0s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10861 | 141 | 0 | - | 20.6s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 11536 | 350 | 0 | - | 54.2s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 95260/4989/21504; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14639-36c1-7110-847d-7810f5a3310e | SUCCESS | 0 | 0.754s | retained | off | 0.0027724299999999998 |
| red-1 | 01a1463b-1333-76b7-9b8c-70fd34d55182 | SUCCESS | 0 | 4.454s | disposable | off | 0.0378165 |
| impl-tests-3 | 01a1463d-39e4-7338-8528-466f95d64246 | SUCCESS | 0 | 0.718s | disposable | off | 0.00275381 |
| verify | 01a1463d-8811-7431-8e9c-5867a9418e5e | SUCCESS | 0 | 4.491s | disposable | off | 0.03802247 |
| existing | 01a1463d-a308-71f5-b92c-faf822e4f616 | SUCCESS | 0 | 1.372s | disposable | off | 0.008657230000000002 |
| mutant-m01-ba8452d645 | 01a1463d-b63e-7595-b8fb-91cb65ec3fd7 | SUCCESS | 0 | 4.264s | disposable | off | 0.034842490000000004 |
| mutant-m02-57f6af0214 | 01a1463d-b682-7080-950d-30d47ed57899 | SUCCESS | 0 | 4.186s | disposable | off | 0.03421611 |
| mutant-m03-1b3e7f0d7f | 01a1463d-b62b-7136-b3d3-e9b65e3fb93b | SUCCESS | 0 | 4.128s | disposable | off | 0.0344039 |
| mutant-m04-e3b6a1be86 | 01a1463d-b65e-77a2-8ecc-baec10d150c7 | SUCCESS | 0 | 4.276s | disposable | off | 0.0348837 |
| mutant-m05-3ae1c5083c | 01a1463d-b635-7325-a908-577bf0a4fa0f | SUCCESS | 0 | 4.224s | disposable | off | 0.03450004 |
| mutant-m06-9753e0bb65 | 01a1463d-b652-762c-8789-f1a37e120565 | SUCCESS | 0 | 4.321s | disposable | off | 0.035148700000000005 |
| mutant-m07-bf026b8432 | 01a1463d-b67e-75b7-97dd-8bb1830669e2 | SUCCESS | 0 | 4.255s | disposable | off | 0.034517110000000004 |
| mutant-m08-647ebba621 | 01a1463d-b6c2-709d-8c38-defe30fb04ff | SUCCESS | 0 | 4.277s | disposable | off | 0.03507076 |
| mutant-m09-380b5ed00e | 01a1463d-d594-73ae-a24f-8acc331cf25c | SUCCESS | 0 | 4.095s | disposable | off | 0.03448539 |
| breaker-tests | 01a1463e-96af-722f-9364-3971a6d65119 | SUCCESS | 0 | 2.393s | disposable | off | 0.01836761 |

Sandbox operations: 15, total guest duration 52.208s, retained images ['4689fcc9-71de-4e7f-baa8-a06974a31551'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
