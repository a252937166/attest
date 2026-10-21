# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: VERIFIED**  
Run `slugkit-regression-001-attest-a2-20261021T030548833889Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:05:48.835322+00:00, finished 2026-10-21T03:08:57.012007+00:00.

**Accept this patch.** All 19 sealed tests pass on the candidate in a fresh sandbox, and 12 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 19 of 19 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No mutable sites were found on the changed lines, so only the tests written after the patch test it structurally (E2, E3). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4). 2 of the tests written after the patch failed as written and were corrected by the arbiter; the correction kept every test method, changed only the failing ones, passes on the candidate and discriminates (1 of 2 corrected test(s) fail on the unmodified base with an authentic result), and the gate was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: mutation gate: no mutable sites were generated on the changed lines; only the adversarial suite (7 tests) tests the patch structurally; arbitration (validated corrections re-run their gates): all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 2 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 19 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 12 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 7 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 7 sealed test(s) which already passed on the base say anything about the change (E1).
- That the mutation check tested anything: no mutable sites were found on the changed lines (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, but which side was wrong is a model judgement; the original tests and results are preserved (E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 12 of 19 failed on the unmodified base; 19 of 19 pass on the candidate |
| E2 | Mutation check | pass | bound | no mutable sites on the changed lines; the adversarial suite (7 tests) carries the load |
| E3 | Tests written after the patch | pass | bound | 2 of 7 failed as written (test_unicode_combining_marks, test_null_bytes_in_string); 2 test(s) corrected by the arbiter and validated (1 of 2 corrected test(s) fail on the unmodified base with an authentic result); the corrected module passes (OK (7 of 7 methods, each in its own process)) |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 2 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `0dd24960-5811-4a1f-849d-526be57f691a`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix the slugify function in slugkit.core so that it lowercases the input, collapses any maximal run of non-ASCII-alphanumeric characters into a single hyphen, strips leading and trailing hyphens, returns empty string when no ASCII letters or digits are present, treats non-ASCII letters as separators, raises TypeError for non-string input, and returns a string. The existing tests in tests/test_basic.py must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugify | slugify(text: str) -> str | Convert text to lowercase. Replace each maximal contiguous sequence of characters that are not in the set [a-z0-9] with a single hyphen ('-'). Remove any leadin | Raise TypeError if text is not a string (e.g., None, int, float, list, bytes). |

Acceptance criteria:
AC1. slugify('Hello--World') == 'hello-world'
AC2. slugify('a -- b') == 'a-b'
AC3. slugify('one , two ; three') == 'one-two-three'
AC4. slugify('x___y') == 'x-y' (runs of separators collapse to one hyphen).
AC5. slugify('end!') == 'end'
AC6. slugify('  padded  ') == 'padded'
AC7. slugify('--both--') == 'both'
AC8. slugify('(parens)') == 'parens' (no leading or trailing hyphen).
AC9. slugify('') == ''
AC10. slugify('!!!') == ''
AC11. slugify('   ') == '' (nothing to keep gives the empty string).
AC12. slugify('Hello World') == 'hello-world' (existing behavior preserved).
AC13. slugify('already-a-slug') == 'already-a-slug' (existing behavior preserved).
AC14. slugify('Python 3') == 'python-3' (existing behavior preserved).
AC15. slugify('MiXeD CaSe 42') == 'mixed-case-42' (existing behavior preserved).
AC16. slugify('café crème') == 'caf-cr-me' (non-ASCII letters are separators).
AC17. slugify('日本語') == '' (non-ASCII letters are separators, no ASCII alnum yields empty string).
AC18. The result is always a str.
AC19. TypeError is raised for non-string input such as None, 3, 2.5, ['a'], b'bytes'.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. All authoritative task criteria (TC1-TC6) are mutually consistent: they specify a single, coherent transformation (lowercase, collapse non-ASCII-alnum runs to one hyphen, strip edge hyphens, empty result when no ASCII alnum, TypeError on non-str) that does not contradict the existing tests in tests/test_basic.py. The current implementation in slugkit/core.py simply fails to implement the full specification, but the specification itself contains no internal contradictions or conflicts with frozen code. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d244efc0236c1728f1f61133968be650f9fb1f3ff4ebe47b4855a957d812ec9d`, 19 test methods, sealed at 2026-10-21T03:06:20.317351+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 19 methods: FAIL 12): 12 of 19 methods failing, 7 passing; operation `01a15c6c-8753-75c5-9b8f-a88c55d51fa0`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSlugifyAcceptance.test_ac10_only_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac11_only_spaces | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac12_hello_world | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac13_already_slug | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac14_python_3 | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac15_mixed_case_42 | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac16_non_ascii_letters_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac17_japanese_no_ascii | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac18_result_is_str | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac19_type_error_non_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac1_hello_world_double_hyphen | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac2_space_hyphen_space | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac3_comma_semicolon | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac4_underscore_run | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac5_trailing_exclam | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac6_padded_spaces | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac7_both_ends_hyphen | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac8_parens | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac9_empty_string | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/slugkit/core.py
+++ b/slugkit/core.py
@@ -6,7 +6,11 @@
 
 
 def slugify(text):
