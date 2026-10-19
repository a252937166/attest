import inspect
import unittest
from typing import get_type_hints

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_from_module


class ParseDurationAcceptance(unittest.TestCase):
    def test_public_signature(self):
        self.assertEqual(parse_duration("1"), 1.0)
        signature = inspect.signature(parse_duration)
        parameters = list(signature.parameters.values())
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters[0].name, "text")
        self.assertEqual(parameters[0].kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertEqual(get_type_hints(parse_duration), {"text": str, "return": float})

    def test_parse_module_public_import(self):
        self.assertEqual(parse_from_module("2h"), 7200.0)

    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("0007", 7.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_units(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_combined_units(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_skipped_units(self):
        self.assertEqual(parse_duration("1d1s"), 86401.0)
        self.assertAlmostEqual(parse_duration("1h1ms"), 3600.001)

    def test_whitespace_between_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\t", "1h\t30m"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_python_unicode_whitespace(self):
        self.assertEqual(parse_duration("\u20031h\u200330m\u2003"), 5400.0)

    def test_whitespace_inside_component_is_rejected(self):
        for text in ("1 h", "1\tm", "1m s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_zero_valued_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zeros_in_components(self):
        self.assertEqual(parse_duration("01h030m"), 5400.0)

    def test_component_quantities_have_no_clock_limits(self):
        self.assertEqual(parse_duration("90m"), 5400.0)
        self.assertAlmostEqual(parse_duration("1500ms"), 1.5)

    def test_all_accepted_forms_return_float(self):
        for text in ("0", "0007", "0ms", "1h", "1h30m", "1s1ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_strings_are_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_signed_fractional_and_malformed_numbers_are_rejected(self):
        for text in ("-1", "-1h", "+1", "+1h", "1.5", "1.5h", ".5s", "1e3s", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_uppercase_and_numberless_units_are_rejected(self):
        for text in ("1x", "1H", "1MS", "h", "ms", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_are_rejected(self):
        for text in ("1h1h", "1ms2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_out_of_order_units_are_rejected(self):
        for text in ("30m1h", "1ms1s", "0s0m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_mixed_bare_numbers_and_trailing_text_are_rejected(self):
        for text in ("1h30", "1 30m", "1 2", "1h,30m", "1h30m!", "1mss"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_nondecimal_numeric_characters_are_rejected(self):
        for text in ("Ⅳ", "Ⅳh", "½", "½h", "①", "①h", "²", "²s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_nonstring_inputs_raise_type_error(self):
        for value in (90, 1.5, None, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)
