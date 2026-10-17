import unittest
from decimal import Decimal
from enum import IntEnum
from fractions import Fraction

from roman import is_roman_numeral, to_roman


class PlainInt(int):
    """An ordinary int subclass: no operator is overridden, so its value is all that can matter."""


class BreakerTests(unittest.TestCase):
    def test_int_enum_is_accepted_as_an_int(self):
        class Year(IntEnum):
            FOUR = 4
            LAST = 3999

        self.assertEqual(to_roman(Year.FOUR), 'IV')
        self.assertEqual(to_roman(Year.LAST), 'MMMCMXCIX')

    # Corrected 17 Oct 2026. The original three tests drove to_roman through int subclasses whose __floordiv__, __mod__,
    # __ge__ and __le__ were overridden to sabotage the implementation. The clarified contract says conversion is by integer
    # value and operator-overriding subclasses are out of scope, so those tests are replaced by value-based subclass tests.
    def test_plain_int_subclass_is_converted_by_value(self):
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')
        self.assertEqual(to_roman(PlainInt(58)), 'LVIII')
        self.assertEqual(to_roman(PlainInt(1)), 'I')
        self.assertEqual(to_roman(PlainInt(3999)), 'MMMCMXCIX')

    def test_plain_int_subclass_out_of_range_raises_value_error(self):
        for value in (PlainInt(0), PlainInt(4000), PlainInt(-7)):
            with self.subTest(value=int(value)), self.assertRaises(ValueError):
                to_roman(value)

    def test_large_magnitude_ints_raise_value_error(self):
        for value in (10 ** 12, -(10 ** 12), 4000, 99999):
            with self.subTest(value=value), self.assertRaises(ValueError):
                to_roman(value)

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
