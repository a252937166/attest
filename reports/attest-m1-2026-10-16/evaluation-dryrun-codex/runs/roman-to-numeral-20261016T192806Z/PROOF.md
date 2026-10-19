# Attest Proof Bundle: roman-to-numeral

**Verdict: NEEDS HUMAN**  
Run `roman-to-numeral-20261016T192806Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:28:06.836259+00:00, finished 2026-10-16T19:43:51.974538+00:00.

Reasons: adversarial suite binding failed: child process nonzero exit: test_valid_int_subclass_with_overridden_comparisons exit 1, test_zero_int_subclass_with_overridden_comparisons exit 1, test_upper_bound_int_subclass_with_overridden_comparisons exit 1, test_int_subclass_with_overridden_floor_division exit 1, test_int_subclass_with_overrid; model-written adversarial tests failed: 5 of 8 (test_breaker.TestAdversarialRomanConversion.test_valid_int_subclass_with_overridden_comparisons, test_breaker.TestAdversarialRomanConversion.test_zero_int_subclass_with_overridden_comparisons, test_breaker.TestAdversarialRomanConversion.test_upper_bound_int_subclass_with_overridden_comparisons, test); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): 5 failing test(s) indicate a real implementation bug; human review required

## 1. Frozen task
Task `roman-to-numeral`, spec digest `84ca2b09acba7164df7a305c5cefdd6c18c821174680c4799f6ff84d69600d24`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `c8f5ca77-1910-44d8-988f-2e401b921e3a`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement roman.to_roman(n) in roman/core.py to return the canonical uppercase Roman numeral string for integers from 1 through 3999 inclusive, using standard subtractive notation. Reject out-of-range integers with ValueError and non-integer inputs with TypeError without coercion. To resolve the wording about booleans, treat bool as invalid; accept other int instances, including int subclasses. Preserve is_roman_numeral, existing exports, and existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| roman.to_roman | to_roman(n) | For an int instance other than bool with 1 <= n <= 3999, return a str containing its canonical uppercase Roman numeral, with no whitespace or separators. Form t | TypeError: n is not an instance of int, or n is a bool; do not coerce strings, floats, or other values.; ValueError: n is an accepted integer type but is less t |
| roman.is_roman_numeral | is_roman_numeral(s) | Preserve the existing implementation exactly: return whether s is a non-empty str whose uppercase characters all belong to IVXLCDM. This checks allowed letters, | Ordinary non-string inputs return False rather than raising an exception. |

Acceptance criteria:
1. 1. from roman import to_roman succeeds, and to_roman is also available from roman.core.
2. 2. to_roman(1) == 'I', to_roman(4) == 'IV', and to_roman(9) == 'IX'.
3. 3. to_roman(40) == 'XL', to_roman(90) == 'XC', to_roman(400) == 'CD', and to_roman(900) == 'CM'.
4. 4. to_roman(5) == 'V', to_roman(10) == 'X', to_roman(50) == 'L', to_roman(100) == 'C', to_roman(500) == 'D', and to_roman(1000) == 'M'.
5. 5. to_roman(2024) == 'MMXXIV', to_roman(1994) == 'MCMXCIV', and to_roman(3999) == 'MMMCMXCIX'.
6. 6. For every integer n in 1..3999, the result equals the concatenation of the indexed thousands table ['', 'M', 'MM', 'MMM'], hundreds table ['', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM'], tens table ['', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC'], and units table ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'], indexed by the corresponding decimal digits of n.
7. 7. Every valid input returns a non-empty str containing only uppercase Roman numeral letters, with no whitespace or separators.
8. 8. Integers outside 1..3999 raise ValueError, including 0, -1, 4000, and integers of arbitrarily large positive or negative magnitude.
9. 9. Non-int inputs raise TypeError, including '5', 5.0, None, [1], True, and False.
10. 10. Instances of an ordinary int subclass follow the same conversion and range-validation rules as built-in int values.
11. 11. is_roman_numeral remains unchanged: 'XIV' and 'mmxxiv' return True; '', 'ABC', and 14 return False; noncanonical strings containing only permitted letters, such as 'IIII' and 'VX', continue to return True.
12. 12. Existing test files remain unchanged and their tests continue to pass.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `c56bc4109ad779726a2648ea1f969e89c2096677d111f6944ea54718d769a4de`, 18 test methods, sealed at 2026-10-16T19:34:03.607107+00:00 by `gpt-6-sol`; attempts: 2.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 18 methods: ERROR 13): 13 of 18 methods failing, 5 passing; operation `01a14635-0391-7568-9e15-f006ffc3138e`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestExistingHelper.test_canonical_strings_are_accepted_case_insensitively | ok (1 ev) | ok (1 ev) |
| test_sealed.TestExistingHelper.test_empty_and_unrecognized_strings_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.TestExistingHelper.test_noncanonical_strings_of_roman_letters_remain_accepted | ok (1 ev) | ok (1 ev) |
| test_sealed.TestExistingHelper.test_ordinary_nonstring_inputs_return_false | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_above_upper_boundary_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_arbitrarily_large_magnitude_raises_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_booleans_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_subclass_converts_normally | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_subclass_obeys_range_validation | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_larger_subtractive_forms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_multi_place_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_none_and_list_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_public_export_matches_core | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_results_are_nonempty_uppercase_roman_text | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_single_symbols | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_strings_and_floats_raise_type_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_units_subtractive_forms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_zero_and_negative_boundary_raise_value_error | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,19 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    if isinstance(n, bool) or not isinstance(n, int):
+        raise TypeError("n must be an integer other than bool")
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (16 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (bound to the sealed suite)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (18 of 18 methods, each in its own process). Operation `01a1463a-aa86-77ea-958a-935c9859fba5`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a1463a-c6ee-71e6-9b48-f4d4d63698fc`, bound through the supervisor: 1 module(s), binding ok.

