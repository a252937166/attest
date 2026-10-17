import unittest
from durationkit import parse_duration

class TestBreaker(unittest.TestCase):
    def test_large_numbers(self):
        self.assertEqual(parse_duration('999999999999'), 999999999999.0)
        self.assertEqual(parse_duration('999999d'), 999999 * 86400.0)
    def test_leading_zeros(self):
        self.assertEqual(parse_duration('001'), 1.0)
        self.assertEqual(parse_duration('000h'), 0.0)
    def test_mixed_whitespace_types(self):
        self.assertEqual(parse_duration('\t1h\n30m '), 5400.0)
    def test_trailing_whitespace_only_after_number_unit(self):
        self.assertEqual(parse_duration('1h '), 3600.0)
    def test_ms_fraction_sum(self):
        self.assertAlmostEqual(parse_duration('1s500ms'), 1.5)
    def test_zero_with_units_all(self):
        self.assertEqual(parse_duration('0d0h0m0s0ms'), 0.0)
    def test_repeated_unit_not_adjacent(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30m1h')
    def test_unit_order_violation_equal(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')
    def test_empty_after_strip_raises(self):
        with self.assertRaises(ValueError):
            parse_duration('   ')
    def test_non_string_types(self):
        for val in [None, 90, 90.0, b'90']:
            with self.assertRaises(TypeError):
                parse_duration(val)
