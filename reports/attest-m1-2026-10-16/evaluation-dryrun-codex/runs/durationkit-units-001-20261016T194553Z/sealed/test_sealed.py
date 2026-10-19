import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_from_module


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_both_public_imports_work(self):
        self.assertEqual(parse_duration("1h"), 3600.0)
        self.assertEqual(parse_duration_from_module("1h"), 3600.0)

    def test_plain_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("7", 7.0), ("0", 0.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_combined_whole_second_components(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_combined_fractional_components(self):
        for text, expected in (("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, places=6)

    def test_skipped_units(self):
        self.assertEqual(parse_duration("1d1s"), 86401.0)
        self.assertAlmostEqual(parse_duration("1h1ms"), 3600.001, places=6)

    def test_surrounding_whitespace(self):
        for text in (" 1h30m ", "\t1h30m\r", "\u20031h30m\u2003"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_whitespace_between_complete_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\r", "1h\u200330m"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_whitespace_inside_components_is_rejected(self):
        for text in ("1 h", "1m 500 ms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_zero_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zeros(self):
        self.assertEqual(parse_duration("00090"), 90.0)
        self.assertEqual(parse_duration("01h030m"), 5400.0)

    def test_component_values_are_unrestricted(self):
        for text, expected in (("90m", 5400.0), ("1000ms", 1.0), ("1s1500ms", 2.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_unicode_decimal_digits(self):
        self.assertEqual(parse_duration("\u0661\u0662"), 12.0)
        self.assertEqual(parse_duration("\u0661h"), 3600.0)

    def test_nondecimal_numeric_character_is_rejected(self):
        for text in ("\u00b2", "\u00b2h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_empty_and_whitespace_only_are_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_signed_numbers_are_rejected(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_fractional_and_exponential_numbers_are_rejected(self):
        for text in ("1.5", "1.5h", ".5s", "1e3s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_or_uppercase_units_are_rejected(self):
        for text in ("1x", "1H"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers_are_rejected(self):
        for text in ("h", "ms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_incomplete_or_mixed_components_are_rejected(self):
        for text in ("1h30", "1 30m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_malformed_text_and_punctuation_are_rejected(self):
        for text in ("abc", "1h,30m", "1mss", "1h!"):
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

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, 1.5, None, True, b"90"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)

    def test_string_subclasses_are_accepted(self):
        class DurationString(str):
            pass

        self.assertEqual(parse_duration(DurationString("1h30m")), 5400.0)

    def test_every_accepted_form_returns_float(self):
        for text in ("7", "0", "0ms", "1h30m", "1ms", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)
