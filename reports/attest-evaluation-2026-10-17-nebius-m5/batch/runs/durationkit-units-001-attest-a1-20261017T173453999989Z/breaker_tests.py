import unittest
from durationkit import parse_duration

class TestBreaker(unittest.TestCase):
    def test_whitespace_variants(self):
        self.assertEqual(parse_duration('\n 2h \t'), 7200.0)
        self.assertEqual(parse_duration('\r\f 45s \r\n'), 45.0)
    def test_uppercase_unit_rejected(self):
        for unit in ['D', 'H', 'M', 'S', 'MS']:
            with self.subTest(unit=unit):
                with self.assertRaises(ValueError):
                    parse_duration(f'1{unit}')
    def test_leading_zeros_allowed(self):
        self.assertEqual(parse_duration('001h02m003s004ms'), 3723.004)
    def test_invalid_character_in_number(self):
        with self.assertRaises(ValueError):
            parse_duration('12a3h')
        with self.assertRaises(ValueError):
            parse_duration('1h2b3m')
    def test_trailing_garbage_after_valid(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30m extra')
        with self.assertRaises(ValueError):
            parse_duration('45s\tfoo')
    def test_multiple_spaces_between_components(self):
        self.assertEqual(parse_duration('1h   30m   15s'), 5415.0)
    def test_ms_without_space_still_works(self):
        self.assertEqual(parse_duration('5ms'), 0.005)
        self.assertEqual(parse_duration('0ms'), 0.0)
    def test_empty_after_strip_raises(self):
        self.assertRaises(ValueError, parse_duration, '')
        self.assertRaises(ValueError, parse_duration, '   ')
        self.assertRaises(ValueError, parse_duration, '\t\n')
