# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261017T122359410274Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T12:23:59.411559+00:00, finished 2026-10-17T12:33:08.025653+00:00.

**Accept this patch.** All 25 sealed tests pass on the candidate in a fresh sandbox, and 12 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 25 of 25 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 25 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 12 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 11 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 13 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 12 of 25 failed on the unmodified base; 25 of 25 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 11 of 11 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `416ecabc-fb82-4144-abd5-7d5210fd76b0`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `b7fdd9eb0b71d237` (34 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-reliability-2026-10-17/evaluation-paced-codex/snapshot/attest`.
Pacing (development gateway): 54 of an assumed 60 requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept both plain non-negative integer seconds and integer components with lowercase units d, h, m, s, and ms, returning total seconds as a float. Unit components must be unique and ordered from largest to smallest, with whitespace permitted only around the input and between complete components. Preserve the public import, existing valid behavior, TypeError for non-string inputs, and all existing tests; reject malformed strings with ValueError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also available as durationkit.parse.parse_duration. After removing surrounding whitespace, accept either one uninterrupted sequence of ASCII digits representing | TypeError: text is not a string.; ValueError: text is empty or contains only whitespace.; ValueError: a number is negative, explicitly signed, fractional, scien |

Acceptance criteria:
1. 1. The imports from durationkit import parse_duration and from durationkit.parse import parse_duration remain available.
2. 2. Existing plain-seconds behavior remains: '90' returns 90.0, '  42 ' returns 42.0, '7' returns 7.0, and '0' returns 0.0.
3. 3. Single components return the specified seconds: '2d' → 172800.0, '3h' → 10800.0, '15m' → 900.0, '45s' → 45.0, and '500ms' → 0.5.
4. 4. Ordered combinations work: '1h30m' → 5400.0, '2d4h' → 187200.0, '1m1s' → 61.0, '1s500ms' → 1.5, and '1d1h1m1s1ms' → 90061.001. Fractional totals are compared with floating-point tolerance.
5. 5. Units may be skipped: '1d1s' returns 86401.0 and '1h1ms' returns approximately 3600.001.
6. 6. Surrounding and inter-component whitespace, including spaces, tabs, and newlines, is accepted: ' 1h 30m ' and '\t1h\n30m\t' both return 5400.0. '1 h', '1\th', and '1m s' raise ValueError.
7. 7. Leading zeros and zero-valued components are accepted: '00090' → 90.0, '01h030m' → 5400.0, '0s' → 0.0, and '0d0h0m0s0ms' → 0.0.
8. 8. Component values have no conventional clock-range restriction: '90m' returns 5400.0 and '1500ms' returns 1.5.
9. 9. Every accepted input returns a float, including inputs whose totals are zero or whole seconds.
10. 10. Empty and whitespace-only strings raise ValueError, including '', '   ', and '\t\n'.
11. 11. Invalid numeric forms raise ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s', and '1_000s'.
12. 12. Unknown or incorrectly cased units and missing numbers raise ValueError, including '1x', '1H', '1MS', 'h', and 'ms'.
13. 13. Repeated or out-of-order units raise ValueError, including '1h1h', '1ms1ms', '30m1h', '1ms1s', '0s0h', and '0h0h'.
14. 14. Mixed bare numbers, incomplete components, separators, and trailing garbage raise ValueError, including '1h30', '1 30m', '1 2', '1h,30m', '1h!', and 'abc'.
15. 15. Non-decimal numeric characters raise ValueError, whether bare or used as component numbers, including 'Ⅳ', '½', '①', and '①h'. Acceptance or rejection of non-ASCII Unicode decimal digits is not tested.
16. 16. Non-string values, including 90, None, 1.5, True, and b'90', raise TypeError.
17. 17. All existing tests in tests/ pass unchanged using python -m unittest discover -s tests -t . -v.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `4c44f4400f8c24353a745eecbaa0db51722b7b8bab137ffadffadbc9af9c0477`, 25 test methods, sealed at 2026-10-17T12:26:10.150076+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 25 methods: ERROR 12): 12 of 25 methods failing, 13 passing; operation `01a149d3-946c-74c4-963a-1a70936252fb`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_all_accepted_forms_return_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_have_no_clock_range_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_day_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_strings_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_hour_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_invalid_numeric_forms_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_millisecond_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_minute_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_mixed_bare_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_decimal_numeric_characters_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_ordered_component_combinations | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_seconds_preserve_existing_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_punctuation_and_trailing_garbage_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_second_component | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_may_be_skipped | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_and_uppercase_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_cannot_split_number_from_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_valued_components_are_accepted | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,40 @@
 """Duration parsing."""
+
+import re
+
+
+_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")
+_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_ORDER = {"d": 0, "h": 1, "m": 2, "s": 3, "ms": 4}
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Return the seconds in a plain integer or ordered unit components."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
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
+
+        number, unit = match.groups()
+        order = _ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        total += float(number) * _UNITS[unit]
+        previous_order = order
+        position = match.end()
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    if previous_order < 0:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    return total
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (32 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| durationkit/parse.py | 6 | dynamic code or decoded payload | _COMPONENT = re.compile(r"([0-9]+)(ms\|[dhms])") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (25 of 25 methods, each in its own process). Operation `01a149d6-69a6-71a3-8710-d06b0e3c1730`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a149d6-8c0b-740e-b3a6-a3d89dc41237`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (11 of 11 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-62ecea6ddd | durationkit/parse.py | 7 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_ordered_compo | 01a149d6-fb4e-7454-ab5e-7bf5a06da1c7 |
| m02-33aff08a51 | durationkit/parse.py | 7 | 3600 -> 3601 | killed | test_sealed.ParseDurationAcceptanceTests.test_hour_component, test_sealed.ParseDurationAcceptanceTests.test_ordered_comp | 01a149d6-fb7e-774b-8f50-847721ee79f2 |
| m03-94a78ec216 | durationkit/parse.py | 7 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_second_component, test_sealed.ParseDurationAcceptanceTests.test_ordered_co | 01a149d6-fb4b-720b-8dc9-9fc3103fc72e |
| m04-b3884cbf14 | durationkit/parse.py | 8 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_ordered_component_combinations, test_sealed.ParseDurationAcceptanceTests.t | 01a149d6-fb26-71a7-86d4-89dc717ea93d |
| m05-bbeb1c1763 | durationkit/parse.py | 8 | 3 -> 4 | killed | test_sealed.ParseDurationAcceptanceTests.test_ordered_component_combinations, test_sealed.ParseDurationAcceptanceTests.t | 01a149d6-fb44-7242-b0da-8ec4433e1c65 |
| m06-ba8f93e561 | durationkit/parse.py | 21 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_hour_componen | 01a149d6-fac3-7517-8329-1e95e4d8753f |
| m07-b622bc2bb8 | durationkit/parse.py | 23 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_hour_componen | 01a149d6-fb3e-73f3-9af1-25bd3c1f22c6 |
| m08-ebf435db42 | durationkit/parse.py | 25 | Is -> IsNot | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_hour_componen | 01a149d6-fb00-7205-8585-06f83e4e0903 |
| m09-6d72a0ada2 | durationkit/parse.py | 30 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error | 01a149d7-22df-70c1-bd18-26a4685d6c8a |
| m10-639f46ba64 | durationkit/parse.py | 32 | Mult -> Div | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_hour_componen | 01a149d7-23ee-7589-bbc5-b66b00eed78f |
| m11-7bcee65723 | durationkit/parse.py | 35 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_hour_componen | 01a149d7-23fc-747c-ae67-f2daac986d96 |
| m12-b12f2f8513 | durationkit/parse.py | 38 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_day_component, test_sealed.ParseDurationAcceptanceTests.test_all_accepted_ | 01a149d7-2442-7040-968d-eaa0d03795c3 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `7f3c76017f418b75cd123dd50c44d0d689e34f586f9ce40c9c886e9679148384`): OK (11 of 11 methods, each in its own process); binding ok; operation `01a149d8-cd56-70ba-8c15-8fdbcad697fd`. Notes: Targets unit ordering across permutations, Unicode whitespace, numeric symbols, incomplete components, and large valid values.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated task: `_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")` recognizes the required components, `order <= previous_order` rejects repeats and incorrect ordering, and `.isspace()` permits whitespace between components. Plain seconds, float returns, and TypeError validation remain intact; existing tests are unchanged, and observed tool output supports the reported passing existing suite and targeted checks.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10758 | 1439 | 0 | - | 51.7s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10932 | 2083 | 0 | - | 58.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10805 | 122 | 7168 | - | 27.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 23514 | 1561 | 18048 | - | 36.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11633 | 142 | 7168 | - | 29.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11876 | 578 | 0 | - | 44.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12364 | 261 | 7168 | - | 29.7s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11324 | 1997 | 0 | - | 90.1s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11980 | 176 | 0 | - | 78.6s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 115186/8359/39552; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a149d1-c638-716b-9d23-8dced1687c78 | SUCCESS | 0 | 0.761s | retained | off | 0.00279481 |
| red-1 | 01a149d3-946c-74c4-963a-1a70936252fb | SUCCESS | 0 | 5.371s | disposable | off | 0.046097900000000004 |
| impl-tests-3 | 01a149d5-27ba-7533-b843-3bded6dae1b7 | SUCCESS | 0 | 0.759s | disposable | off | 0.0027568899999999997 |
| impl-python-4 | 01a149d5-e3b2-769c-9b10-84c5681194a5 | SUCCESS | 0 | 0.573s | disposable | off | 0.0015452500000000002 |
| verify | 01a149d6-69a6-71a3-8710-d06b0e3c1730 | SUCCESS | 0 | 5.355s | disposable | off | 0.04592733 |
| existing | 01a149d6-8c0b-740e-b3a6-a3d89dc41237 | SUCCESS | 0 | 2.044s | disposable | off | 0.01522479 |
| mutant-m01-62ecea6ddd | 01a149d6-fb4e-7454-ab5e-7bf5a06da1c7 | SUCCESS | 0 | 5.155s | disposable | off | 0.042956360000000006 |
| mutant-m03-94a78ec216 | 01a149d6-fb4b-720b-8dc9-9fc3103fc72e | SUCCESS | 0 | 5.134s | disposable | off | 0.04310042000000001 |
| mutant-m02-33aff08a51 | 01a149d6-fb7e-774b-8f50-847721ee79f2 | SUCCESS | 0 | 5.131s | disposable | off | 0.04340353000000001 |
| mutant-m05-bbeb1c1763 | 01a149d6-fb44-7242-b0da-8ec4433e1c65 | SUCCESS | 0 | 5.12s | disposable | off | 0.04289433 |
| mutant-m04-b3884cbf14 | 01a149d6-fb26-71a7-86d4-89dc717ea93d | SUCCESS | 0 | 5.197s | disposable | off | 0.043355580000000005 |
| mutant-m06-ba8f93e561 | 01a149d6-fac3-7517-8329-1e95e4d8753f | SUCCESS | 0 | 5.053s | disposable | off | 0.04274828000000001 |
| mutant-m07-b622bc2bb8 | 01a149d6-fb3e-73f3-9af1-25bd3c1f22c6 | SUCCESS | 0 | 5.179s | disposable | off | 0.043021290000000004 |
| mutant-m08-ebf435db42 | 01a149d6-fb00-7205-8585-06f83e4e0903 | SUCCESS | 0 | 5.197s | disposable | off | 0.043372070000000006 |
| mutant-m09-6d72a0ada2 | 01a149d7-22df-70c1-bd18-26a4685d6c8a | SUCCESS | 0 | 4.944s | disposable | off | 0.04253684 |
| mutant-m10-639f46ba64 | 01a149d7-23ee-7589-bbc5-b66b00eed78f | SUCCESS | 0 | 5.214s | disposable | off | 0.043768510000000004 |
| mutant-m11-7bcee65723 | 01a149d7-23fc-747c-ae67-f2daac986d96 | SUCCESS | 0 | 5.19s | disposable | off | 0.04380423 |
| mutant-m12-b12f2f8513 | 01a149d7-2442-7040-968d-eaa0d03795c3 | SUCCESS | 0 | 5.134s | disposable | off | 0.042935850000000005 |
| breaker-tests | 01a149d8-cd56-70ba-8c15-8fdbcad697fd | SUCCESS | 0 | 2.989s | disposable | off | 0.02361514 |

Sandbox operations: 19, total guest duration 79.5s, retained images ['416ecabc-fb82-4144-abd5-7d5210fd76b0'].

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
