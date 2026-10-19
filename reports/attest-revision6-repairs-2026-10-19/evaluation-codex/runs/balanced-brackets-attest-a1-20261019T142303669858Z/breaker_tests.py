import unittest
from itertools import product
from brackets import is_balanced, is_bracket


class BreakerTests(unittest.TestCase):
    def test_every_two_character_ascii_pattern(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for first, second in product('()[]{}', repeat=2):
            with self.subTest(first=first, second=second):
                self.assertIs(is_balanced(first + second), pairs.get(first) == second)

    def test_all_three_character_bracket_strings_are_unbalanced(self):
        for chars in product('()[]{}', repeat=3):
            with self.subTest(chars=chars):
                self.assertIs(is_balanced(''.join(chars)), False)

    def test_every_three_level_nesting_and_wrong_middle_close(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        wrong = {')': ']', ']': '}', '}': ')'}
        for openings in product(pairs, repeat=3):
            closings = ''.join(pairs[c] for c in reversed(openings))
            valid = ''.join(openings) + closings
            invalid = ''.join(openings) + closings[0] + wrong[closings[1]] + closings[2]
            with self.subTest(openings=openings):
                self.assertIs(is_balanced(valid), True)
                self.assertIs(is_balanced(invalid), False)

    def test_adjacent_and_crossed_pair_orders(self):
        pairs = {'(': ')', '[': ']', '{': '}'}
        for first, second in product(pairs, repeat=2):
            with self.subTest(first=first, second=second):
                self.assertIs(is_balanced(first + pairs[first] + second + pairs[second]), True)
                self.assertIs(
                    is_balanced(first + second + pairs[first] + pairs[second]),
                    first == second,
                )

    def test_quotes_and_backslashes_never_mask_single_brackets(self):
        for bracket in '()[]{}':
            for surrounding in ('"', "'", '\\', '"\\', "\\'"):
                with self.subTest(bracket=bracket, surrounding=surrounding):
                    self.assertIs(is_balanced(surrounding + bracket + surrounding), False)

    def test_unicode_bracket_lookalikes_are_ignored(self):
        self.assertIs(is_balanced('（［｛〈【「」】〉｝］）'), True)
        self.assertIs(is_balanced('（［｛(雪)[雨]{風}｝］）'), True)
        self.assertIs(is_balanced('（［｛(雪][雨){風}｝］）'), False)

    def test_deep_nesting_and_errors_at_the_end(self):
        openings = '([{' * 1000
        closings = '}])' * 1000
        self.assertIs(is_balanced(openings + closings), True)
        self.assertIs(is_balanced(openings + closings[:-1]), False)
        self.assertIs(is_balanced(openings + closings[:-1] + ']'), False)
        self.assertIs(is_balanced(openings + closings + '}'), False)

    def test_other_iterables_and_binary_values_raise_type_error(self):
        values = (b'()', bytearray(b'()'), memoryview(b'()'), range(2),
                  iter('()'), {'(': ')'}, frozenset('()'), 0j)
        for value in values:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_string_subclass_results_are_exact_booleans(self):
        class PlainString(str):
            pass

        for value, expected in (('text', True), ('{x[y](z)}', True),
                                ('{x[y](z]', False), ('text}', False)):
            with self.subTest(value=value):
                result = is_balanced(PlainString(value))
                self.assertIs(type(result), bool)
                self.assertIs(result, expected)

    def test_is_bracket_rejects_unicode_lookalikes(self):
        class PlainString(str):
            pass

        for char in '（ ） ［ ］ ｛ ｝ 〈 〉':
            if char != ' ':
                with self.subTest(char=char):
                    self.assertIs(is_bracket(char), False)
        for char in '()[]{}':
            with self.subTest(char=char):
                self.assertIs(is_bracket(PlainString(char)), True)
