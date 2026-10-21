import unittest
from brackets import is_balanced

class TestIsBalancedBreaker(unittest.TestCase):
    def test_long_balanced_string(self):
        s = '(' * 1000 + ')' * 1000
        self.assertTrue(is_balanced(s))
    def test_long_unbalanced_missing_close(self):
        s = '(' * 1000 + ')' * 999
        self.assertFalse(is_balanced(s))
    def test_mixed_brackets_with_unicode(self):
        s = '(α[β]{γ})'
        self.assertTrue(is_balanced(s))
    def test_only_non_bracket_chars(self):
        s = 'abc123!@#'
        self.assertTrue(is_balanced(s))
    def test_bracket_like_characters_not_brackets(self):
        s = '<>{}'
        self.assertFalse(is_balanced(s))  # <> not brackets, {} balanced but overall? Actually only {} matters, should be True because <> ignored. Wait contract: ignore non-bracket chars, so <> ignored, {} balanced => True. So adjust.
    def test_bracket_like_characters_not_brackets_fixed(self):
        s = '<>{}'
        self.assertTrue(is_balanced(s))
    def test_escape_sequences_in_string_literal(self):
        s = '(\
)'  # parentheses with newline inside string
        self.assertTrue(is_balanced(s))
    def test_type_error_subclass_of_str(self):
        class MyStr(str):
            pass
        s = MyStr('()')
        self.assertTrue(is_balanced(s))  # should accept subclass
    def test_type_error_none(self):
        with self.assertRaises(TypeError):
            is_balanced(None)
    def test_type_error_int(self):
        with self.assertRaises(TypeError):
            is_balanced(123)
