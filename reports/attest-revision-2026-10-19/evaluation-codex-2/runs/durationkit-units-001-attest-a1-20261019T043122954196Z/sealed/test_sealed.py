import unittest

from durationkit import parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_public_import_accepts_plain_seconds(self):
        self.assertEqual(parse_duration('90'), 90.0)

    def test_plain_integer_seconds(self):
        for value, expected in [('  42 ', 42.0), ('0', 0.0), ('0007', 7.0)]:
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), expected)

    def test_single_components(self):
        for value, expected in [('2d', 172800.0), ('3h', 10800.0), ('15m', 900.0), ('45s', 45.0), ('500ms', 0.5)]:
            with self.subTest(value=value):
                self.assertAlmostEqual(parse_duration(value), expected)

    def test_adjacent_ordered_components(self):
        for value, expected in [('1h30m', 5400.0), ('2d4h', 187200.0), ('1m1s', 61.0), ('1s500ms', 1.5), ('1d1h1m1s1ms', 90061.001)]:
            with self.subTest(value=value):
                self.assertAlmostEqual(parse_duration(value), expected)

    def test_units_may_be_skipped(self):
        self.assertAlmostEqual(parse_duration('1d1ms'), 86400.001)

    def test_component_values_have_no_clock_range_limit(self):
        for value, expected in [('90m', 5400.0), ('1500ms', 1.5)]:
            with self.subTest(value=value):
                self.assertAlmostEqual(parse_duration(value), expected)

    def test_zero_valued_components(self):
        for value in ('0s', '0d0h0m0s0ms'):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), 0.0)

    def test_leading_zeros_in_components(self):
        self.assertEqual(parse_duration('001h030m'), 5400.0)

    def test_whitespace_around_and_between_components(self):
        for value in (' 1h 30m ', '\t1h\n30m\r', '\u20031h\u200330m\u2003'):
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), 5400.0)

    def test_every_accepted_form_returns_float(self):
        for value in ('90', '0', '0s', '1h30m', '500ms', '1s500ms'):
            with self.subTest(value=value):
                self.assertIsInstance(parse_duration(value), float)

    def test_empty_or_whitespace_only_input_raises_value_error(self):
        for value in ('', '   ', '\t\n'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_signed_numbers_raise_value_error(self):
        for value in ('-1', '-1h', '+1', '+1h'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_fractional_exponent_and_separator_syntax_raises_value_error(self):
        for value in ('1.5', '1.5h', '1e3', '1e3s', '1_000s'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_unknown_or_uppercase_units_raise_value_error(self):
        for value in ('1x', '1H', '1MS'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_units_without_numbers_raise_value_error(self):
        for value in ('h', 'ms', 'abc'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_repeated_units_raise_value_error(self):
        for value in ('1h1h', '1ms 2ms', '0s0s'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_units_out_of_descending_order_raise_value_error(self):
        for value in ('30m1h', '1ms1s', '1s1m', '0ms0s'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_whitespace_inside_components_raises_value_error(self):
        for value in ('1 h', '1 m s', '1 0s'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_bare_integers_mixed_with_components_raise_value_error(self):
        for value in ('1h30', '1 2'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_trailing_punctuation_and_unconsumed_text_raise_value_error(self):
        for value in ('1h,30m', '1s!'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_non_decimal_numeric_characters_raise_value_error(self):
        for value in ('²', '²h', 'Ⅳ', 'Ⅳh', '½', '½h', '①', '①h'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(value)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, None, 1.5, True, b'90', ['90']):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse_duration(value)
