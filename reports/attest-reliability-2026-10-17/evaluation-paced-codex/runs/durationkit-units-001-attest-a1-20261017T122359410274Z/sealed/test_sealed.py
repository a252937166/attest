import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_from_module


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_both_public_imports_work(self):
        self.assertEqual(parse_duration('7'), 7.0)
        self.assertEqual(parse_duration_from_module('7'), 7.0)

    def test_plain_seconds_preserve_existing_behavior(self):
        for text, expected in [('90', 90.0), ('  42 ', 42.0), ('7', 7.0), ('0', 0.0)]:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_day_component(self):
        self.assertEqual(parse_duration('2d'), 172800.0)

    def test_hour_component(self):
        self.assertEqual(parse_duration('3h'), 10800.0)

    def test_minute_component(self):
        self.assertEqual(parse_duration('15m'), 900.0)

    def test_second_component(self):
        self.assertEqual(parse_duration('45s'), 45.0)

    def test_millisecond_component(self):
        self.assertAlmostEqual(parse_duration('500ms'), 0.5)

    def test_ordered_component_combinations(self):
        cases = [('1h30m', 5400.0), ('2d4h', 187200.0), ('1m1s', 61.0), ('1s500ms', 1.5), ('1d1h1m1s1ms', 90061.001)]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_units_may_be_skipped(self):
        for text, expected in [('1d1s', 86401.0), ('1h1ms', 3600.001)]:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_whitespace_around_and_between_components(self):
        for text in (' 1h 30m ', '\t1h\n30m\t', '1h\u200330m'):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_whitespace_cannot_split_number_from_unit(self):
        for text in ('1 h', '1\th', '1m s'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_leading_zeros_are_accepted(self):
        for text, expected in [('00090', 90.0), ('01h030m', 5400.0)]:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_zero_valued_components_are_accepted(self):
        for text in ('0s', '0d0h0m0s0ms'):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_component_values_have_no_clock_range_limit(self):
        for text, expected in [('90m', 5400.0), ('1500ms', 1.5)]:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_all_accepted_forms_return_float(self):
        for text in ('0', '7', '0s', '2d', '500ms', '1h30m', '1s500ms'):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_strings_raise_value_error(self):
        for text in ('', '   ', '\t\n'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_invalid_numeric_forms_raise_value_error(self):
        for text in ('-1', '-1h', '+1', '+1h', '1.5', '1.5h', '1e3s', '1_000s'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_and_uppercase_units_raise_value_error(self):
        for text in ('1x', '1H', '1MS'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers_raise_value_error(self):
        for text in ('h', 'ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_raise_value_error(self):
        for text in ('1h1h', '1ms1ms', '0h0h'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_out_of_order_units_raise_value_error(self):
        for text in ('30m1h', '1ms1s', '0s0h'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_mixed_bare_numbers_raise_value_error(self):
        for text in ('1h30', '1 30m', '1 2'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_punctuation_and_trailing_garbage_raise_value_error(self):
        for text in ('1h,30m', '1h!', 'abc'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_decimal_numeric_characters_raise_value_error(self):
        for text in ('Ⅳ', '½', '①', '①h'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, None, 1.5, True, b'90'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)
