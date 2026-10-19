# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-attest-a1-20261017T121900586528Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T12:19:00.587570+00:00, finished 2026-10-17T12:26:21.362809+00:00.

**Accept this patch.** All 20 sealed tests pass on the candidate in a fresh sandbox, and 18 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 20 of 20 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: 1 mutant(s) were unknown and excluded from the score

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 20 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 18 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 8 of 8 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 2 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 18 of 20 failed on the unmodified base; 20 of 20 pass on the candidate |
| E2 | Mutation check | pass | bound | 8 of 8 one-line mutants caught, 0 survived, 1 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `55009644-fdba-4a39-860c-1affbf65cc80`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `b7fdd9eb0b71d237` (34 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-reliability-2026-10-17/evaluation-paced-codex/snapshot/attest`.
Pacing (development gateway): 54 of an assumed 60 requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement is_balanced(s) in brackets/core.py, available through from brackets import is_balanced, to determine whether the ASCII brackets (), [] and {} in a string are correctly matched and nested. Ignore every other character, treat empty strings and strings without brackets as balanced, always return a bool for string inputs, and raise TypeError for non-string inputs. Preserve is_bracket and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept str instances, including subclasses. Process the six ASCII bracket characters in their original order, ignoring all other characters. Return True exactly | TypeError: s is not an instance of str; do not coerce or iterate non-string inputs. No particular exception message is required. |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True exactly when c is a str instance of length one containing one of (, ), [, ], {, or }; return False otherwise. |  |

Acceptance criteria:
1. 1. from brackets import is_balanced and from brackets import is_bracket both succeed.
2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}', and '([{}])'.
3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}', and '())'.
5. 5. Closing brackets without preceding unmatched opening brackets are rejected: ')(', '][', and '}{' each return False.
6. 6. Unmatched opening brackets remaining after otherwise valid pairs are rejected: '(()', '[[]', and '{{}' each return False.
7. 7. All non-bracket characters, including whitespace, newlines, Unicode characters, quotes, and backslashes, are ignored. For every string s, its result equals the result for s with all characters outside '()[]{}' removed.
8. 8. Strings containing no ASCII brackets, including 'abc', whitespace-only strings, and '你好（）', return True.
9. 9. For every string input, the result has type bool, rather than an integer or another truthy or falsy object.
10. 10. str subclass instances are accepted and evaluated by the same bracket-matching rules.
11. 11. Non-string inputs, including None, True, 0, 1.5, b'()', ['(', ')'], ('(', ')'), {}, and set(), raise TypeError.
12. 12. Repeated calls are independent: a call returning False or raising TypeError does not affect later calls with balanced strings.
13. 13. is_bracket retains its existing behavior: each character in '()[]{}' returns True; 'a', '', '((', and 1 return False. Its implementation remains unchanged.
14. 14. Existing test files remain unchanged and their tests continue to pass.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `25d42c43ab76b0a1b9976cbfe4049f047b3ee964508816b7e86a865a16e28030`, 20 test methods, sealed at 2026-10-17T12:20:46.501765+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 20 methods: ERROR 18): 18 of 20 methods failing, 2 passing; operation `01a149ce-aede-7770-974f-fc68219ce6f0`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_adjacent_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_closing_brackets_before_opening_brackets_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_crossed_or_mismatched_pairs_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_empty_string_is_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_every_result_is_an_actual_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_extra_closing_bracket_is_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_false_result_does_not_affect_later_calls | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_nested_pairs_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_non_string_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_opening_brackets_left_at_end_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_other_text_between_brackets_is_ignored | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_quotes_and_backslashes_do_not_suppress_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_removing_non_bracket_characters_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_single_unmatched_brackets_are_rejected | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_string_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_strings_without_ascii_brackets_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBalanced.test_type_error_does_not_affect_later_calls | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracket.test_other_values_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsBracket.test_six_ascii_brackets_are_recognized | ok (1 ev) | ok (1 ev) |

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
+    for c in s:
+        if c in OPEN:
+            stack.append(c)
+        elif c in CLOSE:
+            if not stack or stack.pop() != PAIRS[c]:
+                return False
+    return not stack
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (20 of 20 methods, each in its own process). Operation `01a149d1-08c3-7146-8f8b-655ca9c76138`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a149d1-29d6-708e-80b4-583a36eabd1c`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 8 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 8 evaluated: 8 killed, 0 survived, 1 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-2f645511c4 | brackets/core.py | 15 | remove `not` | unknown |  | None |
| m02-2ffcfc5443 | brackets/core.py | 16 | raise -> pass | killed | test_sealed.TestIsBalanced.test_non_string_inputs_raise_type_error | 01a149d1-3e7e-7479-96d4-6b9504faf4a6 |
| m03-6cfb313d75 | brackets/core.py | 20 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_strings_without_ascii_brackets_are_balanced, test_sealed.TestIsBalanced.test_each_simple | 01a149d1-3e9b-740e-bec7-77b49e35edef |
| m04-73277cabdf | brackets/core.py | 22 | In -> NotIn | killed | test_sealed.TestIsBalanced.test_strings_without_ascii_brackets_are_balanced, test_sealed.TestIsBalanced.test_each_simple | 01a149d1-3e6b-73c4-9ecc-af724ea53e14 |
| m05-adb274a753 | brackets/core.py | 23 | remove `not` | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a149d1-3da3-72ae-b04a-3fd6ec80b792 |
| m06-d874ad434e | brackets/core.py | 23 | NotEq -> Eq | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a149d1-3e00-75cc-9f2f-30be167b1c46 |
| m07-d9fa576cc6 | brackets/core.py | 23 | Or -> And | killed | test_sealed.TestIsBalanced.test_each_simple_pair_is_balanced, test_sealed.TestIsBalanced.test_adjacent_pairs_are_balance | 01a149d1-3e24-721e-9b62-06c9c3b94944 |
| m08-1402f59748 | brackets/core.py | 24 | False -> True | killed | test_sealed.TestIsBalanced.test_single_unmatched_brackets_are_rejected, test_sealed.TestIsBalanced.test_crossed_or_misma | 01a149d1-3e57-71f8-b88f-ba14c4cd7244 |
| m09-fc33332e25 | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestIsBalanced.test_empty_string_is_balanced, test_sealed.TestIsBalanced.test_strings_without_ascii_brackets | 01a149d1-5c8d-73dd-abaf-cb69030579c8 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `32efecd815f16411bbf2b1e7bdd36e462d02b62670659308c95969018fb1e831`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a149d3-2384-731d-a21f-5df37bd36341`. Notes: Targets exhaustive short sequences, nesting and suffix boundaries, Unicode lookalikes, deep inputs, string subclasses, additional invalid types, and preserved is_bracket behavior.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `if not isinstance(s, str)` enforces TypeError while accepting str subclasses, stack matching rejects mismatched or premature closings, and `return not stack` returns a bool; other characters are ignored and only is_balanced changes. Existing tests visibly pass and the targeted-check command exits successfully, although its omitted code prevents verifying its coverage.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10118 | 849 | 0 | - | 36.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10174 | 2087 | 0 | - | 52.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10209 | 111 | 0 | - | 20.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10403 | 218 | 10240 | - | 29.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10639 | 87 | 0 | - | 29.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10774 | 379 | 7168 | - | 38.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11125 | 107 | 0 | - | 20.1s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10407 | 1504 | 0 | - | 41.0s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10861 | 160 | 0 | - | 43.3s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 94710/5502/17408; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a149cd-34a8-704e-abd8-5fe22c16cd44 | SUCCESS | 0 | 0.757s | retained | off | 0.00274958 |
| red-1 | 01a149ce-aede-7770-974f-fc68219ce6f0 | SUCCESS | 0 | 4.478s | disposable | off | 0.03777083 |
| impl-tests-3 | 01a149d0-04d0-73fb-aeb9-400ed7e7fef3 | SUCCESS | 0 | 0.758s | disposable | off | 0.00277577 |
| impl-python-4 | 01a149d0-a8cc-760f-ada2-61aca68f1226 | SUCCESS | 0 | 0.55s | disposable | off | 0.0011224400000000002 |
| verify | 01a149d1-08c3-7146-8f8b-655ca9c76138 | SUCCESS | 0 | 4.392s | disposable | off | 0.03779268 |
| existing | 01a149d1-29d6-708e-80b4-583a36eabd1c | SUCCESS | 0 | 1.375s | disposable | off | 0.008691810000000001 |
| mutant-m01-2f645511c4 | None | UNCERTAIN | None | - | disposable | off | None |
| mutant-m03-6cfb313d75 | 01a149d1-3e9b-740e-bec7-77b49e35edef | SUCCESS | 0 | 4.262s | disposable | off | 0.03452704 |
| mutant-m02-2ffcfc5443 | 01a149d1-3e7e-7479-96d4-6b9504faf4a6 | SUCCESS | 0 | 4.288s | disposable | off | 0.034675990000000004 |
| mutant-m04-73277cabdf | 01a149d1-3e6b-73c4-9ecc-af724ea53e14 | SUCCESS | 0 | 4.381s | disposable | off | 0.0355947 |
| mutant-m05-adb274a753 | 01a149d1-3da3-72ae-b04a-3fd6ec80b792 | SUCCESS | 0 | 4.107s | disposable | off | 0.03452662 |
| mutant-m06-d874ad434e | 01a149d1-3e00-75cc-9f2f-30be167b1c46 | SUCCESS | 0 | 4.229s | disposable | off | 0.03450795 |
| mutant-m07-d9fa576cc6 | 01a149d1-3e24-721e-9b62-06c9c3b94944 | SUCCESS | 0 | 4.304s | disposable | off | 0.034835700000000004 |
| mutant-m08-1402f59748 | 01a149d1-3e57-71f8-b88f-ba14c4cd7244 | SUCCESS | 0 | 4.265s | disposable | off | 0.0347832 |
| mutant-m09-fc33332e25 | 01a149d1-5c8d-73dd-abaf-cb69030579c8 | SUCCESS | 0 | 4.201s | disposable | off | 0.034720259999999996 |
| breaker-tests | 01a149d3-2384-731d-a21f-5df37bd36341 | SUCCESS | 0 | 2.76s | disposable | off | 0.02042128 |

Sandbox operations: 16, total guest duration 49.107s, retained images ['55009644-fdba-4a39-860c-1affbf65cc80'].

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
