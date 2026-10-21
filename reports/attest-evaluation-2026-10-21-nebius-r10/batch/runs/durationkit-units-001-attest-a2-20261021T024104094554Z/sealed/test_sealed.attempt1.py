import unittest
from durationkit import parse_duration

class TestParseDurationSealed(unittest.TestCase):
    # AC1
    def test_ac1_plain_int_with_whitespace(self):
        self.assertEqual(parse_duration('90'), 90.0)
        self.assertEqual(parse_duration(' 90 '), 90.0)
    # AC2
    def test_ac2_zero_variants(self):
        self.assertEqual(parse_duration('0'), 0.0)
        self.assertEqual(parse_duration('0s'), 0.0)
    # AC3
    def test_ac3_single_components(self):
        self.assertEqual(parse_duration('2d'), 172800.0)
        self.assertEqual(parse_duration('3h'), 10800.0)
        self.assertEqual(parse_duration('15m'), 900.0)
        self.assertEqual(parse_duration('45s'), 45.0)
        self.assertEqual(parse_duration('500ms'), 0.5)
    # AC4 combined
    def test_ac4_combined_descending(self):
        self.assertEqual(parse_duration('1h30m'), 5400.0)
        self.assertEqual(parse_duration('2d4h'), 187200.0)
        self.assertEqual(parse_duration('1m1s'), 61.0)
        self.assertEqual(parse_duration('1s500ms'), 1.5)
        self.assertEqual(parse_duration('1d1h1m1s1ms'), 90061.001)
    # AC5 whitespace rules
    def test_ac5_whitespace_between_and_around(self):
        self.assertEqual(parse_duration(' 1h 30m '), 5400.0)
        with self.assertRaises(ValueError):
            parse_duration('1 h')
    # AC6 return type always float
    def test_ac6_return_type_float(self):
        self.assertIsInstance(parse_duration('90'), float)
        self.assertIsInstance(parse_duration('1h'), float)
    # AC7 empty/whitespace-only
    def test_ac7_empty_and_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration('')
        with self.assertRaises(ValueError):
            parse_duration('   ')
    # AC8 negative numbers
    def test_ac8_negative_numbers(self):
        with self.assertRaises(ValueError):
            parse_duration('-1h')
    # AC9 fractional numbers
    def test_ac9_fractional_numbers(self):
        with self.assertRaises(ValueError):
            parse_duration('1.5h')
    # AC10 unknown unit
    def test_ac10_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1x')
    # AC11 repeated unit
    def test_ac11_repeated_unit(self):
        with self.assertRaises(ValueError):
            parse_duration('1h1h')
    # AC12 out of order
    def test_ac12_out_of_order(self):
        with self.assertRaises(ValueError):
            parse_duration('30m1h')
    # AC13 unit without number
    def test_ac13_unit_without_number(self):
        with self.assertRaises(ValueError):
            parse_duration('h')
    # AC14 number without unit when others have units
    def test_ac14_number_without_unit_mixed(self):
        with self.assertRaises(ValueError):
            parse_duration('1h30')
    # AC15 completely malformed
    def test_ac15_malformed_text(self):
        with self.assertRaises(ValueError):
            parse_duration('abc')
    # AC16 non-string input
    def test_ac16_non_string_input(self):
        with self.assertRaises(TypeError):
            parse_duration(90)
        with self.assertRaises(TypeError):
            parse_duration(None)
    # AC17 ensure existing tests still pass – we just rely on them; no extra needed.
