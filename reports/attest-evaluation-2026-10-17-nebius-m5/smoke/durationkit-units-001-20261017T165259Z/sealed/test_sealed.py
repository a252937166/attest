import unittest
from durationkit import parse_duration

class TestParseDurationSealed(unittest.TestCase):
    def test_plain_integer_preserved(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_plain_integer_with_surrounding_whitespace_ignored(self):
        self.assertEqual(parse_duration("  42 "), 42.0)

    def test_zero_and_zero_seconds_component(self):
        self.assertEqual(parse_duration("0"), 0.0)
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

    def test_combined_components_descending_order(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)
        self.assertEqual(parse_duration("2d4h"), 187200.0)
        self.assertEqual(parse_duration("1m1s"), 61.0)
        self.assertEqual(parse_duration("1s500ms"), 1.5)
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061.001)

    def test_whitespace_allowed_around_and_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)

    def test_whitespace_between_number_and_unit_is_rejected(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1 h")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_return_type_is_float_for_various_inputs(self):
        self.assertIsInstance(parse_duration("7"), float)
        self.assertIsInstance(parse_duration("1h"), float)
        self.assertIsInstance(parse_duration("0s"), float)
        self.assertIsInstance(parse_duration("1d1h1m1s1ms"), float)

    def test_empty_string_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_whitespace_only_string_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("   ")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_negative_number_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("-1h")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_fractional_number_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1.5h")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_unknown_unit_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1x")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_repeated_unit_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1h1h")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_components_out_of_descending_order_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("30m1h")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_unit_without_preceding_number_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("h")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_number_without_unit_when_other_components_have_units_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1h30")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_completely_malformed_text_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("abc")
        self.assertIn("unsupported duration", str(cm.exception))

    def test_non_string_input_raises_type_error(self):
        with self.assertRaises(TypeError) as cm:
            parse_duration(90)
        self.assertEqual(str(cm.exception), "duration must be a string")

    def test_none_input_raises_type_error(self):
        with self.assertRaises(TypeError) as cm:
            parse_duration(None)
        self.assertEqual(str(cm.exception), "duration must be a string")
