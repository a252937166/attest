# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261019T192714677513Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T19:27:14.677928+00:00, finished 2026-10-19T19:36:22.037202+00:00.

**Accept this patch.** All 29 sealed tests pass on the candidate in a fresh sandbox, and 11 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 29 of 29 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.917, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4). 1 of the tests written after the patch failed as written and were corrected by the arbiter; the correction kept every test method, changed only the failing ones, passes on the candidate and discriminates (1 of 1 corrected test(s) fail on the unmodified base with an authentic result), and the gate was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 2 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; drift audit: score 0.00, widened 0, unsupported claims 1; arbitration (validated corrections re-run their gates): all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 29 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 11 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 18 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, but which side was wrong is a model judgement; the original tests and results are preserved (E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 11 of 29 failed on the unmodified base; 29 of 29 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 1 of 9 failed as written (test_long_leading_zero_component_is_valid); 1 test(s) corrected by the arbiter and validated (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the corrected module passes (OK (9 of 9 methods, each in its own process)) |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `bf16ddd7-3b13-4e74-b6ad-1581378f2557`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.8.0 revision `68e9de49df5b22b8` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision7-repairs-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; a request that was never sent (its connection, proxy tunnel or TLS handshake failed before any byte of it was written) sent again at most 2 times after 2/6 s, each attempt recorded; transport-uncertain failures (the request was written) never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer representing seconds or one or more integer-and-unit components using d, h, m, s, and ms. Components must use distinct units in strictly descending order and may have whitespace around or between them, but not between a number and its unit. Return total seconds as a float, preserve existing valid behavior and tests, and reject malformed strings with ValueError and non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration (also defined in durationkit.parse) | parse_duration(text: str) -> float | Accept str inputs, including str subclasses. After removing surrounding whitespace, accept either an ASCII digit sequence representing seconds, or a sequence of | TypeError: input is not a str; do not coerce other objects to strings.; ValueError: input is empty or contains only whitespace.; ValueError: a number has a sign |

Acceptance criteria:
AC1. 1. All existing tests in tests/ pass unchanged using python -m unittest discover -s tests -t . -v.
AC2. 2. The public import from durationkit import parse_duration remains available with signature parse_duration(text: str) -> float.
AC3. 3. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0, and '00090' returns 90.0.
AC4. 4. Single components return the expected seconds: '2d' → 172800.0, '3h' → 10800.0, '15m' → 900.0, '45s' → 45.0, and '500ms' → 0.5.
AC5. 5. Descending combinations work: '1h30m' → 5400.0, '2d4h' → 187200.0, '1m1s' → 61.0, '1s500ms' → 1.5, and '1d1h1m1s1ms' → approximately 90061.001. Fractional results may be checked with normal floating-point tolerance.
AC6. 6. Units may be skipped: '1d1ms' returns approximately 86400.001, and '1h1s' returns 3601.0.
AC7. 7. Surrounding and inter-component whitespace is accepted: ' 1h 30m ' and '\t1h\n30m\r' both return 5400.0. '1 h', '500 ms', and '1h 30 m' raise ValueError.
AC8. 8. Zero values and leading zeros work for all units: '0s', '0ms', and '0d0h0m0s0ms' return 0.0; '001h030m' returns 5400.0.
AC9. 9. Component values are not restricted to conventional clock ranges: '90m' returns 5400.0 and '1500ms' returns 1.5.
AC10. 10. Every accepted input returns a float, including whole-second and zero results.
AC11. 11. Empty and whitespace-only inputs, including '', '   ', and '\t\n', raise ValueError.
AC12. 12. Signed, fractional, exponential, and separated numeric forms raise ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '.5s', '1e3s', '1_000s', and '1,000s'.
AC13. 13. Unknown or incorrectly cased units and missing numbers raise ValueError, including '1x', '1H', '1MS', 'h', 'ms', and '1hms'.
AC14. 14. Repeated units raise ValueError, including '1h1h', '1ms2ms', and '0s0s'.
AC15. 15. Out-of-order components raise ValueError, including '30m1h', '1ms1s', '1s1d', and '0m0h'.
AC16. 16. Partial matches, mixed bare integers and components, and extraneous text raise ValueError, including '1h30', '1 30m', '1h,30m', 'abc', and '1s500m'.
AC17. 17. Non-decimal numeric-looking characters raise ValueError in bare and component forms, including '①', '①h', 'Ⅳ', 'Ⅳs', '½', and '½h'. Tests must not require either acceptance or rejection of non-ASCII Unicode decimal digits.
AC18. 18. Non-string inputs such as 90, 0.5, None, True, b'90', and [] raise TypeError.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are mutually compatible and can be implemented within durationkit/**. The unchanged tests and public import impose no conflicting behavior; Unicode decimal-digit handling and numeric limits remain explicitly unspecified. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `0b4848072cf5b5bef51a6f742e0a16c3ffb884f719714f106146b2ec1a7c2491`, 29 test methods, sealed at 2026-10-19T19:29:37.458804+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (11 of 29 methods: ERROR 11): 11 of 29 methods failing, 18 passing; operation `01a155a4-0435-709b-a38c-4592cc38e82b`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_all_units_in_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_bare_seconds_cannot_be_mixed_with_components | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_exceeding_clock_ranges | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_descending_component_pairs | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_embedded_numeric_separators_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_inputs_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_exponential_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_extraneous_text_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zero_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_nondecimal_numeric_characters_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_nonstring_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_are_rejected_even_when_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_partial_component_matches_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_public_import_and_signature | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_when_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_str_subclass_is_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_surrounding_and_intercomponent_whitespace | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_whitespace_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_uppercase_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_number_and_unit_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,41 @@
 """Duration parsing."""
+
+import re
+
+
+_BARE_SECONDS = re.compile(r"[0-9]+")
+_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")
+_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_UNIT_ORDER = {"d": 0, "h": 1, "m": 2, "s": 3, "ms": 4}
 
 
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
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if _BARE_SECONDS.fullmatch(stripped):
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
+        value, unit = match.groups()
+        order = _UNIT_ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        total += int(value) * _UNIT_SECONDS[unit]
+        previous_order = order
+        position = match.end()
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

Static tamper scan of the added lines: 2 flagged line(s): dynamic code or decoded payload (33 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| durationkit/parse.py | 6 | dynamic code or decoded payload | _BARE_SECONDS = re.compile(r"[0-9]+") |
| durationkit/parse.py | 7 | dynamic code or decoded payload | _COMPONENT = re.compile(r"([0-9]+)(ms\|[dhms])") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (29 of 29 methods, each in its own process). Operation `01a155a7-d303-7309-9392-5ae6e2acceae`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a155a7-fd44-71e8-82f3-59edeae317b8`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.917 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) on the corrected module (1 test(s) corrected, validated: 1 of 1 corrected test(s) fail on the unmodified base with an authentic result); original failures kept in E3 |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-5c87340a38 | durationkit/parse.py | 8 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-188e-7459-8f98-af3a297c4d09 |
| m02-6b6dd4e7a5 | durationkit/parse.py | 8 | 3600 -> 3601 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-1860-73bf-9bd1-48a2eba27cd1 |
| m03-3000861c70 | durationkit/parse.py | 8 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-18c4-7016-8214-dc4e82f77533 |
| m04-833918a7c5 | durationkit/parse.py | 9 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_descending_component_pairs, test_sealed.ParseDurationAcceptanceTests.test_ | 01a155a8-1882-7002-89e7-5ad553ed2e69 |
| m05-a3a850b6dd | durationkit/parse.py | 9 | 3 -> 4 | killed | test_sealed.ParseDurationAcceptanceTests.test_descending_component_pairs, test_sealed.ParseDurationAcceptanceTests.test_ | 01a155a8-1840-735b-9c1d-5a14aa526698 |
| m06-155470d593 | durationkit/parse.py | 9 | 4 -> 5 | survived |  | 01a155a8-1886-7515-a0be-a3b7e2e2935f |
| m07-3591ec2f61 | durationkit/parse.py | 24 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-1862-7024-9696-c8d80ad8d896 |
| m08-2d85c37d72 | durationkit/parse.py | 26 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-1826-779a-bbd8-974eb734b16b |
| m09-6e9da03485 | durationkit/parse.py | 29 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_number_and_unit_is_rejected, test_sealed.ParseDurationA | 01a155a8-3e6b-70a5-9860-8e24abcb586a |
| m10-f3624dbee0 | durationkit/parse.py | 33 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_when_zero | 01a155a8-3f6f-7220-821b-b777a0798e4e |
| m11-9e0c68e445 | durationkit/parse.py | 35 | Mult -> Div | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-3fdf-7511-a078-9d25f65847c5 |
| m12-bb7e240ad4 | durationkit/parse.py | 38 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_descendin | 01a155a8-4197-73f2-9141-394a04ccde64 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `85594a3b0d6f6388e1c2bc8ed0e1579d8dc294e381f217345fa8393e23fbf409`): FAILED (1 of 9 methods: ERROR 1); binding FAILED; operation `01a155a9-0499-737d-ac7d-3dc0eabdc133`. Notes: Targets the Python integer digit limit, complete parsing, unit ordering, ms boundaries, and Unicode character edges.

| Failing adversarial test | Outcome |
| --- | --- |
| test_long_leading_zero_component_is_valid | ERROR |
Corrected adversarial module (E6): `arbitration/adversarial_corrected.py` sha256 `c4706ee36bc90a86c6a8dcd885fcbbca3614c5ad474bb645fbdd5cd3608cab4b`; corrected tests test_long_leading_zero_component_is_valid; on the candidate OK (9 of 9 methods, each in its own process); validated: 1 of 1 corrected test(s) fail on the unmodified base with an authentic result; operation `01a155a9-f588-77c4-91e3-bc1972bf6d93`. The adversarial gate was re-run on it.
Adversarial authoring: 1 attempt(s).

### Counterexamples
- E3 `test_long_leading_zero_component_is_valid`: ERROR; ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4302 digits; use sys.set_int_max_str_digits() to increase the limit; arbiter: Defective test, by the arbiter; contract basis: Leading zeros are valid, but defining new guarantees beyond Python numeric-conversion limits is explicitly out of scope.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated task: `_COMPONENT` recognizes all five units, `order <= previous_order` rejects repeated or unordered units, and `.isspace()` permits inter-component whitespace while preserving the signature and type checks. Existing tests remain unchanged, and observed output reports all 6 existing tests and 70 additional cases passing.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: “The write result truncated the parser” is unsupported: the observed write result only reports “wrote durationkit/parse.py (1278 bytes)” and shows no truncation.

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (1 of 1 corrected test(s) fail on the unmodified base with an authentic result); the affected gate(s) are re-run on the corrected modules (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates Gates re-run on validated corrections: adversarial_tests (tests test_long_leading_zero_component_is_valid; 1 of 1 corrected test(s) fail on the unmodified base with an authentic result).

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_long_leading_zero_component_is_valid | test_defect | The component contains 4302 digits, exceeding Python 3.12's default integer-string conversion limit. The contract does not require accepting | Leading zeros are valid, but defining new guarantees beyond Python numeric-conversion limits is explicitly out of scope. |

- `adversarial` corrected re-run: candidate OK (9 of 9 methods, each in its own process); base FAILED (4 of 9 methods: ERROR 4); validated=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10756 | 1498 | 0 | - | 52.3s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13117 | 89 | 0 | - | 18.8s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11169 | 3542 | 0 | - | 53.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11053 | 104 | 0 | - | 39.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11258 | 582 | 0 | - | 21.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11504 | 145 | 0 | - | 20.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11755 | 147 | 7168 | - | 16.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 24524 | 791 | 12032 | - | 55.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12911 | 160 | 0 | - | 18.0s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11508 | 1705 | 0 | - | 38.4s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12167 | 263 | 0 | - | 21.9s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 13603 | 1106 | 0 | - | 32.9s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 155325/10132/19200; Inference USD: n/a (development gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a155a2-00f2-745d-8237-999d37a87916 | SUCCESS | 0 | 0.798s | retained | off | 0.0029482199999999997 |
| red-1 | 01a155a4-0435-709b-a38c-4592cc38e82b | SUCCESS | 0 | 6.159s | disposable | off | 0.05254429 |
| impl-tests-3 | 01a155a5-63a5-7475-9c39-5f7b9f8bb197 | SUCCESS | 0 | 0.8s | disposable | off | 0.0028349 |
| impl-python-5 | 01a155a7-13dd-76fc-8925-fdf254c5ad9f | SUCCESS | 0 | 0.657s | disposable | off | 0.0016315400000000001 |
| verify | 01a155a7-d303-7309-9392-5ae6e2acceae | SUCCESS | 0 | 6.107s | disposable | off | 0.05255013 |
| existing | 01a155a7-fd44-71e8-82f3-59edeae317b8 | SUCCESS | 0 | 2.156s | disposable | off | 0.0152893 |
| mutant-m01-5c87340a38 | 01a155a8-188e-7459-8f98-af3a297c4d09 | SUCCESS | 0 | 5.82s | disposable | off | 0.049599529999999996 |
| mutant-m03-3000861c70 | 01a155a8-18c4-7016-8214-dc4e82f77533 | SUCCESS | 0 | 5.829s | disposable | off | 0.04928213 |
| mutant-m02-6b6dd4e7a5 | 01a155a8-1860-73bf-9bd1-48a2eba27cd1 | SUCCESS | 0 | 5.864s | disposable | off | 0.0494873 |
| mutant-m05-a3a850b6dd | 01a155a8-1840-735b-9c1d-5a14aa526698 | SUCCESS | 0 | 5.762s | disposable | off | 0.04904706 |
| mutant-m04-833918a7c5 | 01a155a8-1882-7002-89e7-5ad553ed2e69 | SUCCESS | 0 | 5.861s | disposable | off | 0.04959341 |
| mutant-m06-155470d593 | 01a155a8-1886-7515-a0be-a3b7e2e2935f | SUCCESS | 0 | 5.885s | disposable | off | 0.04974124 |
| mutant-m07-3591ec2f61 | 01a155a8-1862-7024-9696-c8d80ad8d896 | SUCCESS | 0 | 5.883s | disposable | off | 0.04991076 |
| mutant-m08-2d85c37d72 | 01a155a8-1826-779a-bbd8-974eb734b16b | SUCCESS | 0 | 5.882s | disposable | off | 0.04933274 |
| mutant-m09-6e9da03485 | 01a155a8-3e6b-70a5-9860-8e24abcb586a | SUCCESS | 0 | 5.909s | disposable | off | 0.050038969999999995 |
| mutant-m10-f3624dbee0 | 01a155a8-3f6f-7220-821b-b777a0798e4e | SUCCESS | 0 | 5.872s | disposable | off | 0.04971099 |
| mutant-m11-9e0c68e445 | 01a155a8-3fdf-7511-a078-9d25f65847c5 | SUCCESS | 0 | 5.868s | disposable | off | 0.049589760000000004 |
| mutant-m12-bb7e240ad4 | 01a155a8-4197-73f2-9141-394a04ccde64 | SUCCESS | 0 | 5.859s | disposable | off | 0.05000931 |
| breaker-tests | 01a155a9-0499-737d-ac7d-3dc0eabdc133 | SUCCESS | 0 | 2.723s | disposable | off | 0.020287259999999998 |
| arbitrate-adversarial-candidate | 01a155a9-f588-77c4-91e3-bc1972bf6d93 | SUCCESS | 0 | 2.745s | disposable | off | 0.020363469999999998 |
| arbitrate-adversarial-base | 01a155aa-0f5d-7019-beb8-7d3328e23a7c | SUCCESS | 0 | 2.714s | disposable | off | 0.02034594 |

Sandbox operations: 21, total guest duration 95.153s, retained images ['bf16ddd7-3b13-4e74-b6ad-1581378f2557'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

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
