import unittest
from durationkit import parse_duration

class TestParseDurationSealed(unittest.TestCase):
    # AC1
    def test_ac1_plain_integer_with_whitespace(self):
        self.assertEqual(parse_duration('90'), 90.0)
        self.assertEqual(parse_duration(' 90 '), 90.0)
        self.assertEqual(parse_duration('\t90\n'), 90.0)
    # AC2
    def test_ac2_zero_and_zero_unit(self):
        self.assertEqual(parse_duration('0'), 0.0)
        self.assertEqual(parse_duration('0s'), 0.0)
    # AC3
    def test_ac3_single_components(self):
        self.assertEqual(parse_duration('2d'), 172800.0)
        self.assertEqual(parse_duration('3h'), 10800.0)
        self.assertEqual(parse_duration('15m'), 900.0)
        self.assertEqual(parse_duration('45s'), 45.0)
        self.assertEqual(parse_duration('500ms'), 0.5)
    # AC4
    def test_ac4_combined_descending(self):
        self.assertEqual(parse_duration('1h30m'), 5400.0)
        self.assertEqual(parse_duration('2d4h'), 187200.0)
        self.assertEqual(parse_duration('1m1s'), 61.0)
        self.assertEqual(parse_duration('1s500ms'), 1.5)
        self.assertEqual(parse_duration('1d1h1m1s1ms'), 90061.001)
    # AC5
    def test_ac5_whitespace_allowed_between_components(self):
        self.assertEqual(parse_duration(' 1h 30m '), 5400.0)
        self.assertEqual(parse_duration('1h\t30m'), 5400.0)
        self.assertEqual(parse_duration('1h\n30m'), 5400.0)
        # space between number and unit invalid
        with self.assertRaises(ValueError):
            parse_duration('1 h')
        with self.assertRaises(ValueError):
            parse_duration('1h 30')
    # AC6
    def test_ac6_return_type_float(self):
        for inp in ['90', '0', '2d', '1h30m']:
            with self.subTest(inp=inp):
                self.assertIsInstance(parse_duration(inp), float)
    # AC7
    def test_ac7_empty_and_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration('')
        with self.assertRaises(ValueError):
            parse_duration('   ')
        with self.assertRaises(ValueError):
            parse_duration('\t\n')
    # AC8
    def test_ac8_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration('-1h')
        with self.assertRaises(ValueError):
            parse_duration('-5')
    # AC9
    def test_ac9_fractional_number(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')
        with self.assertRaises(ValueError):
            parse_duration('2.0s')
    # AC10
    def test_ac10_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')
        with self.assertRaises(ValueError):
            parse_duration('3h2y')
    # AC11
    def test_ac11_repeated_units(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')
        with self.assertRaises(ValueError):
            parse_duration('2d3d')
    # AC12
    def test_ac12_out_of_order(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')
        with self.assertRaises(ValueError):
            parse_duration('1s2d')
    # AC13
    def test_ac13_unit_without_number(self):
        with self.assertRaises(ValueError):
            parse_duration('h')
        with self.assertRaises(ValueError):
            parse_duration('dm')
    # AC14
    def test_ac14_number_without_unit_in_multi(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30')
        with self.assertRaises(ValueError):
            parse_duration('2d5')
    # AC15
    def test_ac15_completely_malformed(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')
        with self.assertRaises(ValueError):
            parse_duration('1h 2m 3z')
    # AC16
    def test_ac16_non_string_input(self):
        with self.assertRaises(TypeError):
            parse_duration(90)
        with self.assertRaises(TypeError):
            parse_duration(None)
        with self.assertRaises(TypeError):
            parse_duration([])
    # AC17 – ensure existing behaviour still works (run same assertions as original tests)
    def test_ac17_existing_behaviour_preserved(self):
        self.assertEqual(parse_duration('90'), 90.0)
        self.assertEqual(parse_duration('0'), 0.0)
        self.assertEqual(parse_duration('  42 '), 42.0)
        self.assertIsInstance(parse_duration('7'), float)
        with self.assertRaises(ValueError):
            parse_duration('')
        with self.assertRaises(TypeError):
            parse_duration(90)
