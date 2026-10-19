import unittest

from brackets import is_balanced, is_bracket


class TestBalanced(unittest.TestCase):
    def test_public_package_exports(self):
        self.assertTrue(callable(is_balanced))
        self.assertTrue(callable(is_bracket))

    def test_empty_and_simple_pairs_are_balanced(self):
        for value in ('', '()', '[]', '{}', '()[]{}', '([{}])'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_repeated_same_kind_nesting_is_balanced(self):
        for value in ('((()))', '[[]]', '{{}}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_adjacent_and_nested_pairs_are_balanced(self):
        self.assertIs(is_balanced('([]){}[()]'), True)

    def test_interspersed_text_is_ignored(self):
        for value in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_text_without_brackets_is_balanced(self):
        for value in ('ordinary text', ' \t\n ', '你好 🌍 café'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_inserting_or_removing_other_characters_preserves_result(self):
        for plain, decorated in (
            ('([{}])', 'x(α[ \t{q} ] z)y'),
            ('([)]', 'a(β[γ)δ]e'),
        ):
            with self.subTest(plain=plain):
                self.assertIs(is_balanced(decorated), is_balanced(plain))

    def test_quotes_and_backslashes_do_not_hide_brackets(self):
        for value, expected in (('"("', False), ('\\]', False), ("'[()]'", True)):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), expected)

    def test_crossed_and_mismatched_pairs_are_rejected(self):
        for value in ('([)]', '(]', '{[}'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_unmatched_opening_brackets_are_rejected(self):
        for value in ('(', '[', '{', '([]'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_unmatched_closing_brackets_are_rejected(self):
        for value in (')', ']', '}', ')(', '())', '[]]'):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_extra_opening_bracket_after_a_pair_is_rejected(self):
        self.assertIs(is_balanced('{}('), False)

    def test_string_results_are_actual_bools(self):
        for value in ('', '([{}])', 'ordinary text', '(', '([)]', ']'):
            with self.subTest(value=value):
                self.assertIs(type(is_balanced(value)), bool)

    def test_non_string_inputs_raise_type_error(self):
        for value in (None, True, 0, 1.5, b'()', [], (), {}, set()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    is_balanced(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_string_subclasses_follow_the_same_rules(self):
        class Text(str):
            pass

        for value, expected in ((Text('([{}])'), True), (Text('([)]'), False)):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), expected)

    def test_calls_do_not_share_bracket_state(self):
        self.assertIs(is_balanced('(['), False)
        self.assertIs(is_balanced('([])'), True)


class TestBracketHelper(unittest.TestCase):
    def test_each_bracket_character_is_recognized(self):
        for value in '()[]{}':
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), True)

    def test_other_values_are_not_recognized(self):
        for value in ('a', '', '((', 1):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
