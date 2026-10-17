import unittest
from durationkit import parse_duration

class TestParseDurationSealed(unittest.TestCase):
    def test_plain_integer_seconds_preserved(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_plain_integer_with_surrounding_whitespace_ignored(self):
        self.assertEqual(parse_duration("  42 "), 42.0)

    def test_zero_plain(self):
        self.assertEqual(parse_duration("0"), 0.0)

    def test_zero_with_seconds_unit(self):
        self.assertEqual(parse_duration("0s"), 0.0)

    def test_single_component_days(self):
        self.assertEqual(parse_duration("2d"), 2 * 86400.0)

    def test_single_component_hours(self):
        self.assertEqual(parse_duration("3h"), 3 * 3600.0)

    def test_single_component_minutes(self):
        self.assertEqual(parse_duration("15m"), 15 * 60.0)

    def test_single_component_seconds(self):
        self.assertEqual(parse_duration("45s"), 45.0)

    def test_single_component_milliseconds(self):
        self.assertEqual(parse_duration("500ms"), 0.5)

    def test_combined_1h30m(self):
        self.assertAlmostEqual(parse_duration("1h30m"), 5400.0)

    def test_combined_2d4h(self):
        self.assertAlmostEqual(parse_duration("2d4h"), 187200.0)

    def test_combined_1m1s(self):
        self.assertAlmostEqual(parse_duration("1m1s"), 61.0)

    def test_combined_1s500ms(self):
        self.assertAlmostEqual(parse_duration("1s500ms"), 1.5)

    def test_combined_1d1h1m1s1ms(self):
        self.assertAlmostEqual(parse_duration("1d1h1m1s1ms"), 90061.001)

    def test_whitespace_allowed_around_and_between_components(self):
        self.assertAlmostEqual(parse_duration(" 1h 30m "), 5400.0)

    def test_whitespace_between_number_and_unit_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")

    def test_error_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_error_whitespace_only_string(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_error_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")

    def test_error_fractional_number(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_error_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_error_repeated_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_error_out_of_order_units(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_error_missing_number_before_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_error_number_without_unit_in_component_form(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_error_other_malformed_text(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_type_error_for_non_string_input_int(self):
        with self.assertRaises(TypeError):
            parse_duration(90)

    def test_type_error_for_non_string_input_none(self):
        with self.assertRaises(TypeError):
            parse_duration(None)

    def test_return_type_is_float_for_plain_integer(self):
        self.assertIsInstance(parse_duration("90"), float)

    def test_return_type_is_float_for_zero_with_unit(self):
        self.assertIsInstance(parse_duration("0s"), float)

    def test_return_type_is_float_for_days(self):
        self.assertIsInstance(parse_duration("2d"), float)

    def test_return_type_is_float_for_combined(self):
        self.assertIsInstance(parse_duration("1h30m"), float)