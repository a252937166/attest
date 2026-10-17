# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261015T154144Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T15:41:44.241959+00:00, finished 2026-10-15T15:47:56.365582+00:00.

Reasons: model-written adversarial tests failed: 1 of 10 (test_breaker.TestDurationBreaker.test_very_long_zero_component_is_valid); each failure is a bug or a contract disagreement to resolve


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `b186e69f-b769-46b1-81dd-9c9a317b9a75`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either plain non-negative integer seconds or a sequence of integer-and-unit components using d, h, m, s and ms. Require strictly descending unit order, reject malformed input, allow surrounding whitespace and whitespace between complete components, and return total seconds as a float. Preserve the public import and existing tests without modifying those tests.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Also remains available from durationkit.parse. Accept str instances, including subclasses. After removing surrounding whitespace, accept either one unsigned int | TypeError: input is not an instance of str.; ValueError: input is empty or contains only whitespace.; ValueError: any number is negative, explicitly signed, fra |

Acceptance criteria:
1. 1. All existing tests in tests/ pass unchanged using python -m unittest discover -s tests -t . -v.
2. 2. The public import from durationkit import parse_duration continues to work, and durationkit.parse.parse_duration remains available with signature parse_duration(text: str) -> float.
3. 3. Plain integer seconds remain supported: '90' returns 90.0, '  42 ' returns 42.0, '0' returns 0.0, and '0007' returns 7.0.
4. 4. Single components return the expected seconds: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, and '500ms' -> 0.5.
5. 5. Combined components return the expected seconds: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, and '1d1h1m1s1ms' -> approximately 90061.001 with absolute tolerance 1e-9.
6. 6. Units may be skipped and values need not be normalized: '1d1ms' returns approximately 86400.001, '90m' returns 5400.0, and '1500ms' returns 1.5.
7. 7. Zero components and leading zeros are accepted: '0s', '0ms', and '0d0h0m0s0ms' return 0.0; '01h030m' returns 5400.0.
8. 8. Surrounding and inter-component whitespace is accepted: ' 1h 30m ' and '\t1h\n30m\r' return 5400.0. Whitespace within a component is rejected: '1 h' and '1m s' raise ValueError.
9. 9. Unicode decimal digits retain numeric meaning: '１２' returns 12.0 and '١h٣٠m' returns 5400.0. Non-decimal digit text such as '²' raises ValueError.
10. 10. Empty and whitespace-only inputs, including '', '   ', and '\t\n', raise ValueError.
11. 11. Invalid numeric syntax raises ValueError for '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s', and '1_000s'.
12. 12. Unknown or incorrectly cased units raise ValueError for '1x', '1H', '1MS', and '1sec'.
13. 13. Repeated units raise ValueError for '1h1h', '1ms2ms', and '0s0s'. Out-of-order components raise ValueError for '30m1h', '1ms1s', and '0s0m'.
14. 14. Missing numbers or units and mixed forms raise ValueError for 'h', 'ms', '1h30', '90 1s', and '1 2'. Other malformed text, including 'abc', '1h,30m', and '1s!', raises ValueError.
15. 15. Non-string inputs, including 90, None, 1.5, True, b'90', and [], raise TypeError without coercion.
16. 16. Every accepted input returns a float, including plain integers, zero values, whole-second unit forms, and millisecond forms.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `6d773f01bafbc559b5043d31e7347fc524c9e4a9f7aca8b03a15bc2b5869e1a3`, 28 test methods, sealed at 2026-10-15T15:44:05.309481+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 28 methods: ERROR 13): 13 of 28 methods failing, 15 passing; operation `01a1403c-0c2b-7148-ade7-b7d20d2dbad9`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_all_units_in_descending_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_bare_numbers_cannot_mix_with_components | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_combined_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_component_values_have_no_clock_bounds | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_empty_or_whitespace_only_input_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_explicit_signs_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_exponents_and_digit_separators_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros_in_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_nondecimal_digit_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_public_and_module_imports_remain_available | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_public_signature | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_punctuation_and_trailing_junk_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_str_subclass_is_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_surrounding_whitespace | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_decimal_digits | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_may_be_skipped | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_or_uppercase_units_are_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_complete_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_within_components_is_rejected | ok (1 ev) | ok (1 ev) |
| test_sealed.ParseDurationAcceptanceTests.test_zero_components | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -2,14 +2,49 @@
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
+    """Parse non-negative integer seconds or ordered duration components.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Components use the units d, h, m, s, and ms in strictly descending
+    order. Whitespace is allowed around the input and between components.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("duration must not be empty")
+    if stripped.isdecimal():
+        return float(stripped)
+
+    units = {"d": (0, 86400), "h": (1, 3600), "m": (2, 60),
+             "s": (3, 1), "ms": (4, 0.001)}
+    total = 0.0
+    position = 0
+    previous_rank = -1
+
+    while position < len(stripped):
+        number_start = position
+        while position < len(stripped) and stripped[position].isdecimal():
+            position += 1
+        if position == number_start:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        number = int(stripped[number_start:position])
+        if stripped.startswith("ms", position):
+            unit = "ms"
+        elif position < len(stripped) and stripped[position] in "dhms":
+            unit = stripped[position]
+        else:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        rank, seconds = units[unit]
+        if rank <= previous_rank:
+            raise ValueError(f"units out of order: {text!r}")
+        total += number * seconds
+        previous_rank = rank
+        position += len(unit)
+
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: OK (6 passed of 6). Sealed suite: OK (28 of 28 methods, each in its own process). Operation `01a1403e-030b-7590-a154-4b300f3226bc`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
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
| adversarial_tests | FAIL | FAILED (1 of 10 methods: ERROR 1) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-5a8ec3ec38 | durationkit/parse.py | 14 | remove `not` | killed | test_sealed.ParseDurationAcceptanceTests.test_public_signature, test_sealed.ParseDurationAcceptanceTests.test_plain_inte | 01a1403e-2fb2-70e9-854d-c59d732f0194 |
| m02-5bd52d7829 | durationkit/parse.py | 19 | 0 -> 1 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_components, test_sealed.ParseDurationAcceptanceTests.test_all_uni | 01a1403e-2a20-7708-a118-67e265a06c95 |
| m03-dad49bfc74 | durationkit/parse.py | 19 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_combined_components, test_sealed.ParseDurationAcceptanceTests.test_all_uni | 01a1403e-2a66-70cb-a907-0bd671c506bb |
| m04-f59f5c3079 | durationkit/parse.py | 19 | 60 -> 61 | killed | test_sealed.ParseDurationAcceptanceTests.test_single_components, test_sealed.ParseDurationAcceptanceTests.test_combined_ | 01a1403e-2a93-764e-81f4-a41c9620da77 |
| m05-9221b46d08 | durationkit/parse.py | 20 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_public_signature, test_sealed.ParseDurationAcceptanceTests.test_single_com | 01a1403e-2aa7-7199-ac50-9684cbdc949d |
| m06-4fc9863605 | durationkit/parse.py | 23 | 1 -> 2 | survived |  | 01a1403e-2aaf-7739-90e4-1e1750cfbff2 |
| m07-84193a4528 | durationkit/parse.py | 27 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_bare_numbers_cannot_mix_with_components | 01a1403e-2ace-7406-8362-8633693be55c |
| m08-f2aa6f1b9e | durationkit/parse.py | 28 | 1 -> 2 | killed | test_sealed.ParseDurationAcceptanceTests.test_public_signature, test_sealed.ParseDurationAcceptanceTests.test_single_com | 01a1403e-2ae0-7202-95a1-592819b836ca |
| m09-94ea83124a | durationkit/parse.py | 35 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_bare_numbers_cannot_mix_with_components | 01a1403e-4cfb-77cc-b75b-163dcc1c3d97 |
| m10-1b5e25eec0 | durationkit/parse.py | 35 | And -> Or | killed | test_sealed.ParseDurationAcceptanceTests.test_whitespace_within_components_is_rejected, test_sealed.ParseDurationAccepta | 01a1403e-51dc-7368-a613-cca642ee3c66 |
| m11-6451458583 | durationkit/parse.py | 42 | raise -> pass | killed | test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected, test_sealed.ParseDurationAcceptanceTests.test | 01a1403e-52b8-77eb-a34f-479f3b975dda |
| m12-b7a09c7bc5 | durationkit/parse.py | 47 | Lt -> LtE | killed | test_sealed.ParseDurationAcceptanceTests.test_public_signature, test_sealed.ParseDurationAcceptanceTests.test_single_com | 01a1403e-52d7-75d1-8595-aefc894fc49b |

Model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `c0f85e1e87b179b4678b31e15b0da439f910a4a7504e461cf09c007be720e99a`): FAILED (1 of 10 methods: ERROR 1); binding FAILED; operation `01a1403f-570a-7308-9a88-a80ef1cd30f9`. Notes: Targets unbounded decimal components, all unit order pairs, Unicode whitespace and digits, and malformed boundaries.

| Failing adversarial test | Outcome |
| --- | --- |
| test_very_long_zero_component_is_valid | ERROR |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: isdecimal() preserves Unicode decimal input, the scanner recognizes ms before single-letter units, rank <= previous_rank rejects repeated or unordered units, and isspace() permits inter-component whitespace. The signature and existing tests remain unchanged; observed checks report all six existing tests passing plus 25 valid, 32 malformed, and six non-string cases, supporting the implementer's claims.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10625 | 1458 | 0 | - | 64.5s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10781 | 2636 | 7040 | - | 57.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10641 | 87 | 0 | - | 16.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10836 | 693 | 0 | - | 26.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11019 | 119 | 0 | - | 18.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11265 | 794 | 7168 | - | 26.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12001 | 359 | 0 | - | 23.4s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11142 | 2403 | 7040 | - | 55.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11933 | 168 | 0 | - | 19.0s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 100243/8717/21248; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1403a-1498-707f-8e47-32bfb5b06938 | SUCCESS | 0 | 0.768s | retained | off | 0.0027914999999999997 |
| red-1 | 01a1403c-0c2b-7148-ade7-b7d20d2dbad9 | SUCCESS | 0 | 5.721s | disposable | off | 0.048225580000000004 |
| impl-tests-3 | 01a1403d-2542-71ad-9273-d8636fec89fb | SUCCESS | 0 | 0.76s | disposable | off | 0.00278973 |
| impl-python-4 | 01a1403d-987f-75fe-a080-d341d0fd19f1 | SUCCESS | 0 | 0.52s | disposable | off | 0.00115657 |
| verify | 01a1403e-030b-7590-a154-4b300f3226bc | SUCCESS | 0 | 5.796s | disposable | off | 0.04924133 |
| mutant-m01-5a8ec3ec38 | 01a1403e-2fb2-70e9-854d-c59d732f0194 | SUCCESS | 0 | 5.532s | disposable | off | 0.04745644 |
| mutant-m02-5bd52d7829 | 01a1403e-2a20-7708-a118-67e265a06c95 | SUCCESS | 0 | 5.604s | disposable | off | 0.047967600000000006 |
| mutant-m03-dad49bfc74 | 01a1403e-2a66-70cb-a907-0bd671c506bb | SUCCESS | 0 | 5.584s | disposable | off | 0.04749044 |
| mutant-m04-f59f5c3079 | 01a1403e-2a93-764e-81f4-a41c9620da77 | SUCCESS | 0 | 5.605s | disposable | off | 0.04723284 |
| mutant-m05-9221b46d08 | 01a1403e-2aa7-7199-ac50-9684cbdc949d | SUCCESS | 0 | 5.604s | disposable | off | 0.04764782 |
| mutant-m06-4fc9863605 | 01a1403e-2aaf-7739-90e4-1e1750cfbff2 | SUCCESS | 0 | 5.606s | disposable | off | 0.04766985000000001 |
| mutant-m07-84193a4528 | 01a1403e-2ace-7406-8362-8633693be55c | SUCCESS | 0 | 5.585s | disposable | off | 0.04729847 |
| mutant-m08-f2aa6f1b9e | 01a1403e-2ae0-7202-95a1-592819b836ca | SUCCESS | 0 | 5.594s | disposable | off | 0.04738441 |
| mutant-m09-94ea83124a | 01a1403e-4cfb-77cc-b75b-163dcc1c3d97 | SUCCESS | 0 | 5.543s | disposable | off | 0.0471946 |
| mutant-m10-1b5e25eec0 | 01a1403e-51dc-7368-a613-cca642ee3c66 | SUCCESS | 0 | 5.6s | disposable | off | 0.04754875 |
| mutant-m11-6451458583 | 01a1403e-52b8-77eb-a34f-479f3b975dda | SUCCESS | 0 | 5.572s | disposable | off | 0.047340310000000003 |
| mutant-m12-b7a09c7bc5 | 01a1403e-52d7-75d1-8595-aefc894fc49b | SUCCESS | 0 | 5.594s | disposable | off | 0.04752294000000001 |
| breaker-tests | 01a1403f-570a-7308-9a88-a80ef1cd30f9 | SUCCESS | 0 | 2.473s | disposable | off | 0.018405130000000002 |

Sandbox operations: 18, total guest duration 83.061s, retained images ['b186e69f-b769-46b1-81dd-9c9a317b9a75'].

## 11. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
