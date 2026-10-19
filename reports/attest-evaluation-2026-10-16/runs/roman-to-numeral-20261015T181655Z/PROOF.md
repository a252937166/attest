# Attest Proof Bundle: roman-to-numeral

**Verdict: ERROR**  
Run `roman-to-numeral-20261015T181655Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:16:55.631645+00:00, finished 2026-10-15T18:17:04.689558+00:00.

Reasons: TransportError: URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>


## 1. Frozen task
Task `roman-to-numeral`, spec digest `4260759688c40bae278a4a6262c5bdc320c4a49fc026af98ea5bb6d9fde5b0f6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `None`; test runner `unittest`; install: `none` (checkpoint networking off).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (bool counts as non-int for this task is not required; treat only real ints as valid). Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: None. (specification stage did not complete)

(none)

Acceptance criteria:
(none)

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
Grounding not configured.



## 10. Ledger
(none)

Model calls: 0 (0 failed, 0 malformed); tokens in/out/cached 0/0/0; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140c8-2b0a-7794-a562-ca7778de9200 | None | None | - | disposable | off | None |

Sandbox operations: 1, total guest duration 0s, retained images [].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
