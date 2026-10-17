# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261017T164503Z` · profile `submission-smoke` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T16:45:03.744578+00:00, finished 2026-10-17T16:47:39.676721+00:00.

**Hold this patch.** 14 of the 28 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request.

Key evidence (E1): test_single_component_milliseconds: ValueError: malformed duration: '500ms'



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: implementer did not finish within 12 turns; child process nonzero exit: test_single_component_milliseconds exit 1, test_combined_components_seconds_milliseconds exit 1, test_combined_components_all_units exit 1, test_value_error_empty_string exit 1, test_value_error_whitespace_only exit 1, test_value_error_negative_number exit 1, test_value_error_fractional_number exit 
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; drift audit: score 0.40, widened 1, unsupported claims 1

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 14 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- A model audit found the work aligned with the request (score 0.4, off_target (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 12 of 28 failed on the unmodified base; 14 of 28 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.4, off_target (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `bf2f990b-709a-461c-a68b-18e324aabc64`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `13bc4ae26c3a8dcf` (35 package sources; git commit 85701f5d4f8b3f62c933294ca5a3e621ff677db0). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/attest-eval-frozen/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms), in descending unit order, with optional whitespace around the whole string and between components. Preserve existing behavior for plain integer seconds. Return total seconds as float. Raise ValueError for malformed input (empty, negative, fractional, unknown unit, repeated unit, out-of-order components, missing number or unit, etc.) and TypeError for non-string input.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Two input formats are accepted: (1) a plain non-negative integer (ASCII digits 0-9) | TypeError: if text is not a string; ValueError: if text is empty or contains only whitespace; ValueError: if any component contains a negative number (e.g., '-1 |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. TypeError for non-string input such as 90 or None.
8. The return type is float for every accepted input.
9. Existing tests in tests/test_parse.py continue to pass without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d29271d49302bd9bfcd0a54b85c2b57c9e57878d8f3587ae4aca6323cec9c79c`, 28 test methods, sealed at 2026-10-17T16:45:39.831420+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 28 methods: ERROR 12): 12 of 28 methods failing, 16 passing; operation `01a14ac1-28cd-74c2-80b2-b587e7a7fe83`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationSealedAcceptance.test_combined_components_all_units | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_combined_components_days_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_combined_components_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_combined_components_minutes_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_combined_components_seconds_milliseconds | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_existing_behavior_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_existing_behavior_returns_float | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_existing_behavior_surrounding_whitespace_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_existing_behavior_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_return_type_is_float_for_all_accepted_inputs | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_single_component_milliseconds | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_type_error_non_string_input | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_type_error_none_input | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_empty_string | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_fractional_number | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_negative_number | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_number_without_unit_in_multi_component | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_other_malformed_text | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_out_of_order_components | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_repeated_unit | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_unit_without_number | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_unknown_unit | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_value_error_whitespace_only | ok (1 ev) | FAIL (1 ev) |
| test_sealed.TestParseDurationSealedAcceptance.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 12 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,80 @@
 """Duration parsing."""
+
+import re
+
+_UNIT_TO_SECONDS = {
+    'd': 86400,
+    'h': 3600,
+    'm': 60,
+    's': 1,
+    'ms': 0.001
+}
+
+_ORDER = ['d', 'h', 'm', 's', 'ms']
+_INDEX = {u: i for i, u in enumerate(_ORDER)}
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
+    """Parse a duration string and return the total number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepted formats:
+    1. A plain non-negative integer (optionally surrounded by whitespace)
+       representing seconds, e.g. ``"90"``.
+    2. One or more components, each a non-negative integer immediately followed
+       by a unit suffix (d, h, m, s, ms). Components must appear in strictly
+       descending unit order (d > h > m > s > ms), each unit at most once.
+       Whitespace is allowed around the entire string and between components,
+       but not between a number and its unit.
+
+    Returns the sum of all components converted to seconds as a float.
+
+    Raises:
+        TypeError: if ``text`` is not a string.
+        ValueError: for malformed input (see contract).
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("empty duration string")
+
+    # Plain integer seconds (existing behavior)
+    if stripped.isdigit():
+        return float(stripped)
+
+    # Remove *all* whitespace to simplify parsing of components
+    nospace = re.sub(r'\s+', '', stripped)
+    if not nospace:
+        raise ValueError("empty duration string")
+
+    # Pattern for a component: digits followed by unit
+    pattern = re.compile(r'(\d+)(d|h|m|s|ms)')
+    pos = 0
+    total = 0.0
+    seen_units = set()
+    prev_index = -1
+
+    while pos < len(nospace):
+        match = pattern.match(nospace, pos)
+        if not match:
+            raise ValueError(f"malformed duration: {text!r}")
+        number_str, unit = match.groups()
+        # Leading zeros are allowed; int conversion handles them
+        number = int(number_str)
+        if number < 0:
+            raise ValueError(f"negative number in duration: {text!r}")
+        if unit in seen_units:
+            raise ValueError(f"repeated unit '{unit}' in duration: {text!r}")
+        idx = _INDEX[unit]
+        if idx <= prev_index:
+            raise ValueError(f"units out of order in duration: {text!r}")
+        seen_units.add(unit)
+        prev_index = idx
+        total += number * _UNIT_TO_SECONDS[unit]
+        pos = match.end()
+
+    if pos != len(nospace):
+        raise ValueError(f"malformed duration: {text!r}")
+
+    return total
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (71 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| durationkit/parse.py | 52 | dynamic code or decoded payload | pattern = re.compile(r'(\d+)(d\|h\|m\|s\|ms)') |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (14 of 28 methods: ERROR 4, FAIL 10). Operation `01a14ac2-82ba-774f-af25-70334181e623`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14ac2-c702-7760-b2b2-5cad52c5c2c5`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_single_component_milliseconds exit 1, test_combined_components_seconds_milliseconds exit 1, test_combined_components_all_units exit 1, test_value_error_empty_string exit 1, test_value_error_whitespace_only exit 1, test_value_error_negative_number exit 1, test_value_error_fractional_number exit  |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.4 (off_target) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run), implementer did not finish.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
- E1 `test_single_component_milliseconds`: ERROR; ValueError: malformed duration: '500ms'
- E1 `test_combined_components_seconds_milliseconds`: ERROR; ValueError: units out of order in duration: '1s500ms'
- E1 `test_combined_components_all_units`: ERROR; ValueError: repeated unit 'm' in duration: '1d1h1m1s1ms'
- E1 `test_value_error_empty_string`: FAIL; AssertionError: 'unsupported duration' not found in 'empty duration string'
- E1 `test_value_error_whitespace_only`: FAIL; AssertionError: 'unsupported duration' not found in 'empty duration string'
- E1 `test_value_error_negative_number`: FAIL; AssertionError: 'unsupported duration' not found in "malformed duration: '-1h'"
- E1 `test_value_error_fractional_number`: FAIL; AssertionError: 'unsupported duration' not found in "malformed duration: '1.5h'"
- E1 `test_value_error_unknown_unit`: FAIL; AssertionError: 'unsupported duration' not found in "malformed duration: '1x'"
- E1 `test_value_error_repeated_unit`: FAIL; AssertionError: 'unsupported duration' not found in "repeated unit 'h' in duration: '1h1h'"
- E1 `test_value_error_out_of_order_components`: FAIL; AssertionError: 'unsupported duration' not found in "units out of order in duration: '30m1h'"
- E1 `test_value_error_unit_without_number`: FAIL; AssertionError: 'unsupported duration' not found in "malformed duration: 'h'"
- E1 `test_value_error_number_without_unit_in_multi_component`: FAIL; AssertionError: 'unsupported duration' not found in "malformed duration: '1h30'"
- E1 `test_value_error_other_malformed_text`: FAIL; AssertionError: 'unsupported duration' not found in "malformed duration: 'abc'"
- E1 `test_return_type_is_float_for_all_accepted_inputs`: ERROR; ValueError: repeated unit 'm' in duration: '1d1h1m1s1ms'

## 8. E5 Drift audit
Score 0.400 (off_target; threshold 0.6). The implementation fails to parse 'ms' units due to regex alternation order and incorrectly accepts whitespace between numbers and units. Existing tests pass but the new acceptance criteria are not satisfied.

Scope narrowed: The regex pattern order 'd|h|m|s|ms' causes 'ms' to be split into 'm' and 's', rejecting valid inputs like '500ms', '1s500ms', and '1d1h1m1s1ms'.  
Scope widened: The implementation removes all whitespace (re.sub(r'\s+', '', stripped)), which incorrectly accepts whitespace between a number and its unit (e.g., '1 h' becomes '1h' and parses successfully) while the contract requires ValueError for such cases.  
Unsupported claims: turn 3 reason: "Replace the old parse_duration implementation with a new one that supports multi‑component durations while preserving existing plain‑integer behavior and meetin" — the claim of meeting the contract is unsupported because the tool output only shows existing tests passing; the new acceptance criteria (ms parsing, whitespace rejection) are not validated and the implementation fails them.

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | thinking | 1737 | 2472 | 0 | 0.009153 | 8.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | no-thinking | 1864 | 1477 | 0 | 0.001888 | 10.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | no-thinking | 1789 | 75 | 0 | 0.000604 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | no-thinking | 1996 | 68 | 0 | 0.000660 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | no-thinking | 2273 | 1010 | 0 | 0.001591 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | no-thinking | 3324 | 74 | 0 | 0.001064 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | no-thinking | 3593 | 518 | 0 | 0.001544 | 5.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | no-thinking | 3799 | 494 | 0 | 0.001584 | 4.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | no-thinking | 3999 | 348 | 0 | 0.001513 | 4.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | no-thinking | 4198 | 496 | 0 | 0.001706 | 5.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | no-thinking | 4442 | 494 | 0 | 0.001777 | 5.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | no-thinking | 4451 | 644 | 0 | 0.001915 | 5.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | no-thinking | 4388 | 522 | 0 | 0.001786 | 12.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | no-thinking | 3553 | 71 | 0 | 0.001130 | 5.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | thinking | 3160 | 3839 | 0 | 0.014677 | 17.0s | ok |

Model calls: 15 (0 failed, 0 malformed); tokens in/out/cached 48566/12602/0; USD: 0.042592.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ac0-d1cc-75af-a93f-556cd239a986 | SUCCESS | 0 | 0.749s | retained | off | 0.00285751 |
| red-1 | 01a14ac1-28cd-74c2-80b2-b587e7a7fe83 | SUCCESS | 0 | 5.93s | disposable | off | 0.05122526 |
| impl-tests-4 | 01a14ac1-90da-734f-bcca-6dfdfc2422e3 | SUCCESS | 0 | 0.777s | disposable | off | 0.00282441 |
| impl-tests-12 | 01a14ac2-62c5-71ee-beb9-a774924b1086 | SUCCESS | 0 | 0.743s | disposable | off | 0.0028256799999999997 |
| verify | 01a14ac2-82ba-774f-af25-70334181e623 | SUCCESS | 0 | 5.848s | disposable | off | 0.051085030000000003 |
| existing | 01a14ac2-c702-7760-b2b2-5cad52c5c2c5 | SUCCESS | 0 | 2.117s | disposable | off | 0.01532708 |

Sandbox operations: 6, total guest duration 16.164s, retained images ['bf2f990b-709a-461c-a68b-18e324aabc64'].

## 11. Limitations of this bundle
- Profile 'submission-smoke': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