Held-out suite: none configured.

## 6. Gates
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Result | Evidence | Detail |
| --- | --- | --- | --- |
| existing_suite | pass | bound | OK (2 of 2 methods, each in its own process) |
| sealed_binding | pass | bound | all checks pass |
| mutation | pass | bound | score 1.0 on 12 mutants |
| adversarial_tests | FAIL | bound | FAILED (5 of 8 methods: ERROR 2, FAIL 3) |
| drift_audit | pass | model | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-e569010860 | roman/core.py | 10 | remove `not` | killed | test_sealed.TestToRoman.test_units_subtractive_forms, test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed | 01a1463a-d8ed-71ff-94fd-d02756c33026 |
| m02-ced9e25bef | roman/core.py | 11 | raise -> pass | killed | test_sealed.TestToRoman.test_booleans_raise_type_error | 01a1463a-d8c7-77ed-95b9-1d7fbaae3452 |
| m03-50c956a652 | roman/core.py | 12 | 3999 -> 4000 | killed | test_sealed.TestToRoman.test_above_upper_boundary_raises_value_error, test_sealed.TestToRoman.test_int_subclass_obeys_ra | 01a1463a-d966-72da-bf89-71632bfeb6d4 |
| m04-f8348e8693 | roman/core.py | 12 | LtE -> Lt | killed | test_sealed.TestToRoman.test_multi_place_examples, test_sealed.TestToRoman.test_results_are_nonempty_uppercase_roman_tex | 01a1463a-d8f3-7413-8eaf-8895dc387385 |
| m05-1096110a2c | roman/core.py | 13 | raise -> pass | killed | test_sealed.TestToRoman.test_zero_and_negative_boundary_raise_value_error, test_sealed.TestToRoman.test_above_upper_boun | 01a1463a-d906-7175-8ac2-aa2eb534e5bd |
| m06-80d31fb623 | roman/core.py | 21 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_units_subtractive_forms, test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed | 01a1463a-d92a-7406-af7d-5667c104378f |
| m07-3107b4c411 | roman/core.py | 22 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed.TestToRoman.test_single_symbols, test_sealed.TestToRo | 01a1463a-d8cf-77d0-a3fc-9104ff2934b9 |
| m08-6239dc1f27 | roman/core.py | 22 | Mod -> Sub | killed | test_sealed.TestToRoman.test_multi_place_examples, test_sealed.TestToRoman.test_results_are_nonempty_uppercase_roman_tex | 01a1463a-d917-72f6-99ee-41a2dffa171b |
| m09-4cb90d5ac0 | roman/core.py | 23 | 10 -> 11 | killed | test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed.TestToRoman.test_single_symbols, test_sealed.TestToRo | 01a1463a-f853-730b-8781-c8614dfc2003 |
| m10-dee3750ce1 | roman/core.py | 23 | 10 -> 11 | killed | test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed.TestToRoman.test_single_symbols, test_sealed.TestToRo | 01a1463a-fa1d-7635-9004-aae7b38ef708 |
| m11-62c94f47b9 | roman/core.py | 21 | Add -> Sub | killed | test_sealed.TestToRoman.test_units_subtractive_forms, test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed | 01a1463a-fa64-7716-96b8-5402cd7a4ee6 |
| m12-69d31cf12e | roman/core.py | 24 | Mod -> Sub | killed | test_sealed.TestToRoman.test_larger_subtractive_forms, test_sealed.TestToRoman.test_single_symbols, test_sealed.TestToRo | 01a1463b-1686-73d0-a419-9e5915e2d03e |

