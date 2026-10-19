import unittest
from roman import to_roman

class TestToRoman(unittest.TestCase):
    def test_to_roman_1_returns_I(self):
        self.assertEqual(to_roman(1), "I")

    def test_to_roman_4_returns_IV(self):
        self.assertEqual(to_roman(4), "IV")

    def test_to_roman_9_returns_IX(self):
        self.assertEqual(to_roman(9), "IX")

    def test_to_roman_40_returns_XL(self):
        self.assertEqual(to_roman(40), "XL")

    def test_to_roman_90_returns_XC(self):
        self.assertEqual(to_roman(90), "XC")

    def test_to_roman_400_returns_CD(self):
        self.assertEqual(to_roman(400), "CD")

    def test_to_roman_900_returns_CM(self):
        self.assertEqual(to_roman(900), "CM")

    def test_to_roman_2024_returns_MMXXIV(self):
        self.assertEqual(to_roman(2024), "MMXXIV")

    def test_to_roman_3999_returns_MMMCMXCIX(self):
        self.assertEqual(to_roman(3999), "MMMCMXCIX")

    def test_to_roman_1994_returns_MCMXCIV(self):
        self.assertEqual(to_roman(1994), "MCMXCIV")

    def test_to_roman_returns_str_type(self):
        for n in (1, 2, 3, 10, 50, 100, 500, 1000, 3888):
            with self.subTest(n=n):
                result = to_roman(n)
                self.assertIsInstance(result, str)

    def test_to_roman_value_error_on_out_of_range_int(self):
        for n in (0, -1, -10, 4000, 4001, 5000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_to_roman_type_error_on_non_int_inputs(self):
        for n in ("5", 5.0, None, [1], {"a":1}, True, False, b"bytes"):
            with self.subTest(n=n):
                with self.assertRaises(TypeError):
                    to_roman(n)