-    """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
+    """Convert text to lowercase ASCII hyphenated slug."""
     if not isinstance(text, str):
         raise TypeError("text must be a str")
-    return _NOT_ALNUM.sub("-", text.lower())
+    text = text.lower()
+    # Replace any sequence of non-alnum characters with a single hyphen
+    slug = re.sub(r'[^a-z0-9]+', '-', text)
+    # Remove leading/trailing hyphens
+    return slug.strip('-')
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (6 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (19 of 19 methods, each in its own process). Operation `01a15c6e-211c-7504-9256-5ba4faef3ff3`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a15c6e-4322-734c-8b33-7d915a9fa6fb`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | no mutable sites on the changed lines; the adversarial suite (7 tests) carries the load |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (7 of 7 methods, each in its own process) on the corrected module (2 test(s) corrected, validated: 1 of 2 corrected test(s) fail on the unmodified base with an authentic result); original failures kept in E3 |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 0 generated, 0 evaluated: 0 killed, 0 survived, 0 unknown; mutation score - (threshold 0.5).

(none)

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `8bfeaabf1abe6af13d3df4b0eb6658f9b74c4dbc26814746f285425e0a07579f`): FAILED (2 of 7 methods: ERROR 1, FAIL 1); binding FAILED; operation `01a15c6e-6eff-7310-909e-ef9e243f917c`. Notes: Targeted Unicode edge cases, emojis, long strings, mixed ascii/nonascii, null bytes.

| Failing adversarial test | Outcome |
| --- | --- |
| test_unicode_combining_marks | FAIL |
| test_null_bytes_in_string | ERROR |
Corrected adversarial module (E6): `arbitration/adversarial_corrected.py` sha256 `f1d4c9cc7c35aca26d0e110e6fcaf95395e83fbf2384afa23456a5fbd845c75d`; corrected tests test_null_bytes_in_string, test_unicode_combining_marks; on the candidate OK (7 of 7 methods, each in its own process); validated: 1 of 2 corrected test(s) fail on the unmodified base with an authentic result; operation `01a15c6e-dde0-76f2-a78a-65d4d4631243`. The adversarial gate was re-run on it.
Adversarial authoring: 1 attempt(s).

### Counterexamples
- E3 `test_unicode_combining_marks`: FAIL; AssertionError: 'e' != 'e-'; first `'e'` vs second `'e-'` (the test's argument order decides which is the actual value); arbiter: Defective test, by the arbiter; contract basis: Contract: 'Remove any leading or trailing hyphens from the result.'
- E3 `test_null_bytes_in_string`: ERROR; NameError: name 'slugize' is not defined. Did you mean: 'slugify'?; arbiter: Defective test, by the arbiter; contract basis: Contract does not specify test code; the test must correctly call the function.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff correctly implements the required slugify behavior by collapsing non-alphanumeric runs, stripping hyphens, and handling edge cases. All acceptance criteria pass and existing tests remain unmodified.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 2 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 2, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates Gates re-run on validated corrections: adversarial_tests (tests test_null_bytes_in_string, test_unicode_combining_marks; 1 of 2 corrected test(s) fail on the unmodified base with an authentic result).

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_unicode_combining_marks | test_defect | The test expects 'e-' but the contract requires stripping trailing hyphens. The combining mark becomes a hyphen, but it is trailing and shou | Contract: 'Remove any leading or trailing hyphens from the result.' |
| test_null_bytes_in_string | test_defect | The test contains a typo: 'slugize' instead of 'slugify', causing a NameError. The intended test is valid but the test code is defective. | Contract does not specify test code; the test must correctly call the function. |

- `adversarial` corrected re-run: candidate OK (7 of 7 methods, each in its own process); base FAILED (4 of 7 methods: FAIL 4); validated=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1393 | 1725 | 0 | 0.006568 | 5.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 3020 | 964 | 0 | 0.005912 | 4.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1655 | 1150 | 0 | 0.001532 | 6.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1653 | 132 | 0 | 0.000615 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1746 | 101 | 0 | 0.000615 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1915 | 406 | 0 | 0.000940 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2183 | 1912 | 0 | 0.002376 | 19.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2355 | 4803 | 0 | 0.005029 | 34.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2606 | 1714 | 0 | 0.002324 | 12.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2809 | 782 | 0 | 0.001547 | 7.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 3424 | 146 | 0 | 0.001159 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1715 | 459 | 0 | 0.000928 | 5.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1942 | 3859 | 0 | 0.013519 | 11.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 2952 | 3498 | 0 | 0.013446 | 10.6s | ok |

Model calls: 14 (0 failed, 0 malformed); tokens in/out/cached 31368/21651/0; Inference USD: 0.05651.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c6c-338c-75c7-8776-99fcc99b3fd0 | SUCCESS | 0 | 0.828s | retained | off | 0.00290879 |
| red-1 | 01a15c6c-8753-75c5-9b8f-a88c55d51fa0 | SUCCESS | 0 | 4.446s | disposable | off | 0.036280969999999996 |
| impl-tests-6 | 01a15c6d-de48-716e-95b2-5bae5e14f7b5 | SUCCESS | 0 | 0.824s | disposable | off | 0.00288296 |
| impl-python-7 | 01a15c6e-0808-70d8-9e16-88fe5cab8877 | SUCCESS | 0 | 0.696s | disposable | off | 0.00171275 |
| verify | 01a15c6e-211c-7504-9256-5ba4faef3ff3 | SUCCESS | 0 | 4.469s | disposable | off | 0.03641967 |
| existing | 01a15c6e-4322-734c-8b33-7d915a9fa6fb | SUCCESS | 0 | 1.832s | disposable | off | 0.01202646 |
| breaker-tests | 01a15c6e-6eff-7310-909e-ef9e243f917c | SUCCESS | 0 | 2.455s | disposable | off | 0.01697791 |
| arbitrate-adversarial-candidate | 01a15c6e-dde0-76f2-a78a-65d4d4631243 | SUCCESS | 0 | 2.416s | disposable | off | 0.01681425 |
| arbitrate-adversarial-base | 01a15c6e-f57b-75f4-a61e-28ab30ae3eff | SUCCESS | 0 | 2.294s | disposable | off | 0.01673398 |

Sandbox operations: 9, total guest duration 20.26s, retained images ['0dd24960-5811-4a1f-849d-526be57f691a'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
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
