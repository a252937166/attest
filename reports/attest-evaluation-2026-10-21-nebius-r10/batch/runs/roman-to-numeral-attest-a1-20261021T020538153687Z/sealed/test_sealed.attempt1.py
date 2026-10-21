import unittest
from roman import to_roman, is_roman_numeral

class TestToRoman(unittest.TestCase):
    def test_ac1_one(self):
        self.assertEqual(to_roman(1), 'I')
    def test_ac2_four(self):
        self.assertEqual(to_roman(4), 'IV')
    def test_ac3_nine(self):
        self.assertEqual(to_roman(9), 'IX')
    def test_ac4_forty(self):
        self.assertEqual(to_roman(40), 'XL')
    def test_ac5_ninety(self):
        self.assertEqual(to_roman(90), 'XC')
    def test_ac6_four_hundred(self):
        self.assertEqual(to_roman(400), 'CD')
    def test_ac7_nine_hundred(self):
        self.assertEqual(to_roman(900), 'CM')
    def test_ac8_2024(self):
        self.assertEqual(to_roman(2024), 'MMXXIV')
    def test_ac9_3999(self):
        self.assertEqual(to_roman(3999), 'MMMCMXCIX')
    def test_ac10_1994(self):
        self.assertEqual(to_roman(1994), 'MCMXCIV')
    def test_ac11_return_type(self):
        for n in [1, 4, 9, 40, 90, 400, 900, 2024, 3999]:
            self.assertIsInstance(to_roman(n), str)
    def test_ac12_value_error_outside(self):
        for n in [0, -1, 4000]:
            with self.assertRaises(ValueError):
                to_roman(n)
        class MyInt(int):
            pass
        for n in [MyInt(0), MyInt(-5), MyInt(5000)]:
            with self.assertRaises(ValueError):
                to_roman(n)
    def test_ac13_type_error_non_int(self):
        for val in ['5', 5.0, None, [1]]:
            with self.assertRaises(TypeError):
                to_roman(val)
    def test_ac14_int_subclass_in_range(self):
        class PlainInt(int):
            pass
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')

class TestIsRomanNumeral(unittest.TestCase):
    def test_ac15_xiv(self):
        self.assertTrue(is_roman_numeral('XIV'))
    def test_ac16_mmxxiv_lower(self):
        self.assertTrue(is_roman_numeral('mmxxiv'))
    def test_ac17_empty(self):
        self.assertFalse(is_roman_numeral(''))
    def test_ac18_abc(self):
        self.assertFalse(is_roman_numeral('ABC'))
    def test_ac19_non_string(self):
        self.assertFalse(is_roman_numeral(14))
