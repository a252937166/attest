import itertools
import unittest
from collections import UserString

from brackets import is_balanced, is_bracket


class BreakerTests(unittest.TestCase):
    def test_every_open_close_pair_combination(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for opening, closing in itertools.product(pairs, repeat=2):
            value = opening + closing
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), pairs[opening] == closing)

    def test_exhaustive_short_bracket_streams(self):
        for length in range(6):
            for characters in itertools.product('()[]{}', repeat=length):
                value = ''.join(characters)
                reduced = value
                while True:
                    next_value = reduced.replace('()', '').replace('[]', '').replace('{}', '')
                    if next_value == reduced:
                        break
                    reduced = next_value
                with self.subTest(value=value):
                    self.assertIs(is_balanced(value), reduced == '')

    def test_deep_mixed_nesting_and_late_mismatch(self):
        openings = '([{' * 1000
        closings = '}])' * 1000
        self.assertIs(is_balanced(openings + closings), True)
        self.assertIs(is_balanced(openings + closings[:-1] + ']'), False)
        self.assertIs(is_balanced(openings + closings + ')'), False)

    def test_long_adjacent_groups_with_one_unmatched_opener(self):
        groups = '()[]{}' * 1000
        self.assertIs(is_balanced(groups), True)
        self.assertIs(is_balanced(groups[:3000] + '(' + groups[3000:]), False)
        self.assertIs(is_balanced(groups[:3000] + ')' + groups[3000:]), False)

    def test_unicode_lookalikes_and_controls_are_ignored(self):
        noise = '（ ）［ ］｛ ｝〈〉⟦⟧\u200b\x00\n\t😀'
        self.assertIs(is_balanced(noise), True)
        self.assertIs(is_balanced(noise + '([{}])' + noise), True)
        self.assertIs(is_balanced(noise + '([{})' + noise), False)
        self.assertIs(is_balanced(noise + '(' + noise), False)

    def test_quotes_and_backslashes_are_ordinary_noise(self):
        self.assertIs(is_balanced('"[" + "]"'), True)
        self.assertIs(is_balanced("'{' + '}'"), True)
        self.assertIs(is_balanced('\\\\('), False)
        self.assertIs(is_balanced('"\\\\[\\\\]"'), True)
        self.assertIs(is_balanced('"\\\\[\\\\)"'), False)

    def test_str_subclass_uses_its_string_contents(self):
        class MisleadingString(str):
            def __str__(self):
                return '()'

        self.assertIs(is_balanced(MisleadingString('(')), False)
        self.assertIs(is_balanced(MisleadingString('([])')), True)
        self.assertIs(is_balanced(MisleadingString('([)]')), False)

    def test_string_like_non_strings_are_rejected(self):
        class StringImpersonator:
            def __str__(self):
                return '()'

            def __iter__(self):
                return iter('()')

        for value in (UserString('()'), bytearray(b'()'), memoryview(b'()'), StringImpersonator()):
            with self.subTest(type=type(value)):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_is_bracket_accepts_only_single_ascii_brackets(self):
        class BracketString(str):
            pass

        for character in '()[]{}':
            with self.subTest(character=character):
                self.assertIs(is_bracket(BracketString(character)), True)
        for value in ('（', '）', '［', '］', '｛', '｝', '⟦', '⟧', '\x00', '()', UserString('(')):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
