import unittest
from roman import to_roman


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

    def test_return_type_is_str(self):
        result = to_roman(7)
        self.assertIsInstance(result, str)

    def test_value_error_below_range(self):
        with self.assertRaises(ValueError):
            to_roman(0)

    def test_value_error_above_range(self):
        with self.assertRaises(ValueError):
            to_roman(4000)

    def test_type_error_for_string(self):
        with self.assertRaises(TypeError):
            to_roman('5')

    def test_type_error_for_float(self):
        with self.assertRaises(TypeError):
            to_roman(5.0)

    def test_type_error_for_none(self):
        with self.assertRaises(TypeError):
            to_roman(None)

    def test_type_error_for_list(self):
        with self.assertRaises(TypeError):
            to_roman([1])

    def test_int_subclass_in_range(self):
        class PlainInt(int):
            pass
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')

    def test_int_subclass_out_of_range_low(self):
        class PlainInt(int):
            pass
        with self.assertRaises(ValueError):
            to_roman(PlainInt(0))

    def test_int_subclass_out_of_range_high(self):
        class PlainInt(int):
            pass
        with self.assertRaises(ValueError):
            to_roman(PlainInt(4000))
