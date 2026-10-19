# Attest Proof Bundle: roman-to-numeral

**Verdict: VERIFIED**  
Run `roman-to-numeral-20261015T175328Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T17:53:28.148532+00:00, finished 2026-10-15T17:55:43.718736+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `f11c9f8e-d751-449f-b8f0-88d679a77b6b`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the to_roman(n) function in the roman.core module to convert an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (e.g., 4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). The function must return a string. It must raise ValueError for integer inputs outside the valid range and TypeError for non-integer inputs (including bool, since only real ints are valid). The existing is_roman_numeral function and the test suite must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| is_roman_numeral | is_roman_numeral(s) -> bool | Returns True if s is a non-empty string consisting only of Roman numeral letters (I, V, X, L, C, D, M) case-insensitively; otherwise returns False. This functio |  |
| to_roman | to_roman(n) -> str | Converts an integer n in the range 1..3999 inclusive to its standard Roman numeral representation using subtractive notation. The mapping uses the following val | ValueError: raised when n is an integer but not in the range 1..3999 (e.g., 0, -1, 4000).; TypeError: raised when n is not an integer (e.g., string, float, None |

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
12. 12. to_roman raises ValueError for integer inputs outside 1..3999, including 0, -1, and 4000.
13. 13. to_roman raises TypeError for non-integer inputs, including '5', 5.0, None, and [1].
14. 14. The existing is_roman_numeral function continues to pass its current tests (test_true and test_false in tests/test_basic.py).

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `823863f80d8e6c6aed04d0c64a3554a3ef4eb73e8ae0afc68a0fc410d3665e13`, 15 test methods, sealed at 2026-10-15T17:54:11.311851+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 15 methods: ERROR 13): 13 of 15 methods failing, 2 passing; operation `01a140b3-343a-7027-a83f-4d61a763ead6`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsRomanNumeral.test_is_roman_numeral_false | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_is_roman_numeral_true | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_1 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_1994 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_2024 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_3999 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_4 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_40 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_400 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_9 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_90 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_900 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_return_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_type_error_non_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_value_error_out_of_range | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,19 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    """Convert an integer to a Roman numeral."""
+    if not isinstance(n, int) or isinstance(n, bool):
+        raise TypeError("Argument must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("Argument must be between 1 and 3999 inclusive")
+    roman_numerals = [
+        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
+        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
+        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
+    ]
+    result = []
+    for value, symbol in roman_numerals:
+        while n >= value:
+            result.append(symbol)
+            n -= value
+    return ''.join(result)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (2 passed of 2). Sealed suite: OK (15 of 15 methods, each in its own process). Operation `01a140b3-c82e-74f7-b337-fbfbc432dd2b`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout.py): OK (8 passed of 8); operation `01a140b3-e1cb-700e-9d97-72dbd2ca6efb`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | OK |
| mutation | pass | score 0.667 on 12 mutants |
| adversarial_tests | pass | OK (14 of 14 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 8 killed, 4 survived, 0 unknown; mutation score 0.667 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-61f115dd86 | roman/core.py | 11 | remove `not` | killed | test_sealed.TestToRoman.test_to_roman_1, test_sealed.TestToRoman.test_to_roman_4, test_sealed.TestToRoman.test_to_roman_ | 01a140b3-ef19-717f-9820-e193b341c5a2 |
| m02-86c1b5f019 | roman/core.py | 11 | Or -> And | killed | test_sealed.TestToRoman.test_to_roman_type_error_non_int | 01a140b3-ef7e-723d-b32e-17dcb37c5885 |
| m03-c20c07f55c | roman/core.py | 13 | 1 -> 2 | killed | test_sealed.TestToRoman.test_to_roman_1, test_sealed.TestToRoman.test_to_roman_return_type | 01a140b3-ef5e-7249-abb8-7ca7af5ea853 |
| m04-8632ba201c | roman/core.py | 13 | LtE -> Lt | killed | test_sealed.TestToRoman.test_to_roman_1, test_sealed.TestToRoman.test_to_roman_return_type | 01a140b3-ef87-7525-8bfb-a633a47a0f7a |
| m05-eb3f829e67 | roman/core.py | 13 | remove `not` | killed | test_sealed.TestToRoman.test_to_roman_1, test_sealed.TestToRoman.test_to_roman_4, test_sealed.TestToRoman.test_to_roman_ | 01a140b3-efdb-7470-a89e-e9a03aa31fa7 |
| m06-7c6777521d | roman/core.py | 16 | 1000 -> 1001 | killed | test_sealed.TestToRoman.test_to_roman_2024, test_sealed.TestToRoman.test_to_roman_3999, test_sealed.TestToRoman.test_to_ | 01a140b3-ef48-751c-b44d-a9e6a7c23d4c |
| m07-34f0081f1b | roman/core.py | 16 | 500 -> 501 | survived |  | 01a140b3-ef8c-7071-9637-e4e8a9151b55 |
| m08-c3f82387aa | roman/core.py | 17 | 100 -> 101 | survived |  | 01a140b3-eff5-7467-a44e-18e5cebfa39f |
| m09-f031e83c6e | roman/core.py | 17 | 50 -> 51 | survived |  | 01a140b4-0cf7-7708-a6ee-13be957ff9fb |
| m10-14c8c6ea9b | roman/core.py | 18 | 10 -> 11 | killed | test_sealed.TestToRoman.test_to_roman_2024 | 01a140b4-0973-74fb-a31f-895297930a02 |
| m11-e9b1c172d8 | roman/core.py | 18 | 5 -> 6 | survived |  | 01a140b4-0999-7507-b617-9e673c22b040 |
| m12-6dac024c2d | roman/core.py | 18 | 1 -> 2 | killed | test_sealed.TestToRoman.test_to_roman_1 | 01a140b4-09dd-7582-8110-e9e756d224e9 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `1cff4324f730bfc85a1c4636c87729cae1f9a2ce5419e66a73e0eb814656e14c`): OK (14 of 14 methods, each in its own process); binding ok; operation `01a140b4-826f-7291-aaaa-328147ae76a1`. Notes: Adversarial tests targeting edge cases: bool, subclass int, float, string, None, list, dict, set, out-of-range, return type, uppercase, validity, forbidden patterns.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements to_roman exactly as specified, including subtractive notation, range checks, and type checks (including bool). All acceptance criteria are satisfied, and the existing is_roman_numeral and test suite remain unchanged. The implementer's claim of passing all tests is supported by the observed test runs.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1181 | 3396 | 0 | 0.011369 | 13.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1550 | 3451 | 0 | 0.003571 | 15.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1620 | 112 | 0 | 0.000587 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1790 | 1323 | 0 | 0.001728 | 8.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2170 | 95 | 0 | 0.000736 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2314 | 626 | 0 | 0.001258 | 4.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2822 | 396 | 0 | 0.001203 | 3.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 1672 | 4000 | 0 | 0.004102 | 21.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 1967 | 2061 | 0 | 0.008150 | 7.3s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 17086/15460/0; USD: 0.032704.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140b2-ada1-7078-b04b-133137f44503 | SUCCESS | 0 | 0.733s | retained | off | 0.0027406699999999997 |
| red-1 | 01a140b3-343a-7027-a83f-4d61a763ead6 | SUCCESS | 0 | 3.305s | disposable | off | 0.02635842 |
| impl-tests-3 | 01a140b3-85a5-7661-83a5-a2a82d104e33 | SUCCESS | 0 | 0.723s | disposable | off | 0.0027238699999999998 |
| impl-python-4 | 01a140b3-a4b2-7412-8993-799ebcd065f4 | SUCCESS | 0 | 0.551s | disposable | off | 0.00115398 |
| verify | 01a140b3-c82e-74f7-b337-fbfbc432dd2b | SUCCESS | 0 | 3.414s | disposable | off | 0.02801836 |
| heldout | 01a140b3-e1cb-700e-9d97-72dbd2ca6efb | SUCCESS | 0 | 0.799s | disposable | off | 0.00277262 |
| mutant-m01-61f115dd86 | 01a140b3-ef19-717f-9820-e193b341c5a2 | SUCCESS | 0 | 3.265s | disposable | off | 0.026260210000000003 |
| mutant-m02-86c1b5f019 | 01a140b3-ef7e-723d-b32e-17dcb37c5885 | SUCCESS | 0 | 3.363s | disposable | off | 0.02667181 |
| mutant-m03-c20c07f55c | 01a140b3-ef5e-7249-abb8-7ca7af5ea853 | SUCCESS | 0 | 3.338s | disposable | off | 0.02643124 |
| mutant-m04-8632ba201c | 01a140b3-ef87-7525-8bfb-a633a47a0f7a | SUCCESS | 0 | 3.467s | disposable | off | 0.027274040000000003 |
| mutant-m05-eb3f829e67 | 01a140b3-efdb-7470-a89e-e9a03aa31fa7 | SUCCESS | 0 | 3.397s | disposable | off | 0.02646956 |
| mutant-m06-7c6777521d | 01a140b3-ef48-751c-b44d-a9e6a7c23d4c | SUCCESS | 0 | 3.399s | disposable | off | 0.02681072 |
| mutant-m07-34f0081f1b | 01a140b3-ef8c-7071-9637-e4e8a9151b55 | SUCCESS | 0 | 3.376s | disposable | off | 0.02634953 |
| mutant-m08-c3f82387aa | 01a140b3-eff5-7467-a44e-18e5cebfa39f | SUCCESS | 0 | 3.315s | disposable | off | 0.02641228 |
| mutant-m09-f031e83c6e | 01a140b4-0cf7-7708-a6ee-13be957ff9fb | SUCCESS | 0 | 3.303s | disposable | off | 0.026103960000000002 |
| mutant-m10-14c8c6ea9b | 01a140b4-0973-74fb-a31f-895297930a02 | SUCCESS | 0 | 3.273s | disposable | off | 0.02636584 |
| mutant-m11-e9b1c172d8 | 01a140b4-0999-7507-b617-9e673c22b040 | SUCCESS | 0 | 3.274s | disposable | off | 0.02610711 |
| mutant-m12-6dac024c2d | 01a140b4-09dd-7582-8110-e9e756d224e9 | SUCCESS | 0 | 3.351s | disposable | off | 0.02654284 |
| breaker-tests | 01a140b4-826f-7291-aaaa-328147ae76a1 | SUCCESS | 0 | 3.091s | disposable | off | 0.02483565 |

Sandbox operations: 19, total guest duration 52.737s, retained images ['f11c9f8e-d751-449f-b8f0-88d679a77b6b'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
