# Attest Proof Bundle: roman-to-numeral

**Verdict: ERROR**  
Run `roman-to-numeral-attest-a1-20261021T020538153687Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T02:05:38.154231+00:00, finished 2026-10-21T02:07:35.616287+00:00.

**This run stopped for reconciliation.** At stage mutant-m07-ade8d4d4b3 an operation's outcome became uncertain (sandbox executor), so Attest sent nothing further, replayed nothing and certified nothing. The repository was not changed by this run.

Key evidence (E7): 8 operation(s) to reconcile: stopped for reconciliation at mutant-m07-ade8d4d4b3: the outcome of the mutant-m07-ade8d4d4b3 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not ...



What to do: Reconcile the listed operations against the providers' records (each item names its read-only check) before this task is run again; nothing of this run is ever sent again.

Reasons: stopped for reconciliation at mutant-m07-ade8d4d4b3: the outcome of the mutant-m07-ade8d4d4b3 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref c036f4d0]; it was not sent again (outcome uncertain; not retried; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 14 of 19 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the sandbox executor at stage mutant-m07-ade8d4d4b3; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 14 of 19 failed on the unmodified base; 19 of 19 pass on the candidate |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage mutant-m07-ade8d4d4b3: stopped for reconciliation at mutant-m07-ade8d4d4b3: the outcome of the mutant-m07-ade8d4d4b3 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is ... |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `fe1fbf44-d603-47da-be5c-ba5b9e36bd2f`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the `to_roman` function in the `roman.core` module to convert integers from 1 to 3999 inclusive into standard Roman numeral strings using subtractive notation (e.g., 4 -> 'IV', 9 -> 'IX', 40 -> 'XL', 90 -> 'XC', 400 -> 'CD', 900 -> 'CM'). The function must return a string. It must raise `ValueError` for integer inputs outside the range 1..3999, and `TypeError` for non-integer inputs (including numeric strings, floats, None, lists, etc.). Integer subclasses (e.g., `IntEnum` members or custom `int` subclasses) with values in range are accepted and converted identically to the equivalent `int`. The behavior for `bool` (a subclass of `int`) is unspecified; either acceptance or rejection with `TypeError` is permitted but not required, and tests must not depend on either choice. The existing `is_roman_numeral` function and the test suite must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| to_roman | def to_roman(n: int) -> str: | Converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (e.g., 4='IV', 9='IX', 40='XL', 90='XC', 40 | ValueError: raised when n is an instance of int (including int subclasses) with a value outside the range 1..3999 (e.g., 0, -1, 4000).; TypeError: raised when n |
| is_roman_numeral | def is_roman_numeral(s: Any) -> bool: | Returns True if s is a non-empty string consisting only of Roman numeral letters (I, V, X, L, C, D, M) case-insensitively; otherwise returns False. This functio |  |

Acceptance criteria:
AC1. to_roman(1) == 'I'
AC2. to_roman(4) == 'IV'
AC3. to_roman(9) == 'IX'
AC4. to_roman(40) == 'XL'
AC5. to_roman(90) == 'XC'
AC6. to_roman(400) == 'CD'
AC7. to_roman(900) == 'CM'
AC8. to_roman(2024) == 'MMXXIV'
AC9. to_roman(3999) == 'MMMCMXCIX'
AC10. to_roman(1994) == 'MCMXCIV'
AC11. to_roman returns a str for all valid inputs
AC12. ValueError is raised for ints outside 1..3999 (0, -1, 4000), including int subclass instances with such values
AC13. TypeError is raised for non-int input ('5', 5.0, None, [1])
AC14. An int subclass instance with a value in range (e.g., PlainInt(49)) converts like the equal int: PlainInt(49) -> 'XLIX'
AC15. is_roman_numeral('XIV') returns True
AC16. is_roman_numeral('mmxxiv') returns True
AC17. is_roman_numeral('') returns False
AC18. is_roman_numeral('ABC') returns False
AC19. is_roman_numeral(14) returns False

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The authoritative criteria TC1-TC8 are mutually consistent: they define a standard Roman numeral conversion for integers 1..3999 with subtractive notation, specify ValueError for out-of-range ints (including int subclasses), TypeError for non-int inputs, and explicitly permit either acceptance or rejection of bool (an int subclass) without requiring a specific behavior. No conflicts exist among the TCs, and the existing is_roman_numeral function and tests impose no contradictory constraints on to_roman. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d14698ede1939e0cd826d0403b2679a5a17fb693c4cf2d71690b79209481088b`, 19 test methods, sealed at 2026-10-21T02:06:33.780351+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (14 of 19 methods: ERROR 14): 14 of 19 methods failing, 5 passing; operation `01a15c35-cd82-75f6-890f-d5dda13a2220`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsRomanNumeral.test_ac15_xiv | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_ac16_mmxxiv_lower | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_ac17_empty | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_ac18_abc | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_ac19_non_string | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac10_1994 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac11_return_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac12_value_error_outside | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac13_type_error_non_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac14_int_subclass_in_range | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac1_one | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac2_four | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac3_nine | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac4_forty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac5_ninety | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac6_four_hundred | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac7_nine_hundred | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac8_2024 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ac9_3999 | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,29 @@
 
 
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
+        if n == 0:
+            break
+        count, n = divmod(n, value)
+        result.append(symbol * count)
+    return ''.join(result)
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (26 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (19 of 19 methods, each in its own process). Operation `01a15c36-9b68-72dc-a5fa-12605f3520e0`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a15c36-bde3-7544-a2fc-c4a3bd7db7a3`, bound through the supervisor: 1 module(s), binding ok.

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
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1361 | 3921 | 0 | 0.013124 | 12.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 3308 | 3678 | 0 | 0.014342 | 11.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1886 | 2106 | 0 | 0.002461 | 14.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1920 | 134 | 0 | 0.000697 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 2013 | 102 | 0 | 0.000696 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2193 | 1233 | 0 | 0.001768 | 10.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2593 | 126 | 0 | 0.000891 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2739 | 1222 | 0 | 0.001922 | 10.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 3655 | 145 | 0 | 0.001227 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 3801 | 186 | 0 | 0.001308 | 3.2s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 25469/12853/0; Inference USD: 0.038436.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c35-1b89-751d-99ee-c7568c84dae9 | SUCCESS | 0 | 0.781s | retained | off | 0.00288033 |
| red-1 | 01a15c35-cd82-75f6-890f-d5dda13a2220 | SUCCESS | 0 | 4.503s | disposable | off | 0.036530429999999996 |
| impl-tests-4 | 01a15c36-3553-7585-8f76-4bc9a5f312c8 | SUCCESS | 0 | 0.991s | disposable | off | 0.0028282799999999994 |
| impl-python-5 | 01a15c36-69ea-7388-9331-368d2881bc34 | SUCCESS | 0 | 0.593s | disposable | off | 0.00123143 |
| impl-tests-6 | 01a15c36-81cc-7759-8027-ac933891ace2 | SUCCESS | 0 | 0.796s | disposable | off | 0.00288858 |
| verify | 01a15c36-9b68-72dc-a5fa-12605f3520e0 | SUCCESS | 0 | 4.449s | disposable | off | 0.036427339999999996 |
| existing | 01a15c36-bde3-7544-a2fc-c4a3bd7db7a3 | SUCCESS | 0 | 1.508s | disposable | off | 0.00884505 |
| mutant-m01-87b63bf3ce | 01a15c36-d9b1-7649-9196-b96636dc8a05 | ACCEPTED_UNREAD | None | - | disposable | off | None |
| mutant-m02-a5829e3a5a | None | UNCERTAIN | None | - | disposable | off | None |
| mutant-m05-98650f1c9a | 01a15c36-d9cb-74e0-b5c0-a68b6be027ef | ACCEPTED_UNREAD | None | - | disposable | off | None |
| mutant-m03-753d998b37 | 01a15c36-d85b-7041-b69b-c3700cd346c1 | ACCEPTED_UNREAD | None | - | disposable | off | None |
| mutant-m04-12d36c82fd | 01a15c36-d9ed-750d-b829-563228db3aa7 | ACCEPTED_UNREAD | None | - | disposable | off | None |
| mutant-m06-5ffa3e31b5 | 01a15c36-d8fd-705d-b0e1-b5f2e9d7b7dc | ACCEPTED_UNREAD | None | - | disposable | off | None |
| mutant-m07-ade8d4d4b3 | None | UNCERTAIN | None | - | disposable | off | None |
| mutant-m08-a6766ea557 | 01a15c36-d59a-75db-ac1e-77c280efca88 | ACCEPTED_UNREAD | None | - | disposable | off | None |

Sandbox operations: 15, total guest duration 13.621s, retained images ['fe1fbf44-d603-47da-be5c-ba5b9e36bd2f'], 8 operation(s) with an unknown outcome (never replayed).

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

## 12. E7 Failure record
Component: sandbox executor; stage: mutant-m07-ade8d4d4b3; model calls 10 (0 failed); sandbox operations 15; committed inference USD 0.038436; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- stopped for reconciliation at mutant-m07-ade8d4d4b3: the outcome of the mutant-m07-ade8d4d4b3 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref c036f4d0]; it was not sent again (outcome uncertain; not retried; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it

## 12b. Reconciliation (nothing of this run is sent again)
The run stopped at stage `mutant-m07-ade8d4d4b3` (uncertain_operation) at 2026-10-21T02:07:34.383838+00:00: the outcome of the mutant-m07-ade8d4d4b3 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref c036f4d0]; it was not sent again. Each item below is settled by a human with the read-only check it names.

| Item | Service | Stage | Operation | State | Started | How to settle it |
| --- | --- | --- | --- | --- | --- | --- |
| sandbox_operation | sandboxes | mutant-m01-87b63bf3ce | 01a15c36-d9b1-7649-9196-b96636dc8a05 | ACCEPTED_UNREAD | 2026-10-21T02:07:32.667759+00:00 | GET /operations/01a15c36-d9b1-7649-9196-b96636dc8a05 for its final status (read-only); it is never spawned again |
| sandbox_spawn | sandboxes | mutant-m02-a5829e3a5a | s9 | UNCERTAIN | 2026-10-21T02:07:32.667981+00:00 | GET /operations?kind=instance with since/until around started_at, matching image_uuid (the spawn request carries no client id); it is never sent again |
| sandbox_operation | sandboxes | mutant-m05-98650f1c9a | 01a15c36-d9cb-74e0-b5c0-a68b6be027ef | ACCEPTED_UNREAD | 2026-10-21T02:07:32.669474+00:00 | GET /operations/01a15c36-d9cb-74e0-b5c0-a68b6be027ef for its final status (read-only); it is never spawned again |
| sandbox_operation | sandboxes | mutant-m03-753d998b37 | 01a15c36-d85b-7041-b69b-c3700cd346c1 | ACCEPTED_UNREAD | 2026-10-21T02:07:32.669586+00:00 | GET /operations/01a15c36-d85b-7041-b69b-c3700cd346c1 for its final status (read-only); it is never spawned again |
| sandbox_operation | sandboxes | mutant-m04-12d36c82fd | 01a15c36-d9ed-750d-b829-563228db3aa7 | ACCEPTED_UNREAD | 2026-10-21T02:07:32.669850+00:00 | GET /operations/01a15c36-d9ed-750d-b829-563228db3aa7 for its final status (read-only); it is never spawned again |
| sandbox_operation | sandboxes | mutant-m06-5ffa3e31b5 | 01a15c36-d8fd-705d-b0e1-b5f2e9d7b7dc | ACCEPTED_UNREAD | 2026-10-21T02:07:32.669872+00:00 | GET /operations/01a15c36-d8fd-705d-b0e1-b5f2e9d7b7dc for its final status (read-only); it is never spawned again |
| sandbox_spawn | sandboxes | mutant-m07-ade8d4d4b3 | s14 | UNCERTAIN | 2026-10-21T02:07:32.670028+00:00 | GET /operations?kind=instance with since/until around started_at, matching image_uuid (the spawn request carries no client id); it is never sent again |
| sandbox_operation | sandboxes | mutant-m08-a6766ea557 | 01a15c36-d59a-75db-ac1e-77c280efca88 | ACCEPTED_UNREAD | 2026-10-21T02:07:32.670043+00:00 | GET /operations/01a15c36-d59a-75db-ac1e-77c280efca88 for its final status (read-only); it is never spawned again |

Rule: once an operation's outcome is uncertain (a request that may have been executed and whose answer is unknown, an accepted operation whose outcome was not read, an answer that could not be priced) or a record of the run could not be made durable, the run sends nothing further: no model call, no sandbox operation, no poll; it ends ERROR with every such operation listed here with the read-only check that settles it, and none of them is ever sent again

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
