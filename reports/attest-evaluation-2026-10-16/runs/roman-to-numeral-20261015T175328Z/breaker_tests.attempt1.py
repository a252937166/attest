import unittest
from roman import to_roman, is_roman_numeral

class TestToRomanBreaker(unittest.TestCase):
    def test_bool_raises_type_error(self):
        for value in (True, False):
            with self.assertRaises(TypeError):
                to_roman(value)

    def test_subclass_int_accepted(self):
        class MyInt(int):
            pass
        self.assertEqual(to_roman(MyInt(10)), 'X')

    def test_float_raises_type_error(self):
        self.assertRaises(TypeError, to_roman, 5.0)

    def test_string_non_numeric_raises_type_error(self):
        self.assertRaises(TypeError, to_roman, 'hello')

    def test_none_raises_type_error(self):
        self.assertRaises(TypeError, to_roman, None)

    def test_list_raises_type_error(self):
        self.assertRaises(TypeError, to_roman, [1, 2, 3])

    def test_dict_raises_type_error(self):
        self.assertRaises(TypeError, to_roman, {'a': 1})

    def test_set_raises_type_error(self):
        self.assertRaises(TypeError, to_roman, {1, 2})

    def test_out_of_range_high(self):
        for n in (4001, 5000, 10000):
            with self.assertRaises(ValueError):
                to_roman(n)

    def test_out_of_range_low(self):
        for n in (-42, -9999, 0):
            with self.assertRaises(ValueError):
                to_roman(n)

    def test_return_type_str(self):
        for n in (7, 12, 58, 199, 2024):
            self.assertIsInstance(to_roman(n), str)

    def test_output_uppercase_and_valid_chars(self):
        valid_set = set('IVXLCDM')
        for n in (1, 4, 9, 40, 90, 400, 900, 58, 1994, 3999):
            s = to_roman(n)
            self.assertTrue(s.isupper())
            self.assertTrue(all(ch in valid_set for ch in s))

    def test_output_passes_is_roman_numeral(self):
        # sample across range
        for n in range(1, 4000, 127):
            s = to_roman(n)
            self.assertTrue(is_roman_numeral(s))

    def test_no_invalid_sequences(self):
        forbidden = ('IIII', 'VV', 'XXXX', 'LL', 'CCCC', 'DD', 'MMMM')
        for n in range(1, 4000):
            s = to_roman(n)
            for seq in forbidden:
                self.assertNotIn(seq, s, msg=f'Forbidden sequence {seq} found in {s} for n={n}')
