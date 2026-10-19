import unittest
from slugkit import slugify

class TestSlugifyAcceptance(unittest.TestCase):
    def test_hello_world_hyphens_collapse(self):
        self.assertEqual(slugify('Hello--World'), 'hello-world')
    def test_spaces_and_hyphens_collapse(self):
        self.assertEqual(slugify('a -- b'), 'a-b')
    def test_punctuation_and_spaces_collapse(self):
        self.assertEqual(slugify('one , two ; three'), 'one-two-three')
    def test_underscore_runs_collapse(self):
        self.assertEqual(slugify('x___y'), 'x-y')
    def test_trailing_separator_removed(self):
        self.assertEqual(slugify('end!'), 'end')
    def test_leading_trailing_whitespace_removed(self):
        self.assertEqual(slugify('  padded  '), 'padded')
    def test_leading_trailing_hyphens_removed(self):
        self.assertEqual(slugify('--both--'), 'both')
    def test_parentheses_removed_no_extra_hyphen(self):
        self.assertEqual(slugify('(parens)'), 'parens')
    def test_empty_string_returns_empty(self):
        self.assertEqual(slugify(''), '')
    def test_only_separators_returns_empty(self):
        self.assertEqual(slugify('!!!'), '')
    def test_whitespace_only_returns_empty(self):
        self.assertEqual(slugify('   '), '')
    def test_existing_basic_behavior_preserved(self):
        self.assertEqual(slugify('Hello World'), 'hello-world')
    def test_already_a_slug_unchanged(self):
        self.assertEqual(slugify('already-a-slug'), 'already-a-slug')
    def test_digits_kept(self):
        self.assertEqual(slugify('Python 3'), 'python-3')
    def test_mixed_case_lowercased(self):
        self.assertEqual(slugify('MiXeD CaSe 42'), 'mixed-case-42')
    def test_non_ascii_letters_as_separators(self):
        self.assertEqual(slugify('caf\u00e9 cr\u00e8me'), 'caf-cr-me')
    def test_cjk_characters_yield_empty(self):
        self.assertEqual(slugify('\u65e5\u672c\u8a9e'), '')
    def test_none_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify(None)
    def test_int_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify(3)
    def test_float_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify(2.5)
    def test_list_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify(['a'])
    def test_bytes_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify(b'bytes')
    def test_return_value_is_str(self):
        result = slugify('Test')
        self.assertIsInstance(result, str)
