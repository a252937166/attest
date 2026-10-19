import unittest

from brackets import is_balanced, is_bracket


class TestIsBalanced(unittest.TestCase):
    def test_empty_string_is_balanced(self):
        self.assertIs(is_balanced(''), True)

    def test_each_simple_pair_is_balanced(self):
        for value in ('()', '[]', '{}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_adjacent_pairs_are_balanced(self):
        self.assertIs(is_balanced('()[]{}'), True)

    def test_nested_pairs_are_balanced(self):
        for value in ('([{}])', '([]{})'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_nonbracket_characters_inside_pairs_are_ignored(self):
        for value in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_unmatched_openings_are_unbalanced(self):
        for value in ('(', '[', '{', '([]'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_unmatched_closings_are_unbalanced(self):
        for value in (')', ']', '}', '())'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_closing_before_opening_is_unbalanced(self):
        self.assertIs(is_balanced(')('), False)

    def test_mismatched_bracket_types_are_unbalanced(self):
        for value in ('(]', '{[}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_wrong_nesting_order_is_unbalanced(self):
        for value in ('([)]', '{(})'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_strings_without_ascii_brackets_are_balanced(self):
        for value in ('abc123', ' \t\n', '.,;:!?', '你好🙂（［｛）］｝'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_removing_nonbracket_characters_preserves_result(self):
        for value in ('x (a[b]{c}) y', 'prefix ([x)] suffix', 'é]中[🙂', 'one ( two', 'foo 123'):
            with self.subTest(value=value):
                brackets_only = ''.join(c for c in value if c in '()[]{}')
                self.assertEqual(is_balanced(value), is_balanced(brackets_only))

    def test_quotes_do_not_suppress_brackets(self):
        self.assertIs(is_balanced('"("'), False)

    def test_backslashes_do_not_suppress_brackets(self):
        self.assertIs(is_balanced('\\('), False)

    def test_every_string_result_has_bool_type(self):
        for value in ('', '()', '(', '([)]', 'ordinary text'):
            with self.subTest(value=value):
                self.assertIs(type(is_balanced(value)), bool)

    def test_nonstring_inputs_raise_type_error(self):
        for value in (None, True, 0, 1.5, b'()', [], (), {}, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    is_balanced(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_str_subclasses_are_accepted(self):
        class Text(str):
            pass

        self.assertIs(is_balanced(Text('([{}])')), True)
        self.assertIs(is_balanced(Text('([)]')), False)

    def test_successive_calls_are_independent(self):
        self.assertEqual([is_balanced(s) for s in ('(', '()', '')], [False, True, True])


class TestIsBracket(unittest.TestCase):
    def test_six_ascii_bracket_characters_are_recognized(self):
        for value in '()[]{}':
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), True)

    def test_other_inputs_are_not_brackets(self):
        for value in ('a', '', '((', 1):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
