import inspect
import math
import typing
import unittest

from durationkit import parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_public_signature_and_import(self):
        self.assertEqual(parse_duration("1"), 1.0)
        signature = inspect.signature(parse_duration)
        self.assertEqual(list(signature.parameters), ["text"])
        self.assertEqual(signature.parameters["text"].kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertEqual(signature.parameters["text"].default, inspect.Parameter.empty)
        self.assertEqual(typing.get_type_hints(parse_duration), {"text": str, "return": float})

    def test_plain_integer_seconds(self):
        for text, expected in [("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("0007", 7.0)]:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_unit_components(self):
        for text, expected in [("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)]:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_descending_adjacent_components(self):
        cases = [("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertTrue(math.isclose(parse_duration(text), expected, rel_tol=1e-12, abs_tol=1e-9))

    def test_whitespace_between_complete_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\r", "\v1d\f2h\t3m\n"):
            with self.subTest(text=text):
                expected = 90180.0 if "1d" in text else 5400.0
                self.assertEqual(parse_duration(text), expected)

    def test_zero_and_leading_zero_components(self):
        for text, expected in [("0s", 0.0), ("0d0h0m0s0ms", 0.0), ("01h003m", 3780.0)]:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_component_values_have_no_clock_limits(self):
        self.assertEqual(parse_duration("90m"), 5400.0)
        self.assertEqual(parse_duration("1500ms"), 1.5)

    def test_accepted_results_are_floats(self):
        for text in ("0", "7", "0s", "2d", "500ms", "1h30m", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_or_whitespace_only_is_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_invalid_numeric_forms_raise_value_error(self):
        for text in ("-1", "-1h", "+1", "+1h", "1.5", "1.5h", "1e3s", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_unknown_cased_or_numberless_units_raise_value_error(self):
        for text in ("1x", "1H", "1MS", "h", "ms", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_repeated_units_raise_value_error(self):
        for text in ("1h1h", "1ms2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_out_of_order_units_raise_value_error(self):
        for text in ("30m1h", "1ms1s", "1s1m", "0ms0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_whitespace_inside_numbers_or_components_raises_value_error(self):
        for text in ("1 h", "1\tms", "1 0s", "9 0"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_mixed_bare_integers_and_components_raise_value_error(self):
        for text in ("1h30", "90 1s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_separators_and_trailing_junk_raise_value_error(self):
        for text in ("1h,30m", "1h30m!", "1mss", "1h garbage"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_non_decimal_numeric_characters_raise_value_error(self):
        for text in ("Ⅳ", "Ⅳh", "½", "½s", "①", "①m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, 1.5, None, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse_duration(value)
