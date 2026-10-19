import unittest
from brackets import is_balanced, is_bracket


class TestIsBalanced(unittest.TestCase):
    def test_empty_string_is_balanced(self):
        self.assertIs(is_balanced(''), True)

    def test_each_simple_pair_is_balanced(self):
        for s in ('()', '[]', '{}'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_adjacent_groups_are_balanced(self):
        for s in ('()[]{}', '{[]}[()]'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_nested_groups_are_balanced(self):
        for s in ('([{}])', '((()))'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_nonbracket_characters_inside_groups_are_ignored(self):
        for s in ('(a[b]{c})', 'f(x[0], y[1])'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_unmatched_openings_return_false(self):
        for s in ('(', '()(', '([', '{[]}[('):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_closings_without_openings_return_false(self):
        for s in (')', '())', ')(', ']['):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_wrong_types_and_crossed_nesting_return_false(self):
        for s in ('([)]', '(]', '{[}', '[}', '{(])}'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_strings_without_ascii_brackets_are_balanced(self):
        for s in ('abc123', ' \t\n', 'α🙂中', '!?.,;@#$%^&*-_=+<>/|~'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)

    def test_ignoring_other_characters_preserves_result(self):
        samples = ('a(b)c', 'x{y[z]}!', '(a[b)c]', 'λ]μ[ν', '1(2)3[4]5', 'α🙂{β[γ](δ)}!')
        for s in samples:
            with self.subTest(s=s):
                brackets_only = ''.join(c for c in s if c in '()[]{}')
                self.assertIs(is_balanced(s), is_balanced(brackets_only))

    def test_quotes_do_not_suppress_brackets(self):
        for s, expected in (('"("', False), ("'[']", True), ('"([)]"', False)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_backslashes_do_not_suppress_brackets(self):
        slash = chr(92)
        for s, expected in ((slash + '(', False), (slash + '()', True), ('(' + slash + ')', True)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_result_is_builtin_bool(self):
        for s in ('', '()', '(', '([)]', 'text'):
            with self.subTest(s=s):
                self.assertIs(type(is_balanced(s)), bool)

    def test_str_subclasses_are_accepted(self):
        class Text(str):
            pass

        for s, expected in ((Text('([{}])'), True), (Text('([)]'), False)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_nonstring_inputs_raise_type_error(self):
        values = (None, True, False, 0, 1, 1.5, b'()', bytearray(b'()'), [], ['()'], (), ('()',), {}, {'x': '()'}, set(), {'()'})
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    is_balanced(value)


class TestIsBracketPreserved(unittest.TestCase):
    def test_six_ascii_brackets_are_recognized(self):
        for c in '()[]{}':
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), True)

    def test_other_inputs_are_rejected(self):
        for c in ('a', '', '((', 1, None, '（'):
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), False)
