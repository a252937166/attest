import unittest
from durationkit import parse_duration

class TestParseDurationAcceptance(unittest.TestCase):
    def test_plain_integer_seconds_preserved(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_plain_integer_with_whitespace(self):
        self.assertEqual(parse_duration("  42 "), 42.0)

    def test_zero_plain_and_with_unit(self):
        self.assertEqual(parse_duration("0"), 0.0)
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

    def test_two_component_descending_various(self):
        self.assertEqual(parse_duration("1h30m"), 1*3600 + 30*60)
        self.assertEqual(parse_duration("2d4h"), 2*86400 + 4*3600)
        self.assertEqual(parse_duration("1m1s"), 1*60 + 1)
        self.assertEqual(parse_duration("1s500ms"), 1 + 0.5)

    def test_three_component_descending(self):
        self.assertEqual(parse_duration("1d2h3m"), 1*86400 + 2*3600 + 3*60)

    def test_four_component_descending(self):
        self.assertEqual(parse_duration("1d2h3m4s"), 1*86400 + 2*3600 + 3*60 + 4)

    def test_five_component_descending_all_units(self):
        self.assertEqual(parse_duration("1d1h1m1s1ms"), 1*86400 + 1*3600 + 1*60 + 1 + 0.001)

    def test_whitespace_around_string_and_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 1*3600 + 30*60)
        self.assertEqual(parse_duration("  2d   4h  "), 2*86400 + 4*3600)

    def test_whitespace_between_number_and_unit_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("1 h")
        with self.assertRaises(ValueError):
            parse_duration("2d 3h")
        with self.assertRaises(ValueError):
            parse_duration("45s ")

    def test_error_empty_string(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_error_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_duration("   ")
        with self.assertRaises(ValueError):
            parse_duration("\t\n")

    def test_error_negative_number(self):
        with self.assertRaises(ValueError):
            parse_duration("-1h")
        with self.assertRaises(ValueError):
            parse_duration("-5s")

    def test_error_fractional_number(self):
        with self.assertRaises(ValueError):
            parse_duration("1.5h")
        with self.assertRaises(ValueError):
            parse_duration("2.0s")
        with self.assertRaises(ValueError):
            parse_duration("0.5ms")

    def test_error_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1x")
        with self.assertRaises(ValueError):
            parse_duration("2y")

    def test_error_repeated_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("1h1h")
        with self.assertRaises(ValueError):
            parse_duration("2d3d")
        with self.assertRaises(ValueError):
            parse_duration("5s5s")

    def test_error_out_of_order(self):
        with self.assertRaises(ValueError):
            parse_duration("30m1h")
        with self.assertRaises(ValueError):
            parse_duration("45s2m")
        with self.assertRaises(ValueError):
            parse_duration("1ms2s")

    def test_error_missing_number_before_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("h")
        with self.assertRaises(ValueError):
            parse_duration("ms")
        with self.assertRaises(ValueError):
            parse_duration("d")

    def test_error_missing_unit_after_number_in_multi(self):
        with self.assertRaises(ValueError):
            parse_duration("1h30")
        with self.assertRaises(ValueError):
            parse_duration("2d5")
        with self.assertRaises(ValueError):
            parse_duration("3m45s10")

    def test_error_other_malformed(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")
        with self.assertRaises(ValueError):
            parse_duration("12ab")
        with self.assertRaises(ValueError):
            parse_duration("!!")

    def test_type_error_non_string(self):
        with self.assertRaises(TypeError):
            parse_duration(90)
        with self.assertRaises(TypeError):
            parse_duration(None)
        with self.assertRaises(TypeError):
            parse_duration(["1h"])

    def test_return_type_is_float_for_plain(self):
        self.assertIsInstance(parse_duration("7"), float)

    def test_return_type_is_float_for_single_component(self):
        self.assertIsInstance(parse_duration("2d"), float)
        self.assertIsInstance(parse_duration("500ms"), float)

    def test_return_type_is_float_for_combined(self):
        self.assertIsInstance(parse_duration("1h30m"), float)
        self.assertIsInstance(parse_duration("1d1h1m1s1ms"), float)
