# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-20261015T180604Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:06:04.749965+00:00, finished 2026-10-15T18:08:19.913346+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `balanced-brackets`, spec digest `b4b1ed357cf1c1bd54b85a7c1e9d3157d00ec207969b2cf0547512c4dbe167c8`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `50501052-ef44-46a1-9ab8-8c7c97935960`; test runner `unittest`; install: `none` (checkpoint networking off).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the `is_balanced(s)` function in `brackets/core.py` to return True if the string `s` contains correctly matched and nested brackets of types `()`, `[]`, `{}`, ignoring all other characters. Return False otherwise. The empty string is balanced. The function must return a bool and raise TypeError if `s` is not a string. Do not modify the existing `is_bracket` function or the test files.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_balanced | is_balanced(s: str) -> bool | Returns True if all brackets in `s` are properly matched and nested, ignoring non-bracket characters. Returns False otherwise. Empty string returns True. | TypeError if `s` is not a string |

Acceptance criteria:
1. Empty string returns True.
2. Single pairs '()', '[]', '{}' return True.
3. Multiple adjacent pairs '()[]{}' return True.
4. Nested mixed brackets '([{}])' return True.
5. Nested mixed brackets with other characters '(a[b]{c})' and 'f(x[0], y[1])' return True.
6. Unbalanced opening bracket '(' returns False.
7. Unbalanced closing bracket ')' returns False.
8. Mismatched brackets '([)]' returns False.
9. Mismatched brackets '(]' returns False.
10. Mismatched brackets '{[}' returns False.
11. Extra closing bracket '())' returns False.
12. Non-bracket characters are ignored (they do not affect bracket matching).
13. Function returns a bool (True/False) for valid string inputs.
14. Function raises TypeError when input is not a string (e.g., int, list, None).

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d15f660b9709f098ed0a810f89a3528ca512ea3541f0616c1b561cee35952041`, 19 test methods, sealed at 2026-10-15T18:06:33.568366+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (19 of 19 methods: ERROR 19): 19 of 19 methods failing, 0 passing; operation `01a140be-8c80-7092-ba4c-9ef7b9c47590`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_empty_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_extra_closing | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_curly_square | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_round_curly | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_mismatched_round_square | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_multiple_adjacent_pairs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_mixed_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_with_other_chars1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_with_other_chars2 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_non_bracket_only | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_returns_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_single_pair_curly | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_single_pair_parentheses | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_single_pair_square | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_none | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unbalanced_closing | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_unbalanced_opening | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/brackets/core.py
+++ b/brackets/core.py
@@ -11,4 +11,14 @@
 
 
 def is_balanced(s):
-    raise NotImplementedError("is_balanced is not implemented yet")
+    if not isinstance(s, str):
+        raise TypeError("Input must be a string")
+    stack = []
+    for ch in s:
+        if ch in OPEN:
+            stack.append(ch)
+        elif ch in CLOSE:
+            if not stack or stack[-1] != PAIRS[ch]:
+                return False
+            stack.pop()
+    return not stack
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (2 passed of 2). Sealed suite: OK (19 of 19 methods, each in its own process). Operation `01a140bf-47af-756f-9d94-a6360d2b0335`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| static_ids_match_red | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |

Held-out suite (tests/test_heldout.py): OK (8 passed of 8); operation `01a140bf-6476-7373-9cf5-0ce451670dbd`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | OK |
| mutation | pass | score 1.0 on 10 mutants |
| adversarial_tests | pass | OK (14 of 14 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 10 generated, 10 evaluated: 10 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ae970cbcac | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string, test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestI | 01a140bf-7243-72bd-b283-0ec7fac5eccb |
| m02-f95940ff2b | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestIsBalanced.test_type_error_list | 01a140bf-7289-7159-b1b0-2e0e0c96f0f0 |
| m03-13e48417f0 | brackets/core.py | 18 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestIsBalanced.test_single_pair_square, test_sealed | 01a140bf-7216-7391-8350-4b9a76ea0329 |
| m04-25a5fc5b73 | brackets/core.py | 20 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestIsBalanced.test_single_pair_square, test_sealed | 01a140bf-721b-770b-bed0-46900e0397e7 |
| m05-285d71b8c4 | brackets/core.py | 21 | remove `not` | killed | test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestIsBalanced.test_single_pair_square, test_sealed | 01a140bf-7245-741a-903f-b5e0a22a4ec5 |
| m06-9bfdfde8f9 | brackets/core.py | 21 | 1 -> 2 | killed | test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestIsBalanced.test_single_pair_square, test_sealed | 01a140bf-726e-723c-a8de-811a2887fa13 |
| m07-112d16b760 | brackets/core.py | 21 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestIsBalanced.test_single_pair_square, test_sealed | 01a140bf-72c0-77d0-8e5e-ffe2b13b1bd0 |
| m08-9068babf89 | brackets/core.py | 21 | Or -> And | killed | test_sealed.TestIsBalanced.test_unbalanced_closing, test_sealed.TestIsBalanced.test_mismatched_round_square, test_sealed | 01a140bf-72e1-7681-aa89-ac6ceaeef567 |
| m09-1b4087966f | brackets/core.py | 22 | False -> True | killed | test_sealed.TestIsBalanced.test_unbalanced_closing, test_sealed.TestIsBalanced.test_mismatched_round_square, test_sealed | 01a140bf-8b05-75e4-b509-431c2c78f01a |
| m10-3493ff69c1 | brackets/core.py | 24 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string, test_sealed.TestIsBalanced.test_single_pair_parentheses, test_sealed.TestI | 01a140bf-a07e-7327-aa48-df1190b98c60 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `4a28b10a23314d6d0f16466309cc0135364005c351c48a103a3b7afd44d42f5f`): OK (14 of 14 methods, each in its own process); binding ok; operation `01a140c0-18c1-708d-8145-96ef17407caa`. Notes: Targets unbalanced multiples, deep nesting, unicode lookalikes, various non-string types, whitespace, and pure opening/closing strings.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements is_balanced exactly as specified: it validates string input, uses a stack with the provided OPEN/CLOSE/PAIRS constants, ignores non-bracket characters, and returns a bool. All acceptance criteria are satisfied and the existing test suite passes.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1046 | 1388 | 0 | 0.005210 | 5.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1150 | 2401 | 0 | 0.002506 | 12.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1236 | 102 | 0 | 0.000463 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1429 | 844 | 0 | 0.001188 | 5.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1669 | 97 | 0 | 0.000588 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1815 | 818 | 0 | 0.001281 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2456 | 169 | 0 | 0.000889 | 7.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2712 | 117 | 0 | 0.000919 | 7.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 1149 | 3902 | 0 | 0.003857 | 21.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1460 | 976 | 0 | 0.004388 | 4.8s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 16122/10814/0; USD: 0.021289.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140be-39b5-707c-b67f-8bda98956af3 | SUCCESS | 0 | 0.726s | retained | off | 0.0027705499999999997 |
| red-1 | 01a140be-8c80-7092-ba4c-9ef7b9c47590 | SUCCESS | 0 | 3.998s | disposable | off | 0.0329433 |
| impl-tests-3 | 01a140be-cc46-7503-b0af-492d242f4642 | SUCCESS | 0 | 0.72s | disposable | off | 0.0027705099999999995 |
| impl-python-4 | 01a140be-f1b6-712e-af7a-c3ce0213b921 | SUCCESS | 0 | 0.532s | disposable | off | 0.00112625 |
| verify | 01a140bf-47af-756f-9d94-a6360d2b0335 | SUCCESS | 0 | 4.107s | disposable | off | 0.03465854 |
| heldout | 01a140bf-6476-7373-9cf5-0ce451670dbd | SUCCESS | 0 | 0.759s | disposable | off | 0.0027509199999999996 |
| mutant-m02-f95940ff2b | 01a140bf-7289-7159-b1b0-2e0e0c96f0f0 | SUCCESS | 0 | 4.052s | disposable | off | 0.03276685 |
| mutant-m03-13e48417f0 | 01a140bf-7216-7391-8350-4b9a76ea0329 | SUCCESS | 0 | 4.014s | disposable | off | 0.03293188 |
| mutant-m04-25a5fc5b73 | 01a140bf-721b-770b-bed0-46900e0397e7 | SUCCESS | 0 | 3.956s | disposable | off | 0.0323881 |
| mutant-m01-ae970cbcac | 01a140bf-7243-72bd-b283-0ec7fac5eccb | SUCCESS | 0 | 4.069s | disposable | off | 0.03285196 |
| mutant-m05-285d71b8c4 | 01a140bf-7245-741a-903f-b5e0a22a4ec5 | SUCCESS | 0 | 3.958s | disposable | off | 0.03281106 |
| mutant-m06-9bfdfde8f9 | 01a140bf-726e-723c-a8de-811a2887fa13 | SUCCESS | 0 | 4.003s | disposable | off | 0.03282344 |
| mutant-m07-112d16b760 | 01a140bf-72c0-77d0-8e5e-ffe2b13b1bd0 | SUCCESS | 0 | 4.054s | disposable | off | 0.0327123 |
| mutant-m08-9068babf89 | 01a140bf-72e1-7681-aa89-ac6ceaeef567 | SUCCESS | 0 | 4.054s | disposable | off | 0.03284154 |
| mutant-m09-1b4087966f | 01a140bf-8b05-75e4-b509-431c2c78f01a | SUCCESS | 0 | 3.943s | disposable | off | 0.03273746 |
| mutant-m10-3493ff69c1 | 01a140bf-a07e-7327-aa48-df1190b98c60 | SUCCESS | 0 | 3.949s | disposable | off | 0.03262007 |
| breaker-tests | 01a140c0-18c1-708d-8145-96ef17407caa | SUCCESS | 0 | 3.163s | disposable | off | 0.02465712 |

Sandbox operations: 17, total guest duration 54.057s, retained images ['50501052-ef44-46a1-9ab8-8c7c97935960'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
