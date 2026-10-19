import unittest

from durationkit import parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_plain_integer_seconds(self):
        for value, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("00090", 90.0)):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), expected)

    def test_each_single_unit(self):
        for value, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), expected)

    def test_descending_combinations(self):
        for value, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(value=value):
                self.assertAlmostEqual(parse_duration(value), expected, delta=1e-9)

    def test_units_can_be_skipped(self):
        for value, expected in (("1d1s", 86401.0), ("1h1ms", 3600.001)):
            with self.subTest(value=value):
                self.assertAlmostEqual(parse_duration(value), expected, delta=1e-9)

    def test_whitespace_around_and_between_components(self):
        for value in (" 1h 30m ", "\t1h\n30m\r", "1h\u200330m"):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), 5400.0)

    def test_whitespace_inside_components_is_rejected(self):
        for value in ("1 h", "1\tms", "1m s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_zero_valued_components(self):
        for value in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), 0.0)

    def test_leading_zeros_in_components(self):
        self.assertEqual(parse_duration("01h030m"), 5400.0)

    def test_component_values_can_exceed_clock_ranges(self):
        for value, expected in (("90m", 5400.0), ("24h", 86400.0), ("1500ms", 1.5)):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), expected)

    def test_every_accepted_form_returns_float(self):
        for value in ("90", "0", "00090", "0ms", "2d", "1h30m", "1s500ms", "0d0h0m0s0ms"):
            with self.subTest(value=value):
                self.assertIsInstance(parse_duration(value), float)

    def test_empty_and_whitespace_only_are_rejected(self):
        for value in ("", "   ", "\t\n"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_signed_numbers_are_rejected(self):
        for value in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_fractional_and_alternative_notation_is_rejected(self):
        for value in ("1.5h", "1.5", ".5s", "1e3s", "1_000s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_unknown_units_are_rejected(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1x")

    def test_uppercase_units_are_rejected(self):
        for value in ("1H", "1MS"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_units_without_numbers_are_rejected(self):
        for value in ("h", "ms", "1hms"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_adjacent_repeated_units_are_rejected(self):
        for value in ("1h1h", "1ms1ms", "0s0s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_whitespace_separated_repeated_units_are_rejected(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1h 2h")

    def test_out_of_order_units_are_rejected(self):
        for value in ("30m1h", "1ms1s", "1h1d", "0s0m"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_mixed_unitless_and_unit_bearing_text_is_rejected(self):
        for value in ("1h30", "1 30m", "1 2"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_trailing_punctuation_and_garbage_are_rejected(self):
        for value in ("1h,30m", "1h!", "abc"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_non_decimal_numeric_characters_in_plain_form_are_rejected(self):
        for value in ("Ⅳ", "①"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_non_decimal_numeric_characters_in_components_are_rejected(self):
        for value in ("Ⅳh", "½s", "①h", "²s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, 1.5, None, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse_duration(value)
