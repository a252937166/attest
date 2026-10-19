import itertools
import unittest

from brackets import is_balanced, is_bracket


class BreakerTests(unittest.TestCase):
    PAIRS = {'(': ')', '[': ']', '{': '}'}
    SYMBOLS = '()[]{}'

    def test_every_two_bracket_sequence(self):
        valid = {opener + closer for opener, closer in self.PAIRS.items()}
        for chars in itertools.product(self.SYMBOLS, repeat=2):
            value = ''.join(chars)
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), value in valid)

    def test_every_three_bracket_sequence_is_unbalanced(self):
        for chars in itertools.product(self.SYMBOLS, repeat=3):
            value = ''.join(chars)
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_all_mixed_nested_and_adjacent_triples(self):
        for outer, inner, trailing in itertools.product(self.PAIRS, repeat=3):
            value = outer + inner + self.PAIRS[inner] + self.PAIRS[outer]
            value += trailing + self.PAIRS[trailing]
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_a_mismatch_cannot_be_repaired_by_later_brackets(self):
        for opener, wrong_closer in itertools.product(self.PAIRS, self.PAIRS.values()):
            if wrong_closer == self.PAIRS[opener]:
                continue
            value = opener + wrong_closer + self.PAIRS[opener] + '()[]{}'
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_deep_mixed_nesting_and_one_wrong_inner_closer(self):
        openings = '([{' * 1000
        closings = '}])' * 1000
        self.assertIs(is_balanced(openings + closings), True)
        self.assertIs(is_balanced(openings + ']' + closings), False)
        self.assertIs(is_balanced(openings + closings[:-1]), False)

    def test_unicode_lookalikes_do_not_act_as_brackets(self):
        decoration = '（ ）［ ］｛ ｝❨ ❩【 】〈 〉'
        self.assertIs(is_balanced(decoration), True)
        self.assertIs(is_balanced('(' + decoration + ')'), True)
        self.assertIs(is_balanced('(' + decoration + ']'), False)

    def test_other_non_string_types_are_rejected(self):
        values = (1 + 2j, range(3), memoryview(b'()'), frozenset(), bytearray(b'[]'), object())
        for value in values:
            with self.subTest(type=type(value)):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_is_bracket_rejects_lookalikes_and_multiple_characters(self):
        for value in ('（', '❨', '【', '\n', '()', '[]', ' ｛', b'(', None):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
