import unittest
from roman import to_roman, is_roman_numeral


class TestToRoman(unittest.TestCase):
    def test_to_roman_1(self):
        self.assertEqual(to_roman(1), "I")

    def test_to_roman_4(self):
        self.assertEqual(to_roman(4), "IV")

    def test_to_roman_9(self):
        self.assertEqual(to_roman(9), "IX")

    def test_to_roman_40(self):
        self.assertEqual(to_roman(40), "XL")

    def test_to_roman_90(self):
        self.assertEqual(to_roman(90), "XC")

    def test_to_roman_400(self):
        self.assertEqual(to_roman(400), "CD")

    def test_to_roman_900(self):
        self.assertEqual(to_roman(900), "CM")

    def test_to_roman_2024(self):
        self.assertEqual(to_roman(2024), "MMXXIV")

    def test_to_roman_3999(self):
        self.assertEqual(to_roman(3999), "MMMCMXCIX")

    def test_to_roman_1994(self):
        self.assertEqual(to_roman(1994), "MCMXCIV")

    def test_to_roman_return_type(self):
        for n in (1, 4, 9, 40, 90, 400, 900, 2024, 3999, 1994):
            with self.subTest(n=n):
                self.assertIsInstance(to_roman(n), str)

    def test_to_roman_value_error_out_of_range(self):
        for n in (0, -1, 4000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_to_roman_type_error_non_int(self):
        for val in ("5", 5.0, None, [1], True):
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    to_roman(val)


class TestIsRomanNumeral(unittest.TestCase):
    def test_is_roman_numeral_true(self):
        self.assertTrue(is_roman_numeral("XIV"))
        self.assertTrue(is_roman_numeral("mmxxiv"))

    def test_is_roman_numeral_false(self):
        self.assertFalse(is_roman_numeral(""))
        self.assertFalse(is_roman_numeral("ABC"))
        self.assertFalse(is_roman_numeral(14))
