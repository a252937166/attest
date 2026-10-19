import unittest

from brackets import is_balanced, is_bracket


class TestBalanced(unittest.TestCase):
    def test_public_api_exports(self):
        self.assertTrue(callable(is_balanced))
        self.assertTrue(callable(is_bracket))

    def test_empty_and_simple_balanced_strings(self):
        for s in ('', '()', '[]', '{}', '()[]{}'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_nested_balanced_string(self):
        self.assertIs(is_balanced('([{}])'), True)

    def test_text_between_brackets(self):
        for s in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_representative_unbalanced_strings(self):
        for s in ('(', ')', '([)]', '(]', '{[}', '())'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_unmatched_openings_of_every_kind(self):
        for s in ('(', '[', '{', '(()'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_unmatched_closings_of_every_kind(self):
        for s in (')', ']', '}', ')('):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_wrong_type_or_nesting_order(self):
        for s in ('[)', '{]', '([)]', '[(])'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_removing_nonbrackets_preserves_result(self):
        samples = ('a(b[c]{d})!', 'x([)]y', '🙂[x)世界', "'(' ", chr(92) + '(', 'plain text')
        for s in samples:
            with self.subTest(s=s):
                filtered = ''.join(c for c in s if c in '()[]{}')
                self.assertIs(is_balanced(s), is_balanced(filtered))

    def test_strings_without_brackets_are_balanced(self):
        for s in ('ordinary text', ' \t\n ', '世界 café 🙂'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_quotes_do_not_hide_brackets(self):
        for s, expected in (("'('", False), ('"[]"', True), ('"("', False), ("'{", False)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_backslashes_do_not_escape_brackets(self):
        slash = chr(92)
        for s, expected in ((slash + '(', False), (slash + ')', False), (slash + '()', True)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_result_is_exactly_bool(self):
        for s in ('', '()', '(', '([)]', 'words', 'a[b]'):
            with self.subTest(s=s):
                self.assertIs(type(is_balanced(s)), bool)

    def test_nonstring_inputs_raise_type_error(self):
        values = (None, True, 0, 1.5, b'()', [], ['(', ')'], {}, object(), ('(', ')'), iter('()'))
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    is_balanced(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_str_subclasses_are_evaluated(self):
        class Text(str):
            pass

        for s, expected in ((Text('([{}])'), True), (Text('a[b)'), False), (Text(''), True)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)


class TestBracketHelper(unittest.TestCase):
    def test_is_bracket_accepts_six_ascii_brackets(self):
        for c in '()[]{}':
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), True)

    def test_is_bracket_rejects_other_values(self):
        for c in ('a', '', '((', 1):
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), False)
