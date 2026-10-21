import unittest
from durationkit import parse_duration

class TestParseDurationSealed(unittest.TestCase):
    # AC1
    def test_ac1_plain_int_and_whitespace(self):
        self.assertEqual(parse_duration('90'), 90.0)
        self.assertEqual(parse_duration('  90  '), 90.0)
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
    # AC4
    def test_ac4_combined_descending(self):
        self.assertEqual(parse_duration('1h30m'), 5400.0)
        self.assertEqual(parse_duration('2d4h'), 187200.0)
        self.assertEqual(parse_duration('1m1s'), 61.0)
        self.assertEqual(parse_duration('1s500ms'), 1.5)
        self.assertEqual(parse_duration('1d1h1m1s1ms'), 90061.001)
    # AC5
    def test_ac5_whitespace_between_components(self):
        self.assertEqual(parse_duration(' 1h 30m '), 5400.0)
        with self.assertRaises(ValueError):
            parse_duration('1 h')
    # AC6 errors
    def test_ac6_error_cases(self):
        for bad in ['', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc']:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_duration(bad)
    # AC7
    def test_ac7_type_error_non_string(self):
        for val in [90, None, 3.14, []]:
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    parse_duration(val)
    # AC8
    def test_ac8_return_type_is_float(self):
        good_inputs = ['90', '0', '0s', '2d', '3h', '15m', '45s', '500ms', '1h30m', ' 1h 30m ']
        for inp in good_inputs:
            with self.subTest(inp=inp):
                self.assertIsInstance(parse_duration(inp), float)
    # AC9 – ensure existing tests still pass (we just run them via import?)
    # We'll call the existing test class methods to ensure they don't fail.
    def test_ac9_existing_tests_pass(self):
        from tests.test_parse import ParseDurationExistingBehaviour
        existing = ParseDurationExistingBehaviour()
        for meth in dir(existing):
            if meth.startswith('test_'):
                getattr(existing, meth)()

