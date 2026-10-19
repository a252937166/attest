import unittest
from decimal import Decimal
from enum import IntEnum
from fractions import Fraction

from roman import is_roman_numeral, to_roman


class PlainInt(int):
    pass


class RomanValue(IntEnum):
    ONE = 1
    FOUR = 4
    NINE = 9
    FORTY = 40
    NINETY = 90
    FOUR_HUNDRED = 400
    NINE_HUNDRED = 900
    MAXIMUM = 3999


class PlainStr(str):
    pass


class BreakerTests(unittest.TestCase):
    def test_plain_int_subclass_across_decimal_places(self):
        cases = {
            1: 'I', 4: 'IV', 9: 'IX', 40: 'XL', 90: 'XC',
            400: 'CD', 900: 'CM', 944: 'CMXLIV',
            1449: 'MCDXLIX', 2990: 'MMCMXC', 3999: 'MMMCMXCIX',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(to_roman(PlainInt(value)), expected)

    def test_int_enum_across_subtractive_places(self):
        expected = {
            RomanValue.ONE: 'I',
            RomanValue.FOUR: 'IV',
            RomanValue.NINE: 'IX',
            RomanValue.FORTY: 'XL',
            RomanValue.NINETY: 'XC',
            RomanValue.FOUR_HUNDRED: 'CD',
            RomanValue.NINE_HUNDRED: 'CM',
            RomanValue.MAXIMUM: 'MMMCMXCIX',
        }
        for value, numeral in expected.items():
            with self.subTest(value=value):
                self.assertEqual(to_roman(value), numeral)

    def test_subclass_values_far_outside_range(self):
        for value in (-10**50, -4000, 10**50):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    to_roman(PlainInt(value))

    def test_other_numeric_types_are_not_coerced(self):
        for value in (Decimal('49'), Fraction(49, 1), 49.0, 49 + 0j):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_other_containers_and_encoded_values_are_not_coerced(self):
        for value in (b'49', bytearray(b'49'), ('49',), {'value': 49}, '0049'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_generated_subtractive_numerals_are_accepted_by_validator(self):
        for value in (4, 9, 40, 49, 90, 94, 400, 490, 900, 944, 1994, 3999):
            with self.subTest(value=value):
                self.assertTrue(is_roman_numeral(to_roman(PlainInt(value))))

    def test_validator_uses_uppercase_mapping_for_unicode_strings(self):
        self.assertTrue(is_roman_numeral('\u0131'))
        self.assertTrue(is_roman_numeral('\u0131v'))
        self.assertFalse(is_roman_numeral('\u2173'))

    def test_validator_accepts_str_subclasses_and_checks_every_character(self):
        self.assertTrue(is_roman_numeral(PlainStr('mcmxciv')))
        self.assertTrue(is_roman_numeral(PlainStr('vvvv')))
        self.assertFalse(is_roman_numeral(PlainStr('iv ')))
        self.assertFalse(is_roman_numeral(PlainStr('x\n')))
