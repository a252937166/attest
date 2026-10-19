# Attest Proof Bundle: balanced-brackets

**Verdict: ERROR**  
Run `balanced-brackets-attest-a2-20261017T172725258441Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:27:25.258616+00:00, finished 2026-10-17T17:31:15.496459+00:00.

**This run did not complete.** The sandbox executor failed at stage verify. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): sandbox executor error after 10 model call(s): SandboxError: spawn outcome uncertain (TimeoutError: The read operation timed out); inspect account operations, do not replay



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: SandboxError: spawn outcome uncertain (TimeoutError: The read operation timed out); inspect account operations, do not replay


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 18 of 19 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the sandbox executor at stage verify; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 18 of 19 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage verify: SandboxError: spawn outcome uncertain (TimeoutError: The read operation timed out); inspect account operations, do not replay |

## 1. Frozen task and provenance
Task `balanced-brackets`, spec digest `84a644df71119f779e1a38d10248660efd901acec94c0ee01ed3d5db79c00f01`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `b68e8cfc-07f7-4f76-bfc7-217677ba7d9d`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. Do not change is_bracket or the tests.

## 2. Specification and contract
Feasible: True. Implement the is_balanced(s) function in brackets/core.py to check whether all parentheses (), square brackets [], and curly braces {} in the input string s are correctly matched and properly nested, ignoring any non-bracket characters. The function must return a boolean (True for balanced, False otherwise), raise TypeError if s is not a string, and treat the empty string as balanced. The existing is_bracket helper and the constants PAIRS, OPEN, CLOSE must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_balanced | is_balanced(s: str) -> bool | Returns True if every opening bracket in s has a corresponding closing bracket of the same type in the correct order (properly nested), and there are no unmatch | TypeError: raised when s is not a string. |
| is_bracket | is_bracket(c: str) -> bool | Returns True if c is a single-character string and one of the six bracket characters '(', ')', '[', ']', '{', '}'. Returns False for any other input (including  |  |

Acceptance criteria:
1. is_balanced('') returns True.
2. is_balanced('()') returns True.
3. is_balanced('[]') returns True.
4. is_balanced('{}') returns True.
5. is_balanced('()[]{}') returns True.
6. is_balanced('([{}])') returns True.
7. is_balanced('(a[b]{c})') returns True.
8. is_balanced('f(x[0], y[1])') returns True.
9. is_balanced('(') returns False.
10. is_balanced(')') returns False.
11. is_balanced('([)]') returns False.
12. is_balanced('(]') returns False.
13. is_balanced('{[}') returns False.
14. is_balanced('())') returns False.
15. Non-bracket characters are ignored: is_balanced('a') returns True, is_balanced('(a)') returns True.
16. is_balanced returns a bool (True or False) for all valid string inputs.
17. is_balanced raises TypeError when s is not a string (e.g., is_balanced(123), is_balanced(None), is_balanced([1,2])).
18. The existing is_bracket behavior is preserved (as verified by the existing tests).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `9dadb79f8f769f7c491d999ded61522cfe76827b205a64fca9a594c3181ec898`, 19 test methods, sealed at 2026-10-17T17:27:51.177227+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 19 methods: ERROR 18): 18 of 19 methods failing, 1 passing; operation `01a14ae7-ccf9-7057-8327-2e49bda27d91`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsBalanced.test_curly_wrong_pair | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_empty_string_returns_true | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_extra_close | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_function_call_like | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_is_bracket_preserved | ok (1 ev) | - |
| test_sealed.TestIsBalanced.test_misordered_closes | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_multiple_types_ordered | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_nested_properly | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_non_bracket_only_true | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_non_bracket_with_balanced | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_return_type_is_bool | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_simple_curly | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_simple_parentheses | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_simple_square | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_single_close_parenthesis_false | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_single_open_parenthesis_false | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_type_error_on_non_string | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_with_letters_and_numbers | ERROR (1 ev) | - |
| test_sealed.TestIsBalanced.test_wrong_type_pair | ERROR (1 ev) | - |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

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

Static tamper scan of the added lines: no suspicious constructs on the added lines (11 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Drift audit not run.



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1046 | 2013 | 0 | 0.007085 | 6.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1433 | 722 | 0 | 0.001080 | 5.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1434 | 139 | 0 | 0.000555 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1628 | 776 | 0 | 0.001187 | 5.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1858 | 94 | 0 | 0.000642 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2001 | 1098 | 0 | 0.001589 | 8.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2838 | 16000 | 0 | 0.015251 | 77.7s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5-repair | medium | 2928 | 1311 | 0 | 0.002058 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 3657 | 247 | 0 | 0.001319 | 4.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 3800 | 104 | 0 | 0.001234 | 3.3s | ok |

Model calls: 10 (1 failed, 1 malformed); tokens in/out/cached 22623/22504/0; USD: 0.032.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ae7-90e1-7409-9a34-54c5eea99a43 | SUCCESS | 0 | 1.202s | retained | off | 0.00285997 |
| red-1 | 01a14ae7-ccf9-7057-8327-2e49bda27d91 | SUCCESS | 0 | 4.3s | disposable | off | 0.03604878 |
| impl-tests-3 | 01a14ae8-1c37-73fd-87b7-43321a8248fc | SUCCESS | 0 | 0.798s | disposable | off | 0.00285357 |
| impl-python-4 | 01a14ae8-4817-7776-ae08-d9d80ae764fa | SUCCESS | 0 | 0.542s | disposable | off | 0.0012316900000000001 |
| impl-python-5 | 01a14ae9-a51b-7116-b5a1-a5e44b53c6f5 | SUCCESS | 0 | 0.675s | disposable | off | 0.00123236 |
| impl-tests-6 | 01a14ae9-c81a-7726-a020-dd4964d9c4c2 | SUCCESS | 0 | 0.739s | disposable | off | 0.00282183 |
| verify | 01a14ae9-f9e4-72a6-b837-fc62a4a6fd26 | SUCCESS | 0 | 4.944s | disposable | off | 0.03602617 |
| existing | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 8, total guest duration 13.2s, retained images ['b68e8cfc-07f7-4f76-bfc7-217677ba7d9d'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: sandbox executor; stage: verify; model calls 10 (1 failed); sandbox operations 8; committed cost USD 0.032; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- SandboxError: spawn outcome uncertain (TimeoutError: The read operation timed out); inspect account operations, do not replay

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
