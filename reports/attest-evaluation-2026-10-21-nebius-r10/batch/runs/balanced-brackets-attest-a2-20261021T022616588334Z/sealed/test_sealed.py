import unittest
from brackets import is_balanced

class TestIsBalanced(unittest.TestCase):
    def test_empty_string_is_balanced(self):
        self.assertTrue(is_balanced(''))

    def test_simple_pairs_balanced(self):
        self.assertTrue(is_balanced('()'))
        self.assertTrue(is_balanced('[]'))
        self.assertTrue(is_balanced('{}'))

    def test_multiple_pairs_balanced(self):
        self.assertTrue(is_balanced('()[]{}'))

    def test_nested_balanced(self):
        self.assertTrue(is_balanced('([{}])'))

    def test_nested_with_other_chars(self):
        self.assertTrue(is_balanced('(a[b]{c})'))
        self.assertTrue(is_balanced('f(x[0], y[1])'))

    def test_unbalanced_single_open(self):
        self.assertFalse(is_balanced('('))

    def test_unbalanced_single_close(self):
        self.assertFalse(is_balanced(')'))

    def test_wrong_order(self):
        self.assertFalse(is_balanced('([)]'))

    def test_mismatched_types(self):
        self.assertFalse(is_balanced('(]'))
        self.assertFalse(is_balanced('{[}'))

    def test_extra_closing(self):
        self.assertFalse(is_balanced('())'))

    def test_non_bracket_ignored(self):
        self.assertTrue(is_balanced('abc'))
        self.assertTrue(is_balanced('a(b)c[d]{e}f'))

    def test_return_type_bool(self):
        result = is_balanced('')
        self.assertIsInstance(result, bool)
        result = is_balanced('(')
        self.assertIsInstance(result, bool)

    def test_type_error_non_string(self):
        with self.assertRaises(TypeError):
            is_balanced(123)
        with self.assertRaises(TypeError):
            is_balanced(None)
        with self.assertRaises(TypeError):
            is_balanced(['()'])
