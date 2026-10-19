# Attest Proof Bundle: balanced-brackets

**Verdict: VERIFIED**  
Run `balanced-brackets-attest-a1-20261019T082112441317Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T08:21:12.441914+00:00, finished 2026-10-19T08:33:06.584274+00:00.

**Accept this patch.** All 17 sealed tests pass on the candidate in a fresh sandbox, and 14 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 17 of 17 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 17 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 14 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
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
| E1 | Sealed tests, written before the patch | pass | bound | 14 of 17 failed on the unmodified base; 17 of 17 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 9 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ea443985-e5d3-41e9-9db8-2ec4a18179cf`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.5.0 revision `1e12d46217fb6b8a` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement brackets.core.is_balanced(s), available through from brackets import is_balanced, to return a bool indicating whether the ASCII brackets (), [] and {} in a string are correctly paired and nested. Ignore every other character, treat strings containing no brackets as balanced, and raise TypeError for any non-string input. Preserve is_bracket and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| brackets.is_balanced | is_balanced(s) | Accept a str instance, including a str subclass. Process bracket characters in order: each closing bracket must match the most recent unmatched opening bracket, | TypeError: s is not an instance of str, including bytes, None, numbers, lists and other iterable objects; do not coerce such inputs to strings. Exception messag |
| brackets.is_bracket | is_bracket(c) | Preserve the existing implementation: return True only when c is a str instance of length one containing one of ()[]{}; return False otherwise. |  |

Acceptance criteria:
AC1. 1. from brackets import is_balanced and from brackets import is_bracket continue to work.
AC2. 2. is_balanced returns True for each of '', '()', '[]', '{}', '()[]{}' and '([{}])'.
AC3. 3. is_balanced returns True for '(a[b]{c})' and 'f(x[0], y[1])'.
AC4. 4. is_balanced returns False for each of '(', ')', '([)]', '(]', '{[}' and '())'.
AC5. 5. Unmatched opening brackets of every kind return False, including '[', '{' and '(()'. Unmatched closing brackets of every kind return False, including ']', '}' and ')('.
AC6. 6. Matching requires the correct bracket type and nesting order, not merely equal counts; '[)' and '{]' return False.
AC7. 7. Removing every character except ()[]{} from any string leaves its is_balanced result unchanged. Strings containing only ordinary text, whitespace or non-ASCII non-bracket characters return True.
AC8. 8. Brackets inside quotes or preceded by backslashes are still counted; a string consisting of a backslash followed by '(' returns False.
AC9. 9. For every valid string input, the result has type bool, including balanced and unbalanced cases.
AC10. 10. Non-string inputs raise TypeError, including None, True, 0, 1.5, b'()', [], ['(', ')'], {}, and an arbitrary object instance.
AC11. 11. Instances of str subclasses are accepted and evaluated using the same bracket-matching rules.
AC12. 12. is_bracket remains unchanged and returns True for each character in '()[]{}' and False for 'a', '', '((', and 1.
AC13. 13. Existing test files remain unchanged and their tests continue to pass.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by implementing only is_balanced in brackets/core.py with string type validation and ordered bracket matching. Existing exports, constants, is_bracket, and tests can remain unchanged. Rule: a conflict is demonstrated only when it names existing acceptance criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `c0179e20a928a8bc780edd3a336f74c0f6a977f2465a57d30e7f5cc257cac201`, 17 test methods, sealed at 2026-10-19T08:28:31.730191+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (14 of 17 methods: ERROR 14): 14 of 17 methods failing, 3 passing; operation `01a15346-ca03-7718-b0ba-f78273e3081b`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestBalanced.test_backslashes_do_not_escape_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_empty_and_simple_balanced_strings | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_nested_balanced_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_nonstring_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_public_api_exports | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_quotes_do_not_hide_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_removing_nonbrackets_preserves_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_representative_unbalanced_strings | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_result_is_exactly_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_str_subclasses_are_evaluated | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_strings_without_brackets_are_balanced | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_text_between_brackets | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_unmatched_closings_of_every_kind | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_unmatched_openings_of_every_kind | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBalanced.test_wrong_type_or_nesting_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestBracketHelper.test_is_bracket_accepts_six_ascii_brackets | ok (1 ev) | ok (1 ev) |
| test_sealed.TestBracketHelper.test_is_bracket_rejects_other_values | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

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

