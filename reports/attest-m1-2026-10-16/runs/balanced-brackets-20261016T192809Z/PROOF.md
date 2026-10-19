# Attest Proof Bundle: balanced-brackets

**Verdict: NEEDS HUMAN**  
Run `balanced-brackets-20261016T192809Z` · profile `m1-heldout-bound` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:28:09.805771+00:00, finished 2026-10-16T19:41:17.168677+00:00.

Reasons: adversarial suite binding failed: child process nonzero exit: test_all_short_ascii_bracket_sequences exit None; child process killed by signal: test_all_short_ascii_bracket_sequences sig 9; child process timed out: test_all_short_ascii_bracket_sequences; model-written adversarial tests failed: 1 of 9 (test_breaker.TestBreaker.test_all_short_ascii_bracket_sequences); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 1. Frozen task
Task `balanced-brackets`, spec digest `b4b1ed357cf1c1bd54b85a7c1e9d3157d00ec207969b2cf0547512c4dbe167c8`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `10215330-f144-459c-866c-9736a8e460ed`; test runner `unittest`; install: `none` (checkpoint networking off).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement brackets.is_balanced(s) in brackets/core.py to return a bool indicating whether all ASCII brackets (), [] and {} in a string are matched by type and correctly nested. Ignore all other characters, treat the empty string as balanced, and raise TypeError for non-string inputs. Preserve is_bracket, the package exports, and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept str instances, including str subclasses. Ignore every character other than (, ), [, ], { and }. Return True exactly when each closing bracket matches the | TypeError: s is not an instance of str; do not coerce it to a string. No particular exception message is required. |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True exactly when c is a str instance of length one containing one of the six ASCII bracket characters; return Fals |  |

Acceptance criteria:
1. 1. `from brackets import is_balanced, is_bracket` continues to succeed.
2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}', and '([{}])'.
3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}', and '())'.
5. 5. is_balanced returns False for unmatched openings remaining after valid pairs, such as '()(', and for premature closings, such as ')(' and ']['.
6. 6. is_balanced supports repeated nesting and adjacent groups, returning True for '((()))' and '{[]}[()]'.
7. 7. Strings containing no ASCII bracket characters, including letters, digits, whitespace, Unicode characters, and punctuation, return True.
8. 8. For every string s, removing all characters other than the six ASCII bracket characters does not change is_balanced(s). Quotes and backslashes do not suppress bracket recognition.
9. 9. For every string input, the returned value has type bool, including both balanced and unbalanced cases.
10. 10. str subclasses are accepted and evaluated using the same bracket-matching rules.
11. 11. Non-string inputs raise TypeError, including None, booleans, integers, floats, bytes, lists, tuples, dictionaries, and sets, even when empty or containing bracket characters.
12. 12. is_bracket retains its existing behavior: True for each character in '()[]{}' and False for 'a', '', '((', and 1. Its implementation and the existing test files remain unchanged.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `a15d5e79001553e6bddab4644283405be05705661281d22828c8bf2ecec54fb9`, 17 test methods, sealed at 2026-10-16T19:30:57.144780+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 17 methods: ERROR 15): 15 of 17 methods failing, 2 passing; operation `01a14632-295d-7141-a739-cc2d499e20cb`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_adjacent_groups_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_backslashes_do_not_suppress_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_closings_without_openings_return_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_empty_string_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_ignoring_other_characters_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_groups_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nonbracket_characters_inside_groups_are_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nonstring_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_quotes_do_not_suppress_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_result_is_builtin_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_str_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_strings_without_ascii_brackets_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unmatched_openings_return_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_wrong_types_and_crossed_nesting_return_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracketPreserved.test_other_inputs_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracketPreserved.test_six_ascii_brackets_are_recognized | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,14 @@
 
 
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
+    return not stack
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (11 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (bound to the sealed suite)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (17 of 17 methods, each in its own process). Operation `01a14636-3dde-759a-a910-c43864cd9131`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14636-5ae3-7519-bec9-eca5dcf5cc9e`, bound through the supervisor: 1 module(s), binding ok.

Held-out suite (evidence class `bound`; tests/test_heldout.py): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14636-6b74-740a-b1d7-ff1db15eb22f`. Gate: failures block VERIFIED.

## 6. Gates
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Result | Evidence | Detail |
| --- | --- | --- | --- |
| existing_suite | pass | bound | OK (2 of 2 methods, each in its own process) |
| sealed_binding | pass | bound | all checks pass |
| heldout_suite | pass | bound | OK (6 of 6 methods, each in its own process) |
| mutation | pass | bound | score 1.0 on 9 mutants |
| adversarial_tests | FAIL | bound | FAILED (1 of 9 methods: TIMEOUT 1) |
| drift_audit | pass | model | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-17781654c1 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced,  | 01a14636-896c-7567-bc77-dbf328413bc6 |
| m02-1d8db31cc8 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestIsBalanced.test_nonstring_inputs_raise_type_error | 01a14636-8960-76c2-9ae2-94199a9c8332 |
| m03-3ed9a3293a | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_groups_are_balanc | 01a14636-8967-733c-9dab-6f33c1ad73d8 |
| m04-be9c0a1c38 | brackets/core.py | 21 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_groups_are_balanc | 01a14636-8940-76e2-8c62-65da7a6255fe |
| m05-34fe0c49e2 | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_groups_are_balanc | 01a14636-891b-76c6-9063-86a02d85ac3d |
| m06-49e34e734e | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_groups_are_balanc | 01a14636-895f-70c8-9ad3-e8a4359b5f53 |
| m07-fdc74f1cd4 | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_groups_are_balanc | 01a14636-88c8-7174-a770-862ad8ffd4cb |
| m08-4867ef55fc | brackets/core.py | 23 | False -> True | killed | test_sealed.TestIsBalanced.test_closings_without_openings_return_false, test_sealed.TestIsBalanced.test_wrong_types_and_ | 01a14636-8932-773d-ba7a-e5264622891d |
| m09-d543026f6d | brackets/core.py | 24 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced,  | 01a14636-f408-71f5-8ad2-4269d315ad09 |

Model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `0dea373623eb7f357f1326dca7452b6717aa5eafc06070129650a55af24783a3`): FAILED (1 of 9 methods: TIMEOUT 1); binding FAILED; operation `01a14638-6f5b-7496-a277-1bce99386789`. Notes: Targets exhaustive short sequences, deep nesting, boundary mismatches, Unicode lookalikes, deceptive input types, and preserved is_bracket behavior.

