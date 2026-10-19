import unittest
from brackets import is_balanced, is_bracket

class TestIsBalanced(unittest.TestCase):
    def test_empty_string_returns_true(self):
        self.assertTrue(is_balanced(''))
    
    def test_simple_parentheses(self):
        self.assertTrue(is_balanced('()'))
    
    def test_simple_square(self):
        self.assertTrue(is_balanced('[]'))
    
    def test_simple_curly(self):
        self.assertTrue(is_balanced('{}'))
    
    def test_multiple_types_ordered(self):
        self.assertTrue(is_balanced('()[]{}'))
    
    def test_nested_properly(self):
        self.assertTrue(is_balanced('([{}])'))
    
    def test_with_letters_and_numbers(self):
        self.assertTrue(is_balanced('(a[b]{c})'))
    
    def test_function_call_like(self):
        self.assertTrue(is_balanced('f(x[0], y[1])'))
    
    def test_single_open_parenthesis_false(self):
        self.assertFalse(is_balanced('('))
    
    def test_single_close_parenthesis_false(self):
        self.assertFalse(is_balanced(')'))
    
    def test_misordered_closes(self):
        self.assertFalse(is_balanced('([)]'))
    
    def test_wrong_type_pair(self):
        self.assertFalse(is_balanced('(]'))
    
    def test_curly_wrong_pair(self):
        self.assertFalse(is_balanced('{[}'))
    
    def test_extra_close(self):
        self.assertFalse(is_balanced('())'))
    
    def test_non_bracket_only_true(self):
        self.assertTrue(is_balanced('a'))
    
    def test_non_bracket_with_balanced(self):
        self.assertTrue(is_balanced('(a)'))
    
    def test_return_type_is_bool(self):
        result = is_balanced('()')
        self.assertIsInstance(result, bool)
    
    def test_type_error_on_non_string(self):
        for bad in (123, None, [1,2], {'a':1}):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    is_balanced(bad)
    
    def test_is_bracket_preserved(self):
        # reuse existing test logic
        for c in "()[]{}":
            self.assertTrue(is_bracket(c))
        for c in ("a", "", "((", 1):
            self.assertFalse(is_bracket(c))
