import unittest
from roman import to_roman


class HeldOut(unittest.TestCase):
    def test_units(self):
        for n, r in [(1, "I"), (2, "II"), (3, "III"), (4, "IV"), (5, "V"), (9, "IX")]:
            self.assertEqual(to_roman(n), r)

    def test_tens_and_subtractive(self):
        for n, r in [(10, "X"), (40, "XL"), (49, "XLIX"), (90, "XC"), (99, "XCIX")]:
            self.assertEqual(to_roman(n), r)

    def test_hundreds_thousands(self):
        for n, r in [(400, "CD"), (900, "CM"), (1000, "M"), (2024, "MMXXIV"), (3999, "MMMCMXCIX"), (1994, "MCMXCIV")]:
            self.assertEqual(to_roman(n), r)

    def test_returns_str(self):
        self.assertIsInstance(to_roman(1), str)

    def test_out_of_range_raises_valueerror(self):
        for bad in (0, -1, 4000, 10000):
            with self.assertRaises(ValueError):
                to_roman(bad)

    def test_non_int_raises_typeerror(self):
        for bad in ("5", 5.0, None, [1]):
            with self.assertRaises(TypeError):
                to_roman(bad)
