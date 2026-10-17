import unittest
from durationkit import parse_duration

class TestParseDurationBreaker(unittest.TestCase):
    def test_plus_sign_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("+5")
        with self.assertRaises(ValueError):
            parse_duration(" +5 ")
        with self.assertRaises(ValueError):
            parse_duration("+0")

    def test_leading_zeros_plain_integer(self):
        self.assertEqual(parse_duration("00123"), 123.0)
        self.assertEqual(parse_duration("000"), 0.0)
        self.assertEqual(parse_duration("0000"), 0.0)

    def test_multiple_spaces_between_components_allowed(self):
        self.assertEqual(parse_duration("1h   30m"), 5400.0)
        self.assertEqual(parse_duration("2d    4h"), 187200.0)
        self.assertEqual(parse_duration("1m      1s"), 61.0)

    def test_tab_and_newline_between_components_allowed(self):
        self.assertEqual(parse_duration("1h\t30m"), 5400.0)
        self.assertEqual(parse_duration("2d\n4h"), 187200.0)
        self.assertEqual(parse_duration("1m\v1s"), 61.0)
        self.assertEqual(parse_duration("1s\x0c500ms"), 1.5)

    def test_skipping_units_allowed(self):
        self.assertEqual(parse_duration("1d3s"), 86400.0 + 3.0)
        self.assertEqual(parse_duration("2h5ms"), 2*3600.0 + 5*0.001)
        self.assertEqual(parse_duration("1d5s"), 86400.0 + 5.0)
        self.assertEqual(parse_duration("1h20s"), 3600.0 + 20.0)

    def test_zero_values_in_components(self):
        self.assertEqual(parse_duration("1d0h0m0s5ms"), 86400.0 + 0.005)
        self.assertEqual(parse_duration("0d0h0m0s0ms"), 0.0)
        self.assertEqual(parse_duration("0d5h0m0s0ms"), 5*3600.0)

    def test_duplicate_unit_zero_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("0d0d")
        with self.assertRaises(ValueError):
            parse_duration("0h0h")
        with self.assertRaises(ValueError):
            parse_duration("0m0m")
        with self.assertRaises(ValueError):
            parse_duration("0s0s")
        with self.assertRaises(ValueError):
            parse_duration("0ms0ms")

    def test_large_number_days(self):
        big = 10**6
        expected = big * 86400.0
        self.assertEqual(parse_duration(f"{big}d"), expected)

    def test_ms_at_end_with_small_fraction(self):
        self.assertEqual(parse_duration("1s5ms"), 1.0 + 5*0.001)
        self.assertEqual(parse_duration("2s1ms"), 2.0 + 0.001)
        self.assertEqual(parse_duration("0s1ms"), 0.001)

    def test_space_between_number_and_unit_multiple_rejected(self):
        for s in ("1h  30m", "2d   4h", "1m    1s", "5s   500ms"):
            with self.assertRaises(ValueError):
                parse_duration(s)

    def test_trailing_number_without_unit_variants(self):
        for s in ("1h2", "30m45", "1s5", "500ms1", "1d2h3m4s5"):
            with self.assertRaises(ValueError):
                parse_duration(s)

    def test_non_string_types_typeerror(self):
        for val in (1.2, True, [1,2], {"a":1}, b"bytes"):
            with self.assertRaises(TypeError):
                parse_duration(val)
