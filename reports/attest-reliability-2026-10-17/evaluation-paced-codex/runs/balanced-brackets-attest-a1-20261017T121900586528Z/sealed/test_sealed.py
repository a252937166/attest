import unittest

from brackets import is_balanced, is_bracket


class TestIsBalanced(unittest.TestCase):
    def test_empty_string_is_balanced(self):
        self.assertIs(is_balanced(''), True)

    def test_strings_without_ascii_brackets_are_balanced(self):
        for value in ('abc', ' \t\n', '你好（）', '"\\é'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_each_simple_pair_is_balanced(self):
        for value in ('()', '[]', '{}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_adjacent_pairs_are_balanced(self):
        self.assertIs(is_balanced('()[]{}'), True)

    def test_nested_pairs_are_balanced(self):
        self.assertIs(is_balanced('([{}])'), True)

    def test_other_text_between_brackets_is_ignored(self):
        for value in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_single_unmatched_brackets_are_rejected(self):
        for value in ('(', ')'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_crossed_or_mismatched_pairs_are_rejected(self):
        for value in ('([)]', '(]', '{[}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_extra_closing_bracket_is_rejected(self):
        self.assertIs(is_balanced('())'), False)

    def test_closing_brackets_before_opening_brackets_are_rejected(self):
        for value in (')(', '][', '}{'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_opening_brackets_left_at_end_are_rejected(self):
        for value in ('(()', '[[]', '{{}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_removing_non_bracket_characters_preserves_result(self):
        samples = ('a(\n[b] c)', '你{好[世]界}', '"([)]"', '\\)(', 'x（[y]）z', '\n{\t}\n')
        for value in samples:
            with self.subTest(value=value):
                projected = ''.join(c for c in value if c in '()[]{}')
                self.assertIs(is_balanced(value), is_balanced(projected))

    def test_quotes_and_backslashes_do_not_suppress_brackets(self):
        self.assertIs(is_balanced('"("'), False)
        self.assertIs(is_balanced(chr(92) + '()'), True)

    def test_every_result_is_an_actual_bool(self):
        for value in ('', 'abc', '()', '(', '([{}])', '([)]', '\n[你]\n'):
            with self.subTest(value=value):
                self.assertIs(type(is_balanced(value)), bool)

    def test_string_subclasses_are_accepted(self):
        class StringSubclass(str):
            pass

        self.assertIs(is_balanced(StringSubclass('x({[]})y')), True)
        self.assertIs(is_balanced(StringSubclass('x([)]y')), False)

    def test_non_string_inputs_raise_type_error(self):
        for value in (None, True, 0, 1.5, b'()', ['(', ')'], ('(', ')'), {}, set()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    is_balanced(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_false_result_does_not_affect_later_calls(self):
        self.assertIs(is_balanced('([)]'), False)
        self.assertIs(is_balanced('[]'), True)

    def test_type_error_does_not_affect_later_calls(self):
        with self.assertRaises(TypeError) as cm:
            is_balanced(None)
        self.assertIs(type(cm.exception), TypeError)
        self.assertIs(is_balanced('{}'), True)


class TestIsBracket(unittest.TestCase):
    def test_six_ascii_brackets_are_recognized(self):
        for value in '()[]{}':
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), True)

    def test_other_values_are_rejected(self):
        for value in ('a', '', '((', 1):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
