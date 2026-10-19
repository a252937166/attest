# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-attest-a1-20261019T142303669858Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T14:23:03.671886+00:00, finished 2026-10-19T14:33:23.231731+00:00.

**Accept this patch.** All 16 sealed tests pass on the candidate in a fresh sandbox, and 13 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 16 of 16 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 16 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 13 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 3 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 13 of 16 failed on the unmodified base; 16 of 16 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `5b7bd811-b76f-42d8-8969-6366bbc512e9`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.7.0 revision `f836cfd0154faa87` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision6-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement brackets.core.is_balanced(s), available through from brackets import is_balanced, to determine whether the ASCII brackets (), [] and {} in a string are correctly paired and nested while ignoring every other character. Return a bool for all string inputs, including True for empty strings and strings containing no brackets, and raise TypeError for non-string inputs. Preserve is_bracket and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept str instances, including subclasses. Ignore all characters except (, ), [, ], { and }. Return True exactly when each closing bracket matches the most rec | TypeError: s is not an instance of str; do not coerce values to strings or accept bytes or other iterables as strings. The exception message is unspecified. |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True exactly when c is a str instance of length one containing one of ()[]{}; otherwise return False. |  |

Acceptance criteria:
AC1. 1. from brackets import is_balanced and from brackets import is_bracket both succeed.
AC2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}' and '([{}])'.
AC3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
AC4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}' and '())'.
AC5. 5. Each opening bracket alone and each closing bracket alone returns False; unmatched brackets also cause False when preceded by an otherwise balanced sequence, as in '()(' and '()]'.
AC6. 6. Properly nested repeated brackets and adjacent balanced groups return True, including '((()))' and '[{}]({[]})'.
AC7. 7. All non-bracket characters are ignored, including whitespace, Unicode characters, quotes and backslashes. Strings such as 'abc', ' \t\n' and '你好（）' return True. Quotes and backslashes do not escape ASCII brackets or make them inactive.
AC8. 8. For every string input, removing all characters outside ()[]{} leaves the result unchanged.
AC9. 9. Every string input produces a value whose type is bool, rather than an integer, None or another truthy or falsy value.
AC10. 10. Non-string inputs raise TypeError, including None, True, 0, 1.5, b'()', [], ['(', ')'], (), {}, and set().
AC11. 11. Instances of a str subclass with ordinary inherited string behavior are accepted and produce the same results as equivalent plain strings.
AC12. 12. is_bracket remains unchanged: it returns True for each character in '()[]{}' and False for 'a', '', '((', and 1. All existing tests remain unchanged and pass.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are jointly satisfiable by implementing only is_balanced in brackets/core.py. The existing exports, is_bracket, constants, and tests can remain unchanged. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `dd8487107a3a017026ba31ed87ae84a06343a56abda0e9327a0a5c159f7dfa5d`, 16 test methods, sealed at 2026-10-19T14:27:13.752625+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 16 methods: ERROR 13): 13 of 16 methods failing, 3 passing; operation `01a1548f-2e5a-776c-b8aa-a2cf5b8ff3a4`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestBalanced.test_all_result_categories_have_exact_bool_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_basic_balanced_strings | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_brackets_with_interspersed_text | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_each_closing_bracket_alone | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_each_opening_bracket_alone | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_mismatched_and_extra_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_non_string_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_plain_str_subclass_is_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_public_functions_are_importable | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_quotes_and_backslashes_do_not_hide_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_removing_nonbrackets_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_repeated_nesting_and_adjacent_groups | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_strings_without_ascii_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_unmatched_bracket_after_balanced_prefix | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracket.test_each_ascii_bracket_is_recognized | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracket.test_non_brackets_and_invalid_lengths_are_rejected | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

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


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (16 of 16 methods, each in its own process). Operation `01a15493-1062-742d-8761-5765d2971cf0`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15493-2d32-74b1-b9bb-7acf100ba8fc`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 9 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ba8452d645 | brackets/core.py | 15 | remove `not` | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-3fe6-71d7-b942-0b6659ea8805 |
| m02-57f6af0214 | brackets/core.py | 16 | raise -> pass | killed | test_sealed.TestBalanced.test_non_string_inputs_raise_type_error | 01a15493-400d-718e-806f-b1eaf9d81dfa |
| m03-1b3e7f0d7f | brackets/core.py | 20 | In -> NotIn | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-3f62-758a-9e38-3a48c728e4c5 |
| m04-e3b6a1be86 | brackets/core.py | 22 | In -> NotIn | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-402c-75ed-aa15-89ee2ca4c884 |
| m05-3ae1c5083c | brackets/core.py | 23 | remove `not` | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-3faf-70c2-9bf2-2c360fcecb40 |
| m06-9753e0bb65 | brackets/core.py | 23 | NotEq -> Eq | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-3ffd-71a2-8713-819c23ff4e9c |
| m07-bf026b8432 | brackets/core.py | 23 | Or -> And | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-3fef-706a-86f9-261bd26f287c |
| m08-647ebba621 | brackets/core.py | 24 | False -> True | killed | test_sealed.TestBalanced.test_mismatched_and_extra_brackets, test_sealed.TestBalanced.test_each_closing_bracket_alone, t | 01a15493-3fd7-7624-b0ca-480fcfb79c3b |
| m09-380b5ed00e | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestBalanced.test_basic_balanced_strings, test_sealed.TestBalanced.test_brackets_with_interspersed_text, tes | 01a15493-5efb-769e-8998-4677cee79957 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `5e81e842785bca7d78b558af98fa9d71b2c43ad4ea1d6406cc2b72d4d0f3e551`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a15494-85b3-70ef-b541-f9213936bee1`. Notes: Targets complete ASCII pair combinations, odd lengths, nested mismatches, Unicode lookalikes, deep stacks, string subclasses, and additional non-string iterables.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `if not isinstance(s, str)` rejects non-strings while accepting str subclasses, the stack and `stack.pop() != PAIRS[char]` enforce matching and nesting, and `return not stack` returns a bool; other characters are ignored. Only is_balanced changes, preserving is_bracket, constants, exports, and tests; observed outputs support the claims that existing tests and contract smoke checks pass.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10137 | 819 | 0 | - | 49.1s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11805 | 92 | 0 | - | 67.6s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10320 | 3099 | 0 | - | 114.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10330 | 95 | 0 | - | 66.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10516 | 221 | 0 | - | 41.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10751 | 80 | 0 | - | 61.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10884 | 421 | 7168 | - | 30.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11241 | 103 | 0 | - | 35.0s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10364 | 2308 | 0 | - | 67.4s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10825 | 132 | 0 | - | 20.2s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 107173/7370/7168; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1548b-896b-724f-85f2-6e0b92187971 | SUCCESS | 0 | 0.816s | retained | off | 0.00289078 |
| red-1 | 01a1548f-2e5a-776c-b8aa-a2cf5b8ff3a4 | SUCCESS | 0 | 4.384s | disposable | off | 0.03247107 |
| impl-tests-3 | 01a15491-eb35-763f-844f-cc83a100fc1d | SUCCESS | 0 | 0.816s | disposable | off | 0.00287275 |
| impl-python-4 | 01a15492-7501-7008-91d7-404c3792b445 | SUCCESS | 0 | 0.609s | disposable | off | 0.00122264 |
| verify | 01a15493-1062-742d-8761-5765d2971cf0 | SUCCESS | 0 | 3.86s | disposable | off | 0.031552779999999996 |
| existing | 01a15493-2d32-74b1-b9bb-7acf100ba8fc | SUCCESS | 0 | 1.443s | disposable | off | 0.008758549999999999 |
| mutant-m01-ba8452d645 | 01a15493-3fe6-71d7-b942-0b6659ea8805 | SUCCESS | 0 | 3.684s | disposable | off | 0.02948537 |
| mutant-m02-57f6af0214 | 01a15493-400d-718e-806f-b1eaf9d81dfa | SUCCESS | 0 | 3.658s | disposable | off | 0.028665970000000002 |
| mutant-m04-e3b6a1be86 | 01a15493-402c-75ed-aa15-89ee2ca4c884 | SUCCESS | 0 | 3.687s | disposable | off | 0.02886692 |
| mutant-m03-1b3e7f0d7f | 01a15493-3f62-758a-9e38-3a48c728e4c5 | SUCCESS | 0 | 3.726s | disposable | off | 0.028935080000000002 |
| mutant-m05-3ae1c5083c | 01a15493-3faf-70c2-9bf2-2c360fcecb40 | SUCCESS | 0 | 3.712s | disposable | off | 0.02889973 |
| mutant-m07-bf026b8432 | 01a15493-3fef-706a-86f9-261bd26f287c | SUCCESS | 0 | 3.68s | disposable | off | 0.028842390000000002 |
| mutant-m06-9753e0bb65 | 01a15493-3ffd-71a2-8713-819c23ff4e9c | SUCCESS | 0 | 3.605s | disposable | off | 0.02822856 |
| mutant-m08-647ebba621 | 01a15493-3fd7-7624-b0ca-480fcfb79c3b | SUCCESS | 0 | 3.559s | disposable | off | 0.02863215 |
| mutant-m09-380b5ed00e | 01a15493-5efb-769e-8998-4677cee79957 | SUCCESS | 0 | 3.565s | disposable | off | 0.028947250000000004 |
| breaker-tests | 01a15494-85b3-70ef-b541-f9213936bee1 | SUCCESS | 0 | 2.874s | disposable | off | 0.021929909999999997 |

Sandbox operations: 16, total guest duration 47.678s, retained images ['5b7bd811-b76f-42d8-8969-6366bbc512e9'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
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
