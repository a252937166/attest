import unittest
from itertools import product

from brackets import is_balanced
from brackets import is_bracket


class PlainStr(str):
    pass


class TestBalanced(unittest.TestCase):
    def test_public_functions_are_importable(self):
        self.assertTrue(callable(is_balanced))
        self.assertTrue(callable(is_bracket))

    def test_basic_balanced_strings(self):
        for s in ('', '()', '[]', '{}', '()[]{}', '([{}])'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_brackets_with_interspersed_text(self):
        for s in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_mismatched_and_extra_brackets(self):
        for s in ('(', ')', '([)]', '(]', '{[}', '())'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_each_opening_bracket_alone(self):
        for s in '([{':
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_each_closing_bracket_alone(self):
        for s in ')]}':
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_unmatched_bracket_after_balanced_prefix(self):
        for s in ('()(', '()]'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_repeated_nesting_and_adjacent_groups(self):
        for s in ('((()))', '[{}]({[]})'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_strings_without_ascii_brackets(self):
        for s in ('abc', ' \t\n', '你好（）'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_quotes_and_backslashes_do_not_hide_brackets(self):
        cases = (("'()'", True), ('"[]"', True), ("'('", False), ('"}"', False), (chr(92) + '(', False), (chr(92) + ')', False), (chr(92) + '[' + chr(92) + ']', True))
        for s, expected in cases:
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_removing_nonbrackets_preserves_result(self):
        alphabet = "()[]{}a'你" + chr(92)
        samples = ('x([{}])y', 'hello (world]', 'f(x[0], y[1])', '你好（）', '"([)]"')
        for length in range(4):
            for chars in product(alphabet, repeat=length):
                s = ''.join(chars)
                stripped = ''.join(c for c in s if c in '()[]{}')
                with self.subTest(s=s):
                    self.assertIs(is_balanced(s), is_balanced(stripped))
        for s in samples:
            stripped = ''.join(c for c in s if c in '()[]{}')
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), is_balanced(stripped))

    def test_all_result_categories_have_exact_bool_type(self):
        for s in ('', 'abc', '()', '(', '([)]', '(a[b]{c})', '你好（）'):
            with self.subTest(s=s):
                self.assertIs(type(is_balanced(s)), bool)

    def test_non_string_inputs_raise_type_error(self):
        values = (None, True, 0, 1.5, b'()', [], ['(', ')'], (), {}, set())
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    is_balanced(value)

    def test_plain_str_subclass_is_accepted(self):
        for s in ('', 'abc', '([{}])', '([)]', 'f(x[0], y[1])'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(PlainStr(s)), is_balanced(s))
                self.assertIs(type(is_balanced(PlainStr(s))), bool)


class TestIsBracket(unittest.TestCase):
    def test_each_ascii_bracket_is_recognized(self):
        for c in '()[]{}':
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), True)

    def test_non_brackets_and_invalid_lengths_are_rejected(self):
        for c in ('a', '', '((', 1):
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), False)
