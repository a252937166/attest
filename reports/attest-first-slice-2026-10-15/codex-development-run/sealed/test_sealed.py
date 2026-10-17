import unittest

from durationkit import parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("7", 7.0), ("0", 0.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_each_unit_individually(self):
        cases = (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5))
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_ordered_component_combinations(self):
        cases = (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001))
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_omitted_intermediate_units(self):
        self.assertAlmostEqual(parse_duration("1d1ms"), 86400.001, delta=1e-9)

    def test_component_magnitudes_are_unrestricted(self):
        for text, expected in (("90m", 5400.0), ("1500ms", 1.5)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_zero_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zeros(self):
        for text, expected in (("00090", 90.0), ("01h030m", 5400.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_surrounding_and_intercomponent_whitespace(self):
        for text in (" 1h 30m ", "\t1h\n30m\t", "1h\t 30m"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_unicode_decimal_digits(self):
        for text, expected in (("\u0669\u0660", 90.0), ("\u0661h\u0663\u0660m", 5400.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_nondecimal_numeric_characters_are_rejected(self):
        for text in ("\u00b2", "\u00b2s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_empty_and_whitespace_only_strings_are_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_signed_numbers_are_rejected(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_fractional_numbers_are_rejected(self):
        for text in ("1.5", "1.5h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_exponent_notation_is_rejected(self):
        for text in ("1e3", "1e3s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_digit_separators_are_rejected(self):
        for text in ("1_000", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_units_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_uppercase_units_are_rejected(self):
        for text in ("1H", "1MS"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers_are_rejected(self):
        for text in ("h", "ms", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_are_rejected_even_for_zero(self):
        for text in ("1h1h", "1ms2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_out_of_order_units_are_rejected_even_for_zero(self):
        for text in ("30m1h", "1ms1s", "0s0m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_trailing_bare_number_is_rejected(self):
        for text in ("1h30", "1h30m2"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_adjacent_bare_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1 2")

    def test_whitespace_between_number_and_unit_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")

    def test_unit_without_number_after_component_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1m s")

    def test_punctuation_and_trailing_junk_are_rejected(self):
        for text in ("1h,30m", "1s!", "1h30mxyz"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_arguments_raise_type_error(self):
        for value in (90, 1.5, True, b"90", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)

    def test_every_accepted_form_returns_float(self):
        for text in ("0", "90", "0s", "2d", "1s500ms", "\u0669\u0660"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)
