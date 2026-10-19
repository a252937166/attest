import unittest

from roman import is_roman_numeral, to_roman
from roman.core import to_roman as core_to_roman


THOUSANDS = ('', 'M', 'MM', 'MMM')
HUNDREDS = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
TENS = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
UNITS = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')


class DerivedInt(int):
    pass


class TestToRoman(unittest.TestCase):
    def test_public_export_matches_core(self):
        self.assertIs(to_roman, core_to_roman)

    def test_units_subtractive_forms(self):
        for n, expected in ((1, 'I'), (4, 'IV'), (9, 'IX')):
            self.assertEqual(to_roman(n), expected)

    def test_larger_subtractive_forms(self):
        for n, expected in ((40, 'XL'), (90, 'XC'), (400, 'CD'), (900, 'CM')):
            self.assertEqual(to_roman(n), expected)

    def test_single_symbols(self):
        for n, expected in ((5, 'V'), (10, 'X'), (50, 'L'), (100, 'C'), (500, 'D'), (1000, 'M')):
            self.assertEqual(to_roman(n), expected)

    def test_multi_place_examples(self):
        for n, expected in ((2024, 'MMXXIV'), (1994, 'MCMXCIV'), (3999, 'MMMCMXCIX')):
            self.assertEqual(to_roman(n), expected)

    def test_results_are_nonempty_uppercase_roman_text(self):
        for n in (1, 8, 49, 376, 2024, 3999):
            result = to_roman(n)
            self.assertIsInstance(result, str)
            self.assertTrue(result)
            self.assertTrue(all(char in 'IVXLCDM' for char in result))

    def test_zero_and_negative_boundary_raise_value_error(self):
        for n in (0, -1):
            with self.assertRaises(ValueError):
                to_roman(n)

    def test_above_upper_boundary_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(4000)

    def test_arbitrarily_large_magnitude_raises_value_error(self):
        for n in (10**100, -(10**100)):
            with self.assertRaises(ValueError):
                to_roman(n)

    def test_strings_and_floats_raise_type_error(self):
        for value in ('5', 5.0):
            with self.assertRaises(TypeError):
                to_roman(value)

    def test_none_and_list_raise_type_error(self):
        for value in (None, [1]):
            with self.assertRaises(TypeError):
                to_roman(value)

    def test_booleans_raise_type_error(self):
        for value in (True, False):
            with self.assertRaises(TypeError):
                to_roman(value)

    def test_int_subclass_converts_normally(self):
        self.assertEqual(to_roman(DerivedInt(1994)), 'MCMXCIV')

    def test_int_subclass_obeys_range_validation(self):
        for n in (0, 4000):
            with self.assertRaises(ValueError):
                to_roman(DerivedInt(n))


class TestExistingHelper(unittest.TestCase):
    def test_canonical_strings_are_accepted_case_insensitively(self):
        self.assertTrue(is_roman_numeral('XIV'))
        self.assertTrue(is_roman_numeral('mmxxiv'))

    def test_noncanonical_strings_of_roman_letters_remain_accepted(self):
        self.assertTrue(is_roman_numeral('IIII'))
        self.assertTrue(is_roman_numeral('VX'))

    def test_empty_and_unrecognized_strings_are_rejected(self):
        self.assertFalse(is_roman_numeral(''))
        self.assertFalse(is_roman_numeral('ABC'))

    def test_ordinary_nonstring_inputs_return_false(self):
        for value in (14, None, ['X']):
            self.assertFalse(is_roman_numeral(value))


def make_canonical_block_test(block):
    def test_canonical_block(self):
        start = 1 + block * 100
        stop = min(start + 100, 4000)
        for n in range(start, stop):
            expected = (THOUSANDS[n // 1000] + HUNDREDS[n // 100 % 10]
                        + TENS[n // 10 % 10] + UNITS[n % 10])
            self.assertEqual(to_roman(n), expected, f'n={n}')
    return test_canonical_block


for block in range(40):
    setattr(TestToRoman, f'test_canonical_block_{block:02d}', make_canonical_block_test(block))
