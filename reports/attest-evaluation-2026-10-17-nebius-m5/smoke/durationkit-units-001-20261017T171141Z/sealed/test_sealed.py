import unittest
from durationkit import parse_duration

class TestParseDurationExtended(unittest.TestCase):
    def test_plain_integer_with_whitespace(self):
        self.assertEqual(parse_duration("  42 "), 42.0)
    def test_zero_and_zero_seconds_unit(self):
        self.assertEqual(parse_duration("0"), 0.0)
        self.assertEqual(parse_duration("0s"), 0.0)
    def test_single_components_all_units(self):
        self.assertEqual(parse_duration("2d"), 172800.0)
        self.assertEqual(parse_duration("3h"), 10800.0)
        self.assertEqual(parse_duration("15m"), 900.0)
        self.assertEqual(parse_duration("45s"), 45.0)
        self.assertEqual(parse_duration("500ms"), 0.5)
    def test_combined_descending_order(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)
        self.assertEqual(parse_duration("2d4h"), 187200.0)
        self.assertEqual(parse_duration("1m1s"), 61.0)
        self.assertEqual(parse_duration("1s500ms"), 1.5)
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061.001)
    def test_whitespace_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)
    def test_whitespace_number_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")
    def test_return_type_is_float(self):
        self.assertIsInstance(parse_duration("90"), float)
        self.assertIsInstance(parse_duration("1h"), float)
    def test_empty_and_whitespace_only_strings(self):
        with self.assertRaises(ValueError):
            parse_duration("")
        with self.assertRaises(ValueError):
            parse_duration("   ")
    def test_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")
    def test_fractional_number(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")
    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")
    def test_repeated_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")
    def test_out_of_order_components(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")
    def test_unit_without_number(self):
        with self.assertRaises(ValueError):
            parse_duration("h")
    def test_number_without_unit_in_multi_component(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")
    def test_malformed_text(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")
    def test_non_string_input_type_error(self):
        with self.assertRaises(TypeError):
            parse_duration(90)
        with self.assertRaises(TypeError):
            parse_duration(None)
