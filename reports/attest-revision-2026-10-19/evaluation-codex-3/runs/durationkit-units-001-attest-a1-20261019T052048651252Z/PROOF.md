# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-attest-a1-20261019T052048651252Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:20:48.652611+00:00, finished 2026-10-19T05:31:35.077632+00:00.

**Accept this patch.** All 21 sealed tests pass on the candidate in a fresh sandbox, and 10 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 21 of 21 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.917, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 21 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 10 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 11 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 12 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 11 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 10 of 21 failed on the unmodified base; 21 of 21 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 12 of 12 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d9451070-3022-4754-9686-049a0d381d66`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer number of seconds or one or more integer-and-unit components using d, h, m, s and ms. Components must use unique units in strictly descending order, with optional whitespace around the input and between components but none inside a component. Preserve the public import, float return type, existing plain-seconds behavior and existing tests. Reject malformed strings with ValueError and non-string inputs with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Available through both durationkit and durationkit.parse. Accept str instances. Ignore surrounding whitespace using Python string whitespace semantics. The rema | TypeError: text is not a str instance.; ValueError: input is empty or contains only whitespace.; ValueError: a number has a sign, fractional part, exponent, sep |

Acceptance criteria:
AC1. 1. Preserve the public import `from durationkit import parse_duration` and the signature `parse_duration(text: str) -> float`.
AC2. 2. All existing tests in tests/ pass unchanged.
AC3. 3. Plain integer seconds remain valid: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0 and '0007' returns 7.0.
AC4. 4. Single units convert correctly: '2d' returns 172800.0, '3h' returns 10800.0, '15m' returns 900.0, '45s' returns 45.0 and '500ms' returns 0.5.
AC5. 5. Combined units convert correctly: '1h30m' returns 5400.0, '2d4h' returns 187200.0, '1m1s' returns 61.0, '1s500ms' returns 1.5 and '1d1h1m1s1ms' returns approximately 90061.001. Compare fractional totals with a floating-point tolerance.
AC6. 6. Units may be skipped: '1d1s' returns 86401.0 and '1h1ms' returns approximately 3600.001.
AC7. 7. Whitespace around the input and between components is accepted, including spaces, tabs and newlines: ' 1h 30m ' and '\t1h\n30m\t' both return 5400.0. Whitespace inside a component is rejected: '1 h', '1\tm' and '1m s' raise ValueError.
AC8. 8. Zero-valued components and leading zeros are valid: '0s', '0ms' and '0d0h0m0s0ms' return 0.0; '01h030m' returns 5400.0.
AC9. 9. Component quantities have no clock-field limits: '90m' returns 5400.0 and '1500ms' returns 1.5.
AC10. 10. Every accepted input returns a float, including integer-valued totals and zero.
AC11. 11. Empty and whitespace-only strings, including '', '   ' and '\t\n', raise ValueError.
AC12. 12. Signed, fractional and malformed numeric forms raise ValueError: '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '.5s', '1e3s' and '1_000s'.
AC13. 13. Unknown or incorrectly cased units and missing numbers raise ValueError: '1x', '1H', '1MS', 'h', 'ms' and 'abc'.
AC14. 14. Repeated units raise ValueError, including '1h1h', '1ms2ms' and '0s0s'.
AC15. 15. Out-of-order units raise ValueError, including '30m1h', '1ms1s' and '0s0m'.
AC16. 16. Mixed bare and unit-bearing forms and other malformed text raise ValueError, including '1h30', '1 30m', '1 2', '1h,30m', '1h30m!' and '1mss'.
AC17. 17. Non-decimal numeric characters raise ValueError in both bare and unit-bearing forms, including 'Ⅳ', 'Ⅳh', '½', '½h', '①', '①h', '²' and '²s'. Tests must not require acceptance or rejection of non-ASCII Unicode decimal digits.
AC18. 18. Non-string inputs, including 90, 1.5, None, True, b'90' and [], raise TypeError.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing durationkit/parse.py alone while preserving the public export, signature, float return type and existing tests. No requirements demand incompatible results, and no fixed code prevents the specified parsing behavior. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `0c3441bfa841233eea4779871096a4b29b4451398ff1006f322f097464e01470`, 21 test methods, sealed at 2026-10-19T05:25:02.300348+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (10 of 21 methods: ERROR 10): 10 of 21 methods failing, 11 passing; operation `01a1529e-c778-71d6-a772-20bef1d873e9`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptance.test_all_accepted_forms_return_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_combined_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_component_quantities_have_no_clock_limits | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_empty_and_whitespace_only_strings_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_leading_zeros_in_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_mixed_bare_numbers_and_trailing_text_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_nondecimal_numeric_characters_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_nonstring_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_out_of_order_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_parse_module_public_import | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_public_signature | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_python_unicode_whitespace | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_repeated_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_signed_fractional_and_malformed_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_single_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_skipped_units | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_unknown_uppercase_and_numberless_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_whitespace_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_whitespace_inside_component_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptance.test_zero_valued_components | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,39 @@
 """Duration parsing."""
+
+import re
+
+
+_COMPONENT = re.compile(r"([0-9]+)(ms|[dhms])")
+_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_UNIT_ORDER = {unit: index for index, unit in enumerate(_UNIT_SECONDS)}
 
 
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
+        quantity, unit = match.groups()
+        order = _UNIT_ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        total += int(quantity) * _UNIT_SECONDS[unit]
+        previous_order = order
+        position = match.end()
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (31 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| durationkit/parse.py | 6 | dynamic code or decoded payload | _COMPONENT = re.compile(r"([0-9]+)(ms\|[dhms])") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (21 of 21 methods, each in its own process). Operation `01a152a2-821a-763c-918b-462d42e893bc`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a152a2-a434-7393-9433-fef835d9f8a6`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.917 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (12 of 12 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-f11a4c2442 | durationkit/parse.py | 7 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptance.test_single_units, test_sealed.ParseDurationAcceptance.test_combined_units, test_sea | 01a152a2-bc0c-7388-9f4c-57da93cd08dd |
| m02-132239e9b8 | durationkit/parse.py | 7 | 3600 -> 3601 | killed | test_sealed.ParseDurationAcceptance.test_parse_module_public_import, test_sealed.ParseDurationAcceptance.test_single_uni | 01a152a2-bc3b-76ac-adcb-2c10b3785a18 |
| m03-8b8bc89fe1 | durationkit/parse.py | 7 | 60 -> 61 | killed | test_sealed.ParseDurationAcceptance.test_single_units, test_sealed.ParseDurationAcceptance.test_combined_units, test_sea | 01a152a2-bc38-70b4-a65b-d38228701c9a |
| m04-d42ff28ace | durationkit/parse.py | 17 | remove `not` | killed | test_sealed.ParseDurationAcceptance.test_public_signature, test_sealed.ParseDurationAcceptance.test_parse_module_public_ | 01a152a2-bc20-71e4-bd96-4b029da784dc |
| m05-407a92cb00 | durationkit/parse.py | 23 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptance.test_parse_module_public_import, test_sealed.ParseDurationAcceptance.test_single_uni | 01a152a2-bc7b-779d-9aa8-0e361958b78d |
| m06-28ea963660 | durationkit/parse.py | 24 | 1 -> 2 | survived |  | 01a152a2-bc24-77c1-9308-185a098e69d3 |
| m07-ee5777597d | durationkit/parse.py | 27 | Is -> IsNot | killed | test_sealed.ParseDurationAcceptance.test_parse_module_public_import, test_sealed.ParseDurationAcceptance.test_single_uni | 01a152a2-bc22-74ae-b6f3-1d3ac4fc9be0 |
| m08-c7e7ee08cf | durationkit/parse.py | 28 | raise -> pass | killed | test_sealed.ParseDurationAcceptance.test_whitespace_inside_component_is_rejected, test_sealed.ParseDurationAcceptance.te | 01a152a2-bc3a-766a-8422-4975fd8c697b |
| m09-c49f10b1b1 | durationkit/parse.py | 31 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptance.test_repeated_units_are_rejected | 01a152a2-e01c-7394-8d69-97d705206dc7 |
| m10-ae0ff3fc0b | durationkit/parse.py | 33 | Mult -> Div | killed | test_sealed.ParseDurationAcceptance.test_parse_module_public_import, test_sealed.ParseDurationAcceptance.test_single_uni | 01a152a2-e082-7385-9af8-3ddf636fd7d1 |
| m11-e8f1d1a761 | durationkit/parse.py | 36 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptance.test_parse_module_public_import, test_sealed.ParseDurationAcceptance.test_single_uni | 01a152a2-e100-7115-9731-f38abaa6048f |
| m12-3c0db3fb10 | durationkit/parse.py | 36 | And -> Or | killed | test_sealed.ParseDurationAcceptance.test_parse_module_public_import, test_sealed.ParseDurationAcceptance.test_single_uni | 01a152a2-e112-7464-a68b-a62b9d977911 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `94e5a51689e3d3c58b51a911d26b1ca39f9fe527046ea59067afb60a361667f2`): OK (12 of 12 methods, each in its own process); binding ok; operation `01a152a3-cb75-71d7-888c-0f3713317622`. Notes: Targets skipped unit pairs, ms ordering, Python whitespace, zero valued ordering violations, complete consumption, and less common nondecimal numerics.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated task: `([0-9]+)(ms|[dhms])` parses exact components, `order <= previous_order` rejects repeats and incorrect ordering, and `isspace()` permits whitespace between components while the loop enforces full consumption. The signature, float results, and existing test files are preserved; observed output supports all 6 existing tests and 71 additional input checks passing.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10754 | 1471 | 0 | - | 92.1s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12025 | 115 | 0 | - | 37.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11147 | 2925 | 7168 | - | 104.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10981 | 119 | 7168 | - | 20.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11193 | 737 | 7168 | - | 109.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11419 | 98 | 7168 | - | 28.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11665 | 857 | 7168 | - | 37.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12477 | 348 | 7168 | - | 29.5s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11350 | 1856 | 7040 | - | 49.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12053 | 182 | 0 | - | 66.7s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 115064/8708/50048; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1529b-105f-721d-b237-93d735077bb7 | SUCCESS | 0 | 0.787s | retained | off | 0.00284308 |
| red-1 | 01a1529e-c778-71d6-a772-20bef1d873e9 | SUCCESS | 0 | 5.037s | disposable | off | 0.04253109000000001 |
| impl-tests-3 | 01a152a1-566a-73ea-a1fd-3bc7d89b7ca0 | SUCCESS | 0 | 0.802s | disposable | off | 0.00286221 |
| impl-python-4 | 01a152a2-01be-771e-8b61-4de700b9c2ec | SUCCESS | 0 | 0.615s | disposable | off | 0.00161209 |
| verify | 01a152a2-821a-763c-918b-462d42e893bc | SUCCESS | 0 | 5.038s | disposable | off | 0.042858700000000007 |
| existing | 01a152a2-a434-7393-9433-fef835d9f8a6 | SUCCESS | 0 | 2.128s | disposable | off | 0.01527492 |
| mutant-m01-f11a4c2442 | 01a152a2-bc0c-7388-9f4c-57da93cd08dd | SUCCESS | 0 | 4.664s | disposable | off | 0.039097610000000005 |
| mutant-m02-132239e9b8 | 01a152a2-bc3b-76ac-adcb-2c10b3785a18 | SUCCESS | 0 | 4.705s | disposable | off | 0.03920044 |
| mutant-m03-8b8bc89fe1 | 01a152a2-bc38-70b4-a65b-d38228701c9a | SUCCESS | 0 | 4.746s | disposable | off | 0.03923604000000001 |
| mutant-m05-407a92cb00 | 01a152a2-bc7b-779d-9aa8-0e361958b78d | SUCCESS | 0 | 4.803s | disposable | off | 0.03978979 |
| mutant-m04-d42ff28ace | 01a152a2-bc20-71e4-bd96-4b029da784dc | SUCCESS | 0 | 4.707s | disposable | off | 0.039102420000000006 |
| mutant-m06-28ea963660 | 01a152a2-bc24-77c1-9308-185a098e69d3 | SUCCESS | 0 | 4.747s | disposable | off | 0.039566199999999996 |
| mutant-m07-ee5777597d | 01a152a2-bc22-74ae-b6f3-1d3ac4fc9be0 | SUCCESS | 0 | 4.782s | disposable | off | 0.03932162 |
| mutant-m08-c7e7ee08cf | 01a152a2-bc3a-766a-8422-4975fd8c697b | SUCCESS | 0 | 4.802s | disposable | off | 0.0398284 |
| mutant-m09-c49f10b1b1 | 01a152a2-e01c-7394-8d69-97d705206dc7 | SUCCESS | 0 | 4.658s | disposable | off | 0.04012873 |
| mutant-m10-ae0ff3fc0b | 01a152a2-e082-7385-9af8-3ddf636fd7d1 | SUCCESS | 0 | 4.769s | disposable | off | 0.0394054 |
| mutant-m11-e8f1d1a761 | 01a152a2-e100-7115-9731-f38abaa6048f | SUCCESS | 0 | 4.781s | disposable | off | 0.03922035000000001 |
| mutant-m12-3c0db3fb10 | 01a152a2-e112-7464-a68b-a62b9d977911 | SUCCESS | 0 | 4.783s | disposable | off | 0.0392527 |
| breaker-tests | 01a152a3-cb75-71d7-888c-0f3713317622 | SUCCESS | 0 | 3.143s | disposable | off | 0.024954940000000002 |

Sandbox operations: 19, total guest duration 74.497s, retained images ['d9451070-3022-4754-9686-049a0d381d66'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception raised in the code under test is never overridden (only a test-internal crash or a timeout may be corrected). The classification itself remains a model judgement.
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
