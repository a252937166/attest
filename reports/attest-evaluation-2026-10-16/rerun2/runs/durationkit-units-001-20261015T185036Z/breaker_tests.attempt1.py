import unittest
from durationkit import parse_duration

class TestParseDurationBreaker(unittest.TestCase):
    def test_leading_plus_sign_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("+90")

    def test_embedded_space_in_plain_integer_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("9 0")

    def test_whitespace_between_number_and_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")

    def test_multiple_whitespace_between_components_allowed(self):
        self.assertEqual(parse_duration("1h   30m"), 5400.0)

    def test_zero_components_all_units(self):
        self.assertEqual(parse_duration("0d0h0m0s0ms"), 0.0)

    def test_repeated_unit_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration("1h 2h")

    def test_out_of_order_with_whitespace(self):
        with self.assertRaises(ValueError):
            parse_duration("30m 1h")

    def test_unit_ms_must_be_exact_two_letters_no_space(self):
        with self.assertRaises(ValueError):
            parse_duration("1m s")
        self.assertEqual(parse_duration("1ms"), 0.001)

    def test_fractional_number_with_dot_but_no_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5")

    def test_large_number_returns_float(self):
        result = parse_duration("1000000")
        self.assertIsInstance(result, float)
        self.assertEqual(result, 1000000.0)

    def test_uppercase_unit_unknown(self):
        with self.assertRaises(ValueError):
            parse_duration("1H")

    def test_mixed_invalid_chars(self):
        with self.assertRaises(ValueError):
            parse_duration("1h!")
