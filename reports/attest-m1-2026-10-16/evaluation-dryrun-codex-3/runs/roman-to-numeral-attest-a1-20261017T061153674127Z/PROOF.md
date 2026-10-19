# Attest Proof Bundle: roman-to-numeral

**Verdict: NEEDS HUMAN**  
Run `roman-to-numeral-attest-a1-20261017T061153674127Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T06:11:53.674297+00:00, finished 2026-10-17T06:23:13.686278+00:00.

**Hold this patch.** A test written after the patch found an input the implementation handles wrongly. The arbiter classified it as an implementation bug, so this is a defect in the candidate, not in the test. The hold stands until a human decides.

Key evidence (E3): test_int_subclass_with_overridden_arithmetic: AssertionError: subclass arithmetic was used



What to do: Read the counterexample: input, actual result and the arbiter's contract basis. Fix the implementation and run the task again, or reject the patch.

Reasons: adversarial suite binding failed: child process nonzero exit: test_int_subclass_with_overridden_arithmetic exit 1, test_int_subclass_with_overridden_comparisons exit 1, test_out_of_range_subclass_with_misleading_comparisons exit 1; model-written adversarial tests failed: 3 of 9 (test_breaker.BreakerTests.test_int_subclass_with_overridden_arithmetic, test_breaker.BreakerTests.test_int_subclass_with_overridden_comparisons, test_breaker.BreakerTests.test_out_of_range_subclass_with_misleading_comparisons); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): 3 failing test(s) indicate a real implementation bug; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 18 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 3 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 5 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 18 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 6 of 9 pass; 3 failing: test_int_subclass_with_overridden_arithmetic, test_int_subclass_with_overridden_comparisons, test_out_of_range_subclass_with_misleading_comparisons; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | 3 failing test(s) indicate a real implementation bug; human review required |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `84ca2b09acba7164df7a305c5cefdd6c18c821174680c4799f6ff84d69600d24`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `71c15841-17ca-4ef4-b747-d431f0396cb2`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.2.0 revision `b0b50de772bba0ed` (33 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/5` sha256 `8511520ba75a7690`, per-test child `fb466d37f748f9ef`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement roman.core.to_roman(n), available through from roman import to_roman, to convert integers from 1 through 3999 inclusive into canonical uppercase Roman numeral strings using subtractive notation. Reject out-of-range integers with ValueError and non-integer inputs with TypeError. Resolve the ambiguous boolean wording by rejecting bool values; accept other int instances, including int subclasses. Preserve is_roman_numeral and the existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| roman.to_roman | to_roman(n) | For isinstance(n, int) and not isinstance(n, bool), require 1 <= n <= 3999 and return its canonical uppercase Roman numeral as a str. Thousands use '', M, MM, M | TypeError: n is not an int instance, or n is a bool; type validation takes precedence over range validation.; ValueError: n is an accepted integer type but is l |
| roman.is_roman_numeral | is_roman_numeral(s) | Preserve the existing implementation: return True exactly when s is a non-empty str and every character in s.upper() belongs to IVXLCDM. This is a letter-member | Ordinary non-string inputs return False rather than raising an exception. |

