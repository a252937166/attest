import unittest
from enum import IntEnum
from fractions import Fraction

from roman import to_roman


class TestAdversarialRomanConversion(unittest.TestCase):
    def test_valid_int_subclass_with_overridden_comparisons(self):
        class MisleadingComparisons(int):
            def __ge__(self, other):
                return False

            def __le__(self, other):
                return False

        self.assertEqual(to_roman(MisleadingComparisons(44)), 'XLIV')

    def test_zero_int_subclass_with_overridden_comparisons(self):
        class MisleadingComparisons(int):
            def __ge__(self, other):
                return True

            def __le__(self, other):
                return True

        with self.assertRaises(ValueError):
            to_roman(MisleadingComparisons(0))

    def test_upper_bound_int_subclass_with_overridden_comparisons(self):
        class MisleadingComparisons(int):
            def __ge__(self, other):
                return True

            def __le__(self, other):
                return True

        with self.assertRaises(ValueError):
            to_roman(MisleadingComparisons(4000))

    def test_int_subclass_with_overridden_floor_division(self):
        class MisleadingDivision(int):
            def __floordiv__(self, other):
                raise AssertionError('subclass arithmetic was used')

        self.assertEqual(to_roman(MisleadingDivision(3888)), 'MMMDCCCLXXXVIII')

    def test_int_subclass_with_overridden_modulo(self):
        class MisleadingModulo(int):
            def __mod__(self, other):
                raise AssertionError('subclass arithmetic was used')

        self.assertEqual(to_roman(MisleadingModulo(2479)), 'MMCDLXXIX')

    def test_int_subclass_with_overridden_int_conversion(self):
        class MisleadingInt(int):
            def __int__(self):
                raise AssertionError('subclass conversion was used')

        self.assertEqual(to_roman(MisleadingInt(1066)), 'MLXVI')

    def test_int_enum_is_accepted_as_int_subclass(self):
        class Year(IntEnum):
            VALUE = 1989

        self.assertEqual(to_roman(Year.VALUE), 'MCMLXXXIX')

    def test_integer_like_non_int_values_are_not_coerced(self):
        class IntegerLike:
            def __int__(self):
                return 7

            def __index__(self):
                return 7

        for value in (IntegerLike(), Fraction(7, 1)):
            with self.subTest(value=value), self.assertRaises(TypeError):
                to_roman(value)
