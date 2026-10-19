import unittest

from slugkit import slugify
from slugkit.core import slugify as core_slugify


class BreakerTests(unittest.TestCase):
    def test_every_ascii_character_individually(self):
        for code in range(128):
            with self.subTest(code=code):
                char = chr(code)
                if 65 <= code <= 90:
                    expected = chr(code + 32)
                elif 97 <= code <= 122 or 48 <= code <= 57:
                    expected = char
                else:
                    expected = ''
                self.assertEqual(slugify(char), expected)

    def test_ascii_boundary_combinations(self):
        cases = {
            'A!0': 'a-0',
            '9@Z': '9-z',
            'z[`A': 'z-a',
            '0/9': '0-9',
            'A:B': 'a-b',
            'x\\y': 'x-y',
            'a\x7fb': 'a-b',
            'Q\x00\x01R': 'q-r',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_unicode_characters_with_ascii_casefold_equivalents(self):
        for char in ('K', 'ſ', 'İ', 'ı', 'Å', 'ẞ'):
            with self.subTest(char=char):
                self.assertEqual(slugify(char), '')
                self.assertEqual(slugify('A' + char + 'B'), 'a-b')

    def test_non_ascii_number_forms_are_separators(self):
        for char in ('١', '１', '𝟠', '²', '⑦', 'Ⅷ'):
            with self.subTest(char=char):
                self.assertEqual(slugify('4' + char + '5'), '4-5')
                self.assertEqual(slugify(char), '')

    def test_combining_marks_emoji_and_surrogates(self):
        cases = {
            'e\u0301f': 'e-f',
            'A\u200dB': 'a-b',
            'x😀y': 'x-y',
            'P\ud800Q': 'p-q',
            '\u0301\u200d😀\udfff': '',
        }
        for value, expected in cases.items():
            with self.subTest(value=ascii(value)):
                self.assertEqual(slugify(value), expected)

    def test_long_separator_runs_and_alternation(self):
        self.assertEqual(slugify('A' + ('!_ \t' * 900) + 'Z'), 'a-z')
        self.assertEqual(slugify(('X!' * 1000) + 'Y'), ('x-' * 1000) + 'y')
        self.assertEqual(slugify(('😀' * 2000) + '7' + ('\x00' * 2000)), '7')

    def test_slugify_is_idempotent_with_hyphens_in_result(self):
        for value in ('A---B', '__X__Y__', '7 K 8', '\nA\tB\n', 'a😀b', '---', ''):
            with self.subTest(value=value):
                first = slugify(value)
                self.assertEqual(core_slugify(first), first)

    def test_additional_non_string_types_have_exact_typeerror(self):
        for value in (True, 0, 0j, (), {}, bytearray(b'a'), memoryview(b'a')):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError) as cm:
                    slugify(value)
                self.assertEqual(str(cm.exception), 'text must be a str')

    def test_plain_string_subclass_with_unicode_and_separators(self):
        class Text(str):
            pass

        result = core_slugify(Text('  A\u0301---9😀B  '))
        self.assertEqual(result, 'a-9-b')
        self.assertIs(type(result), str)
