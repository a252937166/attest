# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-attest-a2-20261017T173453999942Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:34:54.000124+00:00, finished 2026-10-17T17:40:15.677026+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter; the corrected tests pass on the candidate and still fail on the unmodified base. Arbitration is advisory, so the hold stands until a human confirms. Defect kinds: wrong expected value.

Key evidence (E6): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests



What to do: Check the arbiter's corrections in E6 (original and corrected tests are both kept). If you agree, accept the patch on that basis or re-run with arbitration in apply mode.

Reasons: adversarial suite binding failed: child process nonzero exit: test_mixed_whitespace_between_components exit 1; model-written adversarial tests failed: 1 of 13 (test_breaker.TestBreakerParseDuration.test_mixed_whitespace_between_components); each failure is a bug or a contract disagreement to resolve
Warnings: arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 14 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 9 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 12 of 13 pass; 1 failing: test_mixed_whitespace_between_components; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `07b8ed9e-857c-47bf-a5de-e74d0262dbcf`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms) in descending order, with optional whitespace around the string and between components. The function returns total seconds as a float, preserves existing plain-integer-seconds behavior, raises ValueError for malformed inputs (empty, negative, fractional, unknown unit, repeated unit, out-of-order, missing number, missing unit, whitespace between number and unit, non-digit characters) and TypeError for non-string input. Non-ASCII decimal digits are unspecified and not tested.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (ASCII digits) representing sec | TypeError: input is not a string.; ValueError: input is empty or whitespace-only after stripping.; ValueError: any component contains a negative number (e.g., ' |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. ValueError for empty string '' and whitespace-only '   '.
7. ValueError for negative numbers: '-1h'.
8. ValueError for fractional numbers: '1.5h'.
9. ValueError for unknown units: '1x'.
10. ValueError for repeated units: '1h1h'.
11. ValueError for components out of descending order: '30m1h'.
12. ValueError for unit without a number: 'h'.
13. ValueError for number without a unit in multi-component string: '1h30'.
14. ValueError for malformed text: 'abc'.
15. TypeError for non-string input such as 90 or None.
16. The return type is float for every accepted input.
17. Existing tests in tests/test_parse.py continue to pass without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `e483870c3aa8af7334773a21b38d569350317c3211b9a3a9297dd16b65eb171c`, 23 test methods, sealed at 2026-10-17T17:35:26.147697+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 23 methods: ERROR 9): 9 of 23 methods failing, 14 passing; operation `01a14aee-bdc4-77d4-b6b2-645f2e004819`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationExtended.test_combined_components_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_empty_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_fractional_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_malformed_text_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_negative_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_non_string_input_raises_typeerror | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_number_without_unit_in_multi_component_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_out_of_order_units_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_seconds_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_with_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_repeated_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_return_type_is_float_for_all_valid_inputs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_unit_without_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_unknown_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_between_number_and_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_only_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 10 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,57 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer representing seconds (with optional
+    surrounding whitespace) or a sequence of one or more components, each a
+    non-negative integer immediately followed by a unit (d, h, m, s, ms).
+    Components must appear in descending unit order (d > h > m > s > ms),
+    each unit at most once. Whitespace is allowed around the string and
+    between components, but not between a number and its unit.
+
+    Returns the total number of seconds as a float.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("input is empty or whitespace-only after stripping")
+    # Check for plain integer seconds (no units)
+    tokens = stripped.split()
+    if len(tokens) == 1 and tokens[0].isdigit():
+        return float(tokens[0])
+    # Otherwise parse as sequence of components
+    import re
+    unit_order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    seen_units = set()
+    prev_order = float('inf')
+    total_seconds = 0.0
+    for token in tokens:
+        pos = 0
+        while pos < len(token):
+            match = re.match(r'^(\d+)(ms|d|h|m|s)', token[pos:])
+            if not match:
+                raise ValueError(f"malformed duration: {text!r}")
+            number_str, unit = match.group(1), match.group(2)
+            number = int(number_str)
+            if unit in seen_units:
+                raise ValueError(f"repeated unit: {unit}")
+            seen_units.add(unit)
+            cur_order = unit_order[unit]
+            if cur_order > prev_order:
+                raise ValueError(f"components not in descending unit order")
+            prev_order = cur_order
+            if unit == 'd':
+                total_seconds += number * 86400
+            elif unit == 'h':
+                total_seconds += number * 3600
+            elif unit == 'm':
+                total_seconds += number * 60
+            elif unit == 's':
+                total_seconds += number
+            elif unit == 'ms':
+                total_seconds += number * 0.001
+            else:
+                # Should not happen due to regex
+                raise ValueError(f"unknown unit: {unit}")
+            pos += len(match.group(0))
+    return float(total_seconds)
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (50 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a14af1-96aa-707c-a113-f91ef0cd2309`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14af1-baf1-73b3-8a53-27f40d63a746`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 13 methods: ERROR 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-1474d060d2 | durationkit/parse.py | 19 | remove `not` | killed | test_sealed.TestParseDurationExtended.test_plain_integer_seconds_preserved, test_sealed.TestParseDurationExtended.test_p | 01a14af1-d444-7277-a46b-6e5dc81ef6dc |
| m02-5051b5f527 | durationkit/parse.py | 23 | Eq -> NotEq | killed | test_sealed.TestParseDurationExtended.test_plain_integer_seconds_preserved, test_sealed.TestParseDurationExtended.test_p | 01a14af1-d47c-7333-9870-3aaed579a77e |
| m03-f0a15372a6 | durationkit/parse.py | 24 | 0 -> 1 | killed | test_sealed.TestParseDurationExtended.test_plain_integer_seconds_preserved, test_sealed.TestParseDurationExtended.test_p | 01a14af1-d447-730d-b334-65eda1847d7c |
| m04-81bf04e992 | durationkit/parse.py | 27 | 2 -> 3 | killed | test_sealed.TestParseDurationExtended.test_out_of_order_units_raises | 01a14af1-d455-7233-8a51-ac432a41c447 |
| m05-f75e834a12 | durationkit/parse.py | 32 | 0 -> 1 | killed | test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit, test_sealed.TestParseDurationExtended.test_single | 01a14af1-d470-7001-96fd-01308ff58e74 |
| m06-cbe2877c94 | durationkit/parse.py | 36 | raise -> pass | killed | test_sealed.TestParseDurationExtended.test_whitespace_between_number_and_unit_raises, test_sealed.TestParseDurationExten | 01a14af1-d466-7461-8f94-4b6bd620f179 |
| m07-79290e5715 | durationkit/parse.py | 39 | In -> NotIn | killed | test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit, test_sealed.TestParseDurationExtended.test_single | 01a14af1-d464-73bd-b2c4-bbf676247434 |
| m08-abd06612ea | durationkit/parse.py | 44 | raise -> pass | killed | test_sealed.TestParseDurationExtended.test_out_of_order_units_raises | 01a14af1-d4c3-70f0-8ed5-77cb72ae3450 |
| m09-7c8abc5153 | durationkit/parse.py | 47 | Mult -> Div | killed | test_sealed.TestParseDurationExtended.test_single_component_days, test_sealed.TestParseDurationExtended.test_combined_co | 01a14af1-f2fd-705e-9db6-f12adff604c3 |
| m10-804db6fbd8 | durationkit/parse.py | 49 | Mult -> Div | killed | test_sealed.TestParseDurationExtended.test_single_component_hours, test_sealed.TestParseDurationExtended.test_combined_c | 01a14af1-f5bb-77bb-ac5d-566722731808 |
| m11-05816f1dc8 | durationkit/parse.py | 51 | Mult -> Div | killed | test_sealed.TestParseDurationExtended.test_single_component_minutes, test_sealed.TestParseDurationExtended.test_combined | 01a14af1-f86e-73ee-a7bd-5b49b4e43c28 |
| m12-c037bc9c33 | durationkit/parse.py | 55 | Mult -> Div | killed | test_sealed.TestParseDurationExtended.test_single_component_milliseconds, test_sealed.TestParseDurationExtended.test_com | 01a14af1-f904-70d7-a3b1-45d4698cefee |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `883f5ba1c2486052719ea36bd616468d744e67bc67abb39df2230c615a1c0b8e`): FAILED (1 of 13 methods: ERROR 1); binding FAILED; operation `01a14af2-6245-7299-8626-1d1efdb7f0b7`. Notes: Targeted edge cases: leading zeros, varied whitespace, zero components, missing number/unit with whitespace, repeated units across tokens, out-of-order across tokens, unknown unit, fractional, negative with whitespace, whitespace-only, large plain integer, return type.

