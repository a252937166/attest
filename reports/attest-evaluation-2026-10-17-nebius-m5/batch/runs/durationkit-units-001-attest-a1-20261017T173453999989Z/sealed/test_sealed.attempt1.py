import unittest
from durationkit import parse_duration

class ParseDurationExistingBehaviour(unittest.TestCase):
    def test_plain_integer_is_seconds(self):
        self.assertEqual(parse_duration("90"), 90.0)
    def test_zero(self):
        self.assertEqual(parse_duration("0"), 0.0)
        self.assertEqual(parse_duration("0s"), 0.0)
    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(parse_duration("  42 "), 42.0)
    def test_returns_float(self):
        self.assertIsInstance(parse_duration("7"), float)
    def test_empty_string_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("")
    def test_whitespace_only_string_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")
    def test_non_string_is_rejected(self):
        with self.assertRaises(TypeError):
            parse_duration(90)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            parse_duration(None)  # type: ignore[arg-type]

class ParseDurationExtendedBehaviour(unittest.TestCase):
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
    def test_two_components_descending_order(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)
        self.assertEqual(parse_duration("2d4h"), 187200.0)
        self.assertEqual(parse_duration("1m1s"), 61.0)
        self.assertEqual(parse_duration("1s500ms"), 1.5)
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 90061.001)
    def test_whitespace_allowed_around_and_between(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)
        self.assertEqual(parse_duration(" 2d   4h "), 187200.0)
    def test_space_between_number_and_unit_is_error(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")
        with self.assertRaises(ValueError):
            parse_duration("2d 3h")
    def test_negative_number_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")
        with self.assertRaises(ValueError):
            parse_duration("-5s")
    def test_fractional_number_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")
        with self.assertRaises(ValueError):
            parse_duration("2.0s")
    def test_unknown_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")
        with self.assertRaises(ValueError):
            parse_duration("2y")
    def test_repeated_unit_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")
        with self.assertRaises(ValueError):
            parse_duration("2d3d")
    def test_units_out_of_order_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")
        with self.assertRaises(ValueError):
            parse_duration("5s1m")
    def test_unit_without_number_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("h")
        with self.assertRaises(ValueError):
            parse_duration("ms")
    def test_number_without_unit_in_multi_component_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")
        with self.assertRaises(ValueError):
            parse_duration("2d5")
    def test_completely_malformed_text_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")
        with self.assertRaises(ValueError):
            parse_duration("XII")
        with self.assertRaises(ValueError):
            parse_duration("١٢٣")  # non‑ASCII digits
    def test_return_type_is_float_for_all_valid_inputs(self):
        valid = ["90", "0", "0s", "2d", "3h", "15m", "45s", "500ms",
                 "1h30m", "2d4h", "1m1s", "1s500ms", "1d1h1m1s1ms"]
        for v in valid:
            with self.subTest(v=v):
                self.assertIsInstance(parse_duration(v), float)

test_count = 20
notes = "Cover all acceptance criteria; each test focuses on one behavior."
}