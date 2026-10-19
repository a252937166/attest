import unittest
from brackets import is_balanced

class TestBreaker(unittest.TestCase):
    def test_deeply_nested_balanced(self):
        s = '(' * 1000 + '[' * 500 + '{' * 500 + '}' * 500 + ']' * 500 + ')' * 1000
        self.assertTrue(is_balanced(s))
    def test_deeply_nested_unbalanced_missing_close(self):
        s = '(' * 1000 + '[' * 500 + '{' * 500 + '}' * 500 + ']' * 500
        self.assertFalse(is_balanced(s))
    def test_alternating_brackets_long(self):
        s = ''.join(['()' for _ in range(500)])
        self.assertTrue(is_balanced(s))
    def test_mixed_with_many_non_brackets(self):
        s = 'a'*1000 + '(' + 'b'*1000 + '[' + 'c'*1000 + '{' + 'd'*1000 + '}' + 'e'*1000 + ']' + 'f'*1000 + ')' + 'g'*1000
        self.assertTrue(is_balanced(s))
    def test_unicode_non_bracket_ignored(self):
        s = '(αβγ)[δεζ]{ηθι}'
        self.assertTrue(is_balanced(s))
    def test_type_error_various_non_strings(self):
        for val in [None, 0, 123, [], {}, set(), b'bytes']:
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    is_balanced(val)
    def test_return_type_is_bool_for_edge_strings(self):
        self.assertIsInstance(is_balanced(''), bool)
        self.assertIsInstance(is_balanced('('), bool)
        self.assertIsInstance(is_balanced(')'), bool)
        self.assertIsInstance(is_balanced('([)]'), bool)
    def test_single_bracket_chars(self):
        self.assertFalse(is_balanced('('))
        self.assertFalse(is_balanced(')'))
        self.assertFalse(is_balanced('['))
        self.assertFalse(is_balanced(']'))
        self.assertFalse(is_balanced('{'))
        self.assertFalse(is_balanced('}'))
    def test_impossible_long_string_performance(self):
        # ensure no excessive runtime; just a moderate size
        s = '(' * 10000 + ')' * 10000
        self.assertTrue(is_balanced(s))