| Failing adversarial test | Outcome |
| --- | --- |
| test_all_short_ascii_bracket_sequences | TIMEOUT |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(s, str)` rejects non-strings while accepting str subclasses, the stack and `PAIRS[c]` enforce matching and nesting, and `return not stack` produces a bool while handling empty strings and ignored characters correctly. Only is_balanced changed; observed outputs support the reported passing tests and corrected contract spot checks, with the initial failed check explicitly corrected for quoted brackets.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale |
| --- | --- | --- |
| test_all_short_ascii_bracket_sequences | test_defect | The reduction oracle is correct, but the reported failure is a timeout across 9,331 generated cases, with no incorrect result identified. Th |

- `adversarial` corrected re-run: candidate OK (9 of 9 methods, each in its own process); base n/a; cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10116 | 802 | 0 | - | 75.9s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10118 | 1673 | 7040 | - | 73.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10152 | 92 | 7168 | - | 17.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10339 | 196 | 7168 | - | 32.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10546 | 81 | 0 | - | 30.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10679 | 388 | 0 | - | 16.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11066 | 378 | 0 | - | 91.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 11433 | 113 | 7168 | - | 61.2s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10135 | 1858 | 0 | - | 89.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10853 | 127 | 0 | - | 66.0s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 11513 | 1156 | 0 | - | 79.4s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 116950/6864/28544; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1462f-c0ad-7668-9bb0-edfd96eca03e | SUCCESS | 0 | 0.729s | retained | off | 0.00275093 |
| red-1 | 01a14632-295d-7141-a739-cc2d499e20cb | SUCCESS | 0 | 3.983s | disposable | off | 0.03308288 |
| impl-tests-3 | 01a14633-80bc-75a8-9b6d-fd267cd560f3 | SUCCESS | 0 | 0.77s | disposable | off | 0.0028123 |
| impl-python-4 | 01a14633-cdda-75dd-ad61-eff9eb128215 | SUCCESS | 0 | 0.517s | disposable | off | 0.00112817 |
| impl-python-5 | 01a14635-4055-748f-8eb3-c16aea3b6efe | SUCCESS | 0 | 0.541s | disposable | off | 0.0011531999999999998 |
| verify | 01a14636-3dde-759a-a910-c43864cd9131 | SUCCESS | 0 | 3.981s | disposable | off | 0.03303047 |
| existing | 01a14636-5ae3-7519-bec9-eca5dcf5cc9e | SUCCESS | 0 | 1.424s | disposable | off | 0.008712410000000002 |
| heldout | 01a14636-6b74-740a-b1d7-ff1db15eb22f | SUCCESS | 0 | 2.024s | disposable | off | 0.01510842 |
| mutant-m02-1d8db31cc8 | 01a14636-8960-76c2-9ae2-94199a9c8332 | SUCCESS | 0 | 3.724s | disposable | off | 0.029850370000000005 |
| mutant-m01-17781654c1 | 01a14636-896c-7567-bc77-dbf328413bc6 | SUCCESS | 0 | 3.744s | disposable | off | 0.02982748 |
| mutant-m03-3ed9a3293a | 01a14636-8967-733c-9dab-6f33c1ad73d8 | SUCCESS | 0 | 3.703s | disposable | off | 0.02962674 |
| mutant-m05-34fe0c49e2 | 01a14636-891b-76c6-9063-86a02d85ac3d | SUCCESS | 0 | 3.723s | disposable | off | 0.02990353 |
| mutant-m06-49e34e734e | 01a14636-895f-70c8-9ad3-e8a4359b5f53 | SUCCESS | 0 | 3.691s | disposable | off | 0.029577890000000003 |
| mutant-m04-be9c0a1c38 | 01a14636-8940-76e2-8c62-65da7a6255fe | SUCCESS | 0 | 3.756s | disposable | off | 0.02969957 |
| mutant-m07-fdc74f1cd4 | 01a14636-88c8-7174-a770-862ad8ffd4cb | SUCCESS | 0 | 3.632s | disposable | off | 0.029632850000000002 |
| mutant-m08-4867ef55fc | 01a14636-8932-773d-ba7a-e5264622891d | SUCCESS | 0 | 3.756s | disposable | off | 0.02981495 |
| mutant-m09-d543026f6d | 01a14636-f408-71f5-8ad2-4269d315ad09 | SUCCESS | 0 | 3.639s | disposable | off | 0.029870450000000003 |
| breaker-tests | 01a14638-6f5b-7496-a277-1bce99386789 | SUCCESS | 0 | 62.436s | disposable | off | 0.02061238 |
| arbitrate-adversarial-candidate | 01a1463b-a7d1-7364-8b9c-ed39e240f165 | SUCCESS | 0 | 2.584s | disposable | off | 0.02000317 |

Sandbox operations: 19, total guest duration 112.357s, retained images ['10215330-f144-459c-866c-9736a8e460ed'].

## 11. Limitations of this bundle
- Profile 'm1-heldout-bound': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
