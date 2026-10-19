# Attest Proof Bundle: roman-to-numeral

**Verdict: VERIFIED**  
Run `roman-to-numeral-attest-a1-20261019T041712703144Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:17:12.703747+00:00, finished 2026-10-19T04:31:16.799836+00:00.

**Accept this patch.** All 13 sealed tests pass on the candidate in a fresh sandbox, and 9 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 13 of 13 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.917, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 13 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
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
| E1 | Sealed tests, written before the patch | pass | bound | 9 of 13 failed on the unmodified base; 13 of 13 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `roman-to-numeral`, spec digest `8e0781e39135d0d1bedc4361e0e17c603e03ecf956bda7cf92bdc1ba5a4d5257`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `edb43393-63cd-49a4-ba63-2342c46f4233`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int (for example '5', 5.0, None, [1]); numeric strings and integral floats are not coerced. Type discipline is by value: an instance of an int subclass (for example an IntEnum member or `class PlainInt(int)`) is accepted and converted exactly like the int with the same value, including the range check. Int subclasses that override arithmetic or comparison operators are out of scope: their behaviour is unspecified and tests must not depend on it. bool is a subclass of int; rejecting True and False with TypeError is permitted but not required, and tests must not depend on either choice. Do not change is_roman_numeral or the tests.

## 2. Specification and contract
Feasible: True. Implement roman.core.to_roman(n), available through from roman import to_roman, to return the canonical uppercase Roman numeral string for integer values from 1 through 3999 using standard subtractive notation. Accept ordinary int subclasses by value, reject non-int inputs without coercion, and raise ValueError for out-of-range integers. Preserve is_roman_numeral and existing tests. Boolean handling and behavior for int subclasses overriding arithmetic or comparison operators are excluded from testing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| roman.to_roman | to_roman(n) | Return a str representing n in canonical uppercase Roman notation for 1 <= n <= 3999. Canonical notation concatenates thousands, hundreds, tens, and units in de | ValueError: an int or supported int subclass instance has value less than 1 or greater than 3999, excluding bool from required assertions.; TypeError: input is  |
| roman.is_roman_numeral | is_roman_numeral(s) | Preserve the existing implementation: return True exactly when s is a nonempty str and every character in s.upper() belongs to IVXLCDM. This checks letters, not | Ordinary non-string inputs return False without raising an exception. |

Acceptance criteria:
AC1. 1. from roman import to_roman and from roman import is_roman_numeral continue to work, with their existing one-argument signatures.
AC2. 2. For every integer n from 1 through 3999, to_roman(n) returns a str equal to the concatenation of the canonical representations of its decimal places: thousands ['', 'M', 'MM', 'MMM']; hundreds ['', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM']; tens ['', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC']; units ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']. Each table is indexed by the corresponding decimal digit.
AC3. 3. to_roman(1) == 'I', to_roman(4) == 'IV', to_roman(9) == 'IX', to_roman(40) == 'XL', to_roman(90) == 'XC', to_roman(400) == 'CD', and to_roman(900) == 'CM'.
AC4. 4. to_roman(2024) == 'MMXXIV', to_roman(1994) == 'MCMXCIV', and to_roman(3999) == 'MMMCMXCIX'.
AC5. 5. Integer values outside 1..3999 raise ValueError, including 0, -1, and 4000.
AC6. 6. Non-int inputs raise TypeError without coercion, including '5', 5.0, None, and [1].
AC7. 7. Instances of int subclasses that do not override arithmetic or comparison operators convert identically to equal ints throughout the supported range; specifically, PlainInt(49) and an IntEnum member with value 49 return 'XLIX'.
AC8. 8. Supported int subclass instances outside the range raise ValueError, including PlainInt and IntEnum values of 0, -1, and 4000.
AC9. 9. is_roman_numeral retains its letter-only validation behavior: 'XIV', 'mmxxiv', and 'IIII' return True; '', 'ABC', and 14 return False. Its implementation remains unchanged.
AC10. 10. Existing test files remain unchanged and existing tests continue to pass.
AC11. 11. Tests make no assertions about True or False inputs, or int subclasses that override arithmetic or comparison operators.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by implementing only roman/core.py's to_roman stub with integer type and range checks followed by canonical decimal-place lookup. The existing exports, unchanged letter-only validator, and existing tests impose no conflicting requirements. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `e7715a21ecd7f9ba63c5679b0b522ae90c7bdee3ad5def60773e71b15476a73d`, 13 test methods, sealed at 2026-10-19T04:22:27.322154+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 13 methods: ERROR 9): 9 of 13 methods failing, 4 passing; operation `01a15265-833f-71ed-a21d-b40909f73f12`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestRomanNumeralHelper.test_helper_accepts_roman_letters_without_requiring_canonical_syntax | ok (1 ev) | ok (1 ev) |
| test_sealed.TestRomanNumeralHelper.test_helper_has_one_argument_signature | ok (1 ev) | ok (1 ev) |
| test_sealed.TestRomanNumeralHelper.test_helper_rejects_empty_foreign_letters_and_nonstrings | ok (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_int_enum_member_converts_by_integer_value | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_mixed_place_values_and_maximum | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_non_int_inputs_raise_type_error_without_coercion | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_out_of_range_int_enum_members_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_out_of_range_integers_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_out_of_range_plain_int_subclasses_raise_value_error | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_plain_int_subclass_matches_int_throughout_supported_range | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_subtractive_boundary_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestToRoman.test_to_roman_has_one_argument_signature | ok (1 ev) | ok (1 ev) |


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

Sealed suite: OK (13 of 13 methods, each in its own process). Operation `01a1526b-5b1c-7712-81f0-a2b730767e70`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (2 of 2 methods, each in its own process) (2 passed of 2); operation `01a1526b-72f5-7043-a827-04da3e481dae`, bound through the supervisor: 1 module(s), binding ok.

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

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-87afd84a52 | roman/core.py | 10 | remove `not` | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-810b-75a8-8fb9-bd623284bcec |
| m02-130fe74269 | roman/core.py | 11 | raise -> pass | survived |  | 01a1526b-8111-7149-9298-19892a7641da |
| m03-f05f697a13 | roman/core.py | 12 | 3999 -> 4000 | killed | test_sealed.TestToRoman.test_out_of_range_integers_raise_value_error, test_sealed.TestToRoman.test_out_of_range_plain_in | 01a1526b-81a7-7468-9826-0ee58fba3bac |
| m04-c8342a0eb2 | roman/core.py | 12 | LtE -> Lt | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-80e7-76ed-92f4-bca9dc3cc031 |
| m05-48504acece | roman/core.py | 13 | raise -> pass | killed | test_sealed.TestToRoman.test_out_of_range_integers_raise_value_error, test_sealed.TestToRoman.test_out_of_range_plain_in | 01a1526b-80ea-76dd-9b2b-62c74848b6cf |
| m06-fa01a535be | roman/core.py | 19 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-812d-7471-ad92-7dbb14b12ca3 |
| m07-448e6e34ab | roman/core.py | 19 | FloorDiv -> Mult | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-80f2-7593-8815-04607bd0e142 |
| m08-f7831d6fc5 | roman/core.py | 19 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-8107-726e-bbd5-fe3e82a5212c |
| m09-7a0f5af280 | roman/core.py | 19 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-9918-72a1-8244-18b26b5bda2b |
| m10-e563251b42 | roman/core.py | 19 | 10 -> 11 | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-9ae5-73fe-837b-e91d547ef749 |
| m11-8a5ef4ff26 | roman/core.py | 19 | Add -> Sub | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-9ae3-72a8-9bcb-43024b5b7743 |
| m12-b58ab80b9c | roman/core.py | 19 | Mod -> Sub | killed | test_sealed.TestToRoman.test_every_supported_integer_matches_canonical_place_value_tables, test_sealed.TestToRoman.test_ | 01a1526b-9ae0-7643-b547-24a0f98d7325 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `f33f821cbf25699e6cea6ba2521eeb5ef5825b895b0254ba9478cd20db5cdb5b`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a1526c-cb4e-762f-9b97-11c432bac482`. Notes: Targets non-coercion, IntEnum combinations, Unicode uppercase behavior, letter-only validation, and consistency between conversion and validation.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(n, int)` accepts supported int subclasses, `if not 1 <= n <= 3999` enforces the range, and the decimal-place tables produce canonical subtractive notation. Only to_roman changes, preserving is_roman_numeral and tests; observed outputs report two existing tests passing and successful exhaustive conversion and error checks, though the check script itself is not shown.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10403 | 1099 | 0 | - | 98.2s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11399 | 107 | 0 | - | 79.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10581 | 2823 | 0 | - | 120.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10584 | 106 | 7168 | - | 161.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10768 | 394 | 0 | - | 61.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11121 | 77 | 7168 | - | 71.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11257 | 499 | 7168 | - | 35.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11740 | 148 | 7168 | - | 39.6s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10710 | 2188 | 0 | - | 71.4s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11399 | 183 | 0 | - | 53.0s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 109962/7624/28672; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15260-d7b4-775b-91bc-6547a615589a | SUCCESS | 0 | 0.781s | retained | off | 0.00288054 |
| red-1 | 01a15265-833f-71ed-a21d-b40909f73f12 | SUCCESS | 0 | 3.836s | disposable | off | 0.03145743 |
| impl-tests-3 | 01a1526a-1a74-76b8-ad28-516e09e5fadd | SUCCESS | 0 | 0.758s | disposable | off | 0.0028642499999999996 |
| impl-python-4 | 01a1526a-b08f-763c-9a90-c67ea6996598 | SUCCESS | 0 | 0.59s | disposable | off | 0.00151864 |
| verify | 01a1526b-5b1c-7712-81f0-a2b730767e70 | SUCCESS | 0 | 3.389s | disposable | off | 0.02727877 |
| existing | 01a1526b-72f5-7043-a827-04da3e481dae | SUCCESS | 0 | 1.419s | disposable | off | 0.008783349999999999 |
| mutant-m02-130fe74269 | 01a1526b-8111-7149-9298-19892a7641da | SUCCESS | 0 | 3.088s | disposable | off | 0.02395403 |
| mutant-m03-f05f697a13 | 01a1526b-81a7-7468-9826-0ee58fba3bac | SUCCESS | 0 | 3.106s | disposable | off | 0.02424758 |
| mutant-m01-87afd84a52 | 01a1526b-810b-75a8-8fb9-bd623284bcec | SUCCESS | 0 | 3.482s | disposable | off | 0.028493789999999998 |
| mutant-m04-c8342a0eb2 | 01a1526b-80e7-76ed-92f4-bca9dc3cc031 | SUCCESS | 0 | 3.092s | disposable | off | 0.02399685 |
| mutant-m06-fa01a535be | 01a1526b-812d-7471-ad92-7dbb14b12ca3 | SUCCESS | 0 | 3.623s | disposable | off | 0.029251020000000003 |
| mutant-m05-48504acece | 01a1526b-80ea-76dd-9b2b-62c74848b6cf | SUCCESS | 0 | 3.091s | disposable | off | 0.02401915 |
| mutant-m07-448e6e34ab | 01a1526b-80f2-7593-8815-04607bd0e142 | SUCCESS | 0 | 3.359s | disposable | off | 0.026932189999999998 |
| mutant-m08-f7831d6fc5 | 01a1526b-8107-726e-bbd5-fe3e82a5212c | SUCCESS | 0 | 3.314s | disposable | off | 0.02638884 |
| mutant-m09-7a0f5af280 | 01a1526b-9918-72a1-8244-18b26b5bda2b | SUCCESS | 0 | 3.413s | disposable | off | 0.0272519 |
| mutant-m10-e563251b42 | 01a1526b-9ae5-73fe-837b-e91d547ef749 | SUCCESS | 0 | 3.536s | disposable | off | 0.02762566 |
| mutant-m11-8a5ef4ff26 | 01a1526b-9ae3-72a8-9bcb-43024b5b7743 | SUCCESS | 0 | 3.69s | disposable | off | 0.03002083 |
| mutant-m12-b58ab80b9c | 01a1526b-9ae0-7643-b547-24a0f98d7325 | SUCCESS | 0 | 3.617s | disposable | off | 0.02906433 |
| breaker-tests | 01a1526c-cb4e-762f-9b97-11c432bac482 | SUCCESS | 0 | 2.755s | disposable | off | 0.02091118 |

Sandbox operations: 19, total guest duration 53.939s, retained images ['edb43393-63cd-49a4-ba63-2342c46f4233'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion is never overridden. The classification itself remains a model judgement.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
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
