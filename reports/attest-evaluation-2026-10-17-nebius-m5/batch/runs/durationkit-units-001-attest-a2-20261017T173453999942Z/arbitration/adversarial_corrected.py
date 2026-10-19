import unittest
from durationkit import parse_duration

class TestBreakerParseDuration(unittest.TestCase):
    def test_leading_zero_plain_integer(self):
        self.assertEqual(parse_duration('00123'), 123.0)
    def test_mixed_whitespace_between_components(self):
        # Whitespace between components is allowed (space, tab, newline)
        self.assertEqual(parse_duration('1h 30m'), 5400.0)
        self.assertEqual(parse_duration('1h\t30m'), 5400.0)
        self.assertEqual(parse_duration('1h\n30m'), 5400.0)
        self.assertEqual(parse_duration('1h \t\n 30m'), 5400.0)
    def test_zero_components_all_units(self):
        self.assertEqual(parse_duration('0d0h0m0s0ms'), 0.0)
    def test_number_without_unit_in_multi_component_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration('1h 30')
    def test_unit_without_number_in_multi_component_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration('h 30m')
    def test_out_of_order_across_tokens(self):
        with self.assertRaises(ValueError):
            parse_duration('2h 1d')
    def test_repeated_unit_across_tokens(self):
        with self.assertRaises(ValueError):
            parse_duration('1h 2h')
    def test_unknown_unit_two_letter_not_ms(self):
        with self.assertRaises(ValueError):
            parse_duration('1ds')
    def test_fractional_with_leading_zero(self):
        with self.assertRaises(ValueError):
            parse_duration('0.5h')
    def test_negative_number_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration('- 1h')
    def test_empty_after_strip_but_not_original(self):
        with self.assertRaises(ValueError):
            parse_duration('   \t\n   ')
    def test_large_number_no_unit(self):
        self.assertEqual(parse_duration('9999999999'), 9999999999.0)
    def test_return_type_is_float_for_zero(self):
        self.assertIsInstance(parse_duration('0'), float)
