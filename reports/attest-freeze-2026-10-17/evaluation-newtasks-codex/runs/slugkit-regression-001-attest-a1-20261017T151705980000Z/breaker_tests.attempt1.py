import unittest

from slugkit import slugify


class TestBreaker(unittest.TestCase):
    def test_unicode_case_mappings_do_not_create_ascii_letters(self):
        for text, expected in [
            ('AİB', 'a-b'),
            ('AſB', 'a-b'),
            ('AKB', 'a-b'),
            ('İ', ''),
            ('ſ', ''),
        ]:
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_non_ascii_digits_are_separators(self):
        for text, expected in [
            ('A١B', 'a-b'),
            ('A９B', 'a-b'),
            ('١٢٣', ''),
            ('0١2', '0-2'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_combining_marks_separate_ascii_letters(self):
        self.assertEqual(slugify('e\u0301X'), 'e-x')
        self.assertEqual(slugify('\u0301A\u0301'), 'a')
        self.assertEqual(slugify('\u0301\u0300'), '')

    def test_control_characters_are_separators(self):
        for codepoint in range(32):
            with self.subTest(codepoint=codepoint):
                self.assertEqual(slugify('A' + chr(codepoint) + 'B'), 'a-b')

    def test_each_ascii_punctuation_character_is_a_separator(self):
        punctuation = ''.join(chr(n) for n in range(33, 127)
                              if not ('A' <= chr(n) <= 'Z'
                                      or 'a' <= chr(n) <= 'z'
                                      or '0' <= chr(n) <= '9'))
        for character in punctuation:
            with self.subTest(character=character):
                self.assertEqual(slugify('A' + character + 'B'), 'a-b')

    def test_long_mixed_separator_run_collapses_once(self):
        separators = ('_! \t\né١💡\u0301' * 500)
        self.assertEqual(slugify('A' + separators + 'B'), 'a-b')

    def test_long_separator_only_input_is_empty(self):
        self.assertEqual(slugify(('💡_\u0301 ' * 1000)), '')

    def test_many_alternating_runs_preserve_order(self):
        self.assertEqual(slugify(('Z!7_' * 500) + 'Q'), ('z-7-' * 500) + 'q')

    def test_additional_non_string_types_raise_exact_error(self):
        for value in (True, (), {}, set(), bytearray(b'a'), object()):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError) as cm:
                    slugify(value)
                self.assertEqual(str(cm.exception), 'text must be a str')

    def test_plain_string_subclass_returns_a_string(self):
        class Text(str):
            pass

        result = slugify(Text('A💡B_9'))
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'a-b-9')