| Failing adversarial test | Outcome |
| --- | --- |
| test_mixed_whitespace_between_components | ERROR |

### Counterexamples
- E3 `test_mixed_whitespace_between_components`: ERROR; ValueError: malformed duration: '1\nh\t30m'; arbiter: Defective test, by the arbiter; contract basis: Contract: 'whitespace is allowed around the whole string and between components (but not between a number and its unit).'

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff implements all required functionality for parsing compound duration strings while preserving the existing plain-integer behavior. All acceptance criteria are satisfied and existing tests pass.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_mixed_whitespace_between_components | test_defect | The test expects parse_duration to accept '1\nh\t30m', but this string contains a newline between the number '1' and its unit 'h', which the | Contract: 'whitespace is allowed around the whole string and between components (but not between a number and its unit).' |

- `adversarial` corrected re-run: candidate OK (13 of 13 methods, each in its own process); base FAILED (2 of 13 methods: ERROR 2); cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 2426 | 0 | 0.009015 | 8.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2019 | 1098 | 0 | 0.001594 | 7.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1864 | 118 | 0 | 0.000665 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 2066 | 172 | 0 | 0.000775 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2274 | 5836 | 0 | 0.005935 | 36.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 3184 | 2106 | 0 | 0.002851 | 16.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3447 | 760 | 0 | 0.001718 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 4246 | 1342 | 0 | 0.002482 | 10.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 4908 | 4228 | 0 | 0.005278 | 21.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 6117 | 642 | 0 | 0.002413 | 4.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 6974 | 105 | 0 | 0.002187 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 7036 | 190 | 0 | 0.002282 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 2609 | 914 | 0 | 0.001605 | 7.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3226 | 5580 | 0 | 0.019966 | 16.3s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 3829 | 6807 | 0 | 0.024250 | 19.9s | ok |

