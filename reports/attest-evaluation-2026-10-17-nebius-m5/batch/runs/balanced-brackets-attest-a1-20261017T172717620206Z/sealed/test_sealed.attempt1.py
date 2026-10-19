import unittest
from brackets import is_balanced

class TestIsBalanced(unittest.TestCase):
    def test_empty_string_returns_true(self):
        self.assertTrue(is_balanced(''))
    
    def test_simple_parentheses(self):
        self.assertTrue(is_balanced('()'))
    
    def test_simple_square(self):
        self.assertTrue(is_balanced('[]'))
    
    def test_simple_curly(self):
        self.assertTrue(is_balanced('{}'))
    
    def test_concatenated_pairs(self):
        self.assertTrue(is_balanced('()[]{}'))
    
    def test_nested_mixed(self):
        self.assertTrue(is_balanced('([{}])'))
    
    def test_balanced_with_non_brackets(self):
        self.assertTrue(is_balanced('(a[b]{c})'))
    
    def test_function_like_string(self):
        self.assertTrue(is_balanced('f(x[0], y[1])'))
    
    def test_unclosed_opening(self):
        self.assertFalse(is_balanced('('))
    
    def test_unmatched_closing(self):
        self.assertFalse(is_balanced(')'))
    
    def test_incorrectly_nested(self):
        self.assertFalse(is_balanced('([)]'))
    
    def test_mismatched_parenthesis_square(self):
        self.assertFalse(is_balanced('(]'))
    
    def test_mismatched_curly_square(self):
        self.assertFalse(is_balanced('{[}'))
    
    def test_extra_closing(self):
        self.assertFalse(is_balanced('())'))
    
    def test_non_bracket_characters_only(self):
        self.assertTrue(is_balanced('abc'))
    
    def test_non_bracket_interleaved(self):
        self.assertTrue(is_balanced('a(b)c'))
    
    def test_return_type_is_bool(self):
        result = is_balanced('')
        self.assertIsInstance(result, bool)
        result = is_balanced('([)]')
        self.assertIsInstance(result, bool)
    
    def test_type_error_on_non_string(self):
        for bad in (123, None, [], {}):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    is_balanced(bad)
