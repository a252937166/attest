import unittest
from roman import to_roman, is_roman_numeral

class TestToRoman(unittest.TestCase):
    def test_one(self):
        self.assertEqual(to_roman(1), "I")

    def test_four(self):
        self.assertEqual(to_roman(4), "IV")

    def test_nine(self):
        self.assertEqual(to_roman(9), "IX")

    def test_forty(self):
        self.assertEqual(to_roman(40), "XL")

    def test_ninety(self):
        self.assertEqual(to_roman(90), "XC")

    def test_four_hundred(self):
        self.assertEqual(to_roman(400), "CD")

    def test_nine_hundred(self):
        self.assertEqual(to_roman(900), "CM")

    def test_2024(self):
        self.assertEqual(to_roman(2024), "MMXXIV")

    def test_3999(self):
        self.assertEqual(to_roman(3999), "MMMCMXCIX")

    def test_1994(self):
        self.assertEqual(to_roman(1994), "MCMXCIV")

    def test_return_type_is_str(self):
        self.assertIsInstance(to_roman(5), str)

    def test_value_error_zero(self):
        with self.assertRaises(ValueError) as cm:
            to_roman(0)
        self.assertIsInstance(cm.exception, ValueError)

    def test_value_error_negative(self):
        with self.assertRaises(ValueError) as cm:
            to_roman(-1)
        self.assertIsInstance(cm.exception, ValueError)

    def test_value_error_out_of_range_high(self):
        with self.assertRaises(ValueError) as cm:
            to_roman(4000)
        self.assertIsInstance(cm.exception, ValueError)

    def test_type_error_string(self):
        with self.assertRaises(TypeError) as cm:
            to_roman("5")
        self.assertIsInstance(cm.exception, TypeError)

    def test_type_error_float(self):
        with self.assertRaises(TypeError) as cm:
            to_roman(5.0)
        self.assertIsInstance(cm.exception, TypeError)

    def test_type_error_none(self):
        with self.assertRaises(TypeError) as cm:
            to_roman(None)
        self.assertIsInstance(cm.exception, TypeError)

    def test_type_error_list(self):
        with self.assertRaises(TypeError) as cm:
            to_roman([1])
        self.assertIsInstance(cm.exception, TypeError)

    def test_type_error_bool(self):
        with self.assertRaises(TypeError) as cm:
            to_roman(True)
        self.assertIsInstance(cm.exception, TypeError)

class TestIsRomanNumeral(unittest.TestCase):
    def test_true(self):
        self.assertTrue(is_roman_numeral("XIV"))
        self.assertTrue(is_roman_numeral("mmxxiv"))

    def test_false(self):
        self.assertFalse(is_roman_numeral(""))
        self.assertFalse(is_roman_numeral("ABC"))
        self.assertFalse(is_roman_numeral(14))
