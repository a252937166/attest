import unittest
from brackets import is_balanced

class TestBreaker(unittest.TestCase):
    def test_only_non_bracket_chars_returns_true(self):
        self.assertTrue(is_balanced('abc123!@#'))
    def test_deep_nesting_balanced(self):
        s = '(' * 1000 + '[' * 1000 + '{' * 1000 + '}' * 1000 + ']' * 1000 + ')' * 1000
        self.assertTrue(is_balanced(s))
    def test_deep_nesting_unbalanced_missing_close(self):
        s = '(' * 1000 + '[' * 1000 + '{' * 1000
        self.assertFalse(is_balanced(s))
    def test_large_string_with_random_chars_and_balanced_brackets(self):
        import string
        brackets = '()[]{}'
        # create balanced pattern then fill with random non-bracket chars
        pattern = ''.join(['()', '[]', '{}'] * 100)
        random_chars = ''.join(string.ascii_letters for _ in range(5000))
        s = pattern + random_chars
        self.assertTrue(is_balanced(s))
    def test_type_error_on_float(self):
        with self.assertRaises(TypeError):
            is_balanced(3.14)
    def test_type_error_on_dict(self):
        with self.assertRaises(TypeError):
            is_balanced({'a': 1})
    def test_type_error_on_set(self):
        with self.assertRaises(TypeError):
            is_balanced({1,2,3})
    def test_return_type_is_bool_for_all_string_inputs(self):
        for s in ['', '(', ')', '()', '(]', 'abc', None]:  # None will raise, catch
            if s is None:
                continue
            self.assertIsInstance(is_balanced(s), bool)
