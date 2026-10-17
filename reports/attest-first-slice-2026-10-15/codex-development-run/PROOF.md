# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: VERIFIED**  
Run `durationkit-units-001-20261015T090947Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T09:09:47.812561+00:00, finished 2026-10-15T09:17:33.917410+00:00.

Reasons: all gates passed

## 1. Frozen task
Task `durationkit-units-001`, spec digest `e51653cf1b317948395923522095ddf1b6d11db0574120e38c3472448f457b8c`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `47f59023-7a06-42c3-b842-452d3473e304`.

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend durationkit.parse_duration to accept either a plain non-negative integer representing seconds or a sequence of integer-and-unit components using d, h, m, s and ms. Components must use distinct units in descending order, with optional whitespace around the input and between components. Preserve the public import, float return type, existing plain-seconds behavior and existing tests; reject invalid strings with ValueError and non-string arguments with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| durationkit.parse_duration | parse_duration(text: str) -> float | Remain importable via `from durationkit import parse_duration`, with implementation in durationkit.parse. After stripping surrounding whitespace, accept either  | TypeError: text is not an instance of str, including int, float, bool, bytes and None.; ValueError: input is empty or contains only whitespace.; ValueError: any |

Acceptance criteria:
1. 1. All existing tests in tests/ pass without modification, and `from durationkit import parse_duration` remains valid.
2. 2. Plain integer seconds retain their behavior: '90' returns 90.0, '  42 ' returns 42.0, '7' returns 7.0 and '0' returns 0.0.
3. 3. Each unit works individually: '2d' returns 172800.0, '3h' returns 10800.0, '15m' returns 900.0, '45s' returns 45.0 and '500ms' returns 0.5.
4. 4. Ordered combinations work: '1h30m' returns 5400.0, '2d4h' returns 187200.0, '1m1s' returns 61.0, '1s500ms' returns 1.5 and '1d1h1m1s1ms' returns 90061.001. Fractional results may be checked with an absolute tolerance of 1e-9.
5. 5. Units may be omitted: '1d1ms' returns 86400.001. Component magnitudes need not be normalized: '90m' returns 5400.0 and '1500ms' returns 1.5.
6. 6. Zero and leading zeros are valid: '0s', '0ms' and '0d0h0m0s0ms' return 0.0; '00090' returns 90.0 and '01h030m' returns 5400.0.
7. 7. Surrounding and inter-component whitespace is accepted, including tabs and newlines: ' 1h 30m ' and '\t1h\n30m\t' both return 5400.0.
8. 8. Unicode decimal digits are accepted: '٩٠' returns 90.0 and '١h٣٠m' returns 5400.0. Non-decimal digit characters such as '²' and '²s' raise ValueError.
9. 9. Empty and whitespace-only strings, including '', '   ' and '\t\n', raise ValueError.
10. 10. Signed, fractional and otherwise unsupported numeric forms raise ValueError, including '-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s' and '1_000s'.
11. 11. Unknown or incorrectly cased units and missing numbers raise ValueError, including '1x', '1H', '1MS', 'h', 'ms' and 'abc'.
12. 12. Repeated units raise ValueError, including '1h1h', '1ms2ms' and '0s0s'. Out-of-order units raise ValueError, including '30m1h', '1ms1s' and '0s0m'.
13. 13. Missing units, mixed forms, internal whitespace and extraneous text raise ValueError, including '1h30', '1 2', '1 h', '1m s', '1h,30m' and '1s!'.
14. 14. Non-string inputs, including 90, 1.5, True, b'90' and None, raise TypeError.
15. 15. Every accepted input returns a float, including integral totals and zero.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `a99c48235c87f92e1c4f3c0439db13b46b0519114a1ba8949b3b322c0d055b80`, 27 tests, sealed at 2026-10-15T09:12:19.456865+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint: FAILED (errors=24) (24 failing of 27 ran; operation `01a13ed5-7594-75c6-9aa6-3815f809f21c`).

| Sealed test | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.ParseDurationAcceptanceTests.test_adjacent_bare_numbers_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_component_magnitudes_are_unrestricted | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_digit_separators_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_each_unit_individually | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_empty_and_whitespace_only_strings_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_every_accepted_form_returns_float | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_exponent_notation_is_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_fractional_numbers_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_leading_zeros | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_non_string_arguments_raise_type_error | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_nondecimal_numeric_characters_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_omitted_intermediate_units | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_ordered_component_combinations | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_out_of_order_units_are_rejected_even_for_zero | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_plain_integer_seconds | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_punctuation_and_trailing_junk_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_repeated_units_are_rejected_even_for_zero | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_signed_numbers_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_surrounding_and_intercomponent_whitespace | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_trailing_bare_number_is_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_unicode_decimal_digits | ERROR | ok |
| test_sealed.ParseDurationAcceptanceTests.test_unit_without_number_after_component_is_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_units_without_numbers_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_unknown_units_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_uppercase_units_are_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_whitespace_between_number_and_unit_is_rejected | ok | ok |
| test_sealed.ParseDurationAcceptanceTests.test_zero_components | ERROR | ok |

## 4. Candidate patch
1 changed path(s); scope check passed; 11 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -1,15 +1,51 @@
 """Duration parsing."""
 
 
+_SECONDS_PER_UNIT = {"d": 86400, "h": 3600, "m": 60, "s": 1}
+_UNIT_ORDER = {"d": 0, "h": 1, "m": 2, "s": 3, "ms": 4}
+
+
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
-
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
-    """
+    """Parse plain seconds or ordered duration components into seconds."""
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
+
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if stripped.isdecimal():
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
+            position += 2
+        elif position < len(stripped) and stripped[position] in "dhms":
+            unit = stripped[position]
+            position += 1
+        else:
+            raise ValueError(f"unsupported duration: {text!r}")
+
+        order = _UNIT_ORDER[unit]
+        if order <= previous_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        previous_order = order
+        if unit == "ms":
+            total += float(number + "e-3")
+        else:
+            total += float(number) * _SECONDS_PER_UNIT[unit]
+
+        while position < len(stripped) and stripped[position].isspace():
+            position += 1
+
+    return float(total)
```

