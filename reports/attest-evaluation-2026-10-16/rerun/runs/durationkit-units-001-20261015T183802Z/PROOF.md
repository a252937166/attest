# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261015T183802Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:38:02.374986+00:00, finished 2026-10-15T18:43:42.954114+00:00.

Reasons: model-written adversarial tests could not be produced: adversarial test authoring failed: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protoc; rerun the breaker stage or review manually


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `bdf8669d-583c-4abb-be79-7359387fc27e`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms), in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings (seconds only) and continue to raise TypeError for non-string input and ValueError for all malformed inputs as specified.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (optionally surrounded by white | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only after stripping.; ValueError: if any component has a negative number (e.g., |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. TypeError for non-string input such as 90 or None.
8. The return type is float for every accepted input.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d765a454b21e0b738eb36514ec1b1a8ab341946124aeff01445b2b7594722ae5`, 28 test methods, sealed at 2026-10-15T18:39:33.885679+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 28 methods: ERROR 13): 13 of 28 methods failing, 15 passing; operation `01a140dc-bb3e-7318-b294-65be2419870f`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationExtended.test_all_components_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_duplicate_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_empty_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_five_components_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_four_components_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_fractional_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_missing_number_before_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_negative_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_non_string_input_raises_TypeError | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_number_without_unit_when_other_units_present_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_other_malformed_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_out_of_order_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_plain_integer_with_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_return_type_is_float_for_valid_inputs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_days | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_hours | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_milliseconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_minutes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_single_component_seconds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_three_components_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_two_components_descending | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_unknown_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_around_and_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_between_number_and_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_whitespace_only_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_zero_plain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationExtended.test_zero_with_unit | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 13 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -2,14 +2,75 @@
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
+    """Parse a duration string and return the total number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts two forms:
+    1. A plain non-negative integer (optionally surrounded by whitespace) representing seconds,
+       e.g., ``"90"`` -> 90.0.
+    2. One or more components, each a non-negative integer immediately followed by a unit
+       (d, h, m, s, ms), with components ordered from largest to smallest unit
+       (d > h > m > s > ms), each unit appearing at most once. Whitespace is allowed
+       around the entire string and between components, but not between a number and its unit.
+
+    The returned float is the sum of each component converted to seconds
+    (1d=86400, 1h=3600, 1m=60, 1s=1, 1ms=0.001).
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
-    stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    s = text.strip()
+    if not s:
+        raise ValueError("empty duration string")
+    # Plain integer form (seconds only)
+    if s.isdigit():
+        return float(s)
+    # Component form
+    total = 0.0
+    i = 0
+    n = len(s)
+    # unit info: order rank (lower = larger unit) and factor to seconds
+    unit_rank = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    unit_factor = {'d': 86400.0, 'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
+    seen = set()
+    prev_rank = None  # rank of previous unit (larger unit has smaller rank)
+    while i < n:
+        # skip whitespace
+        while i < n and s[i].isspace():
+            i += 1
+        if i >= n:
+            break
+        # parse number (one or more digits)
+        start = i
+        while i < n and s[i].isdigit():
+            i += 1
+        if start == i:
+            raise ValueError(f"missing number in duration at position {start}")
+        num_str = s[start:i]
+        # leading zeros allowed, but ensure non-negative (already)
+        try:
+            value = int(num_str)
+        except ValueError:
+            raise ValueError(f"invalid number {num_str!r}")
+        # parse unit
+        if i + 2 <= n and s[i:i+2] == 'ms':
+            unit = 'ms'
+            i += 2
+        elif i < n and s[i] in 'dhms':
+            unit = s[i]
+            i += 1
+        else:
+            raise ValueError(f"unknown or missing unit after number {num_str!r}")
+        # check unit not repeated
+        if unit in seen:
+            raise ValueError(f"unit {unit!r} appears more than once")
+        # check order
+        rank = unit_rank[unit]
+        if prev_rank is not None and rank <= prev_rank:
+            raise ValueError(f"units not in descending order: {unit!r} after previous")
+        seen.add(unit)
+        prev_rank = rank
+        # add to total
+        total += value * unit_factor[unit]
+        # after unit, loop continues (whitespace will be skipped)
+    if not seen:
+        raise ValueError(f"no valid components found in {text!r}")
+    return total
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: OK (28 of 28 methods, each in its own process). Operation `01a140df-d3b1-744a-b47a-baa7ca298127`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| static_ids_match_red | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |

Held-out suite: none configured.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | OK |
| sealed_binding | pass | all checks pass |
| mutation | pass | score 0.833 on 12 mutants |
| adversarial_tests | FAIL | adversarial test authoring failed: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protoc |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 10 killed, 2 survived, 0 unknown; mutation score 0.833 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-bec0f43687 | durationkit/parse.py | 21 | remove `not` | killed | test_sealed.TestParseDurationExtended.test_plain_integer_seconds, test_sealed.TestParseDurationExtended.test_plain_integ | 01a140df-f85c-7646-b0c4-e6102c3a1922 |
| m02-7df9839a9e | durationkit/parse.py | 31 | 0 -> 1 | killed | test_sealed.TestParseDurationExtended.test_three_components_descending, test_sealed.TestParseDurationExtended.test_all_c | 01a140df-fc85-7726-938c-390264fdaf17 |
| m03-d4a798ad66 | durationkit/parse.py | 31 | 3 -> 4 | killed | test_sealed.TestParseDurationExtended.test_five_components_descending, test_sealed.TestParseDurationExtended.test_all_co | 01a140df-f8ca-7033-aaef-4351af242e4f |
| m04-2de6b3dbc5 | durationkit/parse.py | 37 | And -> Or | killed | test_sealed.TestParseDurationExtended.test_zero_with_unit, test_sealed.TestParseDurationExtended.test_single_component_d | 01a140df-f8e3-779f-bb7a-7b385c3b946e |
| m05-f548d8f3ed | durationkit/parse.py | 43 | Lt -> LtE | killed | test_sealed.TestParseDurationExtended.test_number_without_unit_when_other_units_present_raises | 01a140df-f8b1-740c-bfb3-17bbbb00be57 |
| m06-b72660f733 | durationkit/parse.py | 46 | raise -> pass | survived |  | 01a140df-f87d-7796-be3b-8aaaa902cf66 |
| m07-1f896d2a55 | durationkit/parse.py | 54 | Add -> Sub | survived |  | 01a140df-f8be-758f-aa78-3d645df33f9d |
| m08-91cfc6dd0f | durationkit/parse.py | 54 | Add -> Sub | killed | test_sealed.TestParseDurationExtended.test_single_component_milliseconds, test_sealed.TestParseDurationExtended.test_fiv | 01a140df-f8bf-7451-acb1-1af6d8c10946 |
| m09-a01cbea3dc | durationkit/parse.py | 57 | Lt -> LtE | killed | test_sealed.TestParseDurationExtended.test_number_without_unit_when_other_units_present_raises | 01a140e0-1e8a-7355-a555-95a62fe4e336 |
| m10-b55eb2696a | durationkit/parse.py | 59 | 1 -> 2 | killed | test_sealed.TestParseDurationExtended.test_two_components_descending, test_sealed.TestParseDurationExtended.test_three_c | 01a140e0-1ebb-729f-8ce5-57bbc84eca5a |
| m11-f012c3a026 | durationkit/parse.py | 67 | IsNot -> Is | killed | test_sealed.TestParseDurationExtended.test_zero_with_unit, test_sealed.TestParseDurationExtended.test_single_component_d | 01a140e0-1f05-72b9-b766-e1cbaf75a0c7 |
| m12-92cd75ff1b | durationkit/parse.py | 68 | raise -> pass | killed | test_sealed.TestParseDurationExtended.test_out_of_order_raises | 01a140e0-1efc-738c-be9c-69f1dab798ed |

Model-written adversarial tests (`breaker_tests.py`, by `None`, sha256 `None`): authoring failed: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of p; binding FAILED; operation `None`. Notes: 

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fully implements the required extension to parse_duration, adding support for multi-component duration strings with units d, h, m, s, ms in descending order while preserving the existing plain-integer behavior. All acceptance criteria pass, existing tests pass, and no extra features or omissions are present.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 1567 | 0 | 0.006323 | 5.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1832 | 12225 | 0 | 0.011552 | 70.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1719 | 105 | 0 | 0.000610 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 1813 | 90 | 0 | 0.000625 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2015 | 16000 | 0 | 0.015005 | 76.5s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3-repair | default | 2080 | 228 | 0 | 0.000829 | 4.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2220 | 1694 | 0 | 0.002191 | 11.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 2426 | 4018 | 0 | 0.004344 | 21.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3543 | 91 | 0 | 0.001145 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3806 | 1132 | 0 | 0.002161 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 4258 | 804 | 0 | 0.002001 | 5.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 4971 | 2335 | 0 | 0.003593 | 11.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 6021 | 558 | 0 | 0.002309 | 4.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 6114 | 2117 | 0 | 0.003739 | 10.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 6857 | 149 | 0 | 0.002191 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | default | 6916 | 268 | 0 | 0.002316 | 3.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | - | - | - | - | 5.0s | error |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3260 | 6384 | 0 | 0.022412 | 19.2s | ok |

Model calls: 18 (2 failed, 1 malformed); tokens in/out/cached 61473/49765/0; USD: 0.083346.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140db-7ed2-75fa-9daf-db2cc8a5fd68 | SUCCESS | 0 | 0.789s | retained | off | 0.0028075599999999997 |
| red-1 | 01a140dc-bb3e-7318-b294-65be2419870f | SUCCESS | 0 | 5.434s | disposable | off | 0.04673171 |
| impl-tests-6 | 01a140de-b77e-75b5-8e6a-4f4dbca875e6 | SUCCESS | 0 | 0.756s | disposable | off | 0.00276181 |
| impl-python-7 | 01a140de-e52b-7422-9c36-d7db9ccf97d2 | SUCCESS | 0 | 0.522s | disposable | off | 0.0011336299999999998 |
| impl-python-8 | 01a140df-085a-7415-8954-546cca054d1c | SUCCESS | 0 | 0.528s | disposable | off | 0.00113086 |
| impl-python-9 | 01a140df-4671-753f-8e97-71b51464e551 | SUCCESS | 0 | 0.54s | disposable | off | 0.0011366500000000001 |
| impl-tests-10 | 01a140df-6a17-7129-95aa-63aa04693268 | SUCCESS | 0 | 0.724s | disposable | off | 0.00275464 |
| impl-python-11 | 01a140df-a095-71a2-b79a-5e1d2483446c | SUCCESS | 0 | 0.55s | disposable | off | 0.00114977 |
| impl-tests-12 | 01a140df-b7aa-705b-b6d0-319af910dede | SUCCESS | 0 | 0.771s | disposable | off | 0.00273846 |
| verify | 01a140df-d3b1-744a-b47a-baa7ca298127 | SUCCESS | 0 | 5.743s | disposable | off | 0.04899678 |
| mutant-m01-bec0f43687 | 01a140df-f85c-7646-b0c4-e6102c3a1922 | SUCCESS | 0 | 5.54s | disposable | off | 0.047586079999999996 |
| mutant-m02-7df9839a9e | 01a140df-fc85-7726-938c-390264fdaf17 | SUCCESS | 0 | 5.642s | disposable | off | 0.04790348 |
| mutant-m04-2de6b3dbc5 | 01a140df-f8e3-779f-bb7a-7b385c3b946e | SUCCESS | 0 | 5.596s | disposable | off | 0.047308319999999994 |
| mutant-m03-d4a798ad66 | 01a140df-f8ca-7033-aaef-4351af242e4f | SUCCESS | 0 | 5.582s | disposable | off | 0.04723135999999999 |
| mutant-m06-b72660f733 | 01a140df-f87d-7796-be3b-8aaaa902cf66 | SUCCESS | 0 | 5.582s | disposable | off | 0.04761696 |
| mutant-m05-f548d8f3ed | 01a140df-f8b1-740c-bfb3-17bbbb00be57 | SUCCESS | 0 | 5.584s | disposable | off | 0.047449439999999996 |
| mutant-m07-1f896d2a55 | 01a140df-f8be-758f-aa78-3d645df33f9d | SUCCESS | 0 | 5.53s | disposable | off | 0.04695747 |
| mutant-m08-91cfc6dd0f | 01a140df-f8bf-7451-acb1-1af6d8c10946 | SUCCESS | 0 | 5.531s | disposable | off | 0.047458679999999996 |
| mutant-m09-a01cbea3dc | 01a140e0-1e8a-7355-a555-95a62fe4e336 | SUCCESS | 0 | 5.529s | disposable | off | 0.0475898 |
| mutant-m10-b55eb2696a | 01a140e0-1ebb-729f-8ce5-57bbc84eca5a | SUCCESS | 0 | 5.521s | disposable | off | 0.04711722 |
| mutant-m11-f012c3a026 | 01a140e0-1f05-72b9-b766-e1cbaf75a0c7 | SUCCESS | 0 | 5.604s | disposable | off | 0.04755105 |
| mutant-m12-92cd75ff1b | 01a140e0-1efc-738c-be9c-69f1dab798ed | SUCCESS | 0 | 5.552s | disposable | off | 0.04747945 |

Sandbox operations: 22, total guest duration 83.15s, retained images ['bdf8669d-583c-4abb-be79-7359387fc27e'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
