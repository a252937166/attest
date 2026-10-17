import unittest

from durationkit import parse_duration


class HeldOut(unittest.TestCase):
    def test_plain_seconds_preserved(self):
        self.assertEqual(parse_duration("90"), 90.0)
        self.assertEqual(parse_duration(" 90 "), 90.0)
        self.assertEqual(parse_duration("0"), 0.0)

    def test_single_units(self):
        self.assertEqual(parse_duration("2d"), 172800.0)
        self.assertEqual(parse_duration("3h"), 10800.0)
        self.assertEqual(parse_duration("15m"), 900.0)
        self.assertEqual(parse_duration("45s"), 45.0)
        self.assertEqual(parse_duration("500ms"), 0.5)
        self.assertEqual(parse_duration("0s"), 0.0)

    def test_combined_descending(self):
        self.assertEqual(parse_duration("1h30m"), 5400.0)
        self.assertEqual(parse_duration("2d4h"), 187200.0)
        self.assertEqual(parse_duration("1m1s"), 61.0)
        self.assertEqual(parse_duration("1s500ms"), 1.5)
        self.assertAlmostEqual(parse_duration("1d1h1m1s1ms"), 90061.001)

    def test_whitespace_between_components(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400.0)

    def test_returns_float(self):
        self.assertIsInstance(parse_duration("90"), float)
        self.assertIsInstance(parse_duration("1h"), float)

    def test_valueerror_cases(self):
        for bad in ("", "   ", "-1h", "1.5h", "1x", "1h1h", "30m1h", "h", "1h30", "abc", "1 h"):
            with self.assertRaises(ValueError):
                parse_duration(bad)

    def test_typeerror_cases(self):
        for bad in (90, None, 1.5, ["1h"]):
            with self.assertRaises(TypeError):
                parse_duration(bad)


if __name__ == "__main__":
    unittest.main()
