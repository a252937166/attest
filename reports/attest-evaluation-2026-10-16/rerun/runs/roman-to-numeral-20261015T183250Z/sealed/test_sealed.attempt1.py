import unittest
from roman import to_roman, is_roman_numeral

class TestToRoman(unittest.TestCase):
    def test_to_roman_one(self):
        self.assertEqual(to_roman(1), 'I')

    def test_to_roman_four(self):
        self.assertEqual(to_roman(4), 'IV')

    def test_to_roman_nine(self):
        self.assertEqual(to_roman(9), 'IX')

    def test_to_roman_forty(self):
        self.assertEqual(to_roman(40), 'XL')

    def test_to_roman_ninety(self):
        self.assertEqual(to_roman(90), 'XC')

    def test_to_roman_four_hundred(self):
        self.assertEqual(to_roman(400), 'CD')

    def test_to_roman_nine_hundred(self):
        self.assertEqual(to_roman(900), 'CM')

    def test_to_roman_2024(self):
        self.assertEqual(to_roman(2024), 'MMXXIV')

    def test_to_roman_3999(self):
        self.assertEqual(to_roman(3999), 'MMMCMXCIX')

    def test_to_roman_1994(self):
        self.assertEqual(to_roman(1994), 'MCMXCIV')

    def test_to_roman_return_type(self):
        result = to_roman(7)
        self.assertIsInstance(result, str)

    def test_to_roman_value_error_zero(self):
        with self.assertRaises(ValueError):
            to_roman(0)

    def test_to_roman_value_error_negative(self):
        with self.assertRaises(ValueError):
            to_roman(-1)

    def test_to_roman_value_error_over(self):
        with self.assertRaises(ValueError):
            to_roman(4000)

    def test_to_roman_type_error_string(self):
        with self.assertRaises(TypeError):
            to_roman('5')

    def test_to_roman_type_error_float(self):
        with self.assertRaises(TypeError):
            to_roman(5.0)

    def test_to_roman_type_error_none(self):
        with self.assertRaises(TypeError):
            to_roman(None)

    def test_to_roman_type_error_list(self):
        with self.assertRaises(TypeError):
            to_roman([1])

    def test_to_roman_type_error_bool(self):
        with self.assertRaises(TypeError):
            to_roman(True)

class TestIsRomanNumeral(unittest.TestCase):
    def test_true(self):
        self.assertTrue(is_roman_numeral('XIV'))
        self.assertTrue(is_roman_numeral('mmxxiv'))

    def test_false(self):
        self.assertFalse(is_roman_numeral(''))
        self.assertFalse(is_roman_numeral('ABC'))
        self.assertFalse(is_roman_numeral(14))
