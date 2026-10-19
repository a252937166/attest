# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261019T043122954196Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:31:22.955520+00:00, finished 2026-10-19T04:43:02.871844+00:00.

**Accept this patch.** All 22 sealed tests pass on the candidate in a fresh sandbox, and 8 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 22 of 22 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 3 one-line change(s) to the patch were not caught by the sealed tests (score 0.75, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4). 2 of the tests written after the patch failed as written and were corrected by the arbiter; the correction kept every test method, changed only the failing ones, passes on the candidate and discriminates (2 of 2 corrected test(s) fail on the unmodified base), and the gate was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: arbitration (validated corrections re-run their gates): all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (2 of 2 corrected test(s) fail on the unmodified base); the affected gate(s) are re-run on the corrected modules

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 22 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 8 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 14 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 3 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, but which side was wrong is a model judgement; the original tests and results are preserved (E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 8 of 22 failed on the unmodified base; 22 of 22 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 12 one-line mutants caught, 3 survived, 0 unknown; score 0.75 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 2 of 10 failed as written (test_large_millisecond_value_with_finite_seconds, test_large_millisecond_value_in_combination); 2 test(s) corrected by the arbiter and validated (2 of 2 corrected test(s) fail on the unmodified base); the corrected module passes (OK (10 of 10 methods, each in its own process)) |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (2 of 2 corrected test(s) fail on the unmodified base); the affected gate(s) are re-run on the corrected modules |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `bd4c4d49-6f89-4995-a6ff-1c35cbe7e64a`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either plain non-negative integer seconds or one or more integer-and-unit components using d, h, m, s, and ms, returning total seconds as a float. Require unique units in strictly descending order, permit surrounding whitespace and whitespace between complete components, reject malformed input with ValueError, and preserve TypeError for non-string input. Preserve the public import and all existing tests without modifying them.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also available from durationkit.parse. Accept a string whose stripped content is either a nonempty sequence of ASCII digits representing seconds, or a sequence  | TypeError: text is not an instance of str.; ValueError: input is empty or contains only whitespace.; ValueError: a number has a sign, fractional part, exponent, |

Acceptance criteria:
AC1. 1. The existing tests in tests/ remain unchanged and pass using python -m unittest discover -s tests -t . -v; from durationkit import parse_duration continues to work.
AC2. 2. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0, and '0007' returns 7.0.
AC3. 3. Single components return the specified seconds: '2d' → 172800.0, '3h' → 10800.0, '15m' → 900.0, '45s' → 45.0, and '500ms' → 0.5.
AC4. 4. Ordered combinations work with adjacent components: '1h30m' → 5400.0, '2d4h' → 187200.0, '1m1s' → 61.0, '1s500ms' → 1.5, and '1d1h1m1s1ms' → 90061.001. Compare fractional results with ordinary floating-point tolerance.
AC5. 5. Units may be skipped: '1d1ms' returns approximately 86400.001. Values need not fit clock ranges: '90m' returns 5400.0 and '1500ms' returns 1.5.
AC6. 6. Zero-valued components and leading zeros are accepted: '0s' returns 0.0, '0d0h0m0s0ms' returns 0.0, and '001h030m' returns 5400.0.
AC7. 7. Whitespace recognized by str.isspace() is accepted around the input and between components: ' 1h 30m ' and '\t1h\n30m\r' return 5400.0.
AC8. 8. Every accepted input returns a float, including plain integers, zero, whole-second unit durations, and millisecond durations.
AC9. 9. Empty and whitespace-only strings raise ValueError, including '', '   ', and '\t\n'.
AC10. 10. Invalid numeric syntax raises ValueError in either form: examples include '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3', '1e3s', and '1_000s'.
AC11. 11. Unknown or incorrectly cased units and missing numbers raise ValueError: '1x', '1H', '1MS', 'h', 'ms', and 'abc'.
AC12. 12. Repeated units raise ValueError even when separated by whitespace or carrying zero: '1h1h', '1ms 2ms', and '0s0s'.
AC13. 13. Components out of descending order raise ValueError, including '30m1h', '1ms1s', '1s1m', and '0ms0s'.
AC14. 14. Split components, split numbers, mixed forms, and trailing garbage raise ValueError: '1 h', '1 m s', '1 0s', '1h30', '1 2', '1h,30m', and '1s!'.
AC15. 15. Non-decimal numeric characters raise ValueError in both plain and component forms, including '²', '²h', 'Ⅳ', 'Ⅳh', '½', '½h', '①', and '①h'. Tests must not assert acceptance or rejection for non-ASCII Unicode decimal digits such as Arabic-Indic or fullwidth digits.
AC16. 16. Non-string inputs raise TypeError, including 90, None, 1.5, True, b'90', and ['90'].

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing only durationkit/parse.py. The required parsing rules are mutually compatible, preserve the public imports, and satisfy all unchanged existing tests. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `f8d172bb216cbf3da30847f17b2eff977c1d3d728f949f1493bfada9a29f9da1`, 22 test methods, sealed at 2026-10-19T04:35:09.340110+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (8 of 22 methods: ERROR 8): 8 of 22 methods failing, 14 passing; operation `01a15271-1bdc-7605-b769-f172d15d42bc`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_adjacent_ordered_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_bare_integers_mixed_with_components_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_have_no_clock_range_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_or_whitespace_only_input_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_exponent_and_separator_syntax_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros_in_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_decimal_numeric_characters_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_public_import_accepts_plain_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_trailing_punctuation_and_unconsumed_text_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_may_be_skipped | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_out_of_descending_order_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_or_uppercase_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_components_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_valued_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,50 @@
 """Duration parsing."""
 
 
+_UNITS = {"d": 86400.0, "h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}
+_ORDER = {unit: index for index, unit in enumerate(_UNITS)}
+
+
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse integer seconds or ordered duration components into seconds."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("duration is empty")
+
+    def is_ascii_digit(char: str) -> bool:
+        return "0" <= char <= "9"
+
+    if all(is_ascii_digit(char) for char in stripped):
+        return float(stripped)
+
+    total = 0.0
+    position = 0
+    previous_order = -1
+    while position < len(stripped):
+        start = position
+        while position < len(stripped) and is_ascii_digit(stripped[position]):
+            position += 1
+        if position == start:
+            raise ValueError(f"invalid duration: {text!r}")
+
+        if stripped.startswith("ms", position):
+            unit = "ms"
+        elif position < len(stripped) and stripped[position] in "dhms":
+            unit = stripped[position]
+        else:
+            raise ValueError(f"invalid duration: {text!r}")
+
+        order = _ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"duration units out of order: {text!r}")
+        previous_order = order
+        total += int(stripped[start:position]) * _UNITS[unit]
+        position += len(unit)
+
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (43 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (22 of 22 methods, each in its own process). Operation `01a15275-deb8-7200-98a2-c303c6078fc9`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a15276-0497-7199-af38-33ac871d342f`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.75 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) on the corrected module (2 test(s) corrected, validated: 2 of 2 corrected test(s) fail on the unmodified base); original failures kept in E3 |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 9 killed, 3 survived, 0 unknown; mutation score 0.750 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ef0f37c856 | durationkit/parse.py | 14 | remove `not` | killed | test_sealed.ParseDurationAcceptanceTests.test_public_import_accepts_plain_seconds, test_sealed.ParseDurationAcceptanceTe | 01a15276-1b22-70a1-ba79-8bb9d5d469c2 |
| m02-19be8d04fe | durationkit/parse.py | 15 | raise -> pass | survived |  | 01a15276-1be0-731c-98d5-b922e7a40da2 |
| m03-2e1df113ac | durationkit/parse.py | 18 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_public_import_accepts_plain_seconds, test_sealed.ParseDurationAcceptanceTe | 01a15276-1bbf-77ac-af23-f992d2f2669b |
| m04-edb25abe2e | durationkit/parse.py | 25 | 1 -> 2 | survived |  | 01a15276-1ba2-7501-bfdd-dd3602fc3165 |
| m05-fb8d5eeec7 | durationkit/parse.py | 28 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_bare_integers_mixed_with_components_raise_value_error | 01a15276-1b5e-72dd-a10b-68f6b6d7de0b |
| m06-f816ad2f88 | durationkit/parse.py | 29 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_adjacent_ | 01a15276-1be8-71a2-ae1e-f2e08f0008d0 |
| m07-9b9bb86e26 | durationkit/parse.py | 31 | raise -> pass | survived |  | 01a15276-1bd6-7546-97d9-593508fbf063 |
| m08-e4ad9e11e5 | durationkit/parse.py | 35 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_bare_integers_mixed_with_components_raise_value_error | 01a15276-1b32-74b4-bff1-0d7156ddefdc |
| m09-b73ff39f13 | durationkit/parse.py | 35 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_fractional_exponent_and_separator_syntax_raises_value_error, test_sealed.P | 01a15276-4200-76ea-a8c2-d492edb2f61d |
| m10-1e70179db5 | durationkit/parse.py | 41 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error | 01a15276-42e6-76b2-aca4-a0b138c2f011 |
| m11-151b63b170 | durationkit/parse.py | 44 | Mult -> Div | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_adjacent_ | 01a15276-43be-77a1-8205-e489c9748db7 |
| m12-822f492ab3 | durationkit/parse.py | 47 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_adjacent_ | 01a15276-4487-74e9-897e-3593da9c4ca7 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `38e88542a00395e730f3d17c5f74822da6ac6dd9c5ec2bb96ba17676771f4d2f`): FAILED (2 of 10 methods: ERROR 2); binding FAILED; operation `01a15277-3b12-75be-9f71-949ec9dcaa81`. Notes: Targets finite results from very large millisecond values, all unit pair orders, Unicode whitespace boundaries, and malformed numeric content.

| Failing adversarial test | Outcome |
| --- | --- |
| test_large_millisecond_value_with_finite_seconds | ERROR |
| test_large_millisecond_value_in_combination | ERROR |
Corrected adversarial module (E6): `arbitration/adversarial_corrected.py` sha256 `cdf4018d7199f026d3bf57f08d052d9f0f05a8d768f1588ae5efe3735875b1b7`; corrected tests test_large_millisecond_value_in_combination, test_large_millisecond_value_with_finite_seconds; on the candidate OK (10 of 10 methods, each in its own process); validated: 2 of 2 corrected test(s) fail on the unmodified base; operation `01a15278-3a90-75e1-8e40-381771cfad2e`. The adversarial gate was re-run on it.
Adversarial authoring: 1 attempt(s).

### Counterexamples
- E3 `test_large_millisecond_value_with_finite_seconds`: ERROR; OverflowError: int too large to convert to float; arbiter: Defective test, by the arbiter; contract basis: The contract excludes new overflow or precision guarantees for extremely large numeric values beyond existing Python numeric behavior.
- E3 `test_large_millisecond_value_in_combination`: ERROR; OverflowError: int too large to convert to float; arbiter: Defective test, by the arbiter; contract basis: Ordered components are required, but new overflow or precision guarantees for extremely large numeric values are explicitly out of scope.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `stripped.startswith("ms", position)` recognizes milliseconds, `order <= previous_order` rejects repeated or misordered units, and `.isspace()` permits whitespace between complete components while strict scanning rejects malformed text. The signature, TypeError check, float results, and existing tests remain unchanged; observed test output supports six existing tests passing and successful checks of 22 valid, 40 invalid, and six non-string inputs.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 2 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (2 of 2 corrected test(s) fail on the unmodified base); the affected gate(s) are re-run on the corrected modules (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 2, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the failing ones, passes on the candidate and still discriminates (fails on the unmodified base, or is caught by a mutant of the patch); a sealed test that failed by assertion is never overridden; a validated correction re-runs its gate and the verdict is derived from the gates Gates re-run on validated corrections: adversarial_tests (tests test_large_millisecond_value_in_combination, test_large_millisecond_value_with_finite_seconds; 2 of 2 corrected test(s) fail on the unmodified base).

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_large_millisecond_value_with_finite_seconds | test_defect | The test requires converting 10**309 milliseconds to finite seconds without intermediate overflow. That imposes an overflow-handling guarant | The contract excludes new overflow or precision guarantees for extremely large numeric values beyond existing Python numeric behavior. |
| test_large_millisecond_value_in_combination | test_defect | Combining seconds with 10**309 milliseconds still requires an unspecified guarantee against intermediate numeric overflow. | Ordered components are required, but new overflow or precision guarantees for extremely large numeric values are explicitly out of scope. |

- `adversarial` corrected re-run: candidate OK (10 of 10 methods, each in its own process); base FAILED (5 of 10 methods: ERROR 5); validated=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10756 | 1445 | 0 | - | 50.9s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11995 | 94 | 0 | - | 76.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11108 | 2438 | 0 | - | 77.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10989 | 128 | 7168 | - | 76.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11084 | 87 | 7168 | - | 31.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11295 | 840 | 7168 | - | 37.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11520 | 111 | 7168 | - | 19.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11764 | 684 | 7168 | - | 25.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12444 | 149 | 7168 | - | 22.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 12919 | 177 | 7168 | - | 78.5s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11473 | 1889 | 7040 | - | 52.3s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12275 | 148 | 0 | - | 18.1s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 13663 | 1284 | 0 | - | 36.1s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 153285/9474/57216; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1526d-cf44-71d8-bc46-0699178e4715 | SUCCESS | 0 | 0.802s | retained | off | 0.00285183 |
| red-1 | 01a15271-1bdc-7605-b769-f172d15d42bc | SUCCESS | 0 | 4.947s | disposable | off | 0.04133874 |
| impl-tests-4 | 01a15273-c760-776a-96b1-cfffe54b8593 | SUCCESS | 0 | 0.776s | disposable | off | 0.0028585399999999997 |
| impl-python-5 | 01a15274-3e8b-742b-97ab-427cdbab74e4 | SUCCESS | 0 | 0.581s | disposable | off | 0.0012435700000000003 |
| verify | 01a15275-deb8-7200-98a2-c303c6078fc9 | SUCCESS | 0 | 4.87s | disposable | off | 0.041243400000000006 |
| existing | 01a15276-0497-7199-af38-33ac871d342f | SUCCESS | 0 | 2.118s | disposable | off | 0.015183569999999999 |
| mutant-m01-ef0f37c856 | 01a15276-1b22-70a1-ba79-8bb9d5d469c2 | SUCCESS | 0 | 4.685s | disposable | off | 0.038324500000000004 |
| mutant-m03-2e1df113ac | 01a15276-1bbf-77ac-af23-f992d2f2669b | SUCCESS | 0 | 4.687s | disposable | off | 0.038680400000000004 |
| mutant-m02-19be8d04fe | 01a15276-1be0-731c-98d5-b922e7a40da2 | SUCCESS | 0 | 4.755s | disposable | off | 0.039147470000000004 |
| mutant-m04-edb25abe2e | 01a15276-1ba2-7501-bfdd-dd3602fc3165 | SUCCESS | 0 | 4.656s | disposable | off | 0.038430030000000004 |
| mutant-m06-f816ad2f88 | 01a15276-1be8-71a2-ae1e-f2e08f0008d0 | SUCCESS | 0 | 4.688s | disposable | off | 0.038880460000000006 |
| mutant-m07-9b9bb86e26 | 01a15276-1bd6-7546-97d9-593508fbf063 | SUCCESS | 0 | 4.707s | disposable | off | 0.03888574 |
| mutant-m05-fb8d5eeec7 | 01a15276-1b5e-72dd-a10b-68f6b6d7de0b | SUCCESS | 0 | 4.706s | disposable | off | 0.03874495 |
| mutant-m08-e4ad9e11e5 | 01a15276-1b32-74b4-bff1-0d7156ddefdc | SUCCESS | 0 | 4.513s | disposable | off | 0.03769444 |
| mutant-m09-b73ff39f13 | 01a15276-4200-76ea-a8c2-d492edb2f61d | SUCCESS | 0 | 4.471s | disposable | off | 0.038169770000000006 |
| mutant-m10-1e70179db5 | 01a15276-42e6-76b2-aca4-a0b138c2f011 | SUCCESS | 0 | 4.611s | disposable | off | 0.03841916 |
| mutant-m11-151b63b170 | 01a15276-43be-77a1-8205-e489c9748db7 | SUCCESS | 0 | 4.577s | disposable | off | 0.037947930000000005 |
| mutant-m12-822f492ab3 | 01a15276-4487-74e9-897e-3593da9c4ca7 | SUCCESS | 0 | 4.576s | disposable | off | 0.03790132 |
| breaker-tests | 01a15277-3b12-75be-9f71-949ec9dcaa81 | SUCCESS | 0 | 2.824s | disposable | off | 0.0218805 |
| arbitrate-adversarial-candidate | 01a15278-3a90-75e1-8e40-381771cfad2e | SUCCESS | 0 | 2.817s | disposable | off | 0.02175098 |
| arbitrate-adversarial-base | 01a15278-550f-75bb-bf9f-8d2a0a7fab81 | SUCCESS | 0 | 2.785s | disposable | off | 0.02164417 |

Sandbox operations: 21, total guest duration 78.152s, retained images ['bd4c4d49-6f89-4995-a6ff-1c35cbe7e64a'].

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
