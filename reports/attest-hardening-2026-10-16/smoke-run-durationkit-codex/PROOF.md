# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261015T170925Z` · profile `hardening-smoke` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T17:09:25.556555+00:00, finished 2026-10-15T17:16:12.645819+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `60bf5f96-a8a2-4b21-a45d-2be0b1bf49eb`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either plain non-negative integer seconds or one or more integer-and-unit components using d, h, m, s and ms, returning total seconds as a float. Require strictly descending unit order with no duplicates, allow whitespace around the input and between complete components, reject malformed input with ValueError, preserve TypeError for non-string input, and keep all existing tests unchanged and passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Preserve the public import from durationkit and the implementation entry point durationkit.parse.parse_duration. After stripping surrounding whitespace, accept  | TypeError: text is not an instance of str, including numbers, None, bytes and containers.; ValueError: input is empty or contains only whitespace.; ValueError:  |

Acceptance criteria:
1. 1. All existing tests in tests/ pass without modification using python -m unittest discover -s tests -t . -v.
2. 2. The public import from durationkit import parse_duration remains valid; parse_duration('90') returns 90.0, '  42 ' returns 42.0, and '0' returns 0.0.
3. 3. Single components return the expected seconds: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0 and '500ms' -> 0.5.
4. 4. Combined components return the expected seconds: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5 and '1d1h1m1s1ms' -> 90061.001, allowing ordinary floating-point rounding.
5. 5. Units may be skipped: '1d1ms' returns 86400.001 and '1h1s' returns 3601.0.
6. 6. Whitespace around the input and between complete components is accepted: ' 1h 30m ' and '\t1h\n30m\r' both return 5400.0. '1 h', '1\tm' and '1m s' raise ValueError.
7. 7. Leading zeros, zero values and values exceeding clock ranges are accepted: '00090' -> 90.0, '01h030m' -> 5400.0, '0s' -> 0.0, '0d0h0m0s0ms' -> 0.0, '90m' -> 5400.0 and '1500ms' -> 1.5.
8. 8. Unicode decimal digits remain accepted: '９０' returns 90.0 and '１h３０m' returns 5400.0. '²' and '²s' raise ValueError.
9. 9. Empty and whitespace-only inputs, including '', '   ' and '\t\n', raise ValueError.
10. 10. Invalid number syntax raises ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '.5s', '1e3s' and '1_000s'.
11. 11. Unknown units, uppercase units and units without numbers raise ValueError, including '1x', '1H', '1MS', 'h', 'ms' and '1hms'.
12. 12. Repeated units raise ValueError, including '1h1h', '1ms2ms' and '0s0s'. Out-of-order components raise ValueError, including '30m1h', '1ms1s', '1s1m' and '0s0h'.
13. 13. Mixed bare integers and components or partially valid text raise ValueError, including '1h30', '90 1s', '1 2', '1h,30m', 'abc', 'abc1h' and '1h!'.
14. 14. Non-string inputs, including 90, 0.5, None, True, b'90', [] and {}, raise TypeError.
15. 15. Every accepted input returns a float, including plain integers, zero durations, whole-second component totals and millisecond totals. Exception message wording is not prescribed.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `3b8fc6a23476b9e64fe1d9b8cf598820db9e2568b116f9db1f0a83cd5fc6e135`, 21 test methods, sealed at 2026-10-15T17:11:39.077591+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 21 methods: ERROR 9): 9 of 21 methods failing, 12 passing; operation `01a1408c-3b94-765c-b306-ffb6742e598b`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_bare_seconds_cannot_be_mixed_with_components | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_can_exceed_clock_ranges | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_components_out_of_order_are_rejected_even_for_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_inputs_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_invalid_number_syntax_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_nondecimal_numeric_characters_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_partially_valid_or_malformed_text_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_for_zero | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_decimal_digits | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_may_be_skipped | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_preceding_integers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_or_uppercase_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_complete_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_number_and_unit_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_valued_components | ERROR (1 ev) | ok (1 ev) |

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
+_NUMBER = re.compile(r"\d+")
+_COMPONENT = re.compile(r"(\d+)(ms|[dhms])")
+_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
+_UNIT_ORDER = {"d": 0, "h": 1, "m": 2, "s": 3, "ms": 4}
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse unsigned seconds or ordered duration components into seconds."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if _NUMBER.fullmatch(stripped):
+        return float(int(stripped))
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
+        order = _UNIT_ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"duration units out of order: {text!r}")
+        total += int(number) * _UNIT_SECONDS[unit]
+        previous_order = order
+        position = match.end()
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: OK (21 of 21 methods, each in its own process). Operation `01a1408e-d11b-7370-9de4-8ea203619bf3`, networking disabled, disposable branch from the checkpoint.

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
| mutation | pass | score 0.917 on 12 mutants |
| adversarial_tests | pass | OK (10 of 10 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-6c475cf699 | durationkit/parse.py | 8 | 86400 -> 86401 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408e-f632-732e-a847-0561bfd7d8e7 |
| m02-c76f809a1e | durationkit/parse.py | 8 | 3600 -> 3601 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408e-f636-70ce-b49a-9562d69da652 |
| m03-0ca785b09b | durationkit/parse.py | 8 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408e-f664-7474-90f3-c79b95ffec85 |
| m04-40c2a60b47 | durationkit/parse.py | 9 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_components, test_sealed.ParseDurationAcceptanceTests.test_whitesp | 01a1408e-f63d-764c-8c29-66efb034b9ed |
| m05-789d2d7cd1 | durationkit/parse.py | 9 | 3 -> 4 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_components, test_sealed.ParseDurationAcceptanceTests.test_zero_va | 01a1408e-f5f8-7305-a32b-ad03b93c47c7 |
| m06-9fd52e98a8 | durationkit/parse.py | 9 | 4 -> 5 | survived |  | 01a1408e-f642-7531-ac0a-6db0f97642ec |
| m07-e06d505299 | durationkit/parse.py | 24 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408e-f5fc-7528-839e-e68b24f60f39 |
| m08-ad92f88c69 | durationkit/parse.py | 26 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408e-fc22-715a-9864-60cdec4c862f |
| m09-744220c0ea | durationkit/parse.py | 29 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_nondecimal_numeric_characters_are_rejected, test_sealed.ParseDurationAccep | 01a1408f-16c8-7259-80b9-f06d25cd0d81 |
| m10-7ff166d4a1 | durationkit/parse.py | 33 | LtE -> Lt | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_for_zero | 01a1408f-19bc-7798-b600-cffe5ae4fb74 |
| m11-2986873404 | durationkit/parse.py | 35 | Mult -> Div | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408f-1d8c-7715-b15f-c9855f87363a |
| m12-023cdac001 | durationkit/parse.py | 38 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1408f-1bab-7371-92bc-32ffebe30a15 |

Model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `95047417adf991ae41f9191a4c3ed6bdc774a3b1986a941df1840b664567d2b7`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a14090-0df1-76a5-bb20-ad982703ee7c`. Notes: Targets m versus ms ambiguity, Unicode digits and whitespace, complete consumption, zero-valued order checks, large integers, and string subclasses.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `_NUMBER.fullmatch(stripped)` preserves unsigned seconds, `(ms|[dhms])` recognizes the required units, `order <= previous_order` rejects duplicates and incorrect ordering, and `isspace()` permits whitespace between complete components while the loop rejects unconsumed malformed text. Only durationkit/parse.py changed, and observed tool output supports the reported success of all 6 existing tests plus 25 valid, 37 invalid, and 7 non-string acceptance cases.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10663 | 1496 | 0 | - | 68.8s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10881 | 1967 | 0 | - | 46.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10651 | 91 | 7168 | - | 23.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 22102 | 834 | 0 | - | 32.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 22268 | 157 | 18048 | - | 22.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11330 | 771 | 7168 | - | 27.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12098 | 202 | 7168 | - | 24.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12521 | 174 | 7168 | - | 24.1s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11098 | 1655 | 0 | - | 53.1s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11940 | 187 | 0 | - | 26.0s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 135552/7534/46720; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1408a-5b0b-77a3-b222-dac8cd16b235 | SUCCESS | 0 | 0.761s | retained | off | 0.00278804 |
| red-1 | 01a1408c-3b94-765c-b306-ffb6742e598b | SUCCESS | 0 | 4.38s | disposable | off | 0.036189740000000005 |
| impl-tests-3 | 01a1408d-912c-749d-be9b-4a7300f01e18 | SUCCESS | 0 | 0.73s | disposable | off | 0.0027477300000000003 |
| impl-python-4 | 01a1408e-07ba-73cd-b561-0f1364490152 | SUCCESS | 0 | 0.618s | disposable | off | 0.00156948 |
| verify | 01a1408e-d11b-7370-9de4-8ea203619bf3 | SUCCESS | 0 | 4.541s | disposable | off | 0.03789403 |
| mutant-m01-6c475cf699 | 01a1408e-f632-732e-a847-0561bfd7d8e7 | SUCCESS | 0 | 4.525s | disposable | off | 0.03696602 |
| mutant-m04-40c2a60b47 | 01a1408e-f63d-764c-8c29-66efb034b9ed | SUCCESS | 0 | 4.479s | disposable | off | 0.03675168 |
| mutant-m03-0ca785b09b | 01a1408e-f664-7474-90f3-c79b95ffec85 | SUCCESS | 0 | 4.399s | disposable | off | 0.03610443000000001 |
| mutant-m02-c76f809a1e | 01a1408e-f636-70ce-b49a-9562d69da652 | SUCCESS | 0 | 4.457s | disposable | off | 0.03664296 |
| mutant-m05-789d2d7cd1 | 01a1408e-f5f8-7305-a32b-ad03b93c47c7 | SUCCESS | 0 | 4.31s | disposable | off | 0.03628043 |
| mutant-m06-9fd52e98a8 | 01a1408e-f642-7531-ac0a-6db0f97642ec | SUCCESS | 0 | 4.482s | disposable | off | 0.03681746 |
| mutant-m07-e06d505299 | 01a1408e-f5fc-7528-839e-e68b24f60f39 | SUCCESS | 0 | 4.421s | disposable | off | 0.03643309 |
| mutant-m08-ad92f88c69 | 01a1408e-fc22-715a-9864-60cdec4c862f | SUCCESS | 0 | 4.447s | disposable | off | 0.036873220000000005 |
| mutant-m09-744220c0ea | 01a1408f-16c8-7259-80b9-f06d25cd0d81 | SUCCESS | 0 | 4.305s | disposable | off | 0.036197320000000005 |
| mutant-m10-7ff166d4a1 | 01a1408f-19bc-7798-b600-cffe5ae4fb74 | SUCCESS | 0 | 4.341s | disposable | off | 0.03636893 |
| mutant-m11-2986873404 | 01a1408f-1d8c-7715-b15f-c9855f87363a | SUCCESS | 0 | 4.307s | disposable | off | 0.03620247 |
| mutant-m12-023cdac001 | 01a1408f-1bab-7371-92bc-32ffebe30a15 | SUCCESS | 0 | 4.328s | disposable | off | 0.036200170000000004 |
| breaker-tests | 01a14090-0df1-76a5-bb20-ad982703ee7c | SUCCESS | 0 | 2.421s | disposable | off | 0.01826927 |

Sandbox operations: 18, total guest duration 66.252s, retained images ['60bf5f96-a8a2-4b21-a45d-2be0b1bf49eb'].

## 11. Limitations of this bundle
- Profile 'hardening-smoke': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
