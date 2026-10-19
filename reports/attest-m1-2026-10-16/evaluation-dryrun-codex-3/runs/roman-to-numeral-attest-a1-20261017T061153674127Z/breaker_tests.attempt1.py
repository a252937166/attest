import unittest
from decimal import Decimal
from enum import IntEnum
from fractions import Fraction

from roman import is_roman_numeral, to_roman


class BreakerTests(unittest.TestCase):
    def test_int_enum_is_accepted_as_an_int(self):
        class Year(IntEnum):
            FOUR = 4
            LAST = 3999

        self.assertEqual(to_roman(Year.FOUR), 'IV')
        self.assertEqual(to_roman(Year.LAST), 'MMMCMXCIX')

    def test_int_subclass_with_overridden_arithmetic(self):
        class UnhelpfulArithmetic(int):
            def __floordiv__(self, other):
                raise AssertionError('subclass arithmetic was used')

            def __mod__(self, other):
                raise AssertionError('subclass arithmetic was used')

        self.assertEqual(to_roman(UnhelpfulArithmetic(49)), 'XLIX')

    def test_int_subclass_with_overridden_comparisons(self):
        class UnhelpfulComparison(int):
            def __ge__(self, other):
                return False

            def __le__(self, other):
                return False

        self.assertEqual(to_roman(UnhelpfulComparison(58)), 'LVIII')

    def test_out_of_range_subclass_with_misleading_comparisons(self):
        class AlwaysInRange(int):
            def __ge__(self, other):
                return True

            def __le__(self, other):
                return True

        with self.assertRaises(ValueError):
            to_roman(AlwaysInRange(4000))
        with self.assertRaises(ValueError):
            to_roman(AlwaysInRange(0))

    def test_numeric_protocols_do_not_make_nonints_valid(self):
        class IntegerLike:
            def __int__(self):
                return 4

            def __index__(self):
                return 4

        with self.assertRaises(TypeError):
            to_roman(IntegerLike())

    def test_other_numeric_types_are_not_coerced(self):
        for value in (Decimal('4'), Fraction(4, 1), 4 + 0j):
            with self.subTest(value=value), self.assertRaises(TypeError):
                to_roman(value)

    def test_nonfinite_floats_raise_type_error(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=value), self.assertRaises(TypeError):
                to_roman(value)

    def test_roman_membership_uses_uppercase_string(self):
        self.assertTrue(is_roman_numeral('ı'))
        self.assertFalse(is_roman_numeral('ⅰ'))
        self.assertFalse(is_roman_numeral('iv '))

    def test_roman_rejects_nonstring_iterables(self):
        for value in (['I', 'V'], ('X',), b'IV', {'I': 1}):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))
