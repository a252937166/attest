import unittest
from enum import IntEnum

from roman import is_roman_numeral, to_roman


class PlainInt(int):
    pass


class RomanYear(IntEnum):
    YEAR = 2024


class Coercible:
    def __int__(self):
        return 5


class TestToRoman(unittest.TestCase):
    def test_every_in_range_value_matches_canonical_place_values(self):
        thousands = ('', 'M', 'MM', 'MMM')
        hundreds = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
        tens = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
        units = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')
        for n in range(1, 4000):
            with self.subTest(n=n):
                expected = (thousands[n // 1000] + hundreds[(n // 100) % 10]
                            + tens[(n // 10) % 10] + units[n % 10])
                self.assertEqual(to_roman(n), expected)

    def test_result_is_a_string(self):
        self.assertIsInstance(to_roman(1), str)

    def test_unit_subtractive_examples(self):
        for n, expected in ((1, 'I'), (4, 'IV'), (9, 'IX')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_tens_subtractive_examples(self):
        for n, expected in ((40, 'XL'), (90, 'XC')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_hundreds_subtractive_examples(self):
        for n, expected in ((400, 'CD'), (900, 'CM')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_multi_place_examples(self):
        for n, expected in ((2024, 'MMXXIV'), (3999, 'MMMCMXCIX'),
                            (1994, 'MCMXCIV')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_out_of_range_ints_raise_value_error(self):
        for n in (0, -1, 4000, 10000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_non_int_inputs_raise_type_error_without_coercion(self):
        for value in ('5', 5.0, None, [1], Coercible()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_plain_int_subclass_uses_its_integer_value(self):
        self.assertEqual(to_roman(PlainInt(49)), 'XLIX')

    def test_int_enum_uses_its_integer_value(self):
        self.assertEqual(to_roman(RomanYear.YEAR), 'MMXXIV')

    def test_out_of_range_int_subclasses_raise_value_error(self):
        for n in (0, -1, 4000):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(PlainInt(n))


class TestIsRomanNumeral(unittest.TestCase):
    def test_accepts_uppercase_and_lowercase_roman_letters(self):
        for value in ('XIV', 'mmxxiv'):
            with self.subTest(value=value):
                self.assertIs(is_roman_numeral(value), True)

    def test_accepts_noncanonical_roman_letter_sequences(self):
        self.assertIs(is_roman_numeral('IIII'), True)

    def test_rejects_empty_and_invalid_strings(self):
        for value in ('', 'ABC', 'X V'):
            with self.subTest(value=value):
                self.assertIs(is_roman_numeral(value), False)

    def test_non_string_inputs_return_false(self):
        for value in (14, None, ['XIV']):
            with self.subTest(value=value):
                self.assertIs(is_roman_numeral(value), False)
