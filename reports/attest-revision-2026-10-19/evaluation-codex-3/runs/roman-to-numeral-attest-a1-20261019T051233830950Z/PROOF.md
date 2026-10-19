# Attest Proof Bundle: roman-to-numeral

**Verdict: VERIFIED**  
Run `roman-to-numeral-attest-a1-20261019T051233830950Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:12:33.831594+00:00, finished 2026-10-19T05:20:41.656365+00:00.

**Accept this patch.** All 14 sealed tests pass on the candidate in a fresh sandbox, and 11 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 14 of 14 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.917, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 14 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 11 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 3 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 11 of 14 failed on the unmodified base; 14 of 14 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `8b58cff8-802d-4a89-8370-dc5dae11f33d`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement roman.core.to_roman(n), available through from roman import to_roman, to return the canonical uppercase Roman numeral string for integer values from 1 through 3999 inclusive. Use standard subtractive notation, accept int subclass instances by their integer value, reject non-int inputs without coercion, and raise ValueError for out-of-range integers. Preserve is_roman_numeral and existing tests. Boolean handling and behavior of int subclasses overriding arithmetic or comparison operators are excluded from testing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| roman.to_roman | to_roman(n) | Return a str containing the canonical uppercase Roman numeral for n in 1..3999. Canonical output concatenates thousands (empty, M, MM, MMM), hundreds (empty, C, | ValueError: n is an int or supported int subclass instance with a value less than 1 or greater than 3999, excluding bool from required assertions.; TypeError: n |
| roman.is_roman_numeral | is_roman_numeral(s) | Preserve the existing implementation unchanged: return True exactly when s is a non-empty str and every character of s.upper() belongs to IVXLCDM; otherwise ret |  |

Acceptance criteria:
AC1. 1. from roman import to_roman and from roman import is_roman_numeral continue to succeed.
AC2. 2. For every built-in integer n from 1 through 3999, to_roman(n) returns a str equal to the canonical decimal-place composition specified in the interface contract, with no whitespace or additional characters.
AC3. 3. to_roman(1) == 'I', to_roman(4) == 'IV', and to_roman(9) == 'IX'.
AC4. 4. to_roman(40) == 'XL', to_roman(90) == 'XC', to_roman(400) == 'CD', and to_roman(900) == 'CM'.
AC5. 5. to_roman(1994) == 'MCMXCIV', to_roman(2024) == 'MMXXIV', and to_roman(3999) == 'MMMCMXCIX'.
AC6. 6. Out-of-range built-in integers raise ValueError, including 0, -1, and 4000.
AC7. 7. Non-int inputs raise TypeError without coercion, including '5', 5.0, None, and [1].
AC8. 8. Instances of int subclasses that do not override arithmetic or comparison operators convert identically to equal built-in integers; specifically, PlainInt(49) and an IntEnum member with value 49 return 'XLIX'.
AC9. 9. Supported int subclass instances with out-of-range values raise ValueError; cover values 0, -1, and 4000.
AC10. 10. is_roman_numeral remains unchanged: 'XIV' and 'mmxxiv' return True; '', 'ABC', and 14 return False; noncanonical strings consisting only of Roman numeral letters, such as 'IIII', continue to return True.
AC11. 11. Existing test files remain unchanged and their tests pass.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are mutually consistent and satisfiable by changing only roman/core.py. Canonical conversion and the specified type and range checks can be implemented while preserving is_roman_numeral, public imports, and existing tests unchanged. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `78bb8b03d7cdc7fbe1c8b78e74364e583659750b74f736f83fed4253f326c6a0`, 14 test methods, sealed at 2026-10-19T05:15:19.635521+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (11 of 14 methods: ERROR 11): 11 of 14 methods failing, 3 passing; operation `01a15295-ed79-7786-bacb-fe6d56e50e68`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsRomanNumeral.test_accepts_noncanonical_sequence_of_roman_letters | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_accepts_uppercase_and_lowercase_roman_letters | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_rejects_empty_invalid_and_non_string_inputs | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_builtin_integers_above_range_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_builtin_integers_below_range_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_enum_converts_by_value | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_enum_out_of_range_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_multi_place_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_non_int_inputs_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_plain_int_subclass_converts_by_value | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_plain_int_subclass_out_of_range_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_tens_and_hundreds_subtractive_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_unit_subtractive_examples | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,14 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    """Return the canonical Roman numeral for an integer from 1 through 3999."""
+    if not isinstance(n, int):
+        raise TypeError("n must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("n must be between 1 and 3999")
+
+    thousands = ("", "M", "MM", "MMM")
+    hundreds = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
+    tens = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
+    units = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
+    return thousands[n // 1000] + hundreds[n // 100 % 10] + tens[n // 10 % 10] + units[n % 10]
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (11 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (14 of 14 methods, each in its own process). Operation `01a15299-4eb5-7741-8c62-d5f95889ff9c`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15299-66e7-729c-92ea-31de77f3e5b8`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.917 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (8 of 8 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-9330f816df | roman/core.py | 11 | remove `not` | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_unit_ | 01a15299-74ae-72f6-b8fe-a70295c99f09 |
| m02-5893a688bd | roman/core.py | 12 | raise -> pass | survived |  | 01a15299-750a-75cb-a86e-48cd967b08d2 |
| m03-d248b9433d | roman/core.py | 13 | 3999 -> 4000 | killed | test_sealed.TestToRoman.test_builtin_integers_above_range_raise_value_error, test_sealed.TestToRoman.test_plain_int_subc | 01a15299-74c7-7171-a1be-acb2e8a721fc |
| m04-e52107ad8b | roman/core.py | 13 | LtE -> Lt | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_multi | 01a15299-74e1-7691-99b4-a9b8e37c87bc |
| m05-5491f3382d | roman/core.py | 14 | raise -> pass | killed | test_sealed.TestToRoman.test_builtin_integers_below_range_raise_value_error, test_sealed.TestToRoman.test_builtin_intege | 01a15299-74c2-770b-982d-864a02f4f57e |
| m06-520ebeee11 | roman/core.py | 20 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_unit_ | 01a15299-74c3-75e6-ac23-ef5cdb1eefdd |
| m07-ca6807d917 | roman/core.py | 20 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_tens_ | 01a15299-7524-7514-b38b-4fc580bea493 |
| m08-64f6b6ae7d | roman/core.py | 20 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_multi | 01a15299-74dc-7690-8402-a0cf6d9b59de |
| m09-24bd0fa661 | roman/core.py | 20 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_tens_ | 01a15299-8e58-717a-8c91-d202c6ba73ff |
| m10-e01fa9265a | roman/core.py | 20 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_tens_ | 01a15299-8f37-7651-a84d-a166ba4d0de8 |
| m11-7fb0c2d731 | roman/core.py | 20 | Add -> Sub | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_unit_ | 01a15299-8f2e-758e-948c-d9365dcf1e84 |
| m12-fbbf73e49f | roman/core.py | 20 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_builtin_integer_matches_decimal_place_composition, test_sealed.TestToRoman.test_tens_ | 01a15299-8f3d-71cc-aa63-373a975ecd48 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `de27782c5b598a63374eef3d805f48044c4df0540b194ea9fcb156483ea8875c`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a1529a-8e75-75e4-976f-7c3b9fea44ac`. Notes: Targets int subclass behavior across subtractive places, rejection of additional non-int types, and validator casing and composition edge cases.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(n, int)` accepts supported integer subclasses and rejects other types, `if not 1 <= n <= 3999` enforces the range, and the decimal-place lookup tables produce canonical subtractive numerals. Only to_roman changes, preserving the validator and tests; observed outputs report both existing tests passing and successful contract checks.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10405 | 1029 | 0 | - | 69.2s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11329 | 100 | 0 | - | 35.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10515 | 2187 | 7168 | - | 44.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10513 | 124 | 7168 | - | 39.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 21476 | 429 | 17664 | - | 34.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11062 | 90 | 7168 | - | 72.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11203 | 550 | 7168 | - | 34.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11713 | 124 | 7168 | - | 27.9s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10664 | 2000 | 7040 | - | 58.2s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11339 | 119 | 0 | - | 18.7s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 120219/6752/60544; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15293-834b-768b-85d4-7ef885ca67c0 | SUCCESS | 0 | 0.839s | retained | off | 0.00285753 |
| red-1 | 01a15295-ed79-7786-bacb-fe6d56e50e68 | SUCCESS | 0 | 3.709s | disposable | off | 0.03043087 |
| impl-tests-3 | 01a15298-43b8-71d9-8369-f9b199adcfa6 | SUCCESS | 0 | 0.817s | disposable | off | 0.00289545 |
| impl-python-4 | 01a15298-d4c1-7715-b381-c4af2e8f6230 | SUCCESS | 0 | 0.726s | disposable | off | 0.00154202 |
| verify | 01a15299-4eb5-7741-8c62-d5f95889ff9c | SUCCESS | 0 | 3.549s | disposable | off | 0.02881614 |
| existing | 01a15299-66e7-729c-92ea-31de77f3e5b8 | SUCCESS | 0 | 1.453s | disposable | off | 0.00877731 |
| mutant-m01-9330f816df | 01a15299-74ae-72f6-b8fe-a70295c99f09 | SUCCESS | 0 | 3.416s | disposable | off | 0.02716009 |
| mutant-m03-d248b9433d | 01a15299-74c7-7171-a1be-acb2e8a721fc | SUCCESS | 0 | 3.263s | disposable | off | 0.025301229999999997 |
| mutant-m02-5893a688bd | 01a15299-750a-75cb-a86e-48cd967b08d2 | SUCCESS | 0 | 3.265s | disposable | off | 0.025294039999999997 |
| mutant-m04-e52107ad8b | 01a15299-74e1-7691-99b4-a9b8e37c87bc | SUCCESS | 0 | 3.265s | disposable | off | 0.02521653 |
| mutant-m05-5491f3382d | 01a15299-74c2-770b-982d-864a02f4f57e | SUCCESS | 0 | 3.265s | disposable | off | 0.02553758 |
| mutant-m07-ca6807d917 | 01a15299-7524-7514-b38b-4fc580bea493 | SUCCESS | 0 | 3.591s | disposable | off | 0.02793836 |
| mutant-m08-64f6b6ae7d | 01a15299-74dc-7690-8402-a0cf6d9b59de | SUCCESS | 0 | 3.348s | disposable | off | 0.02635766 |
| mutant-m06-520ebeee11 | 01a15299-74c3-75e6-ac23-ef5cdb1eefdd | SUCCESS | 0 | 3.505s | disposable | off | 0.02752495 |
| mutant-m09-24bd0fa661 | 01a15299-8e58-717a-8c91-d202c6ba73ff | SUCCESS | 0 | 3.49s | disposable | off | 0.02848386 |
| mutant-m10-e01fa9265a | 01a15299-8f37-7651-a84d-a166ba4d0de8 | SUCCESS | 0 | 3.571s | disposable | off | 0.02845124 |
| mutant-m11-7fb0c2d731 | 01a15299-8f2e-758e-948c-d9365dcf1e84 | SUCCESS | 0 | 3.537s | disposable | off | 0.02814331 |
| mutant-m12-fbbf73e49f | 01a15299-8f3d-71cc-aa63-373a975ecd48 | SUCCESS | 0 | 3.494s | disposable | off | 0.02778768 |
| breaker-tests | 01a1529a-8e75-75e4-976f-7c3b9fea44ac | SUCCESS | 0 | 2.549s | disposable | off | 0.01910336 |

Sandbox operations: 19, total guest duration 54.652s, retained images ['8b58cff8-802d-4a89-8370-dc5dae11f33d'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception raised in the code under test is never overridden (only a test-internal crash or a timeout may be corrected). The classification itself remains a model judgement.
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
