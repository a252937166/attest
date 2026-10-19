# Attest Proof Bundle: roman-to-numeral

**Verdict: ERROR**  
Run `roman-to-numeral-20261015T180250Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:02:50.350254+00:00, finished 2026-10-15T18:05:21.775589+00:00.

Reasons: model provider: inference outcome uncertain (RemoteDisconnected: Remote end closed connection without response); not retried (outcome uncertain; not retried)


## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `a71cf574-b2e7-4592-a12b-6825ec7850f7`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the to_roman(n) function in the roman package to convert an integer n (1..3999 inclusive) to its standard Roman numeral string using subtractive notation. The function must return a string, raise ValueError for integers outside the valid range, and raise TypeError for non-integer inputs (including bool, str, float, None, list, etc.). The existing is_roman_numeral function and the test suite must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| to_roman | to_roman(n: int) -> str | Converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (e.g., 4='IV', 9='IX', 40='XL', 90='XC', 40 | ValueError: if n is an int outside the range 1..3999 (including 0, negative numbers, and numbers >=4000).; TypeError: if n is not an int (including bool, str, f |

Acceptance criteria:
1. to_roman(1) returns 'I', to_roman(4) returns 'IV', to_roman(9) returns 'IX'.
2. to_roman(40) returns 'XL', to_roman(90) returns 'XC', to_roman(400) returns 'CD', to_roman(900) returns 'CM'.
3. to_roman(2024) returns 'MMXXIV', to_roman(3999) returns 'MMMCMXCIX', to_roman(1994) returns 'MCMXCIV'.
4. to_roman returns a value of type str for all valid inputs.
5. to_roman raises ValueError for integer inputs 0, -1, and 4000 (and any other int outside 1..3999).
6. to_roman raises TypeError for non-int inputs such as '5', 5.0, None, and [1].
7. The existing is_roman_numeral function continues to pass its current tests (unchanged behavior).

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `89f598496737b8b0224bd5226397326c37546f17a6b728a8d411f45719487825`, 21 test methods, sealed at 2026-10-15T18:04:14.428283+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (19 of 21 methods: ERROR 19): 19 of 21 methods failing, 2 passing; operation `01a140bc-6c26-73e4-a0ba-0962340bff37`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsRomanNumeral.test_false | ok (1 ev) | - |
| test_sealed.TestIsRomanNumeral.test_true | ok (1 ev) | - |
| test_sealed.TestToRoman.test_1994 | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_2024 | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_3999 | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_forty | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_four | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_four_hundred | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_nine | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_nine_hundred | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_ninety | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_one | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_return_type_is_str | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_type_error_bool | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_type_error_float | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_type_error_list | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_type_error_none | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_type_error_string | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_value_error_negative | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_value_error_out_of_range_high | ERROR (1 ev) | - |
| test_sealed.TestToRoman.test_value_error_zero | ERROR (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: n/a (0 passed of 0). Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint.

(none)

Held-out suite: none configured.

## 6. Gates
(none)

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Drift audit not run.



## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1181 | 2234 | 0 | 0.007883 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1284 | 14526 | 0 | 0.013459 | 65.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1343 | 77 | 0 | 0.000472 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1433 | 96 | 0 | 0.000516 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | - | - | - | - | 62.5s | error |

Model calls: 5 (1 failed, 0 malformed); tokens in/out/cached 5241/16933/0; USD: 0.02233.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140bb-431d-76b7-a6c4-a2277825c15c | SUCCESS | 0 | 0.762s | retained | off | 0.00274303 |
| red-1 | 01a140bc-6c26-73e4-a0ba-0962340bff37 | SUCCESS | 0 | 4.293s | disposable | off | 0.03598806 |

Sandbox operations: 2, total guest duration 5.055s, retained images ['a71cf574-b2e7-4592-a12b-6825ec7850f7'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
