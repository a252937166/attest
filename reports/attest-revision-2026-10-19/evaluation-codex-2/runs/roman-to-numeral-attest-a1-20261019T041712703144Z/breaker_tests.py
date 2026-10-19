import unittest
from decimal import Decimal
from enum import Enum, IntEnum
from fractions import Fraction

from roman import is_roman_numeral, to_roman


class TestBreaker(unittest.TestCase):
    def test_non_int_numeric_values_are_not_coerced(self):
        for value in (Decimal('5'), Fraction(5, 1), 5 + 0j):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_other_non_int_values_are_rejected(self):
        class Number(Enum):
            FIVE = 5

        for value in (Number.FIVE, b'5', (5,), {'value': 5}, range(5)):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_int_enum_values_with_multiple_subtractive_places(self):
        class Number(IntEnum):
            FOUR_HUNDRED_FORTY_FOUR = 444
            NINE_HUNDRED_FORTY_FOUR = 944
            THREE_THOUSAND_EIGHT_HUNDRED_EIGHTY_EIGHT = 3888

        expected = {
            Number.FOUR_HUNDRED_FORTY_FOUR: 'CDXLIV',
            Number.NINE_HUNDRED_FORTY_FOUR: 'CMXLIV',
            Number.THREE_THOUSAND_EIGHT_HUNDRED_EIGHTY_EIGHT: 'MMMDCCCLXXXVIII',
        }
        for value, numeral in expected.items():
            with self.subTest(value=value):
                self.assertEqual(to_roman(value), numeral)

    def test_helper_uses_uppercase_result_for_unicode_input(self):
        self.assertTrue(is_roman_numeral('\u0131'))
        self.assertTrue(is_roman_numeral('m\u0131x'))
        self.assertFalse(is_roman_numeral('\u2163'))

    def test_helper_accepts_noncanonical_letter_sequences(self):
        for value in ('VX', 'IL', 'MMMM', 'dCmXiV', 'IVXLCDM'):
            with self.subTest(value=value):
                self.assertTrue(is_roman_numeral(value))

    def test_helper_rejects_intruders_at_any_position(self):
        for value in (' IX', 'IX ', 'I9X', 'M\n', 'C-D', 'X\u2163'):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))

    def test_helper_rejects_other_ordinary_types(self):
        for value in (b'X', None, 1.0, ['X'], ('X',), {'X': True}):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))

    def test_helper_accepts_plain_str_subclass(self):
        class RomanText(str):
            pass

        self.assertTrue(is_roman_numeral(RomanText('xlix')))
        self.assertFalse(is_roman_numeral(RomanText('XL IX')))

    def test_conversion_outputs_pass_helper_with_subtractive_letters(self):
        for value in (4, 9, 40, 90, 400, 900, 944, 1994, 3999):
            with self.subTest(value=value):
                numeral = to_roman(value)
                self.assertIsInstance(numeral, str)
                self.assertTrue(is_roman_numeral(numeral))
                self.assertEqual(numeral, numeral.upper())
