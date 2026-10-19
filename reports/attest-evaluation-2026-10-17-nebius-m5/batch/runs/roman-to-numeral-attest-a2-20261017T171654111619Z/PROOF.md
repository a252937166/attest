# Attest Proof Bundle: roman-to-numeral

**Verdict: VERIFIED**  
Run `roman-to-numeral-attest-a2-20261017T171654111619Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:16:54.112045+00:00, finished 2026-10-17T17:20:50.288952+00:00.

**Accept this patch.** All 16 sealed tests pass on the candidate in a fresh sandbox, and 16 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 16 of 16 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 3 one-line change(s) to the patch were not caught by the sealed tests (score 0.75, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 16 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 16 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 14 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the sealed tests constrain the lines marked by the 3 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 16 of 16 failed on the unmodified base; 16 of 16 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 12 one-line mutants caught, 3 survived, 0 unknown; score 0.75 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 14 of 14 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `355dc2f8-4d96-46a8-bdcd-23b8ab10dadd`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the to_roman function in the roman package to convert integers from 1 to 3999 inclusive into standard Roman numeral strings using subtractive notation (e.g., 4 -> 'IV', 9 -> 'IX', 40 -> 'XL', 90 -> 'XC', 400 -> 'CD', 900 -> 'CM'). The function must return a string. It must raise ValueError for integer values outside the 1..3999 range (including int subclass instances with such values). It must raise TypeError for non-int inputs (such as strings, floats, None, lists). Int subclasses (e.g., IntEnum, PlainInt) with values in range are accepted and converted like the equivalent int. The behavior for bool (a subclass of int) is unspecified; rejecting or accepting is permitted but tests must not depend on it. The existing is_roman_numeral function and tests must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| to_roman | def to_roman(n: int) -> str: | Converts an integer n in the range 1..3999 inclusive to its standard Roman numeral representation using subtractive notation. Returns the Roman numeral as a str | TypeError: raised when n is not an instance of int (including bool if the implementation chooses to reject, but not required).; ValueError: raised when n is an  |

Acceptance criteria:
1. to_roman(1) == 'I'
2. to_roman(4) == 'IV'
3. to_roman(9) == 'IX'
4. to_roman(40) == 'XL'
5. to_roman(90) == 'XC'
6. to_roman(400) == 'CD'
7. to_roman(900) == 'CM'
8. to_roman(2024) == 'MMXXIV'
9. to_roman(3999) == 'MMMCMXCIX'
10. to_roman(1994) == 'MCMXCIV'
11. to_roman returns a str (type check)
12. ValueError for ints outside 1..3999 (0, -1, 4000), including int subclass instances with such values
13. TypeError for non-int input ('5', 5.0, None, [1])
14. An int subclass instance with a value in range (e.g., PlainInt(49)) converts like the equal int: PlainInt(49) -> 'XLIX'
15. Existing tests in tests/test_basic.py continue to pass (is_roman_numeral behavior unchanged)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `625ebcd156b6122cfe811d195a79004f9a20b27817a5590a2bb52dcee15ce103`, 16 test methods, sealed at 2026-10-17T17:17:36.248171+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 16 methods: ERROR 16): 16 of 16 methods failing, 0 passing; operation `01a14ade-755b-73ed-9804-5e692738873f`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestToRoman.test_1994 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_2024 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_3999 | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_forty | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_four | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_four_hundred | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_subclass_in_range | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_nine | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_nine_hundred | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_ninety | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_one | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_return_type_str | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_type_error_non_int | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_value_error_int_subclass_out_of_range | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_value_error_out_of_range_high | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_value_error_out_of_range_low | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

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
+    roman_numerals = [
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
+    for value, symbol in roman_numerals:
+        while n >= value:
+            result.append(symbol)
+            n -= value
+    return ''.join(result)
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (25 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (16 of 16 methods, each in its own process). Operation `01a14adf-9fc7-70a1-ab43-8ba978ad19ea`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a14ae0-02a4-77bb-b789-644609b7ad1d`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.75 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (14 of 14 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 9 killed, 3 survived, 0 unknown; mutation score 0.750 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-f8722750e5 | roman/core.py | 10 | remove `not` | killed | test_sealed.TestToRoman.test_one, test_sealed.TestToRoman.test_four, test_sealed.TestToRoman.test_nine, test_sealed.Test | 01a14ae0-70e1-7590-a04d-0df73565c45e |
| m02-687dffd1ca | roman/core.py | 11 | raise -> pass | killed | test_sealed.TestToRoman.test_type_error_non_int | 01a14ae0-70cb-702a-9685-be607b180206 |
| m03-f0a784727e | roman/core.py | 12 | 3999 -> 4000 | killed | test_sealed.TestToRoman.test_value_error_out_of_range_high | 01a14ae0-70c8-772d-a093-40a04c8d4d7d |
| m04-a5b6722f3a | roman/core.py | 12 | LtE -> Lt | killed | test_sealed.TestToRoman.test_3999 | 01a14ae0-70dc-7396-8bed-7b8e1642c1bc |
| m05-c73302e8b5 | roman/core.py | 13 | raise -> pass | killed | test_sealed.TestToRoman.test_value_error_out_of_range_low, test_sealed.TestToRoman.test_value_error_out_of_range_high, t | 01a14ae0-70f7-7229-9de1-91311f4dbdc7 |
| m06-a57bbfbe33 | roman/core.py | 16 | 900 -> 901 | killed | test_sealed.TestToRoman.test_nine_hundred, test_sealed.TestToRoman.test_3999, test_sealed.TestToRoman.test_1994 | 01a14ae0-70f4-7598-9bce-992303503e69 |
| m07-bf81179b5f | roman/core.py | 18 | 400 -> 401 | killed | test_sealed.TestToRoman.test_four_hundred | 01a14ae0-c4ac-75de-ba2c-38c1def01e8f |
| m08-8d7ddce38a | roman/core.py | 19 | 100 -> 101 | survived |  | 01a14ae0-70f0-768c-89cc-a2957c13f677 |
| m09-99ee8bf2a2 | roman/core.py | 21 | 50 -> 51 | survived |  | 01a14ae0-d4d0-7618-a6f1-d709c7ea08b6 |
| m10-e0332a44cf | roman/core.py | 23 | 10 -> 11 | killed | test_sealed.TestToRoman.test_2024 | 01a14ae0-d43a-751c-9175-71634181a543 |
| m11-345d5f0bb3 | roman/core.py | 25 | 5 -> 6 | survived |  | 01a14ae0-d4e6-7039-8b75-77d5689ae861 |
| m12-fbf40de850 | roman/core.py | 27 | 1 -> 2 | killed | test_sealed.TestToRoman.test_one | 01a14ae0-d576-7299-b395-e2b53bdd6743 |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `edcfc1dd15361897d421a2b3a116cdaed051c2952310ae91007b6cba510b3121`): OK (14 of 14 methods, each in its own process); binding ok; operation `01a14ae1-40cc-74ba-91b5-73fdcf257664`. Notes: Targeted boundary, type, subclass, and mutation checks not covered by sealed tests.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements to_roman with proper type checking (isinstance(n, int)), range validation (1 <= n <= 3999), and a greedy subtractive-notation conversion using the exact value-symbol pairs specified in the task (including 900='CM', 400='CD'). The existing test suite passes (2/2) and the implementer's sanity check reports 'All tests passed', indicating the acceptance criteria are met.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1361 | 2067 | 0 | 0.007562 | 25.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1482 | 617 | 0 | 0.001000 | 5.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1492 | 136 | 0 | 0.000570 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1661 | 143 | 0 | 0.000627 | 3.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1832 | 879 | 0 | 0.001341 | 8.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2001 | 905 | 0 | 0.001415 | 8.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2180 | 1762 | 0 | 0.002240 | 12.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2571 | 288 | 0 | 0.001030 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2714 | 878 | 0 | 0.001604 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 3266 | 191 | 0 | 0.001152 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1706 | 1267 | 0 | 0.001652 | 9.4s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2158 | 3590 | 0 | 0.012928 | 11.0s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 24424/12723/0; USD: 0.033121.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14add-f0eb-7650-91b3-f6cb329af905 | SUCCESS | 0 | 0.984s | retained | off | 0.00285832 |
| red-1 | 01a14ade-755b-73ed-9804-5e692738873f | SUCCESS | 0 | 3.821s | disposable | off | 0.03178091 |
| impl-tests-6 | 01a14adf-28b3-7348-8205-b4f8167ac367 | SUCCESS | 0 | 3.251s | disposable | off | 0.00285776 |
| impl-python-7 | 01a14adf-5b57-7790-9dc3-1e790df2c225 | SUCCESS | 0 | 11.412s | disposable | off | 0.00122751 |
| verify | 01a14adf-9fc7-70a1-ab43-8ba978ad19ea | SUCCESS | 0 | 23.113s | disposable | off | 0.03136164 |
| existing | 01a14ae0-02a4-77bb-b789-644609b7ad1d | SUCCESS | 0 | 23.082s | disposable | off | 0.00867917 |
| mutant-m01-f8722750e5 | 01a14ae0-70e1-7590-a04d-0df73565c45e | SUCCESS | 0 | 22.681s | disposable | off | 0.028995339999999998 |
| mutant-m03-f0a784727e | 01a14ae0-70c8-772d-a093-40a04c8d4d7d | SUCCESS | 0 | 23.25s | disposable | off | 0.028906539999999998 |
| mutant-m02-687dffd1ca | 01a14ae0-70cb-702a-9685-be607b180206 | SUCCESS | 0 | 23.251s | disposable | off | 0.028285820000000003 |
| mutant-m04-a5b6722f3a | 01a14ae0-70dc-7396-8bed-7b8e1642c1bc | SUCCESS | 0 | 22.662s | disposable | off | 0.0283285 |
| mutant-m05-c73302e8b5 | 01a14ae0-70f7-7229-9de1-91311f4dbdc7 | SUCCESS | 0 | 22.662s | disposable | off | 0.02870184 |
| mutant-m08-8d7ddce38a | 01a14ae0-70f0-768c-89cc-a2957c13f677 | SUCCESS | 0 | 22.663s | disposable | off | 0.028933940000000002 |
| mutant-m07-bf81179b5f | 01a14ae0-c4ac-75de-ba2c-38c1def01e8f | SUCCESS | 0 | 9.623s | disposable | off | 0.02823581 |
| mutant-m06-a57bbfbe33 | 01a14ae0-70f4-7598-9bce-992303503e69 | SUCCESS | 0 | 22.681s | disposable | off | 0.02874793 |
| mutant-m09-99ee8bf2a2 | 01a14ae0-d4d0-7618-a6f1-d709c7ea08b6 | SUCCESS | 0 | 14.515s | disposable | off | 0.028123500000000003 |
| mutant-m10-e0332a44cf | 01a14ae0-d43a-751c-9175-71634181a543 | SUCCESS | 0 | 15.022s | disposable | off | 0.02841005 |
| mutant-m11-345d5f0bb3 | 01a14ae0-d4e6-7039-8b75-77d5689ae861 | SUCCESS | 0 | 14.515s | disposable | off | 0.028178819999999997 |
| mutant-m12-fbf40de850 | 01a14ae0-d576-7299-b395-e2b53bdd6743 | SUCCESS | 0 | 14.516s | disposable | off | 0.028483340000000003 |
| breaker-tests | 01a14ae1-40cc-74ba-91b5-73fdcf257664 | SUCCESS | 0 | 3.655s | disposable | off | 0.028191720000000003 |

Sandbox operations: 19, total guest duration 297.359s, retained images ['355dc2f8-4d96-46a8-bdcd-23b8ab10dadd'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
