# Attest Proof Bundle: roman-to-numeral

**Verdict: ERROR**  
Run `roman-to-numeral-20261015T183250Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:32:50.594794+00:00, finished 2026-10-15T18:33:44.208158+00:00.

Reasons: SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay


## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `07298a32-02de-48a3-a511-f376c606b202`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the `to_roman` function in the `roman.core` module to convert an integer between 1 and 3999 inclusive into its standard Roman numeral representation using subtractive notation (e.g., 4 -> 'IV', 9 -> 'IX', 40 -> 'XL', 90 -> 'XC', 400 -> 'CD', 900 -> 'CM'). The function must return a string. It must raise `ValueError` if the input is an integer outside the valid range, and `TypeError` if the input is not an integer (with `bool` considered non-integer). The existing `is_roman_numeral` function and the test suite must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| to_roman | def to_roman(n: int) -> str | For an integer n in the range 1..3999 inclusive, return the standard Roman numeral string using subtractive notation. The mapping follows the conventional rules | TypeError: raised when n is not of type int (i.e., type(n) is not int). This includes bool, str, float, None, list, etc.; ValueError: raised when n is an int bu |

Acceptance criteria:
1. to_roman(1) returns 'I', to_roman(4) returns 'IV', to_roman(9) returns 'IX'.
2. to_roman(40) returns 'XL', to_roman(90) returns 'XC', to_roman(400) returns 'CD', to_roman(900) returns 'CM'.
3. to_roman(2024) returns 'MMXXIV', to_roman(3999) returns 'MMMCMXCIX', to_roman(1994) returns 'MCMXCIV'.
4. to_roman returns a value of type str for all valid inputs.
5. to_roman raises ValueError for integer inputs outside 1..3999, such as 0, -1, 4000.
6. to_roman raises TypeError for non-int inputs, such as '5', 5.0, None, [1].
7. The existing function is_roman_numeral remains unchanged and passes its current tests.

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1181 | 2091 | 0 | 0.007454 | 7.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1410 | 8297 | 0 | 0.007890 | 36.7s | ok |

Model calls: 2 (0 failed, 0 malformed); tokens in/out/cached 2591/10388/0; USD: 0.015344.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140d6-ba87-71fe-b32b-a638d49ee3dd | SUCCESS | 0 | 0.749s | retained | off | 0.00274737 |
| red-1 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 2, total guest duration 0.749s, retained images ['07298a32-02de-48a3-a511-f376c606b202'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
