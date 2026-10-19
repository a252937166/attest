import unittest
from decimal import Decimal
from enum import IntEnum
from fractions import Fraction

from roman import is_roman_numeral, to_roman


class PlainInteger(int):
    pass


class RomanValue(IntEnum):
    FIRST = 1
    FORTY_FOUR = 44
    NINE_HUNDRED_FORTY_FOUR = 944
    MAXIMUM = 3999


class TestBreaker(unittest.TestCase):
    def test_plain_subclasses_across_place_boundaries(self):
        cases = {
            1: 'I',
            8: 'VIII',
            44: 'XLIV',
            99: 'XCIX',
            404: 'CDIV',
            944: 'CMXLIV',
            1000: 'M',
            3888: 'MMMDCCCLXXXVIII',
            3999: 'MMMCMXCIX',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(to_roman(PlainInteger(value)), expected)

    def test_int_enum_across_range(self):
        cases = {
            RomanValue.FIRST: 'I',
            RomanValue.FORTY_FOUR: 'XLIV',
            RomanValue.NINE_HUNDRED_FORTY_FOUR: 'CMXLIV',
            RomanValue.MAXIMUM: 'MMMCMXCIX',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(to_roman(value), expected)

    def test_distant_out_of_range_subclasses(self):
        for value in (-10**30, -4000, 4001, 10**30):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    to_roman(PlainInteger(value))

    def test_non_integer_numeric_values_are_not_coerced(self):
        values = (Decimal('1'), Fraction(4, 1), 1 + 0j, float('nan'), float('inf'))
        for value in values:
            with self.subTest(value=repr(value)):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_non_integer_containers_are_rejected(self):
        values = (b'IV', bytearray(b'IV'), memoryview(b'IV'), (4,), {4}, {'n': 4}, range(1))
        for value in values:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_place_carry_boundaries(self):
        cases = {
            39: 'XXXIX',
            40: 'XL',
            89: 'LXXXIX',
            90: 'XC',
            399: 'CCCXCIX',
            400: 'CD',
            999: 'CMXCIX',
            1000: 'M',
            1999: 'MCMXCIX',
            2000: 'MM',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(to_roman(value), expected)

    def test_unicode_uppercase_rule(self):
        self.assertTrue(is_roman_numeral('\u0131'))  # Dotless i uppercases to I.
        self.assertTrue(is_roman_numeral('x\u0131v'))
        self.assertFalse(is_roman_numeral('\u2170'))  # Roman numeral glyph is not the letter I.
        self.assertFalse(is_roman_numeral('\u2160'))

    def test_allowed_letters_do_not_require_canonical_syntax(self):
        for value in ('iIiI', 'vx', 'MMMM', 'cdc', 'xXmMiI'):
            with self.subTest(value=value):
                self.assertTrue(is_roman_numeral(value))

    def test_invalid_characters_and_additional_non_strings(self):
        for value in (' IV', 'IV\n', 'I\x00V', 'I\u2160', b'IV', Decimal('4'), Fraction(4, 1), RomanValue.FIRST):
            with self.subTest(value=repr(value)):
                self.assertFalse(is_roman_numeral(value))
