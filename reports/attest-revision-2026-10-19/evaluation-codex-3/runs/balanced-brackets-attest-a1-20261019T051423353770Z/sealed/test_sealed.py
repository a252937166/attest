import unittest

from brackets import is_balanced, is_bracket


class TestBalanced(unittest.TestCase):
    def test_public_exports_are_callable(self):
        self.assertTrue(callable(is_balanced))
        self.assertTrue(callable(is_bracket))

    def test_empty_string_is_balanced(self):
        self.assertIs(is_balanced(''), True)

    def test_each_simple_pair_and_concatenation_are_balanced(self):
        for value in ('()', '[]', '{}', '()[]{}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_mixed_nesting_is_balanced(self):
        self.assertIs(is_balanced('([{}])'), True)

    def test_ordinary_text_between_brackets_is_ignored(self):
        for value in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_mismatched_and_extra_brackets_are_rejected(self):
        for value in ('(', ')', '([)]', '(]', '{[}', '())'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_unmatched_openings_of_each_kind_are_rejected(self):
        for value in ('[', '{', '(()', '([]'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_premature_closings_of_each_kind_are_rejected(self):
        for value in (']', '}', ')(', '][', '}{'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_deep_nesting_and_concatenation_are_balanced(self):
        for value in ('((()))', '[[]]', '{{}}', '([]){}[()]'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_quotes_and_backslashes_do_not_change_bracket_meaning(self):
        for value, expected in (('"("', False), ('\\)', False), ("'[]'", True), ('\\[{}]\\', True)):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), expected)

    def test_removing_ignored_characters_preserves_result(self):
        samples = ('a\n(中[😊]{x})\\\"', '"("', '\\)', 'a[ b ) c ]', '你好（）', '\t{\n[ ]}\t')
        for value in samples:
            with self.subTest(value=value):
                brackets_only = ''.join(c for c in value if c in '()[]{}')
                self.assertIs(is_balanced(value), is_balanced(brackets_only))

    def test_strings_without_ascii_brackets_are_balanced(self):
        for value in ('abc', ' \t\n', '你好（）'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_result_type_is_bool_for_true_and_false_cases(self):
        for value in ('', 'abc', '()', '(', '([)]', '([]){}[()]'):
            with self.subTest(value=value):
                self.assertIs(type(is_balanced(value)), bool)

    def test_non_string_inputs_raise_type_error(self):
        values = (None, True, 0, 1.5, b'()', [], (), {}, iter(['(', ')']))
        for value in values:
            with self.subTest(value=repr(value)):
                with self.assertRaises(TypeError) as cm:
                    is_balanced(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_str_subclass_uses_the_same_matching_rules(self):
        class StringSubclass(str):
            pass

        for value, expected in (('([{}])', True), ('text', True), ('([)]', False), ('[', False)):
            with self.subTest(value=value):
                self.assertIs(is_balanced(StringSubclass(value)), expected)

    def test_repeated_calls_are_independent(self):
        results = [is_balanced(value) for value in ('(', '()', ')', '')]
        self.assertEqual(results, [False, True, False, True])


class TestBracketHelper(unittest.TestCase):
    def test_each_ascii_bracket_is_recognized(self):
        for value in '()[]{}':
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), True)

    def test_original_non_bracket_examples_are_rejected(self):
        for value in ('a', '', '((', 1):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
