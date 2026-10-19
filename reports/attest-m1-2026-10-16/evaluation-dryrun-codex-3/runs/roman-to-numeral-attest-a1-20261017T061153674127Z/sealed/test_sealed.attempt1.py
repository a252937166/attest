import unittest

from roman import is_roman_numeral, to_roman


THOUSANDS = ('', 'M', 'MM', 'MMM')
HUNDREDS = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
TENS = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
UNITS = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')


class TestToRoman(unittest.TestCase):
    def test_every_value_matches_decimal_place_tables(self):
        for n in range(1, 4000):
            expected = (
                THOUSANDS[n // 1000]
                + HUNDREDS[(n // 100) % 10]
                + TENS[(n // 10) % 10]
                + UNITS[n % 10]
            )
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_unit_subtractive_examples(self):
        for n, expected in ((1, 'I'), (4, 'IV'), (9, 'IX')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_tens_and_hundreds_subtractive_examples(self):
        for n, expected in ((40, 'XL'), (90, 'XC'), (400, 'CD'), (900, 'CM')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_composite_examples(self):
        for n, expected in ((2024, 'MMXXIV'), (3999, 'MMMCMXCIX'), (1994, 'MCMXCIV')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_every_valid_result_is_a_nonempty_uppercase_roman_string(self):
        for n in range(1, 4000):
            with self.subTest(n=n):
                result = to_roman(n)
                self.assertIsInstance(result, str)
                self.assertRegex(result, r'\A[IVXLCDM]+\Z')

    def test_zero_and_negative_one_raise_value_error(self):
        for n in (0, -1):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_4000_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(4000)

    def test_arbitrarily_large_magnitude_integers_raise_value_error(self):
        for n in (10**1000, -(10**1000)):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_numeric_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman('5')

    def test_integral_float_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman(5.0)

    def test_none_and_list_raise_type_error(self):
        for value in (None, [1]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_booleans_raise_type_error(self):
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    to_roman(value)

    def test_int_subclass_values_convert(self):
        class MyInt(int):
            pass

        for n, expected in ((MyInt(1), 'I'), (MyInt(4), 'IV'), (MyInt(3999), 'MMMCMXCIX')):
            with self.subTest(n=n):
                self.assertEqual(to_roman(n), expected)

    def test_out_of_range_int_subclass_values_raise_value_error(self):
        class MyInt(int):
            pass

        for n in (MyInt(0), MyInt(4000)):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    to_roman(n)

    def test_named_parameter_n(self):
        self.assertEqual(to_roman(n=4), 'IV')


class TestExistingHelper(unittest.TestCase):
    def test_roman_letter_strings_are_accepted_case_insensitively(self):
        for value in ('XIV', 'mmxxiv'):
            with self.subTest(value=value):
                self.assertTrue(is_roman_numeral(value))

    def test_noncanonical_roman_letter_string_is_accepted(self):
        self.assertTrue(is_roman_numeral('IIII'))

    def test_empty_and_non_roman_strings_are_rejected(self):
        for value in ('', 'ABC'):
            with self.subTest(value=value):
                self.assertFalse(is_roman_numeral(value))

    def test_non_string_input_returns_false(self):
        self.assertFalse(is_roman_numeral(14))
