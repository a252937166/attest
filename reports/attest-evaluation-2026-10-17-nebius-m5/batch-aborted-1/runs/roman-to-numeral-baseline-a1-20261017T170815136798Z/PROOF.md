# Attest Proof Bundle: roman-to-numeral

**Verdict: BASELINE**  
Run `roman-to-numeral-baseline-a1-20261017T170815136798Z` · profile `eval-baseline-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:08:15.136947+00:00, finished 2026-10-17T17:09:17.446585+00:00.

**Baseline run: no verification.** This run belongs to the evaluation's plain-agent arm: the implementer worked without sealed tests, breaker or audit, and the candidate was judged only by the harness. It certifies nothing.

Key evidence (trajectory): candidate produced for the independent judge; no gates recorded



What to do: Compare with the Attest run of the same task in the evaluation report.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- nothing: no gate was reached

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `7669bcd0-82df-43bb-aad7-d36722a8a16d`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `d34d3830d3267ef8` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

(none)

Acceptance criteria:
1. to_roman(1)=='I', to_roman(4)=='IV', to_roman(9)=='IX'
2. to_roman(40)=='XL', to_roman(90)=='XC', to_roman(400)=='CD', to_roman(900)=='CM'
3. to_roman(2024)=='MMXXIV', to_roman(3999)=='MMMCMXCIX', to_roman(1994)=='MCMXCIV'
4. to_roman returns a str
5. ValueError for ints outside 1..3999 (0, -1, 4000), including int subclass instances with such values
6. TypeError for non-int input ('5', 5.0, None, [1])
7. An int subclass instance with a value in range (for example an IntEnum member or PlainInt(49)) converts like the equal int: PlainInt(49) -> 'XLIX'
8. Unspecified, not to be tested: int subclasses that override arithmetic or comparison operators; whether bool is rejected

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,28 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    if not isinstance(n, int):
+        raise TypeError("Argument must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("Argument must be between 1 and 3999 inclusive")
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




## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Drift audit not run.



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1282 | 77 | 0 | 0.000454 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1372 | 94 | 0 | 0.000496 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 1547 | 1873 | 0 | 0.002150 | 13.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 1718 | 1012 | 0 | 0.001426 | 9.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2094 | 115 | 0 | 0.000732 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 2235 | 652 | 0 | 0.001257 | 6.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 2749 | 398 | 0 | 0.001183 | 4.6s | ok |

Model calls: 7 (0 failed, 0 malformed); tokens in/out/cached 12997/4221/0; USD: 0.007698.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ad6-0441-7072-83a7-5f9c7868a4a8 | SUCCESS | 0 | 3.304s | retained | off | 0.00312952 |
| impl-tests-5 | 01a14ad6-a458-721c-a22f-2fa918d19a09 | SUCCESS | 0 | 0.75s | disposable | off | 0.00284259 |
| impl-python-6 | 01a14ad6-c83f-74da-9e0f-93b4fa34150e | SUCCESS | 0 | 0.62s | disposable | off | 0.00150184 |

Sandbox operations: 3, total guest duration 4.674s, retained images ['7669bcd0-82df-43bb-aad7-d36722a8a16d'].

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
