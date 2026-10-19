import unittest
from roman import to_roman

class TestToRoman(unittest.TestCase):
    def test_one(self):
        self.assertEqual(to_roman(1), 'I')
    def test_four(self):
        self.assertEqual(to_roman(4), 'IV')
    def test_nine(self):
        self.assertEqual(to_roman(9), 'IX')
    def test_forty(self):
        self.assertEqual(to_roman(40), 'XL')
    def test_ninety(self):
        self.assertEqual(to_roman(90), 'XC')
    def test_four_hundred(self):
        self.assertEqual(to_roman(400), 'CD')
    def test_nine_hundred(self):
        self.assertEqual(to_roman(900), 'CM')
    def test_2024(self):
        self.assertEqual(to_roman(2024), 'MMXXIV')
    def test_3999(self):
        self.assertEqual(to_roman(3999), 'MMMCMXCIX')
    def test_1994(self):
        self.assertEqual(to_roman(1994), 'MCMXCIV')
    def test_return_type_str(self):
        self.assertIsInstance(to_roman(7), str)
    def test_value_error_out_of_range_low(self):
        with self.assertRaises(ValueError):
            to_roman(0)
    def test_value_error_out_of_range_high(self):
        with self.assertRaises(ValueError):
            to_roman(4000)
    def test_value_error_int_subclass_out_of_range(self):
        class PlainInt(int):
            pass
        with self.assertRaises(ValueError):
            to_roman(PlainInt(0))
    def test_type_error_non_int(self):
        for bad in ('5', 5.0, None, [1]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    to_roman(bad)
    def test_int_subclass_in_range(self):
        class PlainInt(int):
            pass
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')
