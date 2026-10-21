# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: VERIFIED**  
Run `slugkit-regression-001-attest-a1-20261021T030502372330Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:05:02.373822+00:00, finished 2026-10-21T03:07:53.893192+00:00.

**Accept this patch.** All 23 sealed tests pass on the candidate in a fresh sandbox, and 12 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 23 of 23 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No mutable sites were found on the changed lines, so only the tests written after the patch test it structurally (E2, E3). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4). 2 of the tests written after the patch failed as written and were corrected by the arbiter; the correction kept every test method, changed only the failing ones, passes on the candidate and discriminates (2 of 2 corrected test(s) fail on the unmodified base with an authentic result), and the gate was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; mutation gate: no mutable sites were generated on the changed lines; only the adversarial suite (7 tests) tests the patch structurally; arbitration (validated corrections re-run their gates): all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (2 of 2 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 12 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 7 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 11 sealed test(s) which already passed on the base say anything about the change (E1).
- That the mutation check tested anything: no mutable sites were found on the changed lines (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, but which side was wrong is a model judgement; the original tests and results are preserved (E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 12 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | no mutable sites on the changed lines; the adversarial suite (7 tests) carries the load |
| E3 | Tests written after the patch | pass | bound | 2 of 7 failed as written (test_unicode_combining_accents, test_long_string_performance); 2 test(s) corrected by the arbiter and validated (2 of 2 corrected test(s) fail on the unmodified base with an authentic result); the corrected module passes (OK (7 of 7 methods, each in its own process)) |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (2 of 2 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `5014e4c9-786f-45db-8776-2dfd07ee9271`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix the regression in slugkit.slugify so that it lowercases the input, collapses any maximal run of non-ASCII-alphanumeric characters into a single hyphen, strips leading and trailing hyphens, returns an empty string when the input contains no ASCII letters or digits, treats non-ASCII letters as separators, raises TypeError for non-string inputs, and returns a string. The existing tests must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugify | slugify(text: str) -> str | Returns a lowercase ASCII slug derived from text. The algorithm: convert text to lowercase; replace each maximal contiguous sequence of characters that are not  | TypeError: raised if text is not an instance of str. |

Acceptance criteria:
AC1. slugify('Hello--World') == 'hello-world'
AC2. slugify('a -- b') == 'a-b'
AC3. slugify('one , two ; three') == 'one-two-three'
AC4. slugify('x___y') == 'x-y'
AC5. slugify('end!') == 'end'
AC6. slugify('  padded  ') == 'padded'
AC7. slugify('--both--') == 'both'
AC8. slugify('(parens)') == 'parens'
AC9. slugify('') == ''
AC10. slugify('!!!') == ''
AC11. slugify('   ') == ''
AC12. slugify('Hello World') == 'hello-world'
AC13. slugify('already-a-slug') == 'already-a-slug'
AC14. slugify('Python 3') == 'python-3'
AC15. slugify('MiXeD CaSe 42') == 'mixed-case-42'
AC16. slugify('café crème') == 'caf-cr-me'
AC17. slugify('日本語') == ''
AC18. slugify(None) raises TypeError
AC19. slugify(3) raises TypeError
AC20. slugify(2.5) raises TypeError
AC21. slugify(['a']) raises TypeError
AC22. slugify(b'bytes') raises TypeError
AC23. The return value is always a str instance.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. All authoritative task criteria (TC1–TC6) are mutually consistent. The existing tests in tests/ align with TC4 and do not conflict with TC1–TC3, TC5–TC6. The regression in slugkit/core.py can be fixed by implementing the specified algorithm (lowercase, collapse maximal runs of non-ASCII-alphanumerics to a single hyphen, strip leading/trailing hyphens, return empty string when no ASCII alnum present, treat non-ASCII letters as separators, raise TypeError for non-strings) without violating any constraints. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `2ff7f4d7bb2e9a6578a40394b5793e3e0aac7c32377e42ac111affa3c7365be5`, 23 test methods, sealed at 2026-10-21T03:05:43.588291+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 23 methods: FAIL 12): 12 of 23 methods failing, 11 passing; operation `01a15c6b-f7ae-701b-ac88-13156c72fbdf`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSlugifyAcceptance.test_ac10_only_punctuation | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac11_only_spaces | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac12_hello_world | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac13_already_slug | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac14_python_3 | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac15_mixed_case_42 | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac16_accented_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac17_japanese_returns_empty | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac18_none_raises_typeerror | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac19_int_raises_typeerror | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac1_hello_world_double_hyphen | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac20_float_raises_typeerror | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac21_list_raises_typeerror | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac22_bytes_raises_typeerror | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac23_return_is_str | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac2_space_dash_space | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac3_comma_semicolon | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac4_underscores | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac5_trailing_exclamation | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac6_padded_spaces | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac7_both_sides_hyphens | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac8_parens | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_ac9_empty_string | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 9 implementer turn(s).

```diff
--- a/slugkit/core.py
+++ b/slugkit/core.py
@@ -2,11 +2,16 @@
 
 import re
 