Acceptance criteria:
1. 1. Both to_roman and is_roman_numeral remain importable from roman.
2. 2. For every integer from 1 through 3999, to_roman returns the exact string defined by the decimal-place tables in the interface contract.
3. 3. to_roman(1) == 'I', to_roman(4) == 'IV', and to_roman(9) == 'IX'.
4. 4. to_roman(40) == 'XL', to_roman(90) == 'XC', to_roman(400) == 'CD', and to_roman(900) == 'CM'.
5. 5. to_roman(2024) == 'MMXXIV', to_roman(3999) == 'MMMCMXCIX', and to_roman(1994) == 'MCMXCIV'.
6. 6. Every valid conversion returns a non-empty str containing only uppercase IVXLCDM letters, with no whitespace.
7. 7. Integers outside the inclusive range raise ValueError, including 0, -1, 4000, and arbitrarily large positive or negative integers.
8. 8. Non-int inputs raise TypeError, including '5', 5.0, None, and [1]; neither numeric strings nor integral floats are coerced.
9. 9. True and False raise TypeError. Instances of an ordinary int subclass follow the same conversion and range rules as int.
10. 10. Calling to_roman(n=4) returns 'IV', preserving the named parameter n.
11. 11. is_roman_numeral retains its existing behavior: 'XIV', 'mmxxiv', and 'IIII' return True; '', 'ABC', and 14 return False.
12. 12. The implementation of is_roman_numeral and all existing test files remain unchanged.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `b38b3ecca30014bc07b59b104f7fdb352cb52a196c6dd550f60f17ab95bb9cc0`, 23 test methods, sealed at 2026-10-17T06:16:18.518419+00:00 by `gpt-6-sol`; attempts: 2.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 23 methods: ERROR 18): 18 of 23 methods failing, 5 passing; operation `01a14880-f8b4-759d-b1cc-024c22a17b1e`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsRomanNumeral.test_empty_string_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_membership_check_accepts_noncanonical_roman_letters | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_nonstring_is_rejected_without_raising | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_other_letters_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_roman_letter_strings_are_accepted_case_insensitively | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_4000_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_arbitrarily_large_integers_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_bool_values_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_every_valid_result_is_a_nonempty_uppercase_roman_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_hundreds_subtractive_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_subclass_converts_normally | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_integral_float_raises_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_list_raises_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_multi_place_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_named_n_argument | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_negative_one_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_none_raises_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_numeric_string_raises_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_out_of_range_int_subclass_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_tens_subtractive_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_unit_subtractive_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_zero_raises_value_error | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,20 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    """Convert an integer from 1 through 3999 to a Roman numeral."""
+    if not isinstance(n, int) or isinstance(n, bool):
+        raise TypeError("n must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("n must be between 1 and 3999")
+
+    thousands = ("", "M", "MM", "MMM")
+    hundreds = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
+    tens = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
+    units = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
+
+    return (
+        thousands[n // 1000]
+        + hundreds[n // 100 % 10]
+        + tens[n // 10 % 10]
+        + units[n % 10]
+    )
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (17 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a14884-9c44-72e8-8d68-a4a0f5dcb998`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14884-ce21-73e0-9e3f-629003a50d4f`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (3 of 9 methods: ERROR 2, FAIL 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-8b96a158a5 | roman/core.py | 11 | remove `not` | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_unit_subtractive_exa | 01a14884-f468-7155-9112-b3b2ce2bcd43 |
| m02-8626b43250 | roman/core.py | 12 | raise -> pass | killed | test_sealed.TestToRoman.test_bool_values_raise_type_error | 01a14884-f46d-7324-9527-b78beffdab2d |
| m03-df975b8854 | roman/core.py | 13 | 3999 -> 4000 | killed | test_sealed.TestToRoman.test_4000_raises_value_error, test_sealed.TestToRoman.test_out_of_range_int_subclass_raises_valu | 01a14884-f448-700a-9d37-f7377c940353 |
| m04-e8bbc2bade | roman/core.py | 13 | LtE -> Lt | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_multi_place_examples | 01a14884-f4b3-7762-80a7-822b93b8d282 |
| m05-cc98b09a36 | roman/core.py | 14 | raise -> pass | killed | test_sealed.TestToRoman.test_zero_raises_value_error, test_sealed.TestToRoman.test_negative_one_raises_value_error, test | 01a14884-f47a-75a7-be55-bc66971b1ce3 |
| m06-8df3320f37 | roman/core.py | 22 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_unit_subtractive_exa | 01a14884-f48f-75a5-ba9a-75c68de69b61 |
| m07-8c3b66a392 | roman/core.py | 23 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_hundreds_subtractive | 01a14884-f480-75ec-8103-654d5ca72ac0 |
| m08-79f5e1749c | roman/core.py | 23 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_multi_place_examples | 01a14884-f4a4-76cf-96ca-b4ab3072abbe |
| m09-2d2452ea25 | roman/core.py | 24 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_tens_subtractive_exa | 01a14885-1126-73ff-b3df-6be8f031db49 |
| m10-519b6568c9 | roman/core.py | 24 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_hundreds_subtractive | 01a14885-1cb1-77b4-ac4c-fd8574622ef0 |
| m11-4502f5c143 | roman/core.py | 22 | Add -> Sub | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_unit_subtractive_exa | 01a14885-1eb3-7035-bf4a-9e613f57cbda |
| m12-0a9b8d7bfd | roman/core.py | 25 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_value_matches_decimal_place_tables, test_sealed.TestToRoman.test_tens_subtractive_exa | 01a14885-2001-7091-b536-d89d1f078a78 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `87535cff93c85b568daa8e165decb3d15b35f14a07d13d8ccaf8704fac646fbe`): FAILED (3 of 9 methods: ERROR 2, FAIL 1); binding FAILED; operation `01a14885-dda8-772b-bff3-c0841dc6d69a`. Notes: Targets int subclasses with overridden operators, numeric lookalikes, and Unicode and non-string membership edge cases.

| Failing adversarial test | Outcome |
| --- | --- |
| test_int_subclass_with_overridden_arithmetic | FAIL |
| test_int_subclass_with_overridden_comparisons | ERROR |
| test_out_of_range_subclass_with_misleading_comparisons | ERROR |

### Counterexamples
- E3 `test_int_subclass_with_overridden_arithmetic`: FAIL; AssertionError: subclass arithmetic was used; arbiter: Implementation bug, by the arbiter; contract basis: The interface accepts int instances other than bool, including int subclasses, and requires the canonical numeral for their integer value. It does not exclude subclasses that override arithmetic.
- E3 `test_int_subclass_with_overridden_comparisons`: ERROR; ValueError: n must be between 1 and 3999; arbiter: Implementation bug, by the arbiter; contract basis: Accepted int instances from 1 through 3999 must produce the specified canonical numeral. The interface does not restrict subclass acceptance to those with inherited comparison methods.
- E3 `test_out_of_range_subclass_with_misleading_comparisons`: ERROR; IndexError: tuple index out of range; arbiter: Implementation bug, by the arbiter; contract basis: An accepted integer type whose value is below 1 or above 3999 must raise ValueError, including int subclasses.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `if not isinstance(n, int) or isinstance(n, bool)` enforces the contracted type rules, `if not 1 <= n <= 3999` enforces the range, and the four decimal-place tables produce canonical subtractive Roman strings. Only the to_roman stub changes, preserving exports, is_roman_numeral, and tests; observed test outputs report two existing tests passing and successful checks of all 3999 conversions and error cases.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
3 failing test(s) indicate a real implementation bug; human review required (mode: advisory). Classifications: {'implementation_bug': 3, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_int_subclass_with_overridden_arithmetic | implementation_bug | The input is an accepted int instance with value 49. The candidate invokes its overridden arithmetic and raises AssertionError instead of re | The interface accepts int instances other than bool, including int subclasses, and requires the canonical numeral for their integer value. I |
| test_int_subclass_with_overridden_comparisons | implementation_bug | The input is an accepted int instance with value 58. The candidate lets overridden comparisons reject that valid value, raising ValueError i | Accepted int instances from 1 through 3999 must produce the specified canonical numeral. The interface does not restrict subclass acceptance |
| test_out_of_range_subclass_with_misleading_comparisons | implementation_bug | Overridden comparisons bypass the candidate's range check. The value 4000 then causes IndexError, and the value 0 would return an empty stri | An accepted integer type whose value is below 1 or above 3999 must raise ValueError, including int subclasses. |

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10226 | 967 | 0 | - | 35.7s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10269 | 1829 | 0 | - | 41.9s | ok |
| codex_gateway:gpt-6-sol | seal | seal-2 | medium | 10356 | 1798 | 7040 | - | 40.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10290 | 106 | 7168 | - | 25.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 21032 | 159 | 17408 | - | 50.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10566 | 409 | 7168 | - | 52.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10960 | 101 | 7168 | - | 35.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11096 | 575 | 7168 | - | 27.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 11622 | 121 | 0 | - | 23.6s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10498 | 2001 | 7040 | - | 38.7s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11217 | 142 | 0 | - | 43.1s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 11882 | 445 | 0 | - | 54.7s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 140014/8653/60160; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1487d-19ef-72d5-be1c-5af9378bec20 | SUCCESS | 0 | 0.793s | retained | off | 0.00279972 |
| red-1 | 01a1487e-66aa-70dc-a2ff-a25111579aa5 | SUCCESS | 0 | 124.01s | disposable | off | 0.040543169999999996 |
| red-2 | 01a14880-f8b4-759d-b1cc-024c22a17b1e | SUCCESS | 0 | 5.537s | disposable | off | 0.04273936000000001 |
| impl-tests-4 | 01a14883-9d5e-7633-9158-3843fb1d4726 | SUCCESS | 0 | 1.288s | disposable | off | 0.00289536 |
| impl-python-5 | 01a14884-27b6-7193-a939-bac657c92352 | SUCCESS | 0 | 2.141s | disposable | off | 0.00115418 |
| verify | 01a14884-9c44-72e8-8d68-a4a0f5dcb998 | SUCCESS | 0 | 9.129s | disposable | off | 0.042518410000000006 |
| existing | 01a14884-ce21-73e0-9e3f-629003a50d4f | SUCCESS | 0 | 5.541s | disposable | off | 0.00871098 |
| mutant-m01-8b96a158a5 | 01a14884-f468-7155-9112-b3b2ce2bcd43 | SUCCESS | 0 | 4.762s | disposable | off | 0.03928568 |
| mutant-m02-8626b43250 | 01a14884-f46d-7324-9527-b78beffdab2d | SUCCESS | 0 | 4.835s | disposable | off | 0.039736640000000004 |
| mutant-m03-df975b8854 | 01a14884-f448-700a-9d37-f7377c940353 | SUCCESS | 0 | 4.807s | disposable | off | 0.03979983 |
| mutant-m04-e8bbc2bade | 01a14884-f4b3-7762-80a7-822b93b8d282 | SUCCESS | 0 | 4.775s | disposable | off | 0.03944928 |
| mutant-m05-cc98b09a36 | 01a14884-f47a-75a7-be55-bc66971b1ce3 | SUCCESS | 0 | 4.793s | disposable | off | 0.039529230000000005 |
| mutant-m06-8df3320f37 | 01a14884-f48f-75a5-ba9a-75c68de69b61 | SUCCESS | 0 | 4.826s | disposable | off | 0.040047250000000006 |
| mutant-m07-8c3b66a392 | 01a14884-f480-75ec-8103-654d5ca72ac0 | SUCCESS | 0 | 4.802s | disposable | off | 0.03966427 |
| mutant-m08-79f5e1749c | 01a14884-f4a4-76cf-96ca-b4ab3072abbe | SUCCESS | 0 | 4.85s | disposable | off | 0.04024399000000001 |
| mutant-m09-2d2452ea25 | 01a14885-1126-73ff-b3df-6be8f031db49 | SUCCESS | 0 | 4.713s | disposable | off | 0.039583070000000005 |
| mutant-m10-519b6568c9 | 01a14885-1cb1-77b4-ac4c-fd8574622ef0 | SUCCESS | 0 | 4.721s | disposable | off | 0.039781000000000004 |
| mutant-m11-4502f5c143 | 01a14885-1eb3-7035-bf4a-9e613f57cbda | SUCCESS | 0 | 4.814s | disposable | off | 0.039920290000000004 |
| mutant-m12-0a9b8d7bfd | 01a14885-2001-7091-b536-d89d1f078a78 | SUCCESS | 0 | 4.819s | disposable | off | 0.040048490000000006 |
| breaker-tests | 01a14885-dda8-772b-bff3-c0841dc6d69a | SUCCESS | 0 | 2.704s | disposable | off | 0.02065595 |

Sandbox operations: 20, total guest duration 208.66s, retained images ['71c15841-17ca-4ef4-b747-d431f0396cb2'].

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
