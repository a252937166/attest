import unittest
from durationkit import parse_duration

class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_plain_integer_no_whitespace(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_plain_integer_with_surrounding_whitespace(self):
        self.assertEqual(parse_duration("  42 "), 42.0)

    def test_zero_plain(self):
        self.assertEqual(parse_duration("0"), 0.0)

    def test_zero_with_s_unit(self):
        self.assertEqual(parse_duration("0s"), 0.0)

    def test_return_type_is_float_for_plain(self):
        self.assertIsInstance(parse_duration("7"), float)

    def test_empty_string_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_whitespace_only_string_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_non_string_int_raises_TypeError(self):
        with self.assertRaises(TypeError):
            parse_duration(90)

    def test_none_raises_TypeError(self):
        with self.assertRaises(TypeError):
            parse_duration(None)

    def test_single_component_d(self):
        self.assertEqual(parse_duration("2d"), 172800.0)

    def test_single_component_h(self):
        self.assertEqual(parse_duration("3h"), 10800.0)

    def test_single_component_m(self):
        self.assertEqual(parse_duration("15m"), 900.0)

    def test_single_component_s(self):
        self.assertEqual(parse_duration("45s"), 45.0)

    def test_single_component_ms(self):
        self.assertAlmostEqual(parse_duration("500ms"), 0.5)

    def test_combined_1h30m(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)

    def test_combined_2d4h(self):
        self.assertEqual(parse_duration("2d4h"), 187200.0)

    def test_combined_1m1s(self):
        self.assertEqual(parse_duration("1m1s"), 61.0)

    def test_combined_1s500ms(self):
        self.assertAlmostEqual(parse_duration("1s500ms"), 1.5)

    def test_combined_1d1h1m1s1ms(self):
        self.assertAlmostEqual(parse_duration("1d1h1m1s1ms"), 90061.001)

    def test_whitespace_around_and_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)

    def test_whitespace_between_number_and_unit_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")

    def test_negative_number_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")

    def test_fractional_number_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")

    def test_unknown_unit_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")

    def test_repeated_unit_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")

    def test_out_of_order_units_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")

    def test_unit_without_number_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("h")

    def test_number_without_unit_in_multi_component_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")

    def test_other_malformed_text_raises_ValueError(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")