-_NOT_ALNUM = re.compile(r"[^a-z0-9]")
+_NOT_ALNUM = re.compile(r"[^a-z0-9]+")
 
 
 def slugify(text):
-    """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
+    """Return a lowercase ASCII slug derived from text."""
     if not isinstance(text, str):
         raise TypeError("text must be a str")
-    return _NOT_ALNUM.sub("-", text.lower())
+    text = text.lower()
+    # Replace any sequence of non-alnum characters with a single hyphen
+    slug = _NOT_ALNUM.sub("-", text)
+    # Remove leading/trailing hyphens
+    slug = slug.strip("-")
+    return slug
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (8 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| slugkit/core.py | 5 | dynamic code or decoded payload | _NOT_ALNUM = re.compile(r"[^a-z0-9]+") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a15c6d-3d81-71ce-b3f2-1efe5a3af29f`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a15c6d-5f67-765e-87c1-d7da70bf43c4`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | no mutable sites on the changed lines; the adversarial suite (7 tests) carries the load |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (7 of 7 methods, each in its own process) on the corrected module (2 test(s) corrected, validated: 2 of 2 corrected test(s) fail on the unmodified base with an authentic result); original failures kept in E3 |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 0 generated, 0 evaluated: 0 killed, 0 survived, 0 unknown; mutation score - (threshold 0.5).

(none)

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `c5e881e28387de2d91019e91ca875360b1b60af3acc10b7af989cc81872eecce`): FAILED (2 of 7 methods: FAIL 2); binding FAILED; operation `01a15c6d-89f2-713a-9bf5-d53d937dbd9e`. Notes: Targeted edge cases: combining accents, multiple separator runs, leading/trailing hyphens, digits-only, long input, return type, non-ASCII letter as separator.

| Failing adversarial test | Outcome |
| --- | --- |
| test_unicode_combining_accents | FAIL |
| test_long_string_performance | FAIL |
Corrected adversarial module (E6): `arbitration/adversarial_corrected.py` sha256 `8049f82958bc0caad01d6a5451a4816536a8e4cd3332d4e8c732844d92a7add1`; corrected tests test_long_string_performance, test_unicode_combining_accents; on the candidate OK (7 of 7 methods, each in its own process); validated: 2 of 2 corrected test(s) fail on the unmodified base with an authentic result; operation `01a15c6d-e4f8-7558-9e20-e6dd7c5f6aef`. The adversarial gate was re-run on it.
Adversarial authoring: 1 attempt(s).

### Counterexamples
- E3 `test_unicode_combining_accents`: FAIL; AssertionError: 'e' != ''; first `'e'` vs second `''` (the test's argument order decides which is the actual value); arbiter: Defective test, by the arbiter; contract basis: Contract: 'lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits returns empty string.'
- E3 `test_long_string_performance`: FAIL; AssertionError: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[9955 chars]bbbb' != 'a-b'; first `'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa[9955 chars]bbbb'` vs second `'a-b'` (the test's argument order decides which is the actual value); arbiter: Defective test, by the arbiter; contract basis: Contract: 'every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen.' ASCII letters are kept as-is.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff correctly fixes the regression by updating the regex to match sequences of non-alphanumeric characters and adding hyphen stripping, which satisfies all acceptance criteria. The existing tests pass and no unauthorized changes were made.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (2 of 2 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 2, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates Gates re-run on validated corrections: adversarial_tests (tests test_long_string_performance, test_unicode_combining_accents; 2 of 2 corrected test(s) fail on the unmodified base with an authentic result).

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_unicode_combining_accents | test_defect | The test expects empty string for input 'e\u0301', but the contract specifies that ASCII letters/digits are kept. The input contains an ASCI | Contract: 'lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exact |
| test_long_string_performance | test_defect | The test expects the runs of ASCII letters 'a' and 'b' to be collapsed to a single character each, but the contract only requires collapsing | Contract: 'every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen.' ASCII |

- `adversarial` corrected re-run: candidate OK (7 of 7 methods, each in its own process); base FAILED (5 of 7 methods: FAIL 5); validated=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1393 | 1985 | 0 | 0.007348 | 6.6s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 2961 | 2909 | 0 | 0.011688 | 9.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1594 | 1378 | 0 | 0.001718 | 9.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1585 | 126 | 0 | 0.000589 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1676 | 96 | 0 | 0.000589 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1847 | 1577 | 0 | 0.001973 | 22.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2072 | 1134 | 0 | 0.001642 | 8.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2158 | 753 | 0 | 0.001325 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2312 | 1205 | 0 | 0.001778 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2605 | 121 | 0 | 0.000890 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 2812 | 808 | 0 | 0.001571 | 8.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 3349 | 185 | 0 | 0.001171 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1737 | 412 | 0 | 0.000892 | 4.8s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2018 | 1316 | 0 | 0.005966 | 4.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 2945 | 4051 | 0 | 0.015098 | 12.1s | ok |

Model calls: 15 (0 failed, 0 malformed); tokens in/out/cached 33064/18056/0; Inference USD: 0.054238.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c6b-8815-7754-8484-0c8dc18d2e2a | SUCCESS | 0 | 0.848s | retained | off | 0.00286867 |
| red-1 | 01a15c6b-f7ae-701b-ac88-13156c72fbdf | SUCCESS | 0 | 5.169s | disposable | off | 0.04301186 |
| impl-tests-7 | 01a15c6c-f5ad-70e8-aa96-0b848ee1329b | SUCCESS | 0 | 0.788s | disposable | off | 0.00290858 |
| impl-python-8 | 01a15c6d-2448-752d-9ad5-625868c88b74 | SUCCESS | 0 | 0.862s | disposable | off | 0.0016255 |
| verify | 01a15c6d-3d81-71ce-b3f2-1efe5a3af29f | SUCCESS | 0 | 5.211s | disposable | off | 0.04273364 |
| existing | 01a15c6d-5f67-765e-87c1-d7da70bf43c4 | SUCCESS | 0 | 1.799s | disposable | off | 0.01202662 |
| breaker-tests | 01a15c6d-89f2-713a-9bf5-d53d937dbd9e | SUCCESS | 0 | 2.342s | disposable | off | 0.01712363 |
| arbitrate-adversarial-candidate | 01a15c6d-e4f8-7558-9e20-e6dd7c5f6aef | SUCCESS | 0 | 2.363s | disposable | off | 0.01684426 |
| arbitrate-adversarial-base | 01a15c6d-ff0f-7646-93ea-d0592faa6fc4 | SUCCESS | 0 | 2.372s | disposable | off | 0.01706199 |

Sandbox operations: 9, total guest duration 21.754s, retained images ['5014e4c9-786f-45db-8776-2dfd07ee9271'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
