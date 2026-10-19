# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-attest-a1-20261017T062653445208Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T06:26:53.445526+00:00, finished 2026-10-17T06:39:58.661218+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter; the corrected tests pass on the candidate and still fail on the unmodified base. Arbitration is advisory, so the hold stands until a human confirms.

Key evidence (E6): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests



What to do: Check the arbiter's corrections in E6 (original and corrected tests are both kept). If you agree, accept the patch on that basis or re-run with arbitration in apply mode.

Reasons: adversarial suite binding failed: child process nonzero exit: test_mixed_unicode_decimal_scripts exit 1; model-written adversarial tests failed: 1 of 10 (test_breaker.TestBreakerDurationParsing.test_mixed_unicode_decimal_scripts); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 28 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 11 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 17 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 11 of 28 failed on the unmodified base; 28 of 28 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 9 of 10 pass; 1 failing: test_mixed_unicode_decimal_scripts; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `8eb2b7d0-9837-4084-8858-0589d743b144`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.2.0 revision `17360d66f6044ce7` (33 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/5` sha256 `8511520ba75a7690`, per-test child `fb466d37f748f9ef`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either plain non-negative integer seconds or a sequence of integer-valued duration components using d, h, m, s and ms. Require strictly descending unit order without repeated units, allow surrounding whitespace and whitespace between complete components, and return the total seconds as a float. Reject malformed strings with ValueError and non-string arguments with TypeError, while preserving the public import and all existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also accessible as durationkit.parse.parse_duration. Check that text is a string, then ignore leading and trailing whitespace. Accept either an unsigned integer | TypeError: text is not an instance of str, including integers, floats, booleans, bytes and None.; ValueError: the trimmed string is empty.; ValueError: any nume |

Acceptance criteria:
1. 1. All existing tests in tests/ pass unchanged using python -m unittest discover -s tests -t . -v.
2. 2. The import from durationkit import parse_duration remains available, and durationkit.parse.parse_duration exposes the same behavior and signature.
3. 3. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '7' returns 7.0 and '0' returns 0.0.
4. 4. Single components produce the expected seconds: '2d' returns 172800.0, '3h' returns 10800.0, '15m' returns 900.0, '45s' returns 45.0 and '500ms' returns 0.5.
5. 5. Ordered combinations work: '1h30m' returns 5400.0, '2d4h' returns 187200.0, '1m1s' returns 61.0, '1s500ms' returns 1.5 and '1d1h1m1s1ms' returns approximately 90061.001. Compare fractional results with an absolute tolerance of 1e-9.
6. 6. Units may be skipped: '1d1ms' returns approximately 86400.001 and '1h1s' returns 3601.0.
7. 7. Whitespace around the input and between complete components is accepted, including tabs, newlines and Unicode whitespace: ' 1h 30m ' and '\t1h\n30m\u2003' both return 5400.0.
8. 8. Whitespace inside components is rejected with ValueError, including '1 h', '1m  s' and '1 ms'.
9. 9. Zero components and leading zeros are accepted: '0s', '0ms' and '0d0h0m0s0ms' return 0.0; '00090' returns 90.0; '01h030m' returns 5400.0.
10. 10. Component values have no clock-range restriction: '90m' returns 5400.0 and '1500ms' returns 1.5.
11. 11. Unicode decimal digits remain accepted: '９０' returns 90.0 and '１h３０m' returns 5400.0. Non-decimal digit-like text such as '²' or '²s' raises ValueError.
12. 12. Repeated units raise ValueError even when separated by whitespace or assigned zero: '1h1h', '1ms 2ms' and '0s0s'.
13. 13. Any ascending unit transition raises ValueError, including '30m1h', '1ms1s', '1s1d' and '0ms0s'.
14. 14. Empty and whitespace-only strings raise ValueError, including '', '   ' and '\t\n'.
15. 15. Negative, explicitly positive, fractional, scientific-notation and underscore-separated numbers raise ValueError in both forms, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3', '1e3s', '1_000' and '1_000s'.
16. 16. Unknown units, uppercase units and units without numbers raise ValueError, including '1x', '1H', '1MS', 'h', 'ms' and 'abc'.
17. 17. Incomplete components, mixed forms and extraneous text raise ValueError, including '1h30', '90 1s', '1s 90', '1 2', '1h,30m', '1h/30m' and '1mss'.
18. 18. Non-string inputs raise TypeError, including 90, 0.5, None, True, b'90', [] and {}.
19. 19. Every accepted input returns an instance of float, including zero, plain seconds, integral unit totals and fractional millisecond totals.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `18c9adabb0f258386a61a5edefac932369c087d4c68a6db59fbe910287a1c467`, 28 test methods, sealed at 2026-10-17T06:30:32.989914+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (11 of 28 methods: ERROR 11): 11 of 28 methods failing, 17 passing; operation `01a1488e-016f-770f-a596-08a2bf87bea8`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptedTests.test_adjacent_descending_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_all_accepted_forms_return_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_component_values_have_no_clock_range_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_leading_zeros | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_parse_module_public_import_has_same_behavior | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_text_keyword_argument | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_unicode_decimal_digits | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptedTests.test_zero_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_ascending_unit_order | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_bare_seconds_mixed_with_components | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_component_without_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_empty_and_whitespace_only_strings | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_extraneous_punctuation_or_unit_text | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_fractional_numeric_tokens | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_non_decimal_digit_like_characters | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_non_string_arguments | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_repeated_units | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_scientific_notation | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_signed_numbers | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_underscores_in_numeric_tokens | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_units_without_numbers | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_unknown_units | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_uppercase_units | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationRejectedTests.test_whitespace_between_number_and_unit | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,46 @@
 """Duration parsing."""
 
 
+_SECONDS_PER_UNIT = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_UNIT_ORDER = {unit: rank for rank, unit in enumerate(_SECONDS_PER_UNIT)}
+
+
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
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("duration must not be empty")
+    if stripped.isdecimal():
+        return float(stripped)
+
+    total = 0.0
+    previous_rank = -1
+    position = 0
+    while position < len(stripped):
+        number_start = position
+        while position < len(stripped) and stripped[position].isdecimal():
+            position += 1
+        if position == number_start:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        if stripped.startswith("ms", position):
+            unit = "ms"
+        elif position < len(stripped) and stripped[position] in "dhms":
+            unit = stripped[position]
+        else:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        rank = _UNIT_ORDER[unit]
+        if rank <= previous_rank:
+            raise ValueError(f"units out of order: {text!r}")
+        total += float(stripped[number_start:position]) * _SECONDS_PER_UNIT[unit]
+        previous_rank = rank
+        position += len(unit)
+
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (39 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (28 of 28 methods, each in its own process). Operation `01a14893-71d9-715d-a4c5-bcd0b3f47c09`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14893-9832-715b-b7e2-1edc94035877`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.917 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 10 methods: FAIL 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-6985505fba | durationkit/parse.py | 4 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-b49d-7712-859f-f04e0dd2c3ea |
| m02-2816bf6c45 | durationkit/parse.py | 4 | 60 -> 61 | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-b451-742e-a535-87d410c06805 |
| m03-3de279ffb4 | durationkit/parse.py | 14 | remove `not` | killed | test_sealed.ParseDurationAcceptedTests.test_plain_integer_seconds, test_sealed.ParseDurationAcceptedTests.test_single_co | 01a14893-b4b9-72ef-becf-4632631c78e7 |
| m04-33e3a01974 | durationkit/parse.py | 20 | 1 -> 2 | survived |  | 01a14893-b453-7262-af08-19c45549970b |
| m05-dc565233bd | durationkit/parse.py | 22 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-b49e-7042-8394-0c9e2629837f |
| m06-bbde134ff4 | durationkit/parse.py | 24 | And -> Or | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-b458-7171-8112-e65ca1ff7743 |
| m07-b3acb85038 | durationkit/parse.py | 26 | Eq -> NotEq | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-b428-734a-afcb-51efb17f4553 |
| m08-b8a75c2b4b | durationkit/parse.py | 31 | Lt -> LtE | killed | test_sealed.ParseDurationRejectedTests.test_component_without_unit, test_sealed.ParseDurationRejectedTests.test_bare_sec | 01a14893-b42f-7172-b7ff-8e39c42637e4 |
| m09-8a2988c6e0 | durationkit/parse.py | 31 | And -> Or | killed | test_sealed.ParseDurationRejectedTests.test_fractional_numeric_tokens, test_sealed.ParseDurationRejectedTests.test_scien | 01a14893-dca6-74dc-8dcf-b0174c1f6aba |
| m10-007afc3b93 | durationkit/parse.py | 37 | LtE -> Lt | killed | test_sealed.ParseDurationRejectedTests.test_repeated_units | 01a14894-068c-772d-a9ff-f57ceebaface |
| m11-be6c0cda08 | durationkit/parse.py | 39 | Mult -> Div | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-ddbe-745b-b863-9d8def7a8baf |
| m12-5b21752514 | durationkit/parse.py | 43 | And -> Or | killed | test_sealed.ParseDurationAcceptedTests.test_single_components, test_sealed.ParseDurationAcceptedTests.test_adjacent_desc | 01a14893-dfd3-77c7-a9f7-7dea19808121 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `d77e22ab7196be943c49d12ecded47c3debc94034c8a34471fcadb64762ea5f2`): FAILED (1 of 10 methods: FAIL 1); binding FAILED; operation `01a14894-fdd4-76e1-a66c-ebbf986c1d2f`. Notes: Targets all unit subsequences, mixed Unicode digits, uncommon whitespace, token boundaries, nonadjacent order errors, and public API type behavior.

