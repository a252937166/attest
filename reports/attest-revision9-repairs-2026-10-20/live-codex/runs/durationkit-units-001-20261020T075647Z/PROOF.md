# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261020T075647Z` · profile `development-r9-validation` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-20T07:56:47.065514+00:00, finished 2026-10-20T08:05:36.890883+00:00.

**Accept this patch.** All 21 sealed tests pass on the candidate in a fresh sandbox, and 9 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 21 of 21 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4). 1 of the tests written after the patch failed as written and were corrected by the arbiter; the correction kept every test method, changed only the failing ones, passes on the candidate and discriminates (1 of 1 corrected test(s) fail on the unmodified base with an authentic result), and the gate was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; arbitration (validated corrections re-run their gates): all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 21 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 6 of 6 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 11 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 12 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, but which side was wrong is a model judgement; the original tests and results are preserved (E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 9 of 21 failed on the unmodified base; 21 of 21 pass on the candidate |
| E2 | Mutation check | pass | bound | 6 of 6 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 1 of 11 failed as written (test_long_leading_zero_component); 1 test(s) corrected by the arbiter and validated (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the corrected module passes (OK (11 of 11 methods, each in its own process)) |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `f9bdcaa8-7f59-4d28-ac0f-1ef7b2cfa6ee`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.9.0 revision `2449ab27262cc907` (37 package sources; git commit 697d0e73a568d13ccd7d0bcd0b3d7093a02af317). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/clean-697d0e7/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; a request that was never sent (its connection, proxy tunnel or TLS handshake failed before any byte of it was written) sent again at most 2 times after 2/6 s, each attempt recorded; transport-uncertain failures (the request was written) never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 6, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either plain non-negative integer seconds or a sequence of non-negative integer components with lowercase units d, h, m, s and ms. Components must use distinct units in strictly descending order, with whitespace permitted only around the input and between complete components. Return total seconds as a float, preserve existing tests and public imports, and reject malformed strings with ValueError and non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also remains available as durationkit.parse.parse_duration. After removing surrounding whitespace, accept either one integer without a unit (seconds), or one or | TypeError: text is not an instance of str, including integers, floats, bool, bytes and None.; ValueError: input is empty or whitespace-only.; ValueError: any nu |

Acceptance criteria:
AC1. 1. All existing tests in tests/ pass without modifications; from durationkit import parse_duration remains supported.
AC2. 2. Plain seconds preserve existing behavior: '90' returns 90.0, '  42 ' returns 42.0, and '0' returns 0.0.
AC3. 3. Single components return the correct seconds: '2d'=172800.0, '3h'=10800.0, '15m'=900.0, '45s'=45.0 and '500ms'=0.5.
AC4. 4. Valid combinations include '1h30m'=5400.0, '2d4h'=187200.0, '1m1s'=61.0, '1s500ms'=1.5 and '1d1h1m1s1ms'=90061.001. Use approximate floating-point comparison for fractional totals, with absolute tolerance 1e-9 for these examples.
AC5. 5. Units may be skipped: '1d1s' returns 86401.0. Values are not restricted to conventional clock ranges: '90m' returns 5400.0 and '1500ms' returns 1.5.
AC6. 6. Leading zeros and zero components are accepted: '00090'=90.0, '01h030m'=5400.0, '0s'=0.0, '0ms'=0.0 and '0d0h0m0s0ms'=0.0.
AC7. 7. Whitespace around input and between complete components is accepted: ' 1h 30m ' and '\t1h\n30m\r' each return 5400.0. '1 h', '1\th' and '1m s' raise ValueError.
AC8. 8. Every accepted input returns a float, including plain seconds, zero-valued inputs, whole-second unit totals and fractional-second totals.
AC9. 9. Empty and whitespace-only strings, including '', '   ' and '\t\n', raise ValueError.
AC10. 10. Signed, fractional and unsupported numeric notation raise ValueError, including '-1', '-1h', '+1h', '1.5h', '.5s', '1e3s' and '1_000s'.
AC11. 11. Unknown units, incorrect case and missing numbers raise ValueError, including '1x', '1H', '1MS', 'h', 'ms' and 'abc'.
AC12. 12. Repeated or out-of-order units raise ValueError, including '1h1h', '1ms1ms', '30m1h', '1ms1s', '0h0h' and '0s0m'.
AC13. 13. Mixed unitless and unit-bearing forms and trailing garbage raise ValueError, including '1h30', '1 30m', '1 2', '1h,30m', '1h!' and '1msx'.
AC14. 14. Non-decimal numeric characters are rejected with ValueError, including 'Ⅳ', '½', '①', '①h' and '²s'. Tests must not assert either acceptance or rejection of non-ASCII Unicode decimal digits.
AC15. 15. Non-string inputs, including 90, 1.5, True, None and b'90', raise TypeError.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are jointly satisfiable by changing durationkit/parse.py within the write scope. The existing tests and public exports impose no conflicting behavior; Unicode decimal-digit handling and extreme-input guarantees remain unspecified. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d7e2cfd8fd5fbb559655297d7627d3acf380110ec92bd39a801f6997f7d11cf7`, 21 test methods, sealed at 2026-10-20T07:59:36.914067+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 21 methods: ERROR 9): 9 of 21 methods failing, 12 passing; operation `01a15852-a9fa-746d-afa5-de9cfd658f6b`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_all_accepted_forms_return_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_need_not_be_normalized | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_exponent_and_separator_notation_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_mixed_unitless_and_unit_components_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_nondecimal_numeric_characters_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_are_rejected_even_when_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_parse_module_import_remains_available | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_when_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_trailing_punctuation_and_garbage_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_uppercase_and_bare_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_valid_combinations | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_number_and_unit_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_valued_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,39 @@
 """Duration parsing."""
+
+import re
+
+
+_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")
+_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_ORDER = {unit: index for index, unit in enumerate(_UNITS)}
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse non-negative seconds or ordered duration components into seconds."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if re.fullmatch(r"[0-9]+", stripped):
+        return float(stripped)
+
+    total = 0.0
+    position = 0
+    previous_order = -1
+    while position < len(stripped):
+        match = _COMPONENT.match(stripped, position)
+        if match is None:
+            raise ValueError(f"unsupported duration: {text!r}")
+        value, unit = match.groups()
+        order = _ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        total += int(value) * _UNITS[unit]
+        previous_order = order
+        position = match.end()
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (31 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| durationkit/parse.py | 6 | dynamic code or decoded payload | _COMPONENT = re.compile(r"([0-9]+)(ms\|[dhms])") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (21 of 21 methods, each in its own process). Operation `01a15854-f513-750e-b201-3b1b2d869e33`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a15855-1725-7150-ae3e-e1da4eb35597`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 6 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (11 of 11 methods, each in its own process) on the corrected module (1 test(s) corrected, validated: 1 of 1 corrected test(s) fail on the unmodified base with an authentic result); original failures kept in E3 |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 6 generated, 6 evaluated: 6 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-17fd08081d | durationkit/parse.py | 7 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_valid_com | 01a15855-2eef-7486-bf88-04d7e59c94c7 |
| m02-d93bb478f7 | durationkit/parse.py | 7 | 60 -> 61 | killed | test_sealed.ParseDurationAcceptanceTests.test_parse_module_import_remains_available, test_sealed.ParseDurationAcceptance | 01a15855-2f23-73e8-86a9-49966846dac3 |
| m03-97a83a9050 | durationkit/parse.py | 23 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_parse_module_import_remains_available, test_sealed.ParseDurationAcceptance | 01a15855-2ee6-76da-b284-4b939bf9789f |
| m04-dabfedbda7 | durationkit/parse.py | 27 | Is -> IsNot | killed | test_sealed.ParseDurationAcceptanceTests.test_parse_module_import_remains_available, test_sealed.ParseDurationAcceptance | 01a15855-2f12-7273-8088-644e293351b5 |
| m05-d69ef2e841 | durationkit/parse.py | 31 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_when_zero | 01a15855-2f0c-7083-a49c-13d06f616f6b |
| m06-b0b7fc9a17 | durationkit/parse.py | 36 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_parse_module_import_remains_available, test_sealed.ParseDurationAcceptance | 01a15855-2f3a-7315-a5fb-09ab184d80e6 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `9e94d95e16a241b6b1acca1c64fd88b2c0f2f0414e1ec9bcc963e18ad330f7e0`): FAILED (1 of 11 methods: ERROR 1); binding FAILED; operation `01a15856-bd04-77ab-ad54-92f6f9825251`. Notes: Targets full unit-order coverage, Unicode whitespace, malformed component boundaries, and a valid component with 5,000 leading zeros.

| Failing adversarial test | Outcome |
| --- | --- |
| test_long_leading_zero_component | ERROR |
Corrected adversarial module (E6): `arbitration/adversarial_corrected.py` sha256 `71e1ff125d08eeb5ef78a3850d5bef2414d9fd8eb46d448bdd626a6008020f54`; corrected tests test_long_leading_zero_component; on the candidate OK (11 of 11 methods, each in its own process); validated: 1 of 1 corrected test(s) fail on the unmodified base with an authentic result; operation `01a15858-1aca-74ab-9d03-4f656e75df23`. The adversarial gate was re-run on it.
Adversarial authoring: 1 attempt(s).

### Counterexamples
- E3 `test_long_leading_zero_component`: ERROR; ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5001 digits; use sys.set_int_max_str_digits() to increase the limit; arbiter: Defective test, by the arbiter; contract basis: Leading zeros are allowed, but defining new overflow, precision or resource-limit guarantees for extremely large numeric inputs is out of scope.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `([0-9]+)(ms|[dhms])` parses components, `order <= previous_order` rejects repeated or misordered units, and `isspace()` permits whitespace between components while preserving float results and type checks. Only the parser changed, public imports remain intact, and observed output reports all six existing tests and contract examples passing.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates Gates re-run on validated corrections: adversarial_tests (tests test_long_leading_zero_component; 1 of 1 corrected test(s) fail on the unmodified base with an authentic result).

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_long_leading_zero_component | test_defect | The test requires converting a 5001-digit component, exceeding Python 3.12's default integer-string conversion limit. Although leading zeros | Leading zeros are allowed, but defining new overflow, precision or resource-limit guarantees for extremely large numeric inputs is out of sc |

- `adversarial` corrected re-run: candidate OK (11 of 11 methods, each in its own process); base FAILED (4 of 11 methods: ERROR 4); validated=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 11129 | 1438 | 0 | - | 59.7s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13372 | 98 | 0 | - | 27.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11059 | 2586 | 0 | - | 61.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10912 | 98 | 0 | - | 18.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22437 | 627 | 11008 | - | 30.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11343 | 144 | 0 | - | 25.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11587 | 657 | 0 | - | 34.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12206 | 160 | 0 | - | 26.0s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11277 | 2667 | 0 | - | 92.8s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12302 | 162 | 0 | - | 31.0s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 14022 | 1372 | 0 | - | 51.8s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 141646/10009/11008; Inference USD: n/a (development gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15850-4a70-76d6-9e25-541ad26559ac | SUCCESS | 0 | 0.766s | retained | off | 0.0028623399999999997 |
| red-1 | 01a15852-a9fa-746d-afa5-de9cfd658f6b | SUCCESS | 0 | 4.834s | disposable | off | 0.039899739999999996 |
| impl-tests-3 | 01a15853-f0a6-70c6-9b2d-610e46c7c26d | SUCCESS | 0 | 0.779s | disposable | off | 0.00287981 |
| impl-python-4 | 01a15854-8242-75fd-b6ee-09aa6dc8523a | SUCCESS | 0 | 0.647s | disposable | off | 0.001638 |
| verify | 01a15854-f513-750e-b201-3b1b2d869e33 | SUCCESS | 0 | 4.762s | disposable | off | 0.03968545 |
| existing | 01a15855-1725-7150-ae3e-e1da4eb35597 | SUCCESS | 0 | 2.138s | disposable | off | 0.015326109999999999 |
| mutant-m01-17fd08081d | 01a15855-2eef-7486-bf88-04d7e59c94c7 | SUCCESS | 0 | 4.525s | disposable | off | 0.03664344 |
| mutant-m03-97a83a9050 | 01a15855-2ee6-76da-b284-4b939bf9789f | SUCCESS | 0 | 4.464s | disposable | off | 0.036745429999999996 |
| mutant-m02-d93bb478f7 | 01a15855-2f23-73e8-86a9-49966846dac3 | SUCCESS | 0 | 4.525s | disposable | off | 0.03655314 |
| mutant-m04-dabfedbda7 | 01a15855-2f12-7273-8088-644e293351b5 | SUCCESS | 0 | 4.525s | disposable | off | 0.03655902 |
| mutant-m06-b0b7fc9a17 | 01a15855-2f3a-7315-a5fb-09ab184d80e6 | SUCCESS | 0 | 4.514s | disposable | off | 0.03634714 |
| mutant-m05-d69ef2e841 | 01a15855-2f0c-7083-a49c-13d06f616f6b | SUCCESS | 0 | 4.479s | disposable | off | 0.03636104 |
| breaker-tests | 01a15856-bd04-77ab-ad54-92f6f9825251 | SUCCESS | 0 | 3.054s | disposable | off | 0.0234929 |
| arbitrate-adversarial-candidate | 01a15858-1aca-74ab-9d03-4f656e75df23 | SUCCESS | 0 | 3.088s | disposable | off | 0.02387949 |
| arbitrate-adversarial-base | 01a15858-32ff-73c7-9b33-2d69a063d3f8 | SUCCESS | 0 | 3.157s | disposable | off | 0.02370357 |

Sandbox operations: 15, total guest duration 50.257s, retained images ['f9bdcaa8-7f59-4d28-ac0f-1ef7b2cfa6ee'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'development-r9-validation': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
