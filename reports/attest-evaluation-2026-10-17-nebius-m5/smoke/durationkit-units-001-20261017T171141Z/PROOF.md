# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261017T171141Z` · profile `submission-smoke` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:11:41.561776+00:00, finished 2026-10-17T17:15:20.015483+00:00.

**Accept this patch.** All 17 sealed tests pass on the candidate in a fresh sandbox, and 5 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 17 of 17 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 4 one-line change(s) to the patch were not caught by the sealed tests (score 0.667, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 17 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 5 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 8 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 12 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 4 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 5 of 17 failed on the unmodified base; 17 of 17 pass on the candidate |
| E2 | Mutation check | pass | bound | 8 of 12 one-line mutants caught, 4 survived, 0 unknown; score 0.667 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d0878f4b-3cc9-4588-9d43-18d14f5c6f47`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; git commit 6b786a2e51bba634d63cc8b4ee75bb215c168fa7). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/attest-eval-frozen/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms) in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. Plain integer strings (seconds) remain valid. Invalid inputs raise ValueError; non-string inputs raise TypeError. Existing tests must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (optionally surrounded by white | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only after stripping.; ValueError: if any component contains a negative number ( |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('  42 ') == 42.0 (existing test).
3. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
4. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
5. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
6. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0.
7. Whitespace between number and unit is rejected: '1 h' raises ValueError.
8. Return type is float for every accepted input.
9. ValueError for empty string '' and whitespace-only '   '.
10. ValueError for negative numbers: '-1h'.
11. ValueError for fractional numbers: '1.5h'.
12. ValueError for unknown units: '1x'.
13. ValueError for repeated units: '1h1h'.
14. ValueError for components out of descending order: '30m1h'.
15. ValueError for unit without number: 'h'.
16. ValueError for number without unit in multi-component string: '1h30'.
17. ValueError for completely malformed text: 'abc'.
18. TypeError for non-string input such as 90 or None.
19. Existing tests in tests/test_parse.py pass without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `ea74f092055616a082238cef90d0d0c7a2ffddb8f21fb6f555089169ca630b3f`, 17 test methods, sealed at 2026-10-17T17:12:11.942406+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (5 of 17 methods: ERROR 5): 5 of 17 methods failing, 12 passing; operation `01a14ad9-6cfd-720e-91be-8c91e0666c4f`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationExtended.test_combined_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_empty_and_whitespace_only_strings | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_fractional_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_malformed_text | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_negative_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_non_string_input_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_number_without_unit_in_multi_component | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_out_of_order_components | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_with_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_repeated_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_return_type_is_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_components_all_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_unit_without_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_unknown_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_number_unit_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,73 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts two forms:
+    1. A plain non-negative integer representing seconds (e.g., "90").
+    2. One or more components of the form <non-negative integer><unit> where unit
+       is one of d, h, m, s, ms. Components must appear in descending unit order
+       (d > h > m > s > ms), each unit at most once. Whitespace is allowed around
+       the entire string and between components, but not between a number and its
+       unit.
+
+    Returns the total seconds as a float.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("empty duration string")
+    # Plain integer seconds
+    if stripped.isdigit():
+        return float(stripped)
+    # Parse components
+    i = 0
+    total = 0.0
+    seen_units = set()
+    prev_order = None
+    # Order mapping: higher value means larger unit
+    order_map = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    factor_map = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
+    n = len(stripped)
+    while i < n:
+        # Skip whitespace between components
+        while i < n and stripped[i].isspace():
+            i += 1
+        if i >= n:
+            break  # trailing whitespace
+        # Parse number
+        start_num = i
+        while i < n and stripped[i].isdigit():
+            i += 1
+        if start_num == i:
+            raise ValueError(f"missing number in duration at position {start_num}")
+        num_str = stripped[start_num:i]
+        # Parse unit
+        if i >= n:
+            raise ValueError(f"missing unit after number '{num_str}'")
+        # Check for ms first
+        if stripped[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif stripped[i] in 'dhms':
+            unit = stripped[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown unit '{stripped[i]}' after number '{num_str}'")
+        # Convert number
+        try:
+            num = int(num_str)
+        except ValueError:
+            raise ValueError(f"invalid number '{num_str}'")
+        if num < 0:
+            raise ValueError(f"negative number '{num_str}'")
+        # Accumulate
+        total += num * factor_map[unit]
+        # Validate unit uniqueness and order
+        if unit in seen_units:
+            raise ValueError(f"repeated unit '{unit}'")
+        seen_units.add(unit)
+        curr_order = order_map[unit]
+        if prev_order is not None and curr_order >= prev_order:
+            raise ValueError(f"units not in descending order: '{unit}' follows a larger or equal unit")
+        prev_order = curr_order
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (66 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (17 of 17 methods, each in its own process). Operation `01a14adb-605e-701f-be6b-4ea64386756d`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14adb-842f-73a1-a6b9-f47c6bc02f4c`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.667 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 8 killed, 4 survived, 0 unknown; mutation score 0.667 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-1bce36e817 | durationkit/parse.py | 20 | remove `not` | killed | test_sealed.TestParseDurationExtended.test_plain_integer_with_whitespace, test_sealed.TestParseDurationExtended.test_zer | 01a14adb-aef8-77b5-8fa5-ff8d2a4de046 |
| m02-874496f019 | durationkit/parse.py | 31 | 4 -> 5 | survived |  | 01a14adb-af21-7248-afd9-8f732e30e0ca |
| m03-ce6f62dee9 | durationkit/parse.py | 31 | 0 -> 1 | killed | test_sealed.TestParseDurationExtended.test_combined_descending_order | 01a14adb-af29-7535-b2f9-bf18075a24d1 |
| m04-d7d6c47305 | durationkit/parse.py | 32 | 60 -> 61 | killed | test_sealed.TestParseDurationExtended.test_single_components_all_units, test_sealed.TestParseDurationExtended.test_combi | 01a14adb-af18-7295-a31c-5f05591950ac |
| m05-4ca9af9d41 | durationkit/parse.py | 36 | And -> Or | killed | test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit, test_sealed.TestParseDurationExtended.test_single | 01a14adb-af1f-76b8-8250-b20263c72ae8 |
| m06-7ad2e708bd | durationkit/parse.py | 42 | Lt -> LtE | killed | test_sealed.TestParseDurationExtended.test_number_without_unit_in_multi_component | 01a14adb-af01-760b-b036-44800aa37ee9 |
| m07-292f467a6c | durationkit/parse.py | 45 | raise -> pass | survived |  | 01a14adb-aef2-757c-ac4c-292243b9ff4b |
| m08-32e8211491 | durationkit/parse.py | 51 | 2 -> 3 | survived |  | 01a14adb-af0b-7386-a448-08daa21d068c |
| m09-c956a0b048 | durationkit/parse.py | 54 | In -> NotIn | killed | test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit, test_sealed.TestParseDurationExtended.test_single | 01a14adb-c9c3-73de-b721-64713026197b |
| m10-10ba94f773 | durationkit/parse.py | 63 | raise -> pass | survived |  | 01a14adb-d442-77ae-b260-4c6014fa8df8 |
| m11-630d3f35ce | durationkit/parse.py | 67 | Mult -> Div | killed | test_sealed.TestParseDurationExtended.test_single_components_all_units, test_sealed.TestParseDurationExtended.test_combi | 01a14adb-d498-70ce-b457-7c9614e8c585 |
| m12-03628faacd | durationkit/parse.py | 73 | IsNot -> Is | killed | test_sealed.TestParseDurationExtended.test_zero_and_zero_seconds_unit, test_sealed.TestParseDurationExtended.test_single | 01a14adb-d4cf-77b5-baa8-adae459834df |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `2fa3b0a5f89f132ea2cd6811a4675dbec24bd2b15fce127547960f01fa7e1a51`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a14adc-1db7-76c9-a460-0d95a710c45b`. Notes: Targeted edge cases: large numbers, leading zeros, various whitespace chars, trailing whitespace, ms fraction sum, all-zero components, non‑adjacent repeated unit, equal‑unit order violation, empty after strip, non‑string inputs.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The implementation fully satisfies the task requirements, extending parse_duration to parse multi-component duration strings with proper validation while preserving existing behavior for plain integers. All acceptance criteria are met, existing tests pass, and no scope deviations are observed.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 1655 | 0 | 0.006702 | 5.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2000 | 912 | 0 | 0.001421 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1859 | 97 | 0 | 0.000645 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1952 | 91 | 0 | 0.000667 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2154 | 176 | 0 | 0.000805 | 3.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2369 | 4512 | 0 | 0.004772 | 81.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3397 | 99 | 0 | 0.001108 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 3656 | 1547 | 0 | 0.002489 | 13.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 4519 | 109 | 0 | 0.001454 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 2648 | 1201 | 0 | 0.001875 | 9.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3066 | 5835 | 0 | 0.020571 | 17.0s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 29357/16234/0; USD: 0.042509.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ad9-2a8e-7674-8606-3786042fb26e | SUCCESS | 0 | 0.756s | retained | off | 0.0028758399999999997 |
| red-1 | 01a14ad9-6cfd-720e-91be-8c91e0666c4f | SUCCESS | 0 | 4.024s | disposable | off | 0.03324382 |
| impl-tests-5 | 01a14adb-06a1-72df-a874-d7c4b1e7fb47 | SUCCESS | 0 | 0.796s | disposable | off | 0.00282085 |
| impl-python-6 | 01a14adb-46c5-742f-9e9f-64d5a01046c4 | SUCCESS | 0 | 0.646s | disposable | off | 0.00124471 |
| verify | 01a14adb-605e-701f-be6b-4ea64386756d | SUCCESS | 0 | 3.987s | disposable | off | 0.033039450000000005 |
| existing | 01a14adb-842f-73a1-a6b9-f47c6bc02f4c | SUCCESS | 0 | 2.11s | disposable | off | 0.015368839999999998 |
| mutant-m01-1bce36e817 | 01a14adb-aef8-77b5-8fa5-ff8d2a4de046 | SUCCESS | 0 | 3.833s | disposable | off | 0.030006210000000002 |
| mutant-m02-874496f019 | 01a14adb-af21-7248-afd9-8f732e30e0ca | SUCCESS | 0 | 3.754s | disposable | off | 0.02948785 |
| mutant-m03-ce6f62dee9 | 01a14adb-af29-7535-b2f9-bf18075a24d1 | SUCCESS | 0 | 3.856s | disposable | off | 0.03020998 |
| mutant-m05-4ca9af9d41 | 01a14adb-af1f-76b8-8250-b20263c72ae8 | SUCCESS | 0 | 3.755s | disposable | off | 0.02973786 |
| mutant-m04-d7d6c47305 | 01a14adb-af18-7295-a31c-5f05591950ac | SUCCESS | 0 | 3.785s | disposable | off | 0.03010881 |
| mutant-m06-7ad2e708bd | 01a14adb-af01-760b-b036-44800aa37ee9 | SUCCESS | 0 | 3.801s | disposable | off | 0.029761489999999998 |
| mutant-m07-292f467a6c | 01a14adb-aef2-757c-ac4c-292243b9ff4b | SUCCESS | 0 | 3.659s | disposable | off | 0.029996049999999996 |
| mutant-m08-32e8211491 | 01a14adb-af0b-7386-a448-08daa21d068c | SUCCESS | 0 | 3.781s | disposable | off | 0.029711210000000002 |
| mutant-m09-c956a0b048 | 01a14adb-c9c3-73de-b721-64713026197b | SUCCESS | 0 | 3.76s | disposable | off | 0.02992277 |
| mutant-m10-10ba94f773 | 01a14adb-d442-77ae-b260-4c6014fa8df8 | SUCCESS | 0 | 3.731s | disposable | off | 0.030321690000000002 |
| mutant-m11-630d3f35ce | 01a14adb-d498-70ce-b457-7c9614e8c585 | SUCCESS | 0 | 3.73s | disposable | off | 0.02986624 |
| mutant-m12-03628faacd | 01a14adb-d4cf-77b5-baa8-adae459834df | SUCCESS | 0 | 3.73s | disposable | off | 0.03042463 |
| breaker-tests | 01a14adc-1db7-76c9-a460-0d95a710c45b | SUCCESS | 0 | 2.981s | disposable | off | 0.02183859 |

Sandbox operations: 19, total guest duration 60.475s, retained images ['d0878f4b-3cc9-4588-9d43-18d14f5c6f47'].

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
