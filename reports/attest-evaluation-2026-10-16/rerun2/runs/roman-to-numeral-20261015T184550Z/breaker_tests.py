import unittest
from roman import to_roman, is_roman_numeral
from decimal import Decimal
from fractions import Fraction

class TestToRomanBreaker(unittest.TestCase):
    def test_int_subclass_accepted(self):
        class MyInt(int):
            pass
        n = MyInt(10)
        self.assertEqual(to_roman(n), 'X')

    def test_bool_raises_TypeError(self):
        with self.assertRaises(TypeError):
            to_roman(True)
        with self.assertRaises(TypeError):
            to_roman(False)

    def test_float_nonintegral_raises_TypeError(self):
        with self.assertRaises(TypeError):
            to_roman(0.5)

    def test_float_integral_raises_TypeError(self):
        with self.assertRaises(TypeError):
            to_roman(5.0)

    def test_decimal_raises_TypeError(self):
        with self.assertRaises(TypeError):
            to_roman(Decimal('10'))

    def test_fraction_raises_TypeError(self):
        with self.assertRaises(TypeError):
            to_roman(Fraction(10, 1))

    def test_complex_raises_TypeError(self):
        with self.assertRaises(TypeError):
            to_roman(3 + 4j)

    def test_large_int_out_of_range_raises_ValueError(self):
        with self.assertRaises(ValueError):
            to_roman(10 ** 100)

    def test_negative_large_int_raises_ValueError(self):
        with self.assertRaises(ValueError):
            to_roman(-10 ** 100)

    def test_zero_raises_ValueError(self):
        with self.assertRaises(ValueError):
            to_roman(0)

    def test_result_is_uppercase_and_valid_characters(self):
        test_values = [1, 4, 9, 40, 90, 400, 900, 2024, 3999, 1994]
        for n in test_values:
            roman = to_roman(n)
            self.assertTrue(all(c in "MDCLXVI" for c in roman))
            self.assertTrue(roman.isupper())

    def test_is_roman_numeral_returns_true(self):
        step = 123
        for n in range(1, 4000, step):
            roman = to_roman(n)
            self.assertTrue(is_roman_numeral(roman))