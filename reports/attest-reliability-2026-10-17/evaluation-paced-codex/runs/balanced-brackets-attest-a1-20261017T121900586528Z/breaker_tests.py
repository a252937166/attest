import itertools
import unittest

from brackets import is_balanced, is_bracket


class BreakerTests(unittest.TestCase):
    def test_all_short_bracket_sequences_against_independent_oracle(self):
        def expected(s):
            previous = None
            while s != previous:
                previous = s
                for pair in ('()', '[]', '{}'):
                    s = s.replace(pair, '')
            return s == ''

        for length in range(4):
            for chars in itertools.product('()[]{}', repeat=length):
                s = ''.join(chars)
                with self.subTest(s=s):
                    self.assertIs(is_balanced(s), expected(s))

    def test_all_orders_of_three_nested_bracket_types(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for openings in itertools.permutations(pairs):
            s = ''.join(openings) + ''.join(pairs[c] for c in reversed(openings))
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)
                self.assertIs(is_balanced(s[:-1]), False)

    def test_valid_prefix_followed_by_a_wrong_closer(self):
        for prefix in ('()[]{}', '([{}])', '{[()()]}'):
            for bad_suffix in (')', ']', '}'):
                with self.subTest(prefix=prefix, suffix=bad_suffix):
                    self.assertIs(is_balanced(prefix + bad_suffix), False)

    def test_deep_nesting_and_one_missing_closer(self):
        opening = '([{' * 500
        closing = '}])' * 500
        self.assertIs(is_balanced(opening + closing), True)
        self.assertIs(is_balanced(opening + closing[:-1]), False)
        self.assertIs(is_balanced(opening + closing + ']'), False)

    def test_unicode_lookalikes_do_not_count_as_ascii_brackets(self):
        for s in ('（［｛｝］）', '❨❩❲❳', '〈〉「」', '（a）[b]'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), True)
        self.assertIs(is_balanced('（]'), False)
        self.assertIs(is_balanced('(）'), False)

    def test_quotes_and_backslashes_are_ordinary_non_bracket_text(self):
        for s, expected in (("'['", False), ('"}"', False), ('\\(', False), ('\\[\\]', True), ('"([{}])"', True)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), expected)

    def test_plain_str_subclasses_follow_the_same_rules(self):
        class Text(str):
            pass

        for s, expected in (('', True), ('x', True), ('{a[(b)]}', True), ('{a[(b])}', False), (']', False)):
            with self.subTest(s=s):
                self.assertIs(is_balanced(Text(s)), expected)

    def test_additional_non_string_types_raise_and_do_not_affect_next_call(self):
        for value in (bytearray(b'()'), memoryview(b'[]'), range(2), frozenset(), 1 + 2j, Ellipsis):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError):
                    is_balanced(value)
                self.assertIs(is_balanced('{[]}'), True)

    def test_is_bracket_requires_one_ascii_character(self):
        class Character(str):
            pass

        for c in '()[]{}':
            with self.subTest(c=c):
                self.assertIs(is_bracket(Character(c)), True)
        for value in ('（', '❨', '()', ' [', bytearray(b'('), None):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