## 5. Fresh-branch verification
Existing suite: OK (6 passed of 6). Sealed suite: OK (27 passed of 27). Operation `01a13eda-47ab-70dd-9364-1b7f32a2e4cb`, networking disabled, disposable branch from the checkpoint.

## 6. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10550 | 1458 | 0 | 81.9s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10743 | 2205 | 0 | 49.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10467 | 67 | 0 | 18.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 21822 | 998 | 10496 | 42.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10851 | 84 | 0 | 19.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11305 | 151 | 0 | 19.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11534 | 573 | 0 | 29.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 24575 | 583 | 11904 | 29.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 12291 | 1361 | 7168 | 48.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-8 | medium | 12509 | 90 | 0 | 15.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-9 | medium | 12971 | 298 | 0 | 23.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-10 | medium | 13026 | 119 | 7168 | 26.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-11 | medium | 13050 | 152 | 0 | 16.9s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 175694/8139/36736; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13ed3-47b9-75e1-8e81-44abeacb0edc | SUCCESS | 0 | 0.754s | retained | 0.0027566400000000003 |
| red-1 | 01a13ed5-7594-75c6-9aa6-3815f809f21c | SUCCESS | 0 | 0.775s | disposable | 0.0028161500000000003 |
| impl-tests-4 | 01a13ed7-10cc-7608-ad45-ea0bb526371f | SUCCESS | 0 | 0.733s | disposable | 0.00278496 |
| impl-python-5 | 01a13ed7-9af2-703e-a6a0-4600cc6361e6 | SUCCESS | 0 | 0.53s | disposable | 0.00116889 |
| impl-python-6 | 01a13ed8-207a-7347-8ce1-89dee23795a6 | SUCCESS | 0 | 0.549s | disposable | 0.00116575 |
| impl-python-9 | 01a13ed9-8619-7141-a231-1e5bb7ff5fc6 | SUCCESS | 0 | 0.544s | disposable | 0.00114605 |
| impl-tests-10 | 01a13ed9-f84d-7790-9a96-8ec449c40d5d | SUCCESS | 0 | 0.757s | disposable | 0.0027648200000000003 |
| verify | 01a13eda-47ab-70dd-9364-1b7f32a2e4cb | SUCCESS | 0 | 0.949s | disposable | 0.00451343 |

Sandbox operations: 8, total guest duration 5.591s, retained images ['47f59023-7a06-42c3-b842-452d3473e304'].

## 7. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- First slice: single candidate, no breaker/mutation pass, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- Sandbox CPU/RAM quotas are not configurable through the public REST schema; only max_layer_bytes, a timeout and networking=off are enforced per operation.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge.
- The retained checkpoint image stays on the service (no documented delete endpoint) and is listed in the ledger.
