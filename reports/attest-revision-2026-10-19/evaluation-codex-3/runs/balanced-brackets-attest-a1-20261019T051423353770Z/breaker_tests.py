import unittest
from collections import UserString
from itertools import product

from brackets import is_balanced, is_bracket


class BreakerTests(unittest.TestCase):
    def test_every_two_bracket_sequence(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for left, right in product('()[]{}', repeat=2):
            with self.subTest(left=left, right=right):
                self.assertIs(is_balanced(left + right), pairs.get(left) == right)

    def test_every_three_bracket_sequence_is_unbalanced(self):
        for chars in product('()[]{}', repeat=3):
            with self.subTest(chars=chars):
                self.assertIs(is_balanced(''.join(chars)), False)

    def test_all_two_pair_nesting_and_concatenation(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for first, second in product(pairs, repeat=2):
            nested = first + second + pairs[second] + pairs[first]
            adjacent = first + pairs[first] + second + pairs[second]
            with self.subTest(first=first, second=second):
                self.assertIs(is_balanced(nested), True)
                self.assertIs(is_balanced(adjacent), True)

    def test_crossed_pairs_remain_invalid_with_text_between(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for first, second in product(pairs, repeat=2):
            if first == second:
                continue
            value = first + 'text' + second + '\n' + pairs[first] + 'text' + pairs[second]
            with self.subTest(first=first, second=second):
                self.assertIs(is_balanced(value), False)

    def test_extra_closers_at_either_end(self):
        for valid in ('()', '[{}]', '{([])}'):
            for closer in ')]}':
                with self.subTest(valid=valid, closer=closer):
                    self.assertIs(is_balanced(closer + valid), False)
                    self.assertIs(is_balanced(valid + closer), False)

    def test_long_mixed_nesting_and_final_mismatch(self):
        opening = '([{' * 300
        closing = '}])' * 300
        self.assertIs(is_balanced(opening + closing), True)
        self.assertIs(is_balanced(opening + closing[:-1] + ']'), False)

    def test_ignored_characters_have_no_escape_or_quote_effect(self):
        ignored = ('\x00', '（', '）', '\u200d', '\U0001f600', "'", '"', '\\', '\n')
        for character in ignored:
            with self.subTest(character=character):
                self.assertIs(is_balanced('[' + character + ']'), True)
                self.assertIs(is_balanced(']' + character + '['), False)

    def test_other_string_like_and_iterable_inputs_raise_type_error(self):
        values = (UserString('()'), bytearray(b'()'), memoryview(b'()'),
                  range(2), {'(': ')'}, {'(', ')'}, iter('()'), 1 + 2j)
        for value in values:
            with self.subTest(value_type=type(value)):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_is_bracket_for_every_ascii_character(self):
        for codepoint in range(128):
            character = chr(codepoint)
            with self.subTest(codepoint=codepoint):
                self.assertIs(is_bracket(character), character in '()[]{}')
