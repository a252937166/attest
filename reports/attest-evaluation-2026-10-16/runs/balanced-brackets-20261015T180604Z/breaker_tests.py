import unittest
from brackets import is_balanced

class TestBreaker(unittest.TestCase):
    def test_multiple_openings_unbalanced(self):
        self.assertFalse(is_balanced("((("))

    def test_multiple_closings_unbalanced(self):
        self.assertFalse(is_balanced(")))"))

    def test_mixed_unbalanced_open_close(self):
        self.assertFalse(is_balanced("([)"))

    def test_deep_nesting_single_type(self):
        s = "(" * 1000 + ")" * 1000
        self.assertTrue(is_balanced(s))

    def test_deep_nesting_mixed_types(self):
        opens = "([{"
        closes = ")]}"
        depth = 500
        s = ''
        stack = []
        for i in range(depth):
            o = opens[i % 3]
            stack.append(o)
            s += o
        while stack:
            o = stack.pop()
            s += {'(': ')', '[': ']', '{': '}'}[o]
        self.assertTrue(is_balanced(s))

    def test_unicode_brackets_ignored(self):
        self.assertTrue(is_balanced("a【b】c"))
        self.assertTrue(is_balanced("(【】)"))

    def test_bytes_input_type_error(self):
        with self.assertRaises(TypeError):
            is_balanced(b"hello")

    def test_float_input_type_error(self):
        with self.assertRaises(TypeError):
            is_balanced(3.14)

    def test_dict_input_type_error(self):
        with self.assertRaises(TypeError):
            is_balanced({"a": 1})

    def test_set_input_type_error(self):
        with self.assertRaises(TypeError):
            is_balanced({1, 2, 3})

    def test_custom_object_type_error(self):
        class Obj: pass
        with self.assertRaises(TypeError):
            is_balanced(Obj())

    def test_whitespace_and_newline(self):
        s = "\n ( [ { } ] ) \t"
        self.assertTrue(is_balanced(s))

    def test_only_closing_brackets(self):
        self.assertFalse(is_balanced(")]}"))

    def test_only_opening_brackets(self):
        self.assertFalse(is_balanced("([{"))
