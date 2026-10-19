import unittest

from roman import is_roman_numeral, to_roman
from roman.core import to_roman as core_to_roman


class TestToRoman(unittest.TestCase):
    def test_package_and_core_export_same_function(self):
        self.assertIs(to_roman, core_to_roman)

    def test_units_subtractive_forms(self):
        for number, expected in ((1, 'I'), (4, 'IV'), (9, 'IX')):
            with self.subTest(number=number):
                self.assertEqual(to_roman(number), expected)

    def test_higher_place_subtractive_forms(self):
        for number, expected in ((40, 'XL'), (90, 'XC'), (400, 'CD'), (900, 'CM')):
            with self.subTest(number=number):
                self.assertEqual(to_roman(number), expected)

    def test_single_symbol_values(self):
        for number, expected in ((5, 'V'), (10, 'X'), (50, 'L'), (100, 'C'), (500, 'D'), (1000, 'M')):
            with self.subTest(number=number):
                self.assertEqual(to_roman(number), expected)

    def test_mixed_place_examples(self):
        for number, expected in ((2024, 'MMXXIV'), (1994, 'MCMXCIV'), (3999, 'MMMCMXCIX')):
            with self.subTest(number=number):
                self.assertEqual(to_roman(number), expected)

    def test_every_valid_number_uses_canonical_place_forms(self):
        thousands = ('', 'M', 'MM', 'MMM')
        hundreds = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
        tens = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
        units = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')
        for number in range(1, 4000):
            with self.subTest(number=number):
                expected = (thousands[number // 1000]
                            + hundreds[number // 100 % 10]
                            + tens[number // 10 % 10]
                            + units[number % 10])
                self.assertEqual(to_roman(number), expected)

    def test_every_valid_result_is_nonempty_uppercase_roman_text(self):
        for number in range(1, 4000):
            with self.subTest(number=number):
                result = to_roman(number)
                self.assertIsInstance(result, str)
                self.assertTrue(result)
                self.assertTrue(all(character in 'IVXLCDM' for character in result))

    def test_out_of_range_integers_raise_value_error(self):
        for number in (0, -1, 4000, -(10 ** 1000), 10 ** 1000):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    to_roman(number)

    def test_non_integer_inputs_raise_type_error(self):
        for value in ('5', 5.0, None, [1]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_booleans_raise_type_error(self):
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_int_subclass_converts_like_int(self):
        class IntegerChild(int):
            pass

        for number in (1, 4, 1994, 3999):
            with self.subTest(number=number):
                self.assertEqual(to_roman(IntegerChild(number)), to_roman(number))

    def test_out_of_range_int_subclass_raises_value_error(self):
        class IntegerChild(int):
            pass

        for number in (0, -1, 4000, 10 ** 1000):
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    to_roman(IntegerChild(number))


class TestIsRomanNumeral(unittest.TestCase):
    def test_valid_letters_are_case_insensitive(self):
        for value in ('XIV', 'mmxxiv'):
            with self.subTest(value=value):
                self.assertTrue(is_roman_numeral(value))

    def test_empty_and_disallowed_text_are_rejected(self):
        for value in ('', 'ABC'):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))

    def test_non_string_input_returns_false(self):
        for value in (14, None, ['X']):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))

    def test_permitted_but_noncanonical_letters_remain_accepted(self):
        for value in ('IIII', 'VX'):
            with self.subTest(value=value):
                self.assertTrue(is_roman_numeral(value))
