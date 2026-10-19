import unittest

from durationkit import parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_public_import_parses_existing_example(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("0007", 7.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_each_individual_unit(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_descending_unit_combinations(self):
        cases = (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001))
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_skipped_units(self):
        for text, expected in (("1d1s", 86401.0), ("1h1ms", 3600.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_zero_valued_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zero_components(self):
        self.assertEqual(parse_duration("01h030m"), 5400.0)

    def test_component_values_have_no_clock_range(self):
        for text, expected in (("90m", 5400.0), ("1500ms", 1.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_whitespace_around_and_between_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\r", "\u00a01h\u00a030m\u00a0"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_every_accepted_form_returns_float(self):
        for text in ("0", "0007", "0s", "1h30m", "0ms", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_rejected(self):
        for text in ("", "   ", "\t\n", "\u00a0"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_signed_numbers_rejected(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_fraction_exponent_and_separator_rejected(self):
        for text in ("1.5", "1.5h", "1e3s", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_unknown_and_uppercase_units_rejected(self):
        for text in ("1x", "1H", "1MS", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_units_without_numbers_rejected(self):
        for text in ("h", "ms", "1hms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_repeated_units_rejected(self):
        for text in ("1h1h", "1ms1ms", "0h0h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_out_of_order_units_rejected_even_with_zero(self):
        for text in ("30m1h", "1ms1s", "0s0h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_incomplete_or_mixed_components_rejected(self):
        for text in ("1h30", "1 30m", "30m 1"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_whitespace_inside_numbers_or_before_units_rejected(self):
        for text in ("1 h", "1 m s", "1 0s", "12 3s", "1h 2 ms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_extra_text_rejected(self):
        for text in ("1h,30m", "1s!", "x1h", "1h x 30m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, 1.5, None, b"90", [], {}, True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse_duration(value)

    def test_non_decimal_numeric_characters_rejected(self):
        for text in ("Ⅻ", "Ⅻh", "½s", "①s", "²s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)
