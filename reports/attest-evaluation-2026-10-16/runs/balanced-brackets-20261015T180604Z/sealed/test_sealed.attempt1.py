import unittest
from brackets import is_balanced

class TestIsBalanced(unittest.TestCase):
    def test_empty_string(self):
        self.assertTrue(is_balanced(""))
    def test_single_pair_parentheses(self):
        self.assertTrue(is_balanced("()"))
    def test_single_pair_square(self):
        self.assertTrue(is_balanced("[]"))
    def test_single_pair_curly(self):
        self.assertTrue(is_balanced("{}"))
    def test_multiple_adjacent_pairs(self):
        self.assertTrue(is_balanced("()[]{}"))
    def test_nested_mixed_brackets(self):
        self.assertTrue(is_balanced("([{}])"))
    def test_nested_with_other_chars1(self):
        self.assertTrue(is_balanced("(a[b]{c})"))
    def test_nested_with_other_chars2(self):
        self.assertTrue(is_balanced("f(x[0], y[1])"))
    def test_unbalanced_opening(self):
        self.assertFalse(is_balanced("("))
    def test_unbalanced_closing(self):
        self.assertFalse(is_balanced(")"))
    def test_mismatched_round_square(self):
        self.assertFalse(is_balanced("([)]"))
    def test_mismatched_round_curly(self):
        self.assertFalse(is_balanced("(]"))
    def test_mismatched_curly_square(self):
        self.assertFalse(is_balanced("{[}"))
    def test_extra_closing(self):
        self.assertFalse(is_balanced("()))"))
    def test_non_bracket_only(self):
        self.assertTrue(is_balanced("abc"))
    def test_returns_bool(self):
        result = is_balanced("()")
        self.assertIsInstance(result, bool)
    def test_type_error_int(self):
        with self.assertRaises(TypeError):
            is_balanced(123)
    def test_type_error_list(self):
        with self.assertRaises(TypeError):
            is_balanced([1,2])
    def test_type_error_none(self):
        with self.assertRaises(TypeError):
            is_balanced(None)