| Failing adversarial test | Outcome |
| --- | --- |
| test_mixed_unicode_decimal_scripts | FAIL |

### Counterexamples
- E3 `test_mixed_unicode_decimal_scripts`: FAIL; AssertionError: 45240.0 != 58440.0 within 1e-09 delta (13200.0 difference); first `45240.0` vs second `58440.0 within 1e-09 delta (13200.0 difference)` (the test's argument order decides which is the actual value); arbiter: Defective test, by the arbiter; contract basis: Unicode decimal digits are accepted using Python numeric conversion. Hours contribute 3600 seconds each and minutes contribute 60 seconds each: 12 * 3600 + 34 * 60 = 45240.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated task: `stripped.isdecimal()` preserves plain seconds, `startswith("ms", position)` recognizes milliseconds, `rank <= previous_rank` rejects repeated or ascending units, and `isspace()` permits whitespace between complete components. The signature and existing tests remain unchanged, and observed tool output reports all six existing tests passing plus contract examples passing through both import paths.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_mixed_unicode_decimal_scripts | test_defect | The mixed-script digits in '١२h３४m' represent 12 hours and 34 minutes, totaling 45240.0 seconds. The test incorrectly expects 58440.0. | Unicode decimal digits are accepted using Python numeric conversion. Hours contribute 3600 seconds each and minutes contribute 60 seconds ea |

- `adversarial` corrected re-run: candidate OK (10 of 10 methods, each in its own process); base n/a; cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10644 | 1536 | 0 | - | 89.5s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10976 | 2550 | 0 | - | 107.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10836 | 105 | 7168 | - | 42.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22440 | 1143 | 18048 | - | 59.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11233 | 129 | 7168 | - | 59.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11484 | 847 | 7168 | - | 89.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12266 | 224 | 7168 | - | 29.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12707 | 280 | 7168 | - | 60.2s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11237 | 1882 | 0 | - | 53.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12041 | 150 | 0 | - | 32.4s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 12998 | 1310 | 0 | - | 33.1s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 138862/10156/53888; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1488a-d465-7731-9a78-ec5474f9b839 | SUCCESS | 0 | 1.134s | retained | off | 0.00297475 |
| red-1 | 01a1488e-016f-770f-a596-08a2bf87bea8 | SUCCESS | 0 | 6.117s | disposable | off | 0.05077745 |
| impl-tests-3 | 01a14890-9b35-70d2-993b-4badffe1293a | SUCCESS | 0 | 0.762s | disposable | off | 0.00276305 |
| impl-python-4 | 01a14892-04db-7208-bb6d-1d7f8454f397 | SUCCESS | 0 | 0.912s | disposable | off | 0.00115303 |
| verify | 01a14893-71d9-715d-a4c5-bcd0b3f47c09 | SUCCESS | 0 | 5.779s | disposable | off | 0.05063042 |
| existing | 01a14893-9832-715b-b7e2-1edc94035877 | SUCCESS | 0 | 2.017s | disposable | off | 0.01501303 |
| mutant-m01-6985505fba | 01a14893-b49d-7712-859f-f04e0dd2c3ea | SUCCESS | 0 | 5.719s | disposable | off | 0.04816373 |
| mutant-m02-2816bf6c45 | 01a14893-b451-742e-a535-87d410c06805 | SUCCESS | 0 | 5.719s | disposable | off | 0.04783396000000001 |
| mutant-m03-3de279ffb4 | 01a14893-b4b9-72ef-becf-4632631c78e7 | SUCCESS | 0 | 5.718s | disposable | off | 0.04782325 |
| mutant-m04-33e3a01974 | 01a14893-b453-7262-af08-19c45549970b | SUCCESS | 0 | 5.719s | disposable | off | 0.0481761 |
| mutant-m05-dc565233bd | 01a14893-b49e-7042-8394-0c9e2629837f | SUCCESS | 0 | 5.718s | disposable | off | 0.048024250000000004 |
| mutant-m06-bbde134ff4 | 01a14893-b458-7171-8112-e65ca1ff7743 | SUCCESS | 0 | 5.728s | disposable | off | 0.04816803 |
| mutant-m07-b3acb85038 | 01a14893-b428-734a-afcb-51efb17f4553 | SUCCESS | 0 | 5.617s | disposable | off | 0.047725050000000005 |
| mutant-m08-b8a75c2b4b | 01a14893-b42f-7172-b7ff-8e39c42637e4 | SUCCESS | 0 | 5.718s | disposable | off | 0.047642140000000006 |
| mutant-m09-8a2988c6e0 | 01a14893-dca6-74dc-8dcf-b0174c1f6aba | SUCCESS | 0 | 6.223s | disposable | off | 0.04872578000000001 |
| mutant-m10-007afc3b93 | 01a14894-068c-772d-a9ff-f57ceebaface | SUCCESS | 0 | 5.556s | disposable | off | 0.04770085000000001 |
| mutant-m11-be6c0cda08 | 01a14893-ddbe-745b-b863-9d8def7a8baf | SUCCESS | 0 | 5.716s | disposable | off | 0.04954737000000001 |
| mutant-m12-5b21752514 | 01a14893-dfd3-77c7-a9f7-7dea19808121 | SUCCESS | 0 | 5.61s | disposable | off | 0.04804013 |
| breaker-tests | 01a14894-fdd4-76e1-a66c-ebbf986c1d2f | SUCCESS | 0 | 3.174s | disposable | off | 0.02203364 |
| arbitrate-adversarial-candidate | 01a14896-af60-74bf-9aa1-67b52aaa5443 | SUCCESS | 0 | 2.882s | disposable | off | 0.02184795 |

Sandbox operations: 20, total guest duration 91.538s, retained images ['8eb2b7d0-9837-4084-8858-0589d743b144'].

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
