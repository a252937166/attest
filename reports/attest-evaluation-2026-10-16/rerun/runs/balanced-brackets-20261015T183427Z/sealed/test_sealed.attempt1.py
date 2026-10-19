import unittest
from brackets import is_balanced, is_bracket

class TestIsBalanced(unittest.TestCase):
    def test_empty_string(self):
        self.assertTrue(is_balanced(''))
    def test_simple_parentheses(self):
        self.assertTrue(is_balanced('()'))
    def test_simple_brackets(self):
        self.assertTrue(is_balanced('[]'))
    def test_simple_braces(self):
        self.assertTrue(is_balanced('{}'))
    def test_multiple_types_seq(self):
        self.assertTrue(is_balanced('()[]{}'))
    def test_nested_properly(self):
        self.assertTrue(is_balanced('([{}])'))
    def test_mixed_with_letters(self):
        self.assertTrue(is_balanced('(a[b]{c})'))
    def test_function_call_like(self):
        self.assertTrue(is_balanced('f(x[0], y[1])'))
    def test_single_open_paren_false(self):
        self.assertFalse(is_balanced('('))
    def test_single_close_paren_false(self):
        self.assertFalse(is_balanced(')'))
    def test_misordered_closes(self):
        self.assertFalse(is_balanced('([)]'))
    def test_wrong_type_pair(self):
        self.assertFalse(is_balanced('(]'))
    def test_wrong_type_pair2(self):
        self.assertFalse(is_balanced('{[}'))
    def test_extra_closing(self):
        self.assertFalse(is_balanced('())'))
    def test_nonbracket_only_true(self):
        self.assertTrue(is_balanced('a'))
    def test_open_with_letter_false(self):
        self.assertFalse(is_balanced('(a'))
    def test_close_with_letter_false(self):
        self.assertFalse(is_balanced('a)'))
    def test_returns_bool(self):
        self.assertIsInstance(is_balanced(''), bool)
        self.assertIsInstance(is_balanced('('), bool)
        self.assertIsInstance(is_balanced('abc'), bool)
    def test_type_error_nonstring(self):
        for val in (None, 123, [], {}):
            with self.assertRaises(TypeError):
                is_balanced(val)
    def test_is_bracket_true_for_each(self):
        for c in '()[]{}':
            self.assertTrue(is_bracket(c))
    def test_is_bracket_false_for_others(self):
        for c in ('a', '', '(', '[[', 1, None):
            self.assertFalse(is_bracket(c))
