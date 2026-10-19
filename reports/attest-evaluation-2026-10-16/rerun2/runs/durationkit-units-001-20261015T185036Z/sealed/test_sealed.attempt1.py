import unittest
from durationkit import parse_duration

class TestParseDurationSealed(unittest.TestCase):
    def test_plain_integer_without_whitespace(self):
        self.assertEqual(parse_duration('90'), 90.0)

    def test_plain_integer_with_surrounding_whitespace(self):
        self.assertEqual(parse_duration('  90  '), 90.0)
        self.assertEqual(parse_duration('\t90\n'), 90.0)

    def test_zero_and_zero_seconds_component(self):
        self.assertEqual(parse_duration('0'), 0.0)
        self.assertEqual(parse_duration('0s'), 0.0)

    def test_single_day_component(self):
        self.assertEqual(parse_duration('2d'), 172800.0)

    def test_single_hour_component(self):
        self.assertEqual(parse_duration('3h'), 10800.0)

    def test_single_minute_component(self):
        self.assertEqual(parse_duration('15m'), 900.0)

    def test_single_second_component(self):
        self.assertEqual(parse_duration('45s'), 45.0)

    def test_single_millisecond_component(self):
        self.assertEqual(parse_duration('500ms'), 0.5)

    def test_combined_components_descending(self):
        cases = [
            ('1h30m', 5400.0),
            ('2d4h', 187200.0),
            ('1m1s', 61.0),
            ('1s500ms', 1.5),
            ('1d1h1m1s1ms', 90061.001),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_whitespace_between_components_allowed(self):
        self.assertEqual(parse_duration(' 1h 30m '), 5400.0)
        self.assertEqual(parse_duration('\t2d\t4h\n'), 187200.0)

    def test_whitespace_around_string_allowed(self):
        self.assertEqual(parse_duration('   1h30m   '), 5400.0)

    def test_empty_string_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('')

    def test_whitespace_only_string_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('   ')
        with self.assertRaises(ValueError):
            parse_duration('\t\n')

    def test_negative_number_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('-1h')

    def test_fractional_number_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')

    def test_unknown_unit_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')

    def test_repeated_unit_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')

    def test_out_of_order_units_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')

    def test_unit_without_number_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('h')

    def test_number_without_unit_after_other_components_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30')

    def test_invalid_text_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')

    def test_non_string_input_raises_type_error(self):
        with self.assertRaises(TypeError):
            parse_duration(90)
        with self.assertRaises(TypeError):
            parse_duration(None)
        with self.assertRaises(TypeError):
            parse_duration([])

    def test_return_type_is_float_for_all_valid_inputs(self):
        valid_inputs = [
            '90',
            '0',
            '0s',
            '2d',
            '3h',
            '15m',
            '45s',
            '500ms',
            '1h30m',
            '2d4h',
            '1m1s',
            '1s500ms',
            '1d1h1m1s1ms',
            ' 1h 30m ',
            '\t2d\n',
        ]
        for text in valid_inputs:
            with self.subTest(text=text):
                result = parse_duration(text)
                self.assertIsInstance(result, float)
