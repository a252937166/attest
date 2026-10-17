import unittest
from durationkit import parse_duration


class TestParseDurationExtended(unittest.TestCase):
    def test_plain_integer_seconds_with_whitespace(self):
        self.assertEqual(parse_duration("  90 "), 90.0)

    def test_single_component_days(self):
        self.assertEqual(parse_duration("2d"), 172800.0)

    def test_single_component_hours(self):
        self.assertEqual(parse_duration("3h"), 10800.0)

    def test_single_component_minutes(self):
        self.assertEqual(parse_duration("15m"), 900.0)

    def test_single_component_seconds(self):
        self.assertEqual(parse_duration("45s"), 45.0)

    def test_single_component_milliseconds(self):
        self.assertEqual(parse_duration("500ms"), 0.5)

    def test_combined_1h30m(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)

    def test_combined_2d4h(self):
        self.assertEqual(parse_duration("2d4h"), 187200.0)

    def test_combined_1m1s(self):
        self.assertEqual(parse_duration("1m1s"), 61.0)

    def test_combined_1s500ms(self):
        self.assertEqual(parse_duration("1s500ms"), 1.5)

    def test_combined_1d1h1m1s1ms(self):
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061.001)

    def test_whitespace_around_string(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)

    def test_whitespace_between_components(self):
        self.assertEqual(parse_duration("1h 30m"), 5400.0)

    def test_zero_plain(self):
        self.assertEqual(parse_duration("0"), 0.0)

    def test_zero_with_units(self):
        self.assertEqual(parse_duration("0s"), 0.0)

    def test_type_error_non_string(self):
        with self.assertRaises(TypeError):
            parse_duration(90)  # type: ignore[arg-type]

    def test_return_type_is_float(self):
        self.assertIsInstance(parse_duration("7"), float)

    def test_value_error_empty(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_value_error_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_value_error_negative(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")

    def test_value_error_fractional(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_value_error_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_value_error_duplicate_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_value_error_wrong_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_value_error_missing_number(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_value_error_number_without_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_value_error_whitespace_between_number_and_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")

    def test_value_error_other_malformed(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

