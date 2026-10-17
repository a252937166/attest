import unittest

from durationkit import parse_duration


class ParseDurationExistingBehaviour(unittest.TestCase):
    def test_plain_integer_is_seconds(self):
        self.assertEqual(parse_duration("90"), 90.0)

    def test_zero(self):
        self.assertEqual(parse_duration("0"), 0.0)

    def test_surrounding_whitespace_is_ignored(self):
        self.assertEqual(parse_duration("  42 "), 42.0)

    def test_returns_float(self):
        self.assertIsInstance(parse_duration("7"), float)

    def test_empty_string_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_duration("")

    def test_non_string_is_rejected(self):
        with self.assertRaises(TypeError):
            parse_duration(90)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
