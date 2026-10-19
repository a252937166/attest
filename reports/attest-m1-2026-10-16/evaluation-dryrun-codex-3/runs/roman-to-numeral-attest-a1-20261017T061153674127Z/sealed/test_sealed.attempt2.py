import unittest

from roman import is_roman_numeral, to_roman


class OrdinaryInt(int):
    pass


class TestToRoman(unittest.TestCase):
    def test_every_value_matches_decimal_place_tables(self):
        thousands = ('', 'M', 'MM', 'MMM')
        hundreds = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
        tens = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
        units = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')
        for n in range(1, 4000):
            expected = (thousands[n // 1000] + hundreds[n // 100 % 10]
                        + tens[n // 10 % 10] + units[n % 10])
            self.assertEqual(to_roman(n), expected, n)

    def test_unit_subtractive_examples(self):
        self.assertEqual(to_roman(1), 'I')
        self.assertEqual(to_roman(4), 'IV')
        self.assertEqual(to_roman(9), 'IX')

    def test_tens_subtractive_examples(self):
        self.assertEqual(to_roman(40), 'XL')
        self.assertEqual(to_roman(90), 'XC')

    def test_hundreds_subtractive_examples(self):
        self.assertEqual(to_roman(400), 'CD')
        self.assertEqual(to_roman(900), 'CM')

    def test_multi_place_examples(self):
        self.assertEqual(to_roman(2024), 'MMXXIV')
        self.assertEqual(to_roman(3999), 'MMMCMXCIX')
        self.assertEqual(to_roman(1994), 'MCMXCIV')

    def test_every_valid_result_is_a_nonempty_uppercase_roman_string(self):
        for n in range(1, 4000):
            result = to_roman(n)
            self.assertIsInstance(result, str, n)
            self.assertTrue(result, n)
            self.assertTrue(all(char in 'IVXLCDM' for char in result), n)

    def test_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(0)

    def test_negative_one_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(-1)

    def test_4000_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(4000)

    def test_arbitrarily_large_integers_raise_value_error(self):
        for n in (10 ** 100, -(10 ** 100)):
            with self.assertRaises(ValueError):
                to_roman(n)

    def test_numeric_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman('5')

    def test_integral_float_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman(5.0)

    def test_none_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman(None)

    def test_list_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman([1])

    def test_bool_values_raise_type_error(self):
        for value in (True, False):
            with self.assertRaises(TypeError):
                to_roman(value)

    def test_int_subclass_converts_normally(self):
        self.assertEqual(to_roman(OrdinaryInt(4)), 'IV')
        self.assertEqual(to_roman(OrdinaryInt(3999)), 'MMMCMXCIX')

    def test_out_of_range_int_subclass_raises_value_error(self):
        for n in (OrdinaryInt(0), OrdinaryInt(4000)):
            with self.assertRaises(ValueError):
                to_roman(n)

    def test_named_n_argument(self):
        self.assertEqual(to_roman(n=4), 'IV')


class TestIsRomanNumeral(unittest.TestCase):
    def test_roman_letter_strings_are_accepted_case_insensitively(self):
        self.assertTrue(is_roman_numeral('XIV'))
        self.assertTrue(is_roman_numeral('mmxxiv'))

    def test_membership_check_accepts_noncanonical_roman_letters(self):
        self.assertTrue(is_roman_numeral('IIII'))
        self.assertTrue(is_roman_numeral('VX'))

    def test_empty_string_is_rejected(self):
        self.assertFalse(is_roman_numeral(''))

    def test_other_letters_are_rejected(self):
        self.assertFalse(is_roman_numeral('ABC'))

    def test_nonstring_is_rejected_without_raising(self):
        self.assertFalse(is_roman_numeral(14))
        self.assertFalse(is_roman_numeral(None))
