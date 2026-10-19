# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261019T103954946240Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T10:39:54.946611+00:00, finished 2026-10-19T10:51:14.536728+00:00.

**Accept this patch.** All 24 sealed tests pass on the candidate in a fresh sandbox, and 10 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 24 of 24 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 2 one-line change(s) to the patch were not caught by the sealed tests (score 0.833, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 24 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 10 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 10 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 11 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 14 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 2 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 10 of 24 failed on the unmodified base; 24 of 24 pass on the candidate |
| E2 | Mutation check | pass | bound | 10 of 12 one-line mutants caught, 2 survived, 0 unknown; score 0.833 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 11 of 11 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `c915ef77-e8e5-4fe4-95e9-74b92806ed05`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.6.0 revision `b11ec0658845e54d` (36 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision5-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer count of seconds or a sequence of integer-and-unit components using d, h, m, s and ms. Components must use distinct units in descending order, with optional whitespace around the input and between components. Preserve the public import, float return type, existing plain-seconds behavior and TypeError for non-string inputs. Reject malformed strings with ValueError, and leave existing tests unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also remains available as durationkit.parse.parse_duration. After removing surrounding whitespace, accept either an unsigned integer alone or one or more compon | TypeError: input is not a string.; ValueError: input is empty or contains only whitespace.; ValueError: a number has a sign, decimal point, exponent, separator  |

Acceptance criteria:
AC1. 1. All existing tests in tests/ pass without modifying those files.
AC2. 2. The imports from durationkit import parse_duration and from durationkit.parse import parse_duration remain valid.
AC3. 3. Plain seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0 and '0007' returns 7.0.
AC4. 4. Single components produce the expected seconds: '2d' → 172800.0, '3h' → 10800.0, '15m' → 900.0, '45s' → 45.0 and '500ms' → 0.5.
AC5. 5. Combined components work: '1h30m' → 5400.0, '2d4h' → 187200.0, '1m1s' → 61.0, '1s500ms' → 1.5 and '1d1h1m1s1ms' → 90061.001. Fractional results may be checked with floating-point tolerance.
AC6. 6. Skipped units and unrestricted component values are accepted: '1d1ms' returns approximately 86400.001, '90m' returns 5400.0 and '1500ms' returns 1.5.
AC7. 7. Leading zeros and zero components are accepted: '001h030m' returns 5400.0; '0s', '0ms' and '0d0h0m0s0ms' each return 0.0.
AC8. 8. Whitespace around the input and between complete components is accepted: ' 1h 30m ' and '\t1h\n30m\r' each return 5400.0. Python-recognized Unicode whitespace is also accepted in those positions.
AC9. 9. Every accepted input returns an instance of float, including inputs whose result is integral or zero.
AC10. 10. Empty and whitespace-only strings raise ValueError, including '', '   ' and '\t\n'.
AC11. 11. Signed, fractional and other malformed numeric forms raise ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s' and '1_000s'.
AC12. 12. Unknown units, uppercase units and missing numbers raise ValueError, including '1x', '1H', 'h', 'ms' and 'abc'.
AC13. 13. Repeated units raise ValueError, including '1h1h', '1ms2ms' and '0s0s'. Out-of-order units raise ValueError, including '30m1h', '1ms1s' and '0s0m'.
AC14. 14. Missing units, mixed forms and unmatched text raise ValueError, including '1h30', '30 1h', '1 2', '1h,30m' and '1h!'.
AC15. 15. Whitespace within a component raises ValueError, including '1 h', '1\th', '1 0s' and '1m s'.
AC16. 16. Non-decimal numeric characters raise ValueError in both plain and component forms, including 'Ⅳ', 'Ⅳh', '½', '½s', '①' and '①h'. Tests must not require acceptance or rejection of non-ASCII Unicode decimal digits such as '١٢h'.
AC17. 17. Non-string inputs raise TypeError, including 90, None, 1.5, True, b'90' and an empty list.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are mutually compatible and can be implemented within durationkit/** while preserving the public imports, signature, float return type, and existing tests. No unchanged code imposes a conflicting constraint. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness is constrained (no function, class, lambda or dynamic type, no dynamic code; values of the input domain and the unchanged code only); a demonstrated conflict that involves a derived criterion (AC) or an unconstrained witness is held for a human; a claimed-only conflict never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `7b4ecab82e9ccb42739955c1c1e9ee2220fdb088060d0af80007dd3276c54b56`, 24 test methods, sealed at 2026-10-19T10:43:13.413673+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (10 of 24 methods: ERROR 10): 10 of 24 methods failing, 14 passing; operation `01a153c2-0ff7-71fd-af42-119fc749b6e7`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_ascii_whitespace_between_components_and_around_input | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_number_without_unit_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_strings_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_exponent_and_separated_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zero_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_mixed_plain_seconds_and_components_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_decimal_numeric_characters_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_whitespace_between_components_and_around_input | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_and_uppercase_units_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unmatched_punctuation_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unrestricted_component_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_components_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,46 @@
 """Duration parsing."""
 
 
+_UNITS = {
+    "d": (0, 86400.0),
+    "h": (1, 3600.0),
+    "m": (2, 60.0),
+    "s": (3, 1.0),
+    "ms": (4, 0.001),
+}
+
+
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse plain seconds or descending duration components into seconds."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if all("0" <= char <= "9" for char in stripped):
+        return float(stripped)
+
+    total = 0.0
+    position = 0
+    previous_rank = -1
+    while position < len(stripped):
+        start = position
+        while position < len(stripped) and "0" <= stripped[position] <= "9":
+            position += 1
+        if position == start or position == len(stripped):
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        unit = "ms" if stripped.startswith("ms", position) else stripped[position]
+        if unit not in _UNITS:
+            raise ValueError(f"unsupported duration: {text!r}")
+        rank, multiplier = _UNITS[unit]
+        if rank <= previous_rank:
+            raise ValueError(f"unsupported duration: {text!r}")
+        previous_rank = rank
+        total += float(stripped[start:position]) * multiplier
+        position += len(unit)
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (38 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (24 of 24 methods, each in its own process). Operation `01a153c6-f51f-70b3-b44d-e0996bb80df2`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a153c7-2255-7780-bafd-96a007ff832a`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.833 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (11 of 11 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 10 killed, 2 survived, 0 unknown; mutation score 0.833 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-3985b1996c | durationkit/parse.py | 5 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_components, test_sealed.ParseDurationAcceptanceTests.test_zero_co | 01a153c7-4114-72ad-ab35-0ff2526dd0f0 |
| m02-16a651ab7a | durationkit/parse.py | 7 | 2 -> 3 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_components, test_sealed.ParseDurationAcceptanceTests.test_zero_co | 01a153c7-40fc-774d-925f-8cedcbc970ae |
| m03-8418362978 | durationkit/parse.py | 9 | 4 -> 5 | survived |  | 01a153c7-411f-7248-a267-3ec4000a071e |
| m04-9478a965b2 | durationkit/parse.py | 21 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_plain_seconds | 01a153c7-409e-72b6-9196-d362514c689c |
| m05-7519593a25 | durationkit/parse.py | 26 | 1 -> 2 | survived |  | 01a153c7-416a-7562-b5b9-f71b170440b2 |
| m06-8181ad8aa2 | durationkit/parse.py | 29 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_component_number_without_unit_raises_value_error | 01a153c7-4104-77e8-bbe4-ca06b833c8c2 |
| m07-b7d8a4cecb | durationkit/parse.py | 29 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_si | 01a153c7-4085-731c-947b-25b0025ebbe0 |
| m08-e18efbd11c | durationkit/parse.py | 31 | Eq -> NotEq | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_si | 01a153c7-410b-74e8-a404-3e5d7de60cf9 |
| m09-2afe928861 | durationkit/parse.py | 31 | Or -> And | killed | test_sealed.ParseDurationAcceptanceTests.test_component_number_without_unit_raises_value_error | 01a153c7-62b3-712d-8a36-b904455549ec |
| m10-61c1ef2d2c | durationkit/parse.py | 36 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_fractional_exponent_and_separated_numbers_raise_value_error, test_sealed.P | 01a153c7-6357-74ce-af19-3e99644767f9 |
| m11-2669d3a178 | durationkit/parse.py | 39 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_raise_value_error, test_sealed.ParseDurationAcceptanceTests | 01a153c7-637b-7026-b98f-a5d28874b43a |
| m12-35004ec740 | durationkit/parse.py | 43 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_si | 01a153c7-645b-74db-ab6a-7ac59b64d664 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `16feaf5c4950983fde763c08f5767c83b4e74bf1152e75579a80b56a8006099b`): OK (11 of 11 methods, each in its own process); binding ok; operation `01a153c8-7704-7009-a34d-0fe7fbcf3f2b`. Notes: Targets all unit subsequences and reversed pairs, zero-valued ordering, ms token boundaries, Unicode whitespace, later-component syntax, and equivalent duration forms.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `_UNITS` defines the five requested units, `rank <= previous_rank` rejects repeats and incorrect ordering, and `.isspace()` permits whitespace between complete components while ASCII digit scanning rejects malformed numbers. The signature, float results and TypeError check are preserved; only durationkit/parse.py changed, and observed tool output supports six passing existing tests and targeted checks covering both imports.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10756 | 1506 | 0 | - | 60.7s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12735 | 86 | 7552 | - | 50.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11150 | 2436 | 0 | - | 67.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11026 | 153 | 0 | - | 52.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22871 | 1116 | 11008 | - | 46.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11463 | 125 | 0 | - | 116.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11704 | 185 | 0 | - | 24.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12173 | 778 | 7168 | - | 39.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12872 | 200 | 7168 | - | 22.1s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11480 | 2393 | 0 | - | 59.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12222 | 164 | 7552 | - | 64.7s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 140452/9142/40448; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a153bf-3acc-7598-9825-0bff2849a2bb | SUCCESS | 0 | 0.748s | retained | off | 0.0028841099999999996 |
| red-1 | 01a153c2-0ff7-71fd-af42-119fc749b6e7 | SUCCESS | 0 | 5.191s | disposable | off | 0.04447631 |
| impl-tests-3 | 01a153c5-80ee-7592-8f51-63949763e42e | SUCCESS | 0 | 0.803s | disposable | off | 0.002859 |
| impl-python-5 | 01a153c6-8d19-7522-9e7f-bd6e6e0b766f | SUCCESS | 0 | 0.575s | disposable | off | 0.0012279200000000002 |
| verify | 01a153c6-f51f-70b3-b44d-e0996bb80df2 | SUCCESS | 0 | 5.316s | disposable | off | 0.04454972 |
| existing | 01a153c7-2255-7780-bafd-96a007ff832a | SUCCESS | 0 | 2.206s | disposable | off | 0.01526679 |
| mutant-m01-3985b1996c | 01a153c7-4114-72ad-ab35-0ff2526dd0f0 | SUCCESS | 0 | 5.004s | disposable | off | 0.04130378 |
| mutant-m02-16a651ab7a | 01a153c7-40fc-774d-925f-8cedcbc970ae | SUCCESS | 0 | 4.974s | disposable | off | 0.0416156 |
| mutant-m03-8418362978 | 01a153c7-411f-7248-a267-3ec4000a071e | SUCCESS | 0 | 5.099s | disposable | off | 0.04199517 |
| mutant-m04-9478a965b2 | 01a153c7-409e-72b6-9196-d362514c689c | SUCCESS | 0 | 4.975s | disposable | off | 0.04107448 |
| mutant-m05-7519593a25 | 01a153c7-416a-7562-b5b9-f71b170440b2 | SUCCESS | 0 | 5.033s | disposable | off | 0.04143109999999999 |
| mutant-m06-8181ad8aa2 | 01a153c7-4104-77e8-bbe4-ca06b833c8c2 | SUCCESS | 0 | 4.991s | disposable | off | 0.04134946 |
| mutant-m07-b7d8a4cecb | 01a153c7-4085-731c-947b-25b0025ebbe0 | SUCCESS | 0 | 5.052s | disposable | off | 0.04162266 |
| mutant-m08-e18efbd11c | 01a153c7-410b-74e8-a404-3e5d7de60cf9 | SUCCESS | 0 | 5.024s | disposable | off | 0.04202765 |
| mutant-m09-2afe928861 | 01a153c7-62b3-712d-8a36-b904455549ec | SUCCESS | 0 | 4.967s | disposable | off | 0.04129777 |
| mutant-m10-61c1ef2d2c | 01a153c7-6357-74ce-af19-3e99644767f9 | SUCCESS | 0 | 5.036s | disposable | off | 0.041360839999999996 |
| mutant-m11-2669d3a178 | 01a153c7-637b-7026-b98f-a5d28874b43a | SUCCESS | 0 | 5.005s | disposable | off | 0.04135828999999999 |
| mutant-m12-35004ec740 | 01a153c7-645b-74db-ab6a-7ac59b64d664 | SUCCESS | 0 | 5.036s | disposable | off | 0.041617299999999996 |
| breaker-tests | 01a153c8-7704-7009-a34d-0fe7fbcf3f2b | SUCCESS | 0 | 3.02s | disposable | off | 0.0235513 |

Sandbox operations: 19, total guest duration 78.055s, retained images ['c915ef77-e8e5-4fe4-95e9-74b92806ed05'].

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
