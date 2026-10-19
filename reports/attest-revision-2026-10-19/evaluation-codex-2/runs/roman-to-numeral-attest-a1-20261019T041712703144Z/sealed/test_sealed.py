import unittest
from enum import IntEnum

from roman import to_roman, is_roman_numeral


class PlainInt(int):
    pass


class Number(IntEnum):
    FORTY_NINE = 49
    ZERO = 0
    NEGATIVE_ONE = -1
    FOUR_THOUSAND = 4000


class IntLike:
    def __int__(self):
        return 5

    def __index__(self):
        return 5


class TestToRoman(unittest.TestCase):
    def test_to_roman_has_one_argument_signature(self):
        for args in ((), (1, 2)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError) as cm:
                    to_roman(*args)
                self.assertIs(type(cm.exception), TypeError)

    def test_every_supported_integer_matches_canonical_place_value_tables(self):
        thousands = ('', 'M', 'MM', 'MMM')
        hundreds = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
        tens = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
        units = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')
        for n in range(1, 4000):
            with self.subTest(n=n):
                expected = (thousands[n // 1000] + hundreds[(n // 100) % 10]
                            + tens[(n // 10) % 10] + units[n % 10])
                result = to_roman(n)
                self.assertIsInstance(result, str)
                self.assertEqual(result, expected)

    def test_subtractive_boundary_values(self):
        cases = {1: 'I', 4: 'IV', 9: 'IX', 40: 'XL',
                 90: 'XC', 400: 'CD', 900: 'CM'}
        for n, expected in cases.items():
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_mixed_place_values_and_maximum(self):
        cases = {2024: 'MMXXIV', 1994: 'MCMXCIV', 3999: 'MMMCMXCIX'}
        for n, expected in cases.items():
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_out_of_range_integers_raise_value_error(self):
        for n in (0, -1, 4000, -100, 10000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError) as cm:
                    to_roman(n)
                self.assertIs(type(cm.exception), ValueError)

    def test_non_int_inputs_raise_type_error_without_coercion(self):
        for value in ('5', 5.0, None, [1], IntLike()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    to_roman(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_plain_int_subclass_matches_int_throughout_supported_range(self):
        for n in range(1, 4000):
            with self.subTest(n=n):
                self.assertEqual(to_roman(PlainInt(n)), to_roman(n))
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')

    def test_int_enum_member_converts_by_integer_value(self):
        self.assertEqual(to_roman(Number.FORTY_NINE), 'XLIX')

    def test_out_of_range_plain_int_subclasses_raise_value_error(self):
        for n in (0, -1, 4000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError) as cm:
                    to_roman(PlainInt(n))
                self.assertIs(type(cm.exception), ValueError)

    def test_out_of_range_int_enum_members_raise_value_error(self):
        for member in (Number.ZERO, Number.NEGATIVE_ONE, Number.FOUR_THOUSAND):
            with self.subTest(member=member):
                with self.assertRaises(ValueError) as cm:
                    to_roman(member)
                self.assertIs(type(cm.exception), ValueError)


class TestRomanNumeralHelper(unittest.TestCase):
    def test_helper_has_one_argument_signature(self):
        for args in ((), ('I', 'V')):
            with self.subTest(args=args):
                with self.assertRaises(TypeError) as cm:
                    is_roman_numeral(*args)
                self.assertIs(type(cm.exception), TypeError)

    def test_helper_accepts_roman_letters_without_requiring_canonical_syntax(self):
        for value in ('XIV', 'mmxxiv', 'IIII'):
            with self.subTest(value=value):
                self.assertIs(is_roman_numeral(value), True)

    def test_helper_rejects_empty_foreign_letters_and_nonstrings(self):
        for value in ('', 'ABC', 14, None, ['X']):
            with self.subTest(value=value):
                self.assertIs(is_roman_numeral(value), False)
