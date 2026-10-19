import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_from_module


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_both_public_imports_work(self):
        self.assertEqual(parse_duration("1s"), 1.0)
        self.assertEqual(parse_duration_from_module("1s"), 1.0)

    def test_plain_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("0007", 7.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_combined_components(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, places=7)

    def test_skipped_units(self):
        self.assertAlmostEqual(parse_duration("1d1ms"), 86400.001, places=7)

    def test_unrestricted_component_values(self):
        self.assertEqual(parse_duration("90m"), 5400.0)
        self.assertEqual(parse_duration("1500ms"), 1.5)

    def test_leading_zero_components(self):
        self.assertEqual(parse_duration("001h030m"), 5400.0)

    def test_zero_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_ascii_whitespace_between_components_and_around_input(self):
        for text in (" 1h 30m ", "\t1h\n30m\r"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_unicode_whitespace_between_components_and_around_input(self):
        self.assertEqual(parse_duration("\u20031h\u200330m\u2003"), 5400.0)

    def test_every_accepted_form_returns_float(self):
        for text in ("7", "0", "2d", "0ms", "1h30m", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_strings_raise_value_error(self):
        for text in ("", "   ", "\t\n", "\u2003"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_signed_numbers_raise_value_error(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_fractional_exponent_and_separated_numbers_raise_value_error(self):
        for text in ("1.5", "1.5h", "1e3s", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_and_uppercase_units_raise_value_error(self):
        for text in ("1x", "1H", "1MS"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers_raise_value_error(self):
        for text in ("h", "ms", "abc", "1hms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_raise_value_error(self):
        for text in ("1h1h", "1ms2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_out_of_order_units_raise_value_error(self):
        for text in ("30m1h", "1ms1s", "0s0m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_component_number_without_unit_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_mixed_plain_seconds_and_components_raise_value_error(self):
        for text in ("30 1h", "1 2"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unmatched_punctuation_raises_value_error(self):
        for text in ("1h,30m", "1h!"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_whitespace_inside_components_raises_value_error(self):
        for text in ("1 h", "1\th", "1 0s", "1m s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_decimal_numeric_characters_raise_value_error(self):
        for text in ("Ⅳ", "Ⅳh", "½", "½s", "①", "①h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, None, 1.5, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)
