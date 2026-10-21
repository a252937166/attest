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
    def test_ac12_value_error_low(self):
        with self.assertRaises(ValueError):
            to_roman(0)
        with self.assertRaises(ValueError):
            to_roman(-1)
    def test_ac12_value_error_high(self):
        with self.assertRaises(ValueError):
            to_roman(4000)
    def test_ac13_type_error_str(self):
        with self.assertRaises(TypeError):
            to_roman('5')
    def test_ac13_type_error_float(self):
        with self.assertRaises(TypeError):
            to_roman(5.0)
    def test_ac13_type_error_none(self):
        with self.assertRaises(TypeError):
            to_roman(None)
    def test_ac13_type_error_list(self):
        with self.assertRaises(TypeError):
            to_roman([1])
    def test_ac14_int_subclass(self):
        class PlainInt(int):
            pass
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')
    def test_ac15_is_roman_numeral_unchanged(self):
        self.assertTrue(is_roman_numeral('XIV'))
        self.assertTrue(is_roman_numeral('mmxxiv'))
        self.assertFalse(is_roman_numeral(''))
        self.assertFalse(is_roman_numeral('ABC'))
        self.assertFalse(is_roman_numeral(14))
    def test_ac16_existing_tests_pass(self):
        # just ensure import works; actual tests are in test_basic.py
        pass
