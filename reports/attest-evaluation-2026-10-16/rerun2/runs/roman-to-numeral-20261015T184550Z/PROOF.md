# Attest Proof Bundle: roman-to-numeral

**Verdict: NEEDS HUMAN**  
Run `roman-to-numeral-20261015T184550Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:45:50.042014+00:00, finished 2026-10-15T18:48:56.926688+00:00.

Reasons: model-written adversarial tests failed: 1 of 12 (test_breaker.TestToRomanBreaker.test_int_subclass_accepted); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): 1 failing test(s) are contract disputes; a human must decide

## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `53fd9985-c09f-4f5c-bd50-a7521d023135`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the function to_roman(n) in the roman.core module to convert an integer n (1..3999 inclusive) to its standard Roman numeral string using subtractive notation (e.g., 4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). The function must return a str. It must raise ValueError for integer inputs outside the range 1..3999, and raise TypeError for non-integer inputs (including bool, float, str, None, list, etc.). The existing is_roman_numeral function and the test suite must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| to_roman | to_roman(n: int) -> str | Converts an integer n in the range 1 to 3999 inclusive to its Roman numeral representation using standard subtractive notation. Returns the Roman numeral as a s | ValueError: raised when n is an int but not in the range 1..3999 (e.g., 0, -1, 4000).; TypeError: raised when n is not an int (e.g., '5', 5.0, None, [1], True,  |

Acceptance criteria:
1. 1. to_roman(1) returns 'I'.
2. 2. to_roman(4) returns 'IV'.
3. 3. to_roman(9) returns 'IX'.
4. 4. to_roman(40) returns 'XL'.
5. 5. to_roman(90) returns 'XC'.
6. 6. to_roman(400) returns 'CD'.
7. 7. to_roman(900) returns 'CM'.
8. 8. to_roman(2024) returns 'MMXXIV'.
9. 9. to_roman(3999) returns 'MMMCMXCIX'.
10. 10. to_roman(1994) returns 'MCMXCIV'.
11. 11. to_roman returns a value of type str for all valid inputs.
12. 12. to_roman raises ValueError for integer inputs 0, -1, and 4000 (and any other int outside 1..3999).
13. 13. to_roman raises TypeError for non-int inputs: string '5', float 5.0, None, list [1] (and any other non-int type).

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `9549a75586b0bf8149bc5abf313636899e1a84999e539000c3b7706eae15bc84`, 13 test methods, sealed at 2026-10-15T18:46:48.930145+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 13 methods: ERROR 13): 13 of 13 methods failing, 0 passing; operation `01a140e3-6c71-73ae-bca8-ba14b7a6ae09`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestToRoman.test_to_roman_1994_returns_MCMXCIV | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_1_returns_I | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_2024_returns_MMXXIV | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_3999_returns_MMMCMXCIX | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_400_returns_CD | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_40_returns_XL | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_4_returns_IV | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_900_returns_CM | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_90_returns_XC | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_9_returns_IX | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_returns_str_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_type_error_on_non_int_inputs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_value_error_on_out_of_range_int | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,28 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    if type(n) is not int:
+        raise TypeError("n must be an integer")
+    if n < 1 or n > 3999:
+        raise ValueError("n must be between 1 and 3999 inclusive")
+    val_sym = [
+        (1000, 'M'),
+        (900, 'CM'),
+        (500, 'D'),
+        (400, 'CD'),
+        (100, 'C'),
+        (90, 'XC'),
+        (50, 'L'),
+        (40, 'XL'),
+        (10, 'X'),
+        (9, 'IX'),
+        (5, 'V'),
+        (4, 'IV'),
+        (1, 'I')
+    ]
+    result = []
+    for value, symbol in val_sym:
+        while n >= value:
+            result.append(symbol)
+            n -= value
+    return ''.join(result)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (2 passed of 2). Sealed suite: OK (13 of 13 methods, each in its own process). Operation `01a140e4-3f05-7001-927c-31ed59e5c5c0`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| static_ids_match_red | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |

Held-out suite (tests/test_heldout.py): OK (8 passed of 8); operation `01a140e4-69df-7657-8b8f-e1235a37adc8`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | OK |
| mutation | pass | score 0.75 on 12 mutants |
| adversarial_tests | FAIL | FAILED (1 of 12 methods: ERROR 1) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 9 killed, 3 survived, 0 unknown; mutation score 0.750 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-6677eb850c | roman/core.py | 10 | IsNot -> Is | killed | test_sealed.TestToRoman.test_to_roman_1_returns_I, test_sealed.TestToRoman.test_to_roman_4_returns_IV, test_sealed.TestT | 01a140e4-786b-7428-b345-396152ee2060 |
| m02-11894b121b | roman/core.py | 11 | raise -> pass | killed | test_sealed.TestToRoman.test_to_roman_type_error_on_non_int_inputs | 01a140e4-77fa-76c1-9be3-41e5a9175dec |
| m03-db6dc9aeff | roman/core.py | 12 | Lt -> LtE | killed | test_sealed.TestToRoman.test_to_roman_1_returns_I, test_sealed.TestToRoman.test_to_roman_returns_str_type | 01a140e4-7846-7522-9a07-2481ef6883f1 |
| m04-554bced466 | roman/core.py | 12 | Gt -> GtE | killed | test_sealed.TestToRoman.test_to_roman_3999_returns_MMMCMXCIX | 01a140e4-7877-7389-8bb0-91aa3ccfb354 |
| m05-31ea72235f | roman/core.py | 13 | raise -> pass | killed | test_sealed.TestToRoman.test_to_roman_value_error_on_out_of_range_int | 01a140e4-7872-71fe-af9c-7eb3a7b1d858 |
| m06-3fdf57ef9f | roman/core.py | 16 | 900 -> 901 | killed | test_sealed.TestToRoman.test_to_roman_900_returns_CM, test_sealed.TestToRoman.test_to_roman_3999_returns_MMMCMXCIX, test | 01a140e4-7866-7092-b09b-8ae199f9aaa3 |
| m07-56d53aab85 | roman/core.py | 18 | 400 -> 401 | killed | test_sealed.TestToRoman.test_to_roman_400_returns_CD | 01a140e4-78a0-7725-86de-2aad072833eb |
| m08-6e89bfa395 | roman/core.py | 19 | 100 -> 101 | survived |  | 01a140e4-788a-75fb-9881-862802ee0053 |
| m09-c8def1f0f0 | roman/core.py | 21 | 50 -> 51 | survived |  | 01a140e4-9415-77e6-be44-8890eb679aab |
| m10-623ac5a171 | roman/core.py | 23 | 10 -> 11 | killed | test_sealed.TestToRoman.test_to_roman_2024_returns_MMXXIV | 01a140e4-94bf-7164-a976-8e86d3e98cd7 |
| m11-d62c7a1a82 | roman/core.py | 25 | 5 -> 6 | survived |  | 01a140e4-9556-7002-a30d-cb9e4a95f5bd |
| m12-4163cb4128 | roman/core.py | 27 | 1 -> 2 | killed | test_sealed.TestToRoman.test_to_roman_1_returns_I | 01a140e4-95da-71f9-a6b2-e65a62863231 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `e22f25b8afef271b717413912a8fd1c68689c44f706ffed294bdb95d9c0b434f`): FAILED (1 of 12 methods: ERROR 1); binding FAILED; operation `01a140e5-18b1-77f4-8f8e-f2fc45968b6d`. Notes: Targets subclass acceptance, bool, float, decimal, fraction, complex, large ints, zero, output validity, and interaction with is_roman_numeral.

| Failing adversarial test | Outcome |
| --- | --- |
| test_int_subclass_accepted | ERROR |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements to_roman with correct input validation (TypeError for non-int, ValueError for out-of-range int) and a standard greedy conversion using the required subtractive pairs (CM, CD, XC, XL, IX, IV). All acceptance criteria are satisfied, existing tests pass, and no unrelated changes were made.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
1 failing test(s) are contract disputes; a human must decide (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 0, 'contract_dispute': 1}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale |
| --- | --- | --- |
| test_int_subclass_accepted | contract_dispute | The contract states to raise TypeError for non-integer inputs, including bool. However, it does not explicitly specify whether other subclas |

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1181 | 1031 | 0 | 0.004274 | 4.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1350 | 7130 | 0 | 0.006822 | 34.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1401 | 84 | 0 | 0.000496 | 6.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1490 | 104 | 0 | 0.000541 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1668 | 273 | 0 | 0.000746 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1841 | 2042 | 0 | 0.002390 | 11.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2228 | 257 | 0 | 0.000900 | 7.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2375 | 951 | 0 | 0.001568 | 6.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 2946 | 253 | 0 | 0.001111 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 1504 | 4588 | 0 | 0.004580 | 21.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1877 | 1720 | 0 | 0.007037 | 6.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 2416 | 3105 | 0 | 0.011731 | 10.5s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 22277/21538/0; USD: 0.042196.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140e2-b3b5-73db-b654-a2e006cf6616 | SUCCESS | 0 | 0.723s | retained | off | 0.0027348999999999997 |
| red-1 | 01a140e3-6c71-73ae-bca8-ba14b7a6ae09 | SUCCESS | 0 | 2.907s | disposable | off | 0.023024580000000003 |
| impl-tests-5 | 01a140e3-f9a7-71db-8375-557db0fa4321 | SUCCESS | 0 | 0.754s | disposable | off | 0.0027463400000000003 |
| impl-python-6 | 01a140e4-24aa-765a-8768-6e79bbd880e5 | SUCCESS | 0 | 0.561s | disposable | off | 0.00110998 |
| verify | 01a140e4-3f05-7001-927c-31ed59e5c5c0 | SUCCESS | 0 | 3.112s | disposable | off | 0.02474992 |
| heldout | 01a140e4-69df-7657-8b8f-e1235a37adc8 | SUCCESS | 0 | 0.752s | disposable | off | 0.00277025 |
| mutant-m01-6677eb850c | 01a140e4-786b-7428-b345-396152ee2060 | SUCCESS | 0 | 3.052s | disposable | off | 0.023504340000000002 |
| mutant-m02-11894b121b | 01a140e4-77fa-76c1-9be3-41e5a9175dec | SUCCESS | 0 | 3.005s | disposable | off | 0.023279229999999998 |
| mutant-m03-db6dc9aeff | 01a140e4-7846-7522-9a07-2481ef6883f1 | SUCCESS | 0 | 3.056s | disposable | off | 0.023347470000000002 |
| mutant-m04-554bced466 | 01a140e4-7877-7389-8bb0-91aa3ccfb354 | SUCCESS | 0 | 3.036s | disposable | off | 0.02340537 |
| mutant-m05-31ea72235f | 01a140e4-7872-71fe-af9c-7eb3a7b1d858 | SUCCESS | 0 | 3.034s | disposable | off | 0.023151880000000003 |
| mutant-m06-3fdf57ef9f | 01a140e4-7866-7092-b09b-8ae199f9aaa3 | SUCCESS | 0 | 3.057s | disposable | off | 0.02346684 |
| mutant-m07-56d53aab85 | 01a140e4-78a0-7725-86de-2aad072833eb | SUCCESS | 0 | 3.034s | disposable | off | 0.023161510000000003 |
| mutant-m08-6e89bfa395 | 01a140e4-788a-75fb-9881-862802ee0053 | SUCCESS | 0 | 3.036s | disposable | off | 0.0231814 |
| mutant-m09-c8def1f0f0 | 01a140e4-9415-77e6-be44-8890eb679aab | SUCCESS | 0 | 2.912s | disposable | off | 0.02315422 |
| mutant-m10-623ac5a171 | 01a140e4-94bf-7164-a976-8e86d3e98cd7 | SUCCESS | 0 | 3.002s | disposable | off | 0.023548060000000003 |
| mutant-m11-d62c7a1a82 | 01a140e4-9556-7002-a30d-cb9e4a95f5bd | SUCCESS | 0 | 2.926s | disposable | off | 0.02304414 |
| mutant-m12-4163cb4128 | 01a140e4-95da-71f9-a6b2-e65a62863231 | SUCCESS | 0 | 2.995s | disposable | off | 0.02346608 |
| breaker-tests | 01a140e5-18b1-77f4-8f8e-f2fc45968b6d | SUCCESS | 0 | 2.844s | disposable | off | 0.022345300000000002 |

Sandbox operations: 19, total guest duration 47.798s, retained images ['53fd9985-c09f-4f5c-bd50-a7521d023135'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
