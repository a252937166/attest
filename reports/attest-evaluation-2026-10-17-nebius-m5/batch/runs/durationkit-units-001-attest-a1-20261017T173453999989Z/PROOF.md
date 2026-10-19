# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261017T173453999989Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:34:54.000184+00:00, finished 2026-10-17T17:38:13.639455+00:00.

**Accept this patch.** All 20 sealed tests pass on the candidate in a fresh sandbox, and 5 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 20 of 20 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 3 one-line change(s) to the patch were not caught by the sealed tests (score 0.75, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 20 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 5 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 15 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 3 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 5 of 20 failed on the unmodified base; 20 of 20 pass on the candidate |
| E2 | Mutation check | pass | bound | 9 of 12 one-line mutants caught, 3 survived, 0 unknown; score 0.75 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `13778f78-a4bb-4023-b5be-395231c40466`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non-negative integer followed by a unit (d, h, m, s, ms), in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings, reject malformed inputs with ValueError, and reject non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non-negative integer (ASCII digits only) optionally  | TypeError: if text is not a string.; ValueError: if text is empty or whitespace-only after stripping.; ValueError: if any component contains a negative number ( |

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. parse_duration('  42 ') == 42.0 (existing behavior preserved).
4. parse_duration('7') returns a float (existing behavior preserved).
5. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
6. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
7. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError (no space between number and unit).
8. ValueError for empty string '' and whitespace-only '   '.
9. ValueError for negative numbers: '-1h'.
10. ValueError for fractional numbers: '1.5h'.
11. ValueError for unknown units: '1x'.
12. ValueError for repeated units: '1h1h'.
13. ValueError for components out of descending order: '30m1h'.
14. ValueError for unit without a number: 'h'.
15. ValueError for number without a unit in a multi-component string: '1h30'.
16. ValueError for completely malformed text: 'abc'.
17. TypeError for non-string input such as 90 or None.
18. The return type is float for every accepted input.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `44636e14d379d6fefcd590ae1d20ed8487b10bd6473d95ccc7ef23e26f67c4d7`, 20 test methods, sealed at 2026-10-17T17:35:31.644371+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 2.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (5 of 20 methods: ERROR 5): 5 of 20 methods failing, 15 passing; operation `01a14aee-dc2e-7779-afc0-c93c7dbd7c0b`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationAcceptance.test_combined_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_empty_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_fractional_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_malformed_text_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_negative_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_non_string_input_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_number_without_unit_multi_component_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_out_of_order_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_repeated_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_return_type_is_float_for_all_valid | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_returns_float_for_int | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_single_components_all_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_space_between_number_and_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_surrounding_whitespace_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_unit_without_number_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_unknown_unit_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_whitespace_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_whitespace_only_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationAcceptance.test_zero_and_zero_s | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,87 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer (seconds) or a sequence of
+    components like ``'1h30m'``. Each component is a non-negative integer
+    immediately followed by a unit suffix (d, h, m, s, ms). Components
+    must be in strictly descending order (d > h > m > s > ms) and each
+    unit may appear at most once. Whitespace is ignored around the string
+    and between components.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
-    stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    s = text.strip()
+    if not s:
+        raise ValueError("empty duration")
+    # Plain integer case (seconds)
+    if s.isdigit():
+        return float(s)
+    # Component-based parsing
+    total = 0.0
+    i = 0
+    n = len(s)
+    # order: higher value means larger unit
+    order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
+    seen = set()
+    prev_order = 5  # larger than any possible order
+    while i < n:
+        # Skip whitespace between components
+        while i < n and s[i].isspace():
+            i += 1
+        if i >= n:
+            break  # Should not happen because outer whitespace stripped
+        # Parse number
+        start = i
+        while i < n and s[i].isdigit():
+            i += 1
+        if start == i:
+            raise ValueError("missing number before unit")
+        num_str = s[start:i]
+        # Parse unit
+        if i < n and s[i] == 'm':
+            # Could be 'ms' or 'm'
+            if i + 1 < n and s[i + 1] == 's':
+                unit = 'ms'
+                i += 2
+            else:
+                unit = 'm'
+                i += 1
+        elif i < n and s[i] in 'dhsm':
+            unit = s[i]
+            i += 1
+        else:
+            raise ValueError("missing unit after number")
+        # Validate unit
+        if unit not in order:
+            raise ValueError(f"unknown unit: {unit}")
+        # Check for duplicate unit
+        if unit in seen:
+            raise ValueError(f"duplicate unit: {unit}")
+        seen.add(unit)
+        # Check descending order
+        cur_order = order[unit]
+        if cur_order >= prev_order:
+            raise ValueError("units not in descending order")
+        prev_order = cur_order
+        # Convert number
+        try:
+            num = int(num_str)
+        except ValueError:
+            raise ValueError(f"invalid number: {num_str}")
+        if num < 0:
+            raise ValueError("negative number")
+        # Convert to seconds
+        if unit == 'd':
+            sec = num * 86400
+        elif unit == 'h':
+            sec = num * 3600
+        elif unit == 'm':
+            sec = num * 60
+        elif unit == 's':
+            sec = num
+        elif unit == 'ms':
+            sec = num * 0.001
+        else:  # Should not happen
+            raise ValueError(f"unsupported unit: {unit}")
+        total += sec
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (81 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (20 of 20 methods, each in its own process). Operation `01a14aef-e015-749b-aed2-bbc0efef50ae`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14af0-042b-7686-a271-4493914ee178`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.75 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (8 of 8 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 9 killed, 3 survived, 0 unknown; mutation score 0.750 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-25f31e9261 | durationkit/parse.py | 17 | remove `not` | killed | test_sealed.TestParseDurationAcceptance.test_plain_integer_seconds, test_sealed.TestParseDurationAcceptance.test_zero_an | 01a14af0-1dda-7723-b604-2f4c89183096 |
| m02-a0315e287a | durationkit/parse.py | 27 | 3 -> 4 | killed | test_sealed.TestParseDurationAcceptance.test_combined_descending_order, test_sealed.TestParseDurationAcceptance.test_ret | 01a14af0-1d59-73fa-aab5-adaab7b95436 |
| m03-b5b23c5ed8 | durationkit/parse.py | 30 | Lt -> LtE | survived |  | 01a14af0-1d94-75d6-b2fb-72c193ecb26a |
| m04-68d183a8d1 | durationkit/parse.py | 38 | Lt -> LtE | killed | test_sealed.TestParseDurationAcceptance.test_number_without_unit_multi_component_raises | 01a14af0-1d84-7312-b27c-8cde1125e46b |
| m05-b819c1f915 | durationkit/parse.py | 44 | Lt -> LtE | killed | test_sealed.TestParseDurationAcceptance.test_number_without_unit_multi_component_raises | 01a14af0-1d68-72b3-a5a2-b45dfb2d0198 |
| m06-edc93fcd72 | durationkit/parse.py | 46 | Lt -> LtE | killed | test_sealed.TestParseDurationAcceptance.test_single_components_all_units, test_sealed.TestParseDurationAcceptance.test_c | 01a14af0-1d8a-773c-9573-7b1423a3116d |
| m07-79d9f8ad39 | durationkit/parse.py | 48 | 2 -> 3 | survived |  | 01a14af0-1dc5-737c-9d60-ef0bf358e29d |
| m08-a24969a64b | durationkit/parse.py | 54 | 1 -> 2 | killed | test_sealed.TestParseDurationAcceptance.test_combined_descending_order, test_sealed.TestParseDurationAcceptance.test_ret | 01a14af0-1d65-707d-99ef-fc7a5e907def |
| m09-56fa639b5e | durationkit/parse.py | 62 | raise -> pass | survived |  | 01a14af0-40ed-723e-8580-25bd0554596d |
| m10-be0e5898d8 | durationkit/parse.py | 74 | Lt -> LtE | killed | test_sealed.TestParseDurationAcceptance.test_zero_and_zero_s | 01a14af0-4130-71a4-98fe-ca403616fdbe |
| m11-9b3b7b7108 | durationkit/parse.py | 79 | Eq -> NotEq | killed | test_sealed.TestParseDurationAcceptance.test_single_components_all_units, test_sealed.TestParseDurationAcceptance.test_c | 01a14af0-422f-720b-9fca-b59e3db5885c |
| m12-c39ced9645 | durationkit/parse.py | 82 | Mult -> Div | killed | test_sealed.TestParseDurationAcceptance.test_single_components_all_units, test_sealed.TestParseDurationAcceptance.test_c | 01a14af0-4291-7594-91da-8bc3333ee275 |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `93de081275930c2870e9287d218f5a3d34c13a09b2946f8cc9e514780cc324e4`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a14af1-1ab0-76ee-bcef-43e68ccd03c7`. Notes: Targeted edge cases: whitespace variants, uppercase units, leading zeros, invalid chars in numbers, trailing garbage, multiple spaces, ms handling, empty after strip.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The implementation adds component-based parsing with order validation and whitespace handling while keeping the plain-integer fast path (lines 15-18). All error cases required by the contract are covered, and the existing test suite passes without modification.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 1721 | 0 | 0.006900 | 6.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1979 | 1482 | 0 | 0.001927 | 9.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-2 | low | 2026 | 1002 | 0 | 0.001510 | 6.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1856 | 103 | 0 | 0.000650 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1950 | 90 | 0 | 0.000666 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2152 | 4097 | 0 | 0.004333 | 24.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 3261 | 168 | 0 | 0.001129 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3519 | 1021 | 0 | 0.001975 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 4430 | 134 | 0 | 0.001450 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 4689 | 217 | 0 | 0.001602 | 3.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 2750 | 931 | 0 | 0.001663 | 6.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3107 | 5257 | 0 | 0.018878 | 15.1s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 33456/16223/0; USD: 0.042683.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14aee-69fb-767e-bb33-bd75561f1fa0 | SUCCESS | 0 | 0.843s | retained | off | 0.00284079 |
| red-2 | 01a14aee-dc2e-7779-afc0-c93c7dbd7c0b | SUCCESS | 0 | 4.696s | disposable | off | 0.037855330000000006 |
| impl-tests-4 | 01a14aef-76ca-766f-a9f8-20de18c0f053 | SUCCESS | 0 | 0.999s | disposable | off | 0.0028748499999999995 |
| impl-python-5 | 01a14aef-a225-7619-96d2-bd609f59185d | SUCCESS | 0 | 0.926s | disposable | off | 0.00123698 |
| impl-tests-6 | 01a14aef-ba75-7595-b213-6de14e778d5f | SUCCESS | 0 | 0.795s | disposable | off | 0.0028697500000000003 |
| verify | 01a14aef-e015-749b-aed2-bbc0efef50ae | SUCCESS | 0 | 4.57s | disposable | off | 0.038285280000000005 |
| existing | 01a14af0-042b-7686-a271-4493914ee178 | SUCCESS | 0 | 2.462s | disposable | off | 0.01529376 |
| mutant-m01-25f31e9261 | 01a14af0-1dda-7723-b604-2f4c89183096 | SUCCESS | 0 | 4.319s | disposable | off | 0.034962070000000005 |
| mutant-m02-a0315e287a | 01a14af0-1d59-73fa-aab5-adaab7b95436 | SUCCESS | 0 | 4.372s | disposable | off | 0.03559956 |
| mutant-m03-b5b23c5ed8 | 01a14af0-1d94-75d6-b2fb-72c193ecb26a | SUCCESS | 0 | 4.316s | disposable | off | 0.034990360000000005 |
| mutant-m04-68d183a8d1 | 01a14af0-1d84-7312-b27c-8cde1125e46b | SUCCESS | 0 | 4.368s | disposable | off | 0.035410460000000005 |
| mutant-m05-b819c1f915 | 01a14af0-1d68-72b3-a5a2-b45dfb2d0198 | SUCCESS | 0 | 4.317s | disposable | off | 0.035194180000000005 |
| mutant-m06-edc93fcd72 | 01a14af0-1d8a-773c-9573-7b1423a3116d | SUCCESS | 0 | 4.37s | disposable | off | 0.03552139 |
| mutant-m07-79d9f8ad39 | 01a14af0-1dc5-737c-9d60-ef0bf358e29d | SUCCESS | 0 | 4.319s | disposable | off | 0.03462481 |
| mutant-m08-a24969a64b | 01a14af0-1d65-707d-99ef-fc7a5e907def | SUCCESS | 0 | 4.337s | disposable | off | 0.03502069000000001 |
| mutant-m09-56fa639b5e | 01a14af0-40ed-723e-8580-25bd0554596d | SUCCESS | 0 | 4.478s | disposable | off | 0.034590470000000005 |
| mutant-m10-be0e5898d8 | 01a14af0-4130-71a4-98fe-ca403616fdbe | SUCCESS | 0 | 4.256s | disposable | off | 0.035115930000000004 |
| mutant-m11-9b3b7b7108 | 01a14af0-422f-720b-9fca-b59e3db5885c | SUCCESS | 0 | 4.202s | disposable | off | 0.034567730000000005 |
| mutant-m12-c39ced9645 | 01a14af0-4291-7594-91da-8bc3333ee275 | SUCCESS | 0 | 4.203s | disposable | off | 0.03495977 |
| breaker-tests | 01a14af1-1ab0-76ee-bcef-43e68ccd03c7 | SUCCESS | 0 | 2.444s | disposable | off | 0.0185329 |

Sandbox operations: 20, total guest duration 69.592s, retained images ['13778f78-a4bb-4023-b5be-395231c40466'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
