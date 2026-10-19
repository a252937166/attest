import unittest
from roman import to_roman

class TestToRomanBreaker(unittest.TestCase):
    def test_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(0)
    def test_negative_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(-1)
    def test_too_large_raises_value_error(self):
        with self.assertRaises(ValueError):
            to_roman(4000)
    def test_float_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman(3.14)
    def test_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman('42')
    def test_none_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman(None)
    def test_list_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman([1, 2, 3])
    def test_dict_raises_type_error(self):
        with self.assertRaises(TypeError):
            to_roman({'a': 1})
    def test_non_int_subclass_with_int_method_raises_type_error(self):
        class AlmostInt:
            def __int__(self):
                return 10
        with self.assertRaises(TypeError):
            to_roman(AlmostInt())
    def test_int_subclass_preserves_value(self):
        class MyInt(int):
            pass
        self.assertEqual(to_roman(MyInt(58)), 'LVIII')
    def test_int_subclass_out_of_range_raises_value_error(self):
        class MyInt(int):
            pass
        with self.assertRaises(ValueError):
            to_roman(MyInt(0))
        with self.assertRaises(ValueError):
            to_roman(MyInt(4000))
    def test_return_type_is_str(self):
        self.assertIsInstance(to_roman(1), str)
    def test_function_does_not_mutate_input(self):
        n = 10
        original = n
        to_roman(n)
        self.assertEqual(n, original)
    def test_boundary_values(self):
        cases = [
            (1, 'I'), (2, 'II'), (3, 'III'), (5, 'V'), (8, 'VIII'),
            (10, 'X'), (11, 'XI'), (14, 'XIV'), (15, 'XV'), (16, 'XVI'),
            (19, 'XIX'), (20, 'XX'), (30, 'XXX'), (39, 'XXXIX'), (40, 'XL'),
            (41, 'XLI'), (49, 'XLIX'), (50, 'L'), (51, 'LI'), (90, 'XC'),
            (91, 'XCI'), (99, 'XCIX'), (100, 'C'), (101, 'CI'), (400, 'CD'),
            (401, 'CDI'), (500, 'D'), (501, 'DI'), (900, 'CM'), (901, 'CMI'),
            (1000, 'M'), (1001, 'MI'), (1994, 'MCMXCIV'), (2024, 'MMXXIV'),
            (3999, 'MMMCMXCIX')
        ]
        for arabic, expected in cases:
            with self.subTest(arabic=arabic):
                self.assertEqual(to_roman(arabic), expected)
