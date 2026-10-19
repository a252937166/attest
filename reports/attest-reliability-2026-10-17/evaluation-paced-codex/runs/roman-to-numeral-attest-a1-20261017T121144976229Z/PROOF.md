# Attest Proof Bundle: roman-to-numeral

**Verdict: VERIFIED**  
Run `roman-to-numeral-attest-a1-20261017T121144976229Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T12:11:44.976396+00:00, finished 2026-10-17T12:18:13.491512+00:00.

**Accept this patch.** All 15 sealed tests pass on the candidate in a fresh sandbox, and 11 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 15 of 15 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.917, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 15 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 11 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 4 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 11 of 15 failed on the unmodified base; 15 of 15 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e9171ae7-23a4-4c60-8611-ebfa9f9c8dc0`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `b7fdd9eb0b71d237` (34 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-reliability-2026-10-17/evaluation-paced-codex/snapshot/attest`.
Pacing (development gateway): 54 of an assumed 60 requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement the existing to_roman(n) stub in roman/core.py, retaining access through from roman import to_roman. Convert integers from 1 through 3999 inclusive into canonical uppercase Roman numeral strings using subtractive notation. Accept int subclass instances according to their integer value, reject non-int inputs without coercion, and raise ValueError for out-of-range integers. Preserve is_roman_numeral and all existing tests. Boolean handling and int subclasses that override arithmetic or comparison operators are excluded from required verification.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| roman.to_roman | to_roman(n) | For an int value n in 1..3999, return a str containing its canonical uppercase Roman numeral, with no whitespace. Construct the representation by concatenating  | TypeError: n is not an instance of int; do not coerce strings, floats, None, containers, or other non-int objects.; ValueError: n is an int with value less than |
| roman.is_roman_numeral | is_roman_numeral(s) | Preserve the existing implementation: return True precisely when s is a non-empty str and every character in s.upper() belongs to 'IVXLCDM'; otherwise return Fa | Ordinary non-string inputs return False rather than raising a type-validation exception. |

Acceptance criteria:
1. 1. from roman import to_roman and from roman import is_roman_numeral continue to succeed.
2. 2. Every integer n from 1 through 3999 returns a str equal to the canonical place-value representation defined in the interface contract, with uppercase letters and no whitespace.
3. 3. to_roman(1) == 'I', to_roman(4) == 'IV', and to_roman(9) == 'IX'.
4. 4. to_roman(40) == 'XL', to_roman(90) == 'XC', to_roman(400) == 'CD', and to_roman(900) == 'CM'.
5. 5. to_roman(2024) == 'MMXXIV', to_roman(3999) == 'MMMCMXCIX', and to_roman(1994) == 'MCMXCIV'.
6. 6. Integer inputs outside 1..3999 raise ValueError, including 0, -1, and 4000.
7. 7. Non-int inputs raise TypeError without coercion, including '5', 5.0, None, and [1].
8. 8. Supported int subclass instances in range convert exactly like their equal int values; verify a plain int subclass instance with value 49 returns 'XLIX' and an IntEnum member with an in-range value returns the corresponding numeral.
9. 9. Supported int subclass instances outside the range raise ValueError; verify subclass values 0, -1, and 4000.
10. 10. is_roman_numeral retains its existing behavior: 'XIV', 'mmxxiv', and noncanonical letter sequences such as 'IIII' return True; '', 'ABC', and 14 return False.
11. 11. The implementation of is_roman_numeral and all existing test files remain unchanged, and the existing tests pass.
12. 12. Verification imposes no requirements on boolean inputs or int subclasses overriding arithmetic or comparison operators.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `dfaa300c1d20f6ca884301b0fdadaa8b5e2d23eca55ce8e7622209091be99832`, 15 test methods, sealed at 2026-10-17T12:13:31.475757+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (11 of 15 methods: ERROR 11): 11 of 15 methods failing, 4 passing; operation `01a149c8-0e1c-7657-8c83-774a21371910`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsRomanNumeral.test_accepts_noncanonical_roman_letter_sequences | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_accepts_uppercase_and_lowercase_roman_letters | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_non_string_inputs_return_false | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsRomanNumeral.test_rejects_empty_and_invalid_strings | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_hundreds_subtractive_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_enum_uses_its_integer_value | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_multi_place_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_non_int_inputs_raise_type_error_without_coercion | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_out_of_range_int_subclasses_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_out_of_range_ints_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_plain_int_subclass_uses_its_integer_value | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_result_is_a_string | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_tens_subtractive_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_unit_subtractive_examples | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/roman/core.py
+++ b/roman/core.py
@@ -7,4 +7,13 @@
 
 
 def to_roman(n):
-    raise NotImplementedError("to_roman is not implemented yet")
+    if not isinstance(n, int):
+        raise TypeError("n must be an integer")
+    if not 1 <= n <= 3999:
+        raise ValueError("n must be between 1 and 3999")
+
+    thousands = ("", "M", "MM", "MMM")
+    hundreds = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
+    tens = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
+    units = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
+    return thousands[n // 1000] + hundreds[n // 100 % 10] + tens[n // 10 % 10] + units[n % 10]
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (10 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (15 of 15 methods, each in its own process). Operation `01a149ca-9ca3-72b6-8383-f6863e6160ec`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a149ca-b8b7-756b-a8fc-3729b2b0864b`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (2 of 2 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.917 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-87afd84a52 | roman/core.py | 10 | remove `not` | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_result_is | 01a149ca-cdfc-746b-a1a3-e3b81be8203a |
| m02-130fe74269 | roman/core.py | 11 | raise -> pass | survived |  | 01a149ca-cdc4-713f-881d-0be3bb529613 |
| m03-f05f697a13 | roman/core.py | 12 | 3999 -> 4000 | killed | test_sealed.TestToRoman.test_out_of_range_ints_raise_value_error, test_sealed.TestToRoman.test_out_of_range_int_subclass | 01a149ca-cd72-7605-844f-c0a952f80ad8 |
| m04-c8342a0eb2 | roman/core.py | 12 | LtE -> Lt | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_multi_pla | 01a149ca-cdda-758d-8ba1-78835e7da360 |
| m05-48504acece | roman/core.py | 13 | raise -> pass | killed | test_sealed.TestToRoman.test_out_of_range_ints_raise_value_error, test_sealed.TestToRoman.test_out_of_range_int_subclass | 01a149ca-cd59-704e-b884-9a313d656394 |
| m06-fa01a535be | roman/core.py | 19 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_result_is | 01a149ca-cdc3-70cd-90c5-cf900be06baa |
| m07-448e6e34ab | roman/core.py | 19 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_hundreds_ | 01a149ca-cde1-75ef-a97d-eecc8840c665 |
| m08-f7831d6fc5 | roman/core.py | 19 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_multi_pla | 01a149ca-cdc6-742a-b178-703fd4e72a72 |
| m09-7a0f5af280 | roman/core.py | 19 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_tens_subt | 01a149ca-f139-75f6-825c-e75a87417311 |
| m10-e563251b42 | roman/core.py | 19 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_hundreds_ | 01a149ca-f2c6-709b-bdeb-c7ae053458bd |
| m11-8a5ef4ff26 | roman/core.py | 19 | Add -> Sub | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_result_is | 01a149ca-f3aa-7454-844b-97d2b4aa6ca5 |
| m12-b58ab80b9c | roman/core.py | 19 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_in_range_value_matches_canonical_place_values, test_sealed.TestToRoman.test_tens_subt | 01a149ca-f3cc-74fc-8a6d-8a172f37fa84 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `d68c4fa095097c9218f56b6edd046e378b1e87989c344f34e9ad827b63ad54af`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a149cb-ed93-748d-b3e4-1d669b26dec9`. Notes: Targets subclass boundaries, non-int numeric inputs, place carries, and Unicode uppercase behavior in the preserved validator.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(n, int)` accepts supported int subclasses, `if not 1 <= n <= 3999` enforces the range, and the four place-value tables produce canonical subtractive Roman numerals. Only to_roman changes; observed tool output reports both existing tests passing and successful verification of all 3999 values, subclass cases, errors, and helper behavior.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10405 | 1088 | 0 | - | 46.6s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10399 | 1693 | 0 | - | 41.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10440 | 117 | 0 | - | 25.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10615 | 383 | 0 | - | 37.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10965 | 81 | 7168 | - | 30.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11097 | 583 | 7168 | - | 29.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11627 | 137 | 7168 | - | 30.3s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10658 | 2251 | 0 | - | 55.0s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11386 | 125 | 0 | - | 28.2s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 97592/6458/21504; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a149c6-94e2-7236-a7e0-d3bb9308bedc | SUCCESS | 0 | 0.807s | retained | off | 0.0028404499999999996 |
| red-1 | 01a149c8-0e1c-7657-8c83-774a21371910 | SUCCESS | 0 | 3.857s | disposable | off | 0.032309 |
| impl-tests-3 | 01a149c9-9550-759f-ac1c-06617a8ad71f | SUCCESS | 0 | 0.733s | disposable | off | 0.00273552 |
| impl-python-4 | 01a149ca-1857-72ab-b6da-6b33bd85309e | SUCCESS | 0 | 0.568s | disposable | off | 0.0014392900000000002 |
| verify | 01a149ca-9ca3-72b6-8383-f6863e6160ec | SUCCESS | 0 | 3.683s | disposable | off | 0.030091749999999997 |
| existing | 01a149ca-b8b7-756b-a8fc-3729b2b0864b | SUCCESS | 0 | 1.389s | disposable | off | 0.008648280000000001 |
| mutant-m02-130fe74269 | 01a149ca-cdc4-713f-881d-0be3bb529613 | SUCCESS | 0 | 3.446s | disposable | off | 0.027200079999999998 |
| mutant-m01-87afd84a52 | 01a149ca-cdfc-746b-a1a3-e3b81be8203a | SUCCESS | 0 | 3.617s | disposable | off | 0.02878646 |
| mutant-m04-c8342a0eb2 | 01a149ca-cdda-758d-8ba1-78835e7da360 | SUCCESS | 0 | 3.446s | disposable | off | 0.02700534 |
| mutant-m03-f05f697a13 | 01a149ca-cd72-7605-844f-c0a952f80ad8 | SUCCESS | 0 | 3.266s | disposable | off | 0.0266348 |
| mutant-m05-48504acece | 01a149ca-cd59-704e-b884-9a313d656394 | SUCCESS | 0 | 3.349s | disposable | off | 0.02666462 |
| mutant-m06-fa01a535be | 01a149ca-cdc3-70cd-90c5-cf900be06baa | SUCCESS | 0 | 3.682s | disposable | off | 0.0292781 |
| mutant-m07-448e6e34ab | 01a149ca-cde1-75ef-a97d-eecc8840c665 | SUCCESS | 0 | 3.692s | disposable | off | 0.029611619999999998 |
| mutant-m08-f7831d6fc5 | 01a149ca-cdc6-742a-b178-703fd4e72a72 | SUCCESS | 0 | 3.53s | disposable | off | 0.028033199999999998 |
| mutant-m09-7a0f5af280 | 01a149ca-f139-75f6-825c-e75a87417311 | SUCCESS | 0 | 3.645s | disposable | off | 0.0299554 |
| mutant-m10-e563251b42 | 01a149ca-f2c6-709b-bdeb-c7ae053458bd | SUCCESS | 0 | 3.725s | disposable | off | 0.03013844 |
| mutant-m11-8a5ef4ff26 | 01a149ca-f3aa-7454-844b-97d2b4aa6ca5 | SUCCESS | 0 | 3.704s | disposable | off | 0.029824919999999998 |
| mutant-m12-b58ab80b9c | 01a149ca-f3cc-74fc-8a6d-8a172f37fa84 | SUCCESS | 0 | 3.661s | disposable | off | 0.029402550000000003 |
| breaker-tests | 01a149cb-ed93-748d-b3e4-1d669b26dec9 | SUCCESS | 0 | 2.699s | disposable | off | 0.020640949999999998 |

Sandbox operations: 19, total guest duration 56.499s, retained images ['e9171ae7-23a4-4c60-8611-ebfa9f9c8dc0'].

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
