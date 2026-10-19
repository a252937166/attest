import unittest
from enum import IntEnum

from roman import to_roman
from roman import is_roman_numeral


class PlainInt(int):
    pass


class RomanValue(IntEnum):
    FORTY_NINE = 49
    ZERO = 0
    NEGATIVE_ONE = -1
    FOUR_THOUSAND = 4000


class TestToRoman(unittest.TestCase):
    def test_every_builtin_integer_matches_decimal_place_composition(self):
        thousands = ('', 'M', 'MM', 'MMM')
        hundreds = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
        tens = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
        units = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')
        for n in range(1, 4000):
            with self.subTest(n=n):
                expected = (thousands[n // 1000] + hundreds[n // 100 % 10]
                            + tens[n // 10 % 10] + units[n % 10])
                actual = to_roman(n)
                self.assertIsInstance(actual, str)
                self.assertEqual(actual, expected)

    def test_unit_subtractive_examples(self):
        for n, expected in ((1, 'I'), (4, 'IV'), (9, 'IX')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_tens_and_hundreds_subtractive_examples(self):
        for n, expected in ((40, 'XL'), (90, 'XC'), (400, 'CD'), (900, 'CM')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_multi_place_examples(self):
        for n, expected in ((1994, 'MCMXCIV'), (2024, 'MMXXIV'),
                            (3999, 'MMMCMXCIX')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_builtin_integers_below_range_raise_value_error(self):
        for n in (0, -1):
            with self.subTest(n=n):
                with self.assertRaises(ValueError) as cm:
                    to_roman(n)
                self.assertIs(type(cm.exception), ValueError)

    def test_builtin_integers_above_range_raise_value_error(self):
        with self.assertRaises(ValueError) as cm:
            to_roman(4000)
        self.assertIs(type(cm.exception), ValueError)

    def test_non_int_inputs_raise_type_error(self):
        for value in ('5', 5.0, None, [1]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    to_roman(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_plain_int_subclass_converts_by_value(self):
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')

    def test_int_enum_converts_by_value(self):
        self.assertEqual(to_roman(RomanValue.FORTY_NINE), 'XLIX')

    def test_plain_int_subclass_out_of_range_raises_value_error(self):
        for n in (0, -1, 4000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError) as cm:
                    to_roman(PlainInt(n))
                self.assertIs(type(cm.exception), ValueError)

    def test_int_enum_out_of_range_raises_value_error(self):
        for value in (RomanValue.ZERO, RomanValue.NEGATIVE_ONE,
                      RomanValue.FOUR_THOUSAND):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as cm:
                    to_roman(value)
                self.assertIs(type(cm.exception), ValueError)


class TestIsRomanNumeral(unittest.TestCase):
    def test_accepts_uppercase_and_lowercase_roman_letters(self):
        self.assertTrue(is_roman_numeral('XIV'))
        self.assertTrue(is_roman_numeral('mmxxiv'))

    def test_rejects_empty_invalid_and_non_string_inputs(self):
        for value in ('', 'ABC', 14):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))

    def test_accepts_noncanonical_sequence_of_roman_letters(self):
        self.assertTrue(is_roman_numeral('IIII'))
