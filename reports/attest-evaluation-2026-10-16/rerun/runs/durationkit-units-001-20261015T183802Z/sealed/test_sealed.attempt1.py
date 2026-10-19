import unittest
from durationkit import parse_duration

class TestParseDurationExtended(unittest.TestCase):
    def test_plain_integer_seconds(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_plain_integer_with_whitespace(self):
        self.assertEqual(parse_duration("  42 "), 42.0)

    def test_zero_plain(self):
        self.assertEqual(parse_duration("0"), 0.0)

    def test_zero_with_unit(self):
        self.assertEqual(parse_duration("0s"), 0.0)

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

    def test_two_components_descending(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)

    def test_three_components_descending(self):
        self.assertEqual(parse_duration("2d4h"), 187200.0)

    def test_four_components_descending(self):
        self.assertEqual(parse_duration("1m1s"), 61.0)

    def test_five_components_descending(self):
        self.assertEqual(parse_duration("1s500ms"), 1.5)

    def test_all_components_descending(self):
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061.001)

    def test_whitespace_around_and_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)

    def test_whitespace_between_number_and_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")

    def test_duplicate_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_out_of_order_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_missing_number_before_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_number_without_unit_when_other_units_present_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_unknown_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_fractional_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_negative_number_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_whitespace_only_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_other_malformed_string_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_non_string_input_raises_TypeError(self):
        with self.assertRaises(TypeError):
            parse_duration(90)

    def test_return_type_is_float_for_valid_inputs(self):
        for inp in ["90", "  42 ", "0", "0s", "2d", "3h", "15m", "45s", "500ms", "1h30m", "2d4h", "1m1s", "1s500ms", "1d1h1m1s1ms", " 1h 30m "]:
            self.assertIsInstance(parse_duration(inp), float)
