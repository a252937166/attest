# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261016T194553Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:45:53.576472+00:00, finished 2026-10-16T19:52:26.257034+00:00.

Reasons: model-written adversarial tests could not be produced: adversarial test authoring failed: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key; rerun the breaker stage or review manually; drift audit unavailable: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `3290aefb-d3d9-46b8-9e7b-4a713e2d79c2`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either plain non-negative integer seconds or a sequence of integer-and-unit components using d, h, m, s and ms. Require strictly descending unit order without repetition, permit surrounding whitespace and whitespace between complete components, and return the total seconds as a float. Preserve the public import, existing valid plain-integer behavior, input-type checking and all existing tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also remains available from durationkit.parse. Accept str instances, including subclasses. Strip surrounding whitespace using Python string whitespace semantics | TypeError: text is not an instance of str, including integers, floats, bytes, booleans and None.; ValueError: text is empty or contains only whitespace.; ValueE |

Acceptance criteria:
1. 1. The existing tests under tests/ pass unchanged with python -m unittest discover -s tests -t . -v.
2. 2. Both from durationkit import parse_duration and from durationkit.parse import parse_duration remain valid and expose the specified behavior.
3. 3. Plain seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '7' returns 7.0 and '0' returns 0.0.
4. 4. Single components produce: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0 and '500ms' -> 0.5.
5. 5. Combined components produce: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5 and '1d1h1m1s1ms' -> 90061.001. Use floating-point tolerance when checking fractional totals.
6. 6. Skipped units are valid: '1d1s' returns 86401.0 and '1h1ms' returns approximately 3600.001.
7. 7. Whitespace around input and between components is accepted: ' 1h 30m ' and '\t1h\n30m\r' each return 5400.0. Whitespace inside a component is rejected: '1 h' and '1m 500 ms' raise ValueError.
8. 8. Zero values and leading zeros are accepted: '0s', '0ms' and '0d0h0m0s0ms' return 0.0; '00090' returns 90.0 and '01h030m' returns 5400.0.
9. 9. Component magnitudes are not restricted by the next larger unit: '90m' returns 5400.0, '1000ms' returns 1.0 and '1s1500ms' returns 2.5.
10. 10. Unicode decimal digits remain supported: '١٢' returns 12.0 and '١h' returns 3600.0. Non-decimal numeric characters such as '²' raise ValueError.
11. 11. Empty and whitespace-only strings raise ValueError, including '', '   ' and '\t\n'.
12. 12. Invalid numeric forms raise ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '.5s' and '1e3s'.
13. 13. Unknown units and malformed tokens raise ValueError, including '1x', '1H', 'h', 'ms', 'abc', '1h30', '1 30m', '1h,30m', '1mss' and '1h!'.
14. 14. Repeated units raise ValueError, including '1h1h', '1ms2ms' and '0s0s'. Out-of-order units raise ValueError, including '30m1h', '1ms1s' and '0s0m'.
15. 15. Non-string inputs raise TypeError, including 90, 1.5, None, True and b'90'.
16. 16. Every accepted input returns a float, including plain integers, zero, whole-second unit totals and fractional-second totals.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `47100720907acf4ebb61912188bb41c6da2496ee65716a715d97a582f75f2fc3`, 26 test methods, sealed at 2026-10-16T19:48:17.662876+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 26 methods: ERROR 13): 13 of 26 methods failing, 13 passing; operation `01a14642-0839-720f-86e3-c47ddef45dcb`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_fractional_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_whole_second_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_are_unrestricted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_and_exponential_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_incomplete_or_mixed_components_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_malformed_text_and_punctuation_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_nondecimal_numeric_character_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_string_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_surrounding_whitespace | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_decimal_digits | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_or_uppercase_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_complete_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_components_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_components | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,47 @@
 """Duration parsing."""
 
 
