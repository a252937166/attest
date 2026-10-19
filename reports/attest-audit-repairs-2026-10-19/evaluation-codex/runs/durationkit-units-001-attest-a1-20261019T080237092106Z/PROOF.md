# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261019T080237092106Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T08:02:37.093666+00:00, finished 2026-10-19T08:18:03.805698+00:00.

**Accept this patch.** All 21 sealed tests pass on the candidate in a fresh sandbox, and 9 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 21 of 21 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 2 one-line change(s) to the patch were not caught by the sealed tests (score 0.833, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: drift audit: score 0.00, widened 0, unsupported claims 1

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 21 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 10 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 12 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 12 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 2 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 9 of 21 failed on the unmodified base; 21 of 21 pass on the candidate |
| E2 | Mutation check | pass | bound | 10 of 12 one-line mutants caught, 2 survived, 0 unknown; score 0.833 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 12 of 12 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ebe0984b-76ff-48f1-83a1-817543b9f6ed`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.5.0 revision `722cd6dd1a217c6d` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-audit-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer representing seconds or a sequence of integer-and-unit components using d, h, m, s and ms. Require unique units in strictly descending duration order, allow whitespace around the input and between complete components, and return total seconds as a float. Preserve the existing public import and tests, reject malformed strings with ValueError, and reject non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration (also durationkit.parse.parse_duration) | parse_duration(text: str) -> float | Accept strings, including str subclasses. After ignoring surrounding whitespace, accept either an uninterrupted sequence of ASCII digits interpreted as seconds, | TypeError: input is not an instance of str.; ValueError: input is empty or contains only whitespace.; ValueError: a number has a sign, decimal point, exponent,  |

Acceptance criteria:
AC1. 1. The imports from durationkit import parse_duration and from durationkit.parse import parse_duration remain available with signature parse_duration(text: str) -> float.
AC2. 2. Existing tests in tests/ pass unchanged using python -m unittest discover -s tests -t . -v.
AC3. 3. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0 and '0007' returns 7.0.
AC4. 4. Single components return the correct seconds: '2d' → 172800.0, '3h' → 10800.0, '15m' → 900.0, '45s' → 45.0 and '500ms' → 0.5.
AC5. 5. Combined components return the correct seconds: '1h30m' → 5400.0, '2d4h' → 187200.0, '1m1s' → 61.0, '1s500ms' → 1.5 and '1d1h1m1s1ms' → approximately 90061.001. Fractional results may be compared with normal floating-point tolerance.
AC6. 6. Units may be skipped: '1d1s' returns 86401.0 and '1h1ms' returns approximately 3600.001.
AC7. 7. Whitespace around the input and between complete components is accepted: ' 1h 30m ' and '\t1h\n30m\r' both return 5400.0.
AC8. 8. Leading zeros, zero-valued components and values above conventional clock ranges are accepted: '01h030m' returns 5400.0, '0s' and '0d0h0m0s0ms' return 0.0, '90m' returns 5400.0 and '1500ms' returns 1.5.
AC9. 9. Every accepted input returns a float, including inputs whose result is an integral number of seconds or zero.
AC10. 10. Empty and whitespace-only strings raise ValueError, including '', '   ' and '\t\n'.
AC11. 11. Signed, fractional and otherwise unsupported number syntax raises ValueError: '-1', '-1h', '+1', '+1h', '1.5h', '.5s', '1e3s', '1_000s' and '1,000s'.
AC12. 12. Unknown units, uppercase units and missing numbers raise ValueError: '1x', '1H', '1MS', 'h', 'ms' and 'abc'.
AC13. 13. Repeated units raise ValueError even when separated or zero-valued: '1h1h', '1h 0h', '0s0s' and '1ms1ms'.
AC14. 14. Components outside descending order raise ValueError: '30m1h', '1ms1s', '1s1d' and '0s0h'.
AC15. 15. Whitespace within a component or plain number raises ValueError: '1 h', '500 ms', '1\th' and '1 0'.
AC16. 16. Mixed bare and unit-bearing values and trailing malformed text raise ValueError: '1h30', '1 30m', '1h!', '1h,30m' and '1mss'.
AC17. 17. Non-decimal numeric characters raise ValueError both alone and in numeric positions, including 'Ⅰ', 'Ⅰh', '½', '½s', '①', '①m' and '²s'.
AC18. 18. Non-string inputs raise TypeError, including 90, 0.5, None, True, b'90' and [].
AC19. 19. Tests must not require either acceptance or rejection of non-ASCII Unicode decimal digits such as '١٢h' or '１２'.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing only durationkit/parse.py while preserving its signature and public export. The unchanged existing tests are compatible with the required syntax, validation rules and float results. Rule: a conflict is demonstrated only when it names existing acceptance criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `9e94441e65d21f97145def5eec6bada83b3676fd2f2c94ae5690ce526dee70e1`, 21 test methods, sealed at 2026-10-19T08:07:23.909055+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 21 methods: ERROR 9): 9 of 21 methods failing, 12 passing; operation `01a15333-5cfd-7530-aefe-2b8eb97cdee0`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_combined_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_can_exceed_clock_ranges | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_strings | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros_in_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_mixed_bare_values_and_unmatched_trailing_text | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_decimal_numeric_characters | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_public_imports_and_signature | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_str_subclass_is_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_decimal_digits_may_be_accepted_or_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_out_of_descending_order | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_uppercase_and_numberless_units | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unsupported_number_syntax | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_valid_results_are_floats | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_complete_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_number_or_component | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_valued_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -2,14 +2,46 @@
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse non-negative seconds or descending duration components."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+
+    def is_digit(char: str) -> bool:
+        return "0" <= char <= "9"
+
+    if all(is_digit(char) for char in stripped):
+        return float(stripped)
+
+    units = (("d", 86400), ("h", 3600), ("m", 60), ("s", 1), ("ms", 0.001))
+    position = 0
+    previous_rank = -1
+    total = 0.0
+
+    while position < len(stripped):
+        start = position
+        while position < len(stripped) and is_digit(stripped[position]):
+            position += 1
+        if position == start:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        for rank, (unit, multiplier) in enumerate(units):
+            if unit == "m" and stripped.startswith("ms", position):
+                continue
+            if stripped.startswith(unit, position):
+                break
+        else:
+            raise ValueError(f"unsupported duration: {text!r}")
+        if rank <= previous_rank:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        total += int(stripped[start:position]) * multiplier
+        previous_rank = rank
+        position += len(unit)
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (39 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (21 of 21 methods, each in its own process). Operation `01a15339-e081-73de-b2a6-0b73fbcd1f14`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a1533a-0ccd-7487-881f-f20604253e54`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.833 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (12 of 12 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 10 killed, 2 survived, 0 unknown; mutation score 0.833 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-9f51ab71c6 | durationkit/parse.py | 10 | remove `not` | killed | test_sealed.ParseDurationAcceptanceTests.test_public_imports_and_signature, test_sealed.ParseDurationAcceptanceTests.tes | 01a1533a-298d-70d9-957b-b2e6a8980641 |
| m02-f9cfc0891c | durationkit/parse.py | 14 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_public_imports_and_signature, test_sealed.ParseDurationAcceptanceTests.tes | 01a1533a-29a5-75d5-b0e9-dccc7f5fb8cc |
| m03-b991ef5c0c | durationkit/parse.py | 19 | 3600 -> 3601 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1533a-295b-75e9-899b-ecba9169299b |
| m04-9aefa0231e | durationkit/parse.py | 19 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1533a-299e-7419-9752-27efdc45965f |
| m05-4c89317123 | durationkit/parse.py | 21 | 1 -> 2 | survived |  | 01a1533a-29bf-7584-a385-b9745c2d6f84 |
| m06-f8f32175b1 | durationkit/parse.py | 26 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_mixed_bare_values_and_unmatched_trailing_text | 01a1533a-29a8-72f9-a74c-e1e9181cc670 |
| m07-4469f03e00 | durationkit/parse.py | 27 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1533a-29c5-7658-a141-a6b3942b0519 |
| m08-8574f402f5 | durationkit/parse.py | 29 | raise -> pass | survived |  | 01a1533a-2a38-71fe-8352-9e31b279aa03 |
| m09-6c6303ae8d | durationkit/parse.py | 32 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1533a-655e-729e-8df1-91094d9df92c |
| m10-e953214af0 | durationkit/parse.py | 38 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units | 01a1533a-65a9-7560-856b-4a80c3aaa925 |
| m11-71a98c3192 | durationkit/parse.py | 41 | Mult -> Div | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1533a-65c9-758d-af8e-3c876a4a59a3 |
| m12-e7bb8d0985 | durationkit/parse.py | 44 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1533a-65f2-7441-b8ba-e416c7170373 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `3f12372a7d4cdfc2b113ecfcdf5788a76d6488d4d6ead560fb871f18805beefc`): OK (12 of 12 methods, each in its own process); binding ok; operation `01a1533c-17e3-74a0-945b-0f3d37407a5d`. Notes: Targets all unit subsequences, whitespace boundaries, millisecond ambiguity, ordering, complete consumption, and numeric type edges.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated task: ASCII digit scanning, the special handling of the 'ms' prefix, 'rank <= previous_rank', and inter-component 'isspace()' enforce the required syntax and ordering while preserving float returns and TypeError for non-strings. Only durationkit/parse.py changes, and the observed existing test run passes all six tests; no scope narrowing or widening is evident.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: “all stated valid and invalid examples were checked” — the observed run_python output only says “Contract examples passed”; the executed checks are not shown, so exhaustive coverage cannot be verified.

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10754 | 1533 | 7680 | - | 68.2s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12085 | 88 | 7552 | - | 75.7s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11190 | 2784 | 0 | - | 109.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11099 | 89 | 0 | - | 19.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22827 | 810 | 11136 | - | 62.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 23981 | 303 | 11776 | - | 37.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12100 | 114 | 0 | - | 105.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12348 | 800 | 0 | - | 42.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 13073 | 203 | 0 | - | 133.9s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11458 | 2150 | 0 | - | 97.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12217 | 237 | 0 | - | 71.7s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 153132/9111/38144; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1532f-4977-76a8-92c8-87d1a1b54551 | SUCCESS | 0 | 0.83s | retained | off | 0.0028663399999999998 |
| red-1 | 01a15333-5cfd-7530-aefe-2b8eb97cdee0 | SUCCESS | 0 | 4.824s | disposable | off | 0.03979398 |
| impl-tests-4 | 01a15337-004e-7269-8aa2-ac446c50550d | SUCCESS | 0 | 0.791s | disposable | off | 0.0028231099999999998 |
| impl-python-5 | 01a15337-b9c4-75d7-97cd-b13f0d8e1c8a | SUCCESS | 0 | 0.578s | disposable | off | 0.00124053 |
| verify | 01a15339-e081-73de-b2a6-0b73fbcd1f14 | SUCCESS | 0 | 4.745s | disposable | off | 0.03956911 |
| existing | 01a1533a-0ccd-7487-881f-f20604253e54 | SUCCESS | 0 | 2.162s | disposable | off | 0.01518072 |
| mutant-m02-f9cfc0891c | 01a1533a-29a5-75d5-b0e9-dccc7f5fb8cc | SUCCESS | 0 | 4.486s | disposable | off | 0.03645668999999999 |
| mutant-m01-9f51ab71c6 | 01a1533a-298d-70d9-957b-b2e6a8980641 | SUCCESS | 0 | 4.508s | disposable | off | 0.03665919 |
| mutant-m04-9aefa0231e | 01a1533a-299e-7419-9752-27efdc45965f | SUCCESS | 0 | 4.509s | disposable | off | 0.03649442 |
| mutant-m03-b991ef5c0c | 01a1533a-295b-75e9-899b-ecba9169299b | SUCCESS | 0 | 4.495s | disposable | off | 0.03687057 |
| mutant-m07-4469f03e00 | 01a1533a-29c5-7658-a141-a6b3942b0519 | SUCCESS | 0 | 4.529s | disposable | off | 0.03678993 |
| mutant-m05-4c89317123 | 01a1533a-29bf-7584-a385-b9745c2d6f84 | SUCCESS | 0 | 4.485s | disposable | off | 0.03638937 |
| mutant-m08-8574f402f5 | 01a1533a-2a38-71fe-8352-9e31b279aa03 | SUCCESS | 0 | 4.432s | disposable | off | 0.0362717 |
| mutant-m06-f8f32175b1 | 01a1533a-29a8-72f9-a74c-e1e9181cc670 | SUCCESS | 0 | 4.529s | disposable | off | 0.036890589999999994 |
| mutant-m09-6c6303ae8d | 01a1533a-655e-729e-8df1-91094d9df92c | SUCCESS | 0 | 4.381s | disposable | off | 0.03647899 |
| mutant-m10-e953214af0 | 01a1533a-65a9-7560-856b-4a80c3aaa925 | SUCCESS | 0 | 4.504s | disposable | off | 0.0366998 |
| mutant-m11-71a98c3192 | 01a1533a-65c9-758d-af8e-3c876a4a59a3 | SUCCESS | 0 | 4.45s | disposable | off | 0.03639563 |
| mutant-m12-e7bb8d0985 | 01a1533a-65f2-7441-b8ba-e416c7170373 | SUCCESS | 0 | 4.525s | disposable | off | 0.03664324 |
| breaker-tests | 01a1533c-17e3-74a0-945b-0f3d37407a5d | SUCCESS | 0 | 3.211s | disposable | off | 0.02495432 |

Sandbox operations: 19, total guest duration 70.974s, retained images ['ebe0984b-76ff-48f1-83a1-817543b9f6ed'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
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