Model calls: 15 (0 failed, 0 malformed); tokens in/out/cached 55536/32324/0; USD: 0.083016.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14aee-6a17-72fe-9875-7c7cdf7972fb | SUCCESS | 0 | 0.9s | retained | off | 0.00284984 |
| red-1 | 01a14aee-bdc4-77d4-b6b2-645f2e004819 | SUCCESS | 0 | 5.466s | disposable | off | 0.04287322 |
| impl-tests-4 | 01a14aef-c745-75ff-8744-516757c757ca | SUCCESS | 0 | 1.046s | disposable | off | 0.00286123 |
| impl-python-5 | 01a14af0-c6c1-7408-ba8b-f68de263de7f | SUCCESS | 0 | 0.626s | disposable | off | 0.0016333300000000001 |
| impl-python-8 | 01a14af1-62af-774a-aaec-d938fda8dc7d | SUCCESS | 0 | 0.614s | disposable | off | 0.00163385 |
| impl-tests-9 | 01a14af1-7a95-7111-afad-c2f5b51ee7cf | SUCCESS | 0 | 0.745s | disposable | off | 0.0028488 |
| verify | 01a14af1-96aa-707c-a113-f91ef0cd2309 | SUCCESS | 0 | 5.193s | disposable | off | 0.043126290000000005 |
| existing | 01a14af1-baf1-73b3-8a53-27f40d63a746 | SUCCESS | 0 | 2.116s | disposable | off | 0.01530715 |
| mutant-m01-1474d060d2 | 01a14af1-d444-7277-a46b-6e5dc81ef6dc | SUCCESS | 0 | 4.755s | disposable | off | 0.03970039 |
| mutant-m02-5051b5f527 | 01a14af1-d47c-7333-9870-3aaed579a77e | SUCCESS | 0 | 4.84s | disposable | off | 0.0398039 |
| mutant-m03-f0a15372a6 | 01a14af1-d447-730d-b334-65eda1847d7c | SUCCESS | 0 | 4.763s | disposable | off | 0.039737810000000005 |
| mutant-m04-81bf04e992 | 01a14af1-d455-7233-8a51-ac432a41c447 | SUCCESS | 0 | 4.77s | disposable | off | 0.03956842 |
| mutant-m05-f75e834a12 | 01a14af1-d470-7001-96fd-01308ff58e74 | SUCCESS | 0 | 4.784s | disposable | off | 0.0396333 |
| mutant-m06-cbe2877c94 | 01a14af1-d466-7461-8f94-4b6bd620f179 | SUCCESS | 0 | 4.813s | disposable | off | 0.03981715 |
| mutant-m07-79290e5715 | 01a14af1-d464-73bd-b2c4-bbf676247434 | SUCCESS | 0 | 4.832s | disposable | off | 0.03975507 |
| mutant-m08-abd06612ea | 01a14af1-d4c3-70f0-8ed5-77cb72ae3450 | SUCCESS | 0 | 4.792s | disposable | off | 0.039539580000000005 |
| mutant-m09-7c8abc5153 | 01a14af1-f2fd-705e-9db6-f12adff604c3 | SUCCESS | 0 | 4.669s | disposable | off | 0.03939547 |
| mutant-m10-804db6fbd8 | 01a14af1-f5bb-77bb-ac5d-566722731808 | SUCCESS | 0 | 4.689s | disposable | off | 0.039533740000000005 |
| mutant-m11-05816f1dc8 | 01a14af1-f86e-73ee-a7bd-5b49b4e43c28 | SUCCESS | 0 | 4.741s | disposable | off | 0.039688400000000006 |
| mutant-m12-c037bc9c33 | 01a14af1-f904-70d7-a3b1-45d4698cefee | SUCCESS | 0 | 4.779s | disposable | off | 0.04029134 |
| breaker-tests | 01a14af2-6245-7299-8626-1d1efdb7f0b7 | SUCCESS | 0 | 3.274s | disposable | off | 0.026412619999999998 |
| arbitrate-adversarial-candidate | 01a14af3-0cee-72ba-9010-8c55d95c36e5 | SUCCESS | 0 | 3.308s | disposable | off | 0.02644177 |
| arbitrate-adversarial-base | 01a14af3-2f2a-7689-9820-e3c1a3ded75d | SUCCESS | 0 | 3.255s | disposable | off | 0.02643785 |

Sandbox operations: 23, total guest duration 83.77s, retained images ['07b8ed9e-857c-47bf-a5de-e74d0262dbcf'].

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