+_SECONDS_PER_UNIT = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_UNIT_ORDER = {"d": 0, "h": 1, "m": 2, "s": 3, "ms": 4}
+
+
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse plain seconds or descending duration components as seconds."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if all(character.isdecimal() for character in stripped):
+        return float(stripped)
+
+    total = 0.0
+    position = 0
+    previous_order = -1
+    while position < len(stripped):
+        number_start = position
+        while position < len(stripped) and stripped[position].isdecimal():
+            position += 1
+        if position == number_start:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        number = stripped[number_start:position]
+        if stripped.startswith("ms", position):
+            unit = "ms"
+        elif position < len(stripped) and stripped[position] in "dhms":
+            unit = stripped[position]
+        else:
+            raise ValueError(f"unsupported duration: {text!r}")
+        position += len(unit)
+
+        order = _UNIT_ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        previous_order = order
+        total += float(number) * _SECONDS_PER_UNIT[unit]
+
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return total
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (39 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (bound to the sealed suite)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (26 of 26 methods, each in its own process). Operation `01a14645-2272-7433-9757-444ba1df7f03`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a14645-4d69-72c8-9ec6-69c20a611c1d`, bound through the supervisor: 1 module(s), binding ok.

Held-out suite: none configured.

## 6. Gates
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Result | Evidence | Detail |
| --- | --- | --- | --- |
| existing_suite | pass | bound | OK (6 of 6 methods, each in its own process) |
| sealed_binding | pass | bound | all checks pass |
| mutation | pass | bound | score 0.917 on 12 mutants |
| adversarial_tests | FAIL | bound | adversarial test authoring failed: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key |
| drift_audit | FAIL | model | audit call failed: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-3681ef0886 | durationkit/parse.py | 4 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a14645-710a-75ed-98fc-1e210af93a5a |
| m02-d5f2e6b089 | durationkit/parse.py | 4 | 60 -> 61 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a14645-6cf8-7388-af01-221b76f639f5 |
| m03-40a5b12b4c | durationkit/parse.py | 5 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_whole_second_components, test_sealed.ParseDurationAcceptanceTests | 01a14645-6ce4-7247-9022-0c83e259a150 |
| m04-ad9220fb30 | durationkit/parse.py | 5 | 3 -> 4 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_fractional_components, test_sealed.ParseDurationAcceptanceTests.t | 01a14645-6ccc-7184-baf8-5c27094e2047 |
| m05-3ae54ffb59 | durationkit/parse.py | 14 | remove `not` | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_pl | 01a14645-b0d3-70b4-b166-3ef44c6640cf |
| m06-e1a1ac7428 | durationkit/parse.py | 21 | 1 -> 2 | survived |  | 01a14645-6cf5-73de-b225-f40499885bfe |
| m07-34131e3868 | durationkit/parse.py | 24 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_si | 01a14645-6d2d-7543-b47f-9c4988e57e60 |
| m08-f5f00ca008 | durationkit/parse.py | 26 | Eq -> NotEq | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_si | 01a14645-6d06-76c0-bdb2-a5bd2f27066c |
| m09-a54fd82f2a | durationkit/parse.py | 32 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_incomplete_or_mixed_components_are_rejected | 01a14645-8f4f-720d-a956-68749fdcba02 |
| m10-0ef40c7f67 | durationkit/parse.py | 35 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_whitespace_inside_components_is_rejected, test_sealed.ParseDurationAccepta | 01a14645-91d3-70da-becc-1b064ac76c99 |
| m11-f09136f236 | durationkit/parse.py | 40 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected, test_sealed.ParseDurationAcceptanceTests.test | 01a14645-920a-7516-8ebf-659a576e2a10 |
| m12-089e6d5c4a | durationkit/parse.py | 44 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_both_public_imports_work, test_sealed.ParseDurationAcceptanceTests.test_si | 01a14645-ac22-7440-86b3-6c1c1e3be72e |

Model-written adversarial tests: unusable (adversarial test authoring failed: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key); the gate fails.



## 8. Drift audit
Drift audit unavailable: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key



## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10646 | 1522 | 0 | - | 81.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10894 | 2152 | 0 | - | 46.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10758 | 95 | 7168 | - | 26.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10954 | 700 | 0 | - | 36.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11176 | 161 | 7168 | - | 25.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11420 | 705 | 7168 | - | 25.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12064 | 311 | 7168 | - | 20.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12529 | 298 | 7168 | - | 52.7s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | - | - | - | - | 3.3s | error |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | - | - | - | - | 4.5s | error |

Model calls: 10 (2 failed, 0 malformed); tokens in/out/cached 90441/5944/35840; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1463f-fb44-703c-8091-22780c136ab7 | SUCCESS | 0 | 0.74s | retained | off | 0.00276905 |
| red-1 | 01a14642-0839-720f-86e3-c47ddef45dcb | SUCCESS | 0 | 5.519s | disposable | off | 0.04754119 |
| impl-tests-3 | 01a14643-7f06-7218-8756-48adddfa9a82 | SUCCESS | 0 | 0.744s | disposable | off | 0.0027699499999999998 |
| impl-python-4 | 01a14643-f679-7424-998a-e09cc88c2aa7 | SUCCESS | 0 | 0.582s | disposable | off | 0.00113554 |
| verify | 01a14645-2272-7433-9757-444ba1df7f03 | SUCCESS | 0 | 5.625s | disposable | off | 0.04818036 |
| existing | 01a14645-4d69-72c8-9ec6-69c20a611c1d | SUCCESS | 0 | 2.049s | disposable | off | 0.01507835 |
| mutant-m01-3681ef0886 | 01a14645-710a-75ed-98fc-1e210af93a5a | SUCCESS | 0 | 5.173s | disposable | off | 0.04471858 |
| mutant-m02-d5f2e6b089 | 01a14645-6cf8-7388-af01-221b76f639f5 | SUCCESS | 0 | 5.275s | disposable | off | 0.044277079999999996 |
| mutant-m03-40a5b12b4c | 01a14645-6ce4-7247-9022-0c83e259a150 | SUCCESS | 0 | 5.33s | disposable | off | 0.044606770000000004 |
| mutant-m04-ad9220fb30 | 01a14645-6ccc-7184-baf8-5c27094e2047 | SUCCESS | 0 | 5.208s | disposable | off | 0.04466196 |
| mutant-m05-3ae54ffb59 | 01a14645-b0d3-70b4-b166-3ef44c6640cf | SUCCESS | 0 | 5.145s | disposable | off | 0.0441608 |
| mutant-m06-e1a1ac7428 | 01a14645-6cf5-73de-b225-f40499885bfe | SUCCESS | 0 | 5.275s | disposable | off | 0.04472023 |
| mutant-m08-f5f00ca008 | 01a14645-6d06-76c0-bdb2-a5bd2f27066c | SUCCESS | 0 | 5.198s | disposable | off | 0.044444170000000005 |
| mutant-m07-34131e3868 | 01a14645-6d2d-7543-b47f-9c4988e57e60 | SUCCESS | 0 | 5.304s | disposable | off | 0.04454703 |
| mutant-m09-a54fd82f2a | 01a14645-8f4f-720d-a956-68749fdcba02 | SUCCESS | 0 | 5.23s | disposable | off | 0.044427879999999996 |
| mutant-m10-0ef40c7f67 | 01a14645-91d3-70da-becc-1b064ac76c99 | SUCCESS | 0 | 5.251s | disposable | off | 0.04477793 |
| mutant-m11-f09136f236 | 01a14645-920a-7516-8ebf-659a576e2a10 | SUCCESS | 0 | 5.231s | disposable | off | 0.04457494 |
| mutant-m12-089e6d5c4a | 01a14645-ac22-7440-86b3-6c1c1e3be72e | SUCCESS | 0 | 5.149s | disposable | off | 0.04428116 |

Sandbox operations: 18, total guest duration 78.028s, retained images ['3290aefb-d3d9-46b8-9e7b-4a713e2d79c2'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
