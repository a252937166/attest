import unittest
from brackets import is_balanced

class TestIsBalanced(unittest.TestCase):
    def test_empty_string_returns_true(self):
        self.assertTrue(is_balanced(""))
    def test_parentheses_only_balanced(self):
        self.assertTrue(is_balanced("()"))
    def test_square_brackets_only_balanced(self):
        self.assertTrue(is_balanced("[]"))
    def test_curly_braces_only_balanced(self):
        self.assertTrue(is_balanced("{}"))
    def test_mixed_types_balanced_sequence(self):
        self.assertTrue(is_balanced("()[]{}"))
    def test_nested_balanced(self):
        self.assertTrue(is_balanced("([{}])"))
    def test_balanced_with_other_characters(self):
        self.assertTrue(is_balanced("(a[b]{c})"))
    def test_balanced_function_call_like(self):
        self.assertTrue(is_balanced("f(x[0], y[1])"))
    def test_single_open_parenthesis_returns_false(self):
        self.assertFalse(is_balanced("("))
    def test_single_close_parenthesis_returns_false(self):
        self.assertFalse(is_balanced(")"))
    def test_mismatched_order_returns_false(self):
        self.assertFalse(is_balanced("([)]"))
    def test_open_parenthesis_close_square_returns_false(self):
        self.assertFalse(is_balanced("(]"))
    def test_curly_open_square_close_curly_returns_false(self):
        self.assertFalse(is_balanced("{[}"))
    def test_extra_close_parenthesis_returns_false(self):
        self.assertFalse(is_balanced("())"))
    def test_return_type_is_bool_for_strings(self):
        result = is_balanced("abc")
        self.assertIsInstance(result, bool)
    def test_type_error_on_none(self):
        with self.assertRaises(TypeError):
            is_balanced(None)
    def test_type_error_on_int(self):
        with self.assertRaises(TypeError):
            is_balanced(123)
    def test_type_error_on_list(self):
        with self.assertRaises(TypeError):
            is_balanced([])