Sealed suite: OK (17 of 17 methods, each in its own process). Operation `01a15348-8748-7505-b000-5cf82533ad13`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15348-bfe3-7200-95cf-4ee5069d275b`, bound through the supervisor: 1 module(s), binding ok.

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

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-17781654c1 | brackets/core.py | 14 | remove `not` | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15348-e6ca-741f-81ea-3c29f09fd736 |
| m02-1d8db31cc8 | brackets/core.py | 15 | raise -> pass | killed | test_sealed.TestBalanced.test_nonstring_inputs_raise_type_error | 01a15348-e69b-700d-a336-ba77575c6bf1 |
| m03-3ed9a3293a | brackets/core.py | 19 | In -> NotIn | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15348-e643-7203-8806-10dccb8d9835 |
| m04-be9c0a1c38 | brackets/core.py | 21 | In -> NotIn | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15348-e6c7-711a-989a-bedea8cfa97b |
| m05-34fe0c49e2 | brackets/core.py | 22 | remove `not` | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15348-e6ea-7631-b041-d08d9a310fa4 |
| m06-49e34e734e | brackets/core.py | 22 | NotEq -> Eq | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15348-e6b6-77ca-bd61-3872d3bff67f |
| m07-fdc74f1cd4 | brackets/core.py | 22 | Or -> And | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15348-e6c6-7236-a2b7-80d41ef2a7c0 |
| m08-4867ef55fc | brackets/core.py | 23 | False -> True | killed | test_sealed.TestBalanced.test_representative_unbalanced_strings, test_sealed.TestBalanced.test_unmatched_closings_of_eve | 01a15348-e6d4-713b-ae0c-75bc3fc1b07b |
| m09-d543026f6d | brackets/core.py | 25 | remove `not` | killed | test_sealed.TestBalanced.test_empty_and_simple_balanced_strings, test_sealed.TestBalanced.test_nested_balanced_string, t | 01a15349-0cb2-7166-a76c-8618672afacd |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `d543d29defa873fc61978dd52c9a520d6d958c3e12be68579832d7d0fc4fea46`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a1534a-a58b-768b-85c2-69812bcccb26`. Notes: Targets deep nesting, long sequences, irreparable mismatches, Unicode lookalikes, quote and backslash handling, iterable type errors, and public API boundaries.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `if not isinstance(s, str)` rejects non-strings while accepting str subclasses, `stack.pop() != PAIRS[c]` enforces matching types and nesting, and `return not stack` returns a bool and rejects unmatched openings; other characters are ignored. Only is_balanced changes, preserving is_bracket, constants, exports and tests, and the observed test run supports the claim that existing tests pass (2 passed, exit 0).

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10116 | 817 | 7680 | - | 45.3s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 10958 | 97 | 7552 | - | 177.9s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10332 | 2469 | 0 | - | 190.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10322 | 88 | 7168 | - | 27.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10510 | 233 | 7168 | - | 29.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10721 | 78 | 7168 | - | 24.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10855 | 120 | 7168 | - | 20.4s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10353 | 2144 | 0 | - | 95.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10745 | 139 | 7552 | - | 22.0s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 94912/6185/51456; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15340-5136-7746-931f-f42297d6ad75 | SUCCESS | 0 | 0.825s | retained | off | 0.0028569299999999997 |
| red-1 | 01a15346-ca03-7718-b0ba-f78273e3081b | SUCCESS | 0 | 4.129s | disposable | off | 0.033346 |
| impl-tests-3 | 01a15348-26af-7364-9701-93b6ab37a693 | SUCCESS | 0 | 1.004s | disposable | off | 0.0028780299999999997 |
| verify | 01a15348-8748-7505-b000-5cf82533ad13 | SUCCESS | 0 | 4.066s | disposable | off | 0.03309881 |
| existing | 01a15348-bfe3-7200-95cf-4ee5069d275b | SUCCESS | 0 | 1.442s | disposable | off | 0.00875403 |
| mutant-m01-17781654c1 | 01a15348-e6ca-741f-81ea-3c29f09fd736 | SUCCESS | 0 | 3.835s | disposable | off | 0.029801470000000004 |
| mutant-m07-fdc74f1cd4 | 01a15348-e6c6-7236-a2b7-80d41ef2a7c0 | SUCCESS | 0 | 3.895s | disposable | off | 0.03004993 |
| mutant-m03-3ed9a3293a | 01a15348-e643-7203-8806-10dccb8d9835 | SUCCESS | 0 | 3.849s | disposable | off | 0.03050024 |
| mutant-m05-34fe0c49e2 | 01a15348-e6ea-7631-b041-d08d9a310fa4 | SUCCESS | 0 | 3.834s | disposable | off | 0.029878360000000003 |
| mutant-m04-be9c0a1c38 | 01a15348-e6c7-711a-989a-bedea8cfa97b | SUCCESS | 0 | 3.855s | disposable | off | 0.03029118 |
| mutant-m06-49e34e734e | 01a15348-e6b6-77ca-bd61-3872d3bff67f | SUCCESS | 0 | 3.833s | disposable | off | 0.029750550000000004 |
| mutant-m02-1d8db31cc8 | 01a15348-e69b-700d-a336-ba77575c6bf1 | SUCCESS | 0 | 3.833s | disposable | off | 0.02964731 |
| mutant-m08-4867ef55fc | 01a15348-e6d4-713b-ae0c-75bc3fc1b07b | SUCCESS | 0 | 3.896s | disposable | off | 0.03026671 |
| mutant-m09-d543026f6d | 01a15349-0cb2-7166-a76c-8618672afacd | SUCCESS | 0 | 3.673s | disposable | off | 0.02996569 |
| breaker-tests | 01a1534a-a58b-768b-85c2-69812bcccb26 | SUCCESS | 0 | 2.677s | disposable | off | 0.02003899 |

Sandbox operations: 15, total guest duration 48.646s, retained images ['ea443985-e5d3-41e9-9db8-2ec4a18179cf'].

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
