import unittest
from durationkit import parse_duration

class TestParseDurationAcceptance(unittest.TestCase):
    def test_plain_integer_seconds(self):
        self.assertEqual(parse_duration('90'), 90.0)
    def test_zero_and_zero_s(self):
        self.assertEqual(parse_duration('0'), 0.0)
        self.assertEqual(parse_duration('0s'), 0.0)
    def test_surrounding_whitespace_ignored(self):
        self.assertEqual(parse_duration('  42 '), 42.0)
    def test_returns_float_for_int(self):
        self.assertIsInstance(parse_duration('7'), float)
    def test_single_components_all_units(self):
        self.assertEqual(parse_duration('2d'), 172800.0)
        self.assertEqual(parse_duration('3h'), 10800.0)
        self.assertEqual(parse_duration('15m'), 900.0)
        self.assertEqual(parse_duration('45s'), 45.0)
        self.assertEqual(parse_duration('500ms'), 0.5)
    def test_combined_descending_order(self):
        self.assertEqual(parse_duration('1h30m'), 5400.0)
        self.assertEqual(parse_duration('2d4h'), 187200.0)
        self.assertEqual(parse_duration('1m1s'), 61.0)
        self.assertEqual(parse_duration('1s500ms'), 1.5)
        self.assertEqual(parse_duration('1d1h1m1s1ms'), 90061.001)
    def test_whitespace_between_components(self):
        self.assertEqual(parse_duration(' 1h 30m '), 5400.0)
    def test_space_between_number_and_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1 h')
    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('')
    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('   ')
    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('-1h')
    def test_fractional_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')
    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')
    def test_repeated_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')
    def test_out_of_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')
    def test_unit_without_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('h')
    def test_number_without_unit_multi_component_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30')
    def test_malformed_text_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')
    def test_non_string_input_type_error(self):
        with self.assertRaises(TypeError):
            parse_duration(90)
        with self.assertRaises(TypeError):
            parse_duration(None)
    def test_return_type_is_float_for_all_valid(self):
        for inp in ['90', '0', '  42 ', '2d', '3h', '15m', '45s', '500ms', '1h30m', '2d4h']:
            self.assertIsInstance(parse_duration(inp), float)
