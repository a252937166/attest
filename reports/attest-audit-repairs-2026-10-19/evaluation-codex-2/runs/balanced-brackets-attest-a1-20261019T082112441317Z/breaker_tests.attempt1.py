import itertools
import unittest

from brackets import is_balanced, is_bracket


class TestBreaker(unittest.TestCase):
    def test_deep_mixed_nesting(self):
        s = '(' * 800 + '[' * 800 + '{' * 800 + '}' * 800 + ']' * 800 + ')' * 800
        self.assertIs(is_balanced(s), True)
        self.assertIs(is_balanced(s[:-1]), False)

    def test_many_adjacent_groups(self):
        s = '()[]{}' * 800
        self.assertIs(is_balanced(s), True)
        self.assertIs(is_balanced(s + ']'), False)
        self.assertIs(is_balanced('[' + s), False)

    def test_every_three_bracket_sequence_is_unbalanced(self):
        for chars in itertools.product('()[]{}', repeat=3):
            with self.subTest(chars=chars):
                self.assertIs(is_balanced(''.join(chars)), False)

    def test_later_brackets_cannot_repair_earlier_errors(self):
        for s in ('][', '}{', '([)][]', '{[}]{}', '())(()', '[])([]'):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_unicode_bracket_lookalikes_are_ignored(self):
        self.assertIs(is_balanced('（［｛〈«【⟨⦃』）'), True)
        self.assertIs(is_balanced('（[］'), False)
        self.assertIs(is_balanced('（[ ]）'), True)

    def test_quotes_and_backslashes_inside_groups(self):
        self.assertIs(is_balanced('(' + '"' + chr(92) + '[' + ']' + '"' + ')'), True)
        self.assertIs(is_balanced('(' + '"' + chr(92) + ']' + '"' + ')'), False)
        self.assertIs(is_balanced(chr(92) + '{' + chr(92) + '}'), True)

    def test_additional_nonstring_iterables_raise_typeerror(self):
        values = (bytearray(b'()'), memoryview(b'[]'), range(2), iter('()'), ('(', ')'), frozenset('[]'))
        for value in values:
            with self.subTest(type=type(value)):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_plain_str_subclass_with_deep_content(self):
        class Text(str):
            pass

        self.assertIs(is_balanced(Text('x' + '([{}])' * 100 + 'y')), True)
        self.assertIs(is_balanced(Text('x' + '([{}])' * 100 + ']')), False)

    def test_is_bracket_single_ascii_character_boundary(self):
        class Character(str):
            pass

        for c in '()[]{}':
            with self.subTest(c=c):
                self.assertIs(is_bracket(Character(c)), True)
        for c in ('（', '［', '｛', '🙂', '\n', ' [', '()'):
            with self.subTest(c=c):
                self.assertIs(is_bracket(c), False)
