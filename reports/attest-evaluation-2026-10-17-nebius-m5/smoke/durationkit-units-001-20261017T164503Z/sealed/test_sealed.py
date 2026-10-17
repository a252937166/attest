import unittest
from durationkit import parse_duration

class TestParseDurationSealedAcceptance(unittest.TestCase):
    def test_existing_behavior_plain_integer_seconds(self):
        self.assertEqual(parse_duration("90"), 90.0)
    
    def test_existing_behavior_zero(self):
        self.assertEqual(parse_duration("0"), 0.0)
    
    def test_existing_behavior_surrounding_whitespace_ignored(self):
        self.assertEqual(parse_duration("  42 "), 42.0)
    
    def test_existing_behavior_returns_float(self):
        self.assertIsInstance(parse_duration("7"), float)
    
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
    
    def test_combined_components_days_hours(self):
        self.assertEqual(parse_duration("2d4h"), 187200.0)
    
    def test_combined_components_minutes_seconds(self):
        self.assertEqual(parse_duration("1m1s"), 61.0)
    
    def test_combined_components_seconds_milliseconds(self):
        self.assertEqual(parse_duration("1s500ms"), 1.5)
    
    def test_combined_components_all_units(self):
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061.001)
    
    def test_whitespace_around_and_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)
    
    def test_value_error_empty_string(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_whitespace_only(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("   ")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_negative_number(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("-1h")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_fractional_number(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1.5h")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_unknown_unit(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1x")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_repeated_unit(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1h1h")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_out_of_order_components(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("30m1h")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_unit_without_number(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("h")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_number_without_unit_in_multi_component(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("1h30")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_value_error_other_malformed_text(self):
        with self.assertRaises(ValueError) as cm:
            parse_duration("abc")
        self.assertIn("unsupported duration", str(cm.exception))
    
    def test_type_error_non_string_input(self):
        with self.assertRaises(TypeError) as cm:
            parse_duration(90)
        self.assertEqual(str(cm.exception), "duration must be a string")
    
    def test_type_error_none_input(self):
        with self.assertRaises(TypeError) as cm:
            parse_duration(None)
        self.assertEqual(str(cm.exception), "duration must be a string")
    
    def test_return_type_is_float_for_all_accepted_inputs(self):
        test_cases = ["90", "0", "2d", "3h", "15m", "45s", "500ms", "1h30m", "2d4h", "1m1s", "1s500ms", "1d1h1m1s1ms", " 1h 30m "]
        for case in test_cases:
            with self.subTest(case=case):
                self.assertIsInstance(parse_duration(case), float)
