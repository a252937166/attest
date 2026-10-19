import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_from_module


class ParseDurationAcceptedTests(unittest.TestCase):
    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("7", 7.0), ("0", 0.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_adjacent_descending_components(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_skipped_units(self):
        for text, expected in (("1d1ms", 86400.001), ("1h1s", 3601.0)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_whitespace_around_and_between_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\u2003"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_zero_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zeros(self):
        for text, expected in (("00090", 90.0), ("01h030m", 5400.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_component_values_have_no_clock_range_limit(self):
        for text, expected in (("90m", 5400.0), ("1500ms", 1.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_unicode_decimal_digits(self):
        for text, expected in (("\uff19\uff10", 90.0), ("\uff11h\uff13\uff10m", 5400.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_all_accepted_forms_return_float(self):
        for text in ("0", "90", "1h", "0ms", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_parse_module_public_import_has_same_behavior(self):
        self.assertEqual(parse_duration_from_module("1h30m"), parse_duration("1h30m"))

    def test_text_keyword_argument(self):
        self.assertEqual(parse_duration(text="1m"), 60.0)


class ParseDurationRejectedTests(unittest.TestCase):
    def test_empty_and_whitespace_only_strings(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_arguments(self):
        for value in (90, 0.5, None, True, b"90", [], {}):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)

    def test_signed_numbers(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_fractional_numeric_tokens(self):
        for text in ("1.5", "1.5h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_scientific_notation(self):
        for text in ("1e3", "1e3s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_underscores_in_numeric_tokens(self):
        for text in ("1_000", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_units(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_uppercase_units(self):
        for text in ("1H", "1MS"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers(self):
        for text in ("h", "ms", "abc", "1hms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_component_without_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_whitespace_between_number_and_unit(self):
        for text in ("1 h", "1m  s", "1 ms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units(self):
        for text in ("1h1h", "1ms 2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_ascending_unit_order(self):
        for text in ("30m1h", "1ms1s", "1s1d", "0ms0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_bare_seconds_mixed_with_components(self):
        for text in ("90 1s", "1s 90", "1 2"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_extraneous_punctuation_or_unit_text(self):
        for text in ("1h,30m", "1h/30m", "1mss"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_decimal_digit_like_characters(self):
        for text in ("\u00b2", "\u00b2s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)