Model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `3474eed14c088f827e50af1534f9bc047475d73a3a77421d12b30d3c81f702ed`): FAILED (5 of 8 methods: ERROR 2, FAIL 3); binding FAILED; operation `01a1463c-9dbb-77bf-82fc-37e5e7472e52`. Notes: Targets int subclasses with overridden operators and conversion methods, plus integer-like non-int inputs.

| Failing adversarial test | Outcome |
| --- | --- |
| test_valid_int_subclass_with_overridden_comparisons | ERROR |
| test_zero_int_subclass_with_overridden_comparisons | FAIL |
| test_upper_bound_int_subclass_with_overridden_comparisons | ERROR |
| test_int_subclass_with_overridden_floor_division | FAIL |
| test_int_subclass_with_overridden_modulo | FAIL |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fulfills the contract: `isinstance(n, bool) or not isinstance(n, int)` rejects invalid types, `if not 1 <= n <= 3999` rejects invalid ranges, and the four indexed tables produce canonical Roman numerals while accepting ordinary int subclasses. Only the to_roman stub changes, preserving the helper, exports, and tests; observed tool output reports two existing tests passing and successful contract checks, consistent with the implementer's summary.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
5 failing test(s) indicate a real implementation bug; human review required (mode: advisory). Classifications: {'implementation_bug': 5, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale |
| --- | --- | --- |
| test_valid_int_subclass_with_overridden_comparisons | implementation_bug | The input is an accepted int subclass with integer value 44. Its comparison overrides cause the candidate to raise ValueError instead of ret |
| test_zero_int_subclass_with_overridden_comparisons | implementation_bug | The input has integer value 0. Its comparison overrides bypass validation, causing the candidate to return an empty string instead of raisin |
| test_upper_bound_int_subclass_with_overridden_comparisons | implementation_bug | The input has integer value 4000. Its comparison overrides bypass validation, leading to an IndexError from the thousands table instead of t |
| test_int_subclass_with_overridden_floor_division | implementation_bug | The accepted input has integer value 3888, but the candidate invokes its overridden floor division and raises AssertionError instead of retu |
| test_int_subclass_with_overridden_modulo | implementation_bug | The accepted input has integer value 2479, but the candidate invokes its overridden modulo and raises AssertionError instead of returning 'M |

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10224 | 1143 | 0 | - | 51.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10414 | 1493 | 0 | - | 74.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-2 | medium | 10501 | 2733 | 0 | - | 82.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10442 | 117 | 7168 | - | 52.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10609 | 448 | 7168 | - | 88.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10980 | 86 | 7168 | - | 105.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11121 | 516 | 7168 | - | 34.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11579 | 109 | 7168 | - | 72.2s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10577 | 2249 | 7040 | - | 92.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11277 | 180 | 0 | - | 20.2s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 12016 | 636 | 0 | - | 69.7s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 119740/9710/42880; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1462f-b3a4-770d-bf3f-c42f8f1b1656 | SUCCESS | 0 | 0.724s | retained | off | 0.00275286 |
| red-1 | 01a14631-ba76-76ee-a969-87cfc4046793 | SUCCESS | 0 | 123.628s | disposable | off | 0.03581895 |
| red-2 | 01a14635-0391-7568-9e15-f006ffc3138e | SUCCESS | 0 | 4.152s | disposable | off | 0.03458317 |
| impl-tests-3 | 01a14638-e02c-744e-b942-352191fdfd8d | SUCCESS | 0 | 0.779s | disposable | off | 0.00282076 |
| impl-python-4 | 01a14639-72d6-73ce-909c-2a387c78ab8b | SUCCESS | 0 | 0.523s | disposable | off | 0.00117178 |
| verify | 01a1463a-aa86-77ea-958a-935c9859fba5 | SUCCESS | 0 | 4.175s | disposable | off | 0.03480438 |
| existing | 01a1463a-c6ee-71e6-9b48-f4d4d63698fc | SUCCESS | 0 | 1.353s | disposable | off | 0.008629940000000001 |
| mutant-m02-ced9e25bef | 01a1463a-d8c7-77ed-95b9-1d7fbaae3452 | SUCCESS | 0 | 3.823s | disposable | off | 0.03117729 |
| mutant-m01-e569010860 | 01a1463a-d8ed-71ff-94fd-d02756c33026 | SUCCESS | 0 | 3.871s | disposable | off | 0.03150797 |
| mutant-m03-50c956a652 | 01a1463a-d966-72da-bf89-71632bfeb6d4 | SUCCESS | 0 | 3.873s | disposable | off | 0.031202350000000004 |
| mutant-m04-f8348e8693 | 01a1463a-d8f3-7413-8eaf-8895dc387385 | SUCCESS | 0 | 3.873s | disposable | off | 0.031880280000000004 |
| mutant-m05-1096110a2c | 01a1463a-d906-7175-8ac2-aa2eb534e5bd | SUCCESS | 0 | 3.851s | disposable | off | 0.03150692 |
| mutant-m06-80d31fb623 | 01a1463a-d92a-7406-af7d-5667c104378f | SUCCESS | 0 | 3.901s | disposable | off | 0.03168407 |
| mutant-m07-3107b4c411 | 01a1463a-d8cf-77d0-a3fc-9104ff2934b9 | SUCCESS | 0 | 3.84s | disposable | off | 0.03131047 |
| mutant-m08-6239dc1f27 | 01a1463a-d917-72f6-99ee-41a2dffa171b | SUCCESS | 0 | 3.85s | disposable | off | 0.03139756 |
| mutant-m09-4cb90d5ac0 | 01a1463a-f853-730b-8781-c8614dfc2003 | SUCCESS | 0 | 3.785s | disposable | off | 0.031485360000000004 |
| mutant-m10-dee3750ce1 | 01a1463a-fa1d-7635-9004-aae7b38ef708 | SUCCESS | 0 | 3.867s | disposable | off | 0.0320265 |
| mutant-m11-62c94f47b9 | 01a1463a-fa64-7716-96b8-5402cd7a4ee6 | SUCCESS | 0 | 3.843s | disposable | off | 0.031465389999999996 |
| mutant-m12-69d31cf12e | 01a1463b-1686-73d0-a419-9e5915e2d03e | SUCCESS | 0 | 3.889s | disposable | off | 0.03187551 |
| breaker-tests | 01a1463c-9dbb-77bf-82fc-37e5e7472e52 | SUCCESS | 0 | 2.483s | disposable | off | 0.01898787 |

Sandbox operations: 20, total guest duration 184.083s, retained images ['c8f5ca77-1910-44d8-988f-2e401b921e3a'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
