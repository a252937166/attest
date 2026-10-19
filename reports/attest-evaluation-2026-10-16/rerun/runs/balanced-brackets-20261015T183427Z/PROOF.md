# Attest Proof Bundle: balanced-brackets

**Verdict: ERROR**  
Run `balanced-brackets-20261015T183427Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:34:27.698114+00:00, finished 2026-10-15T18:36:25.352475+00:00.

Reasons: model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not retried)


## 1. Frozen task
Task `balanced-brackets`, spec digest `b4b1ed357cf1c1bd54b85a7c1e9d3157d00ec207969b2cf0547512c4dbe167c8`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `84b50c07-a184-484a-85d9-feb5e6edff54`; test runner `unittest`; install: `none` (checkpoint networking off).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the is_balanced(s) function in brackets/core.py to check if a string has balanced and properly nested brackets of three types: (), [], {}. Non-bracket characters are ignored. The function must return a boolean (True for balanced, False otherwise). It must raise TypeError if the input is not a string. The existing is_bracket helper function and the test suite must not be modified.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_bracket | is_bracket(c: Any) -> bool | Returns True if c is a single-character string and one of the six bracket characters '(', ')', '[', ']', '{', '}'. Returns False otherwise (including for non-st |  |
| is_balanced | is_balanced(s: str) -> bool | Returns True if all brackets in the string s are correctly matched and properly nested, ignoring any non-bracket characters. Returns False if brackets are unmat | TypeError: raised when s is not a string. |

Acceptance criteria:
1. 1. is_balanced('') returns True.
2. 2. is_balanced('()') returns True.
3. 3. is_balanced('[]') returns True.
4. 4. is_balanced('{}') returns True.
5. 5. is_balanced('()[]{}') returns True.
6. 6. is_balanced('([{}])') returns True.
7. 7. is_balanced('(a[b]{c})') returns True.
8. 8. is_balanced('f(x[0], y[1])') returns True.
9. 9. is_balanced('(') returns False.
10. 10. is_balanced(')') returns False.
11. 11. is_balanced('([)]') returns False.
12. 12. is_balanced('(]') returns False.
13. 13. is_balanced('{[}') returns False.
14. 14. is_balanced('())') returns False.
15. 15. Non-bracket characters are ignored: is_balanced('a') returns True, is_balanced('(a') returns False, is_balanced('a)') returns False.
16. 16. is_balanced returns a bool (True or False) for all string inputs.
17. 17. is_balanced raises TypeError when s is not a string (e.g., None, 123, [], {}).
18. 18. Existing is_bracket behavior is preserved: is_bracket(c) returns True for each of '(', ')', '[', ']', '{', '}' and False for any other input.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `2d0e814836d32ef3c393eaee066fff6bb5f03a634babd3939385dd5759fb5a2d`, 21 test methods, sealed at 2026-10-15T18:36:20.342048+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (20 of 21 methods: ERROR 19, FAIL 1): 20 of 21 methods failing, 1 passing; operation `01a140d9-cbe2-70b3-bfe7-8e221f0f7e36`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_close_with_letter_false | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_empty_string | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_extra_closing | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_function_call_like | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_is_bracket_false_for_others | FAIL (1 ev) | - |
| test_sealed.TestIsBalanced.test_is_bracket_true_for_each | ok (1 ev) | - |
| test_sealed.TestIsBalanced.test_misordered_closes | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_mixed_with_letters | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_multiple_types_seq | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_nested_properly | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_nonbracket_only_true | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_open_with_letter_false | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_returns_bool | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_simple_braces | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_simple_brackets | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_simple_parentheses | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_single_close_paren_false | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_single_open_paren_false | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_type_error_nonstring | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_wrong_type_pair | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_wrong_type_pair2 | ERROR (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: n/a (0 passed of 0). Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint.

(none)

Held-out suite: none configured.

## 6. Gates
(none)

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Drift audit not run.



## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1046 | 2448 | 0 | 0.008390 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1407 | 16000 | 0 | 0.014822 | 78.5s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1-repair | default | 1492 | 2308 | 0 | 0.002525 | 11.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | - | - | - | - | 5.0s | error |

Model calls: 4 (2 failed, 1 malformed); tokens in/out/cached 3945/20756/0; USD: 0.025737.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140d8-3612-76de-9dad-1729b942dde3 | SUCCESS | 0 | 0.736s | retained | off | 0.0027399399999999997 |
| red-1 | 01a140d9-cbe2-70b3-bfe7-8e221f0f7e36 | SUCCESS | 0 | 4.422s | disposable | off | 0.036074590000000004 |

Sandbox operations: 2, total guest duration 5.158s, retained images ['84b50c07-a184-484a-85d9-feb5e6edff54'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
