import unittest
from durationkit import parse_duration

class TestParseDurationBreaker(unittest.TestCase):
    def test_plain_integer_with_leading_zeros(self):
        self.assertEqual(parse_duration('001'), 1.0)
        self.assertEqual(parse_duration('  0005  '), 5.0)

    def test_multiple_whitespace_between_components(self):
        self.assertEqual(parse_duration('1h   30m'), 5400.0)
        self.assertEqual(parse_duration('2d\t4h'), 187200.0)  # tab

    def test_whitespace_characters_variety(self):
        self.assertEqual(parse_duration('\n1h\t30m\n'), 5400.0)
        self.assertEqual(parse_duration('\r\n 2d 4h \r\n'), 187200.0)

    def test_unit_without_number_in_multicomponent(self):
        with self.assertRaises(ValueError):
            parse_duration('1h m')
        with self.assertRaises(ValueError):
            parse_duration('2d   s')

    def test_number_without_unit_in_multicomponent_with_space(self):
        with self.assertRaises(ValueError):
            parse_duration('1h 30')
        with self.assertRaises(ValueError):
            parse_duration('2d   4')

    def test_repeated_unit_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration('1h 1h')
        with self.assertRaises(ValueError):
            parse_duration('2d\t2d')

    def test_out_of_order_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration('30m 1h')
        with self.assertRaises(ValueError):
            parse_duration('45s\t2m')

    def test_unknown_unit_variants(self):
        with self.assertRaises(ValueError):
            parse_duration('1msx')
        with self.assertRaises(ValueError):
            parse_duration('1dxx')

    def test_negative_number_with_space_after_sign(self):
        with self.assertRaises(ValueError):
            parse_duration('- 1h')
        with self.assertRaises(ValueError):
            parse_duration('+2h')  # plus sign not allowed

    def test_large_number_still_returns_float(self):
        # Large but within float range
        self.assertEqual(parse_duration('1000000'), 1000000.0)
        # Very large that becomes inf? We'll avoid overflow.

    def test_skip_units(self):
        self.assertEqual(parse_duration('1d2s'), 86400.0 + 2.0)
        self.assertEqual(parse_duration('2h5ms'), 7200.0 + 0.005)

    def test_return_type_is_always_float(self):
        self.assertIsInstance(parse_duration('1h30m'), float)
        self.assertIsInstance(parse_duration('0'), float)
