import unittest
from slugkit import slugify

class TestSlugifyAcceptance(unittest.TestCase):
    def test_hello_world_double_hyphen(self):
        self.assertEqual(slugify('Hello--World'), 'hello-world')
    def test_spaces_and_hyphens(self):
        self.assertEqual(slugify('a -- b'), 'a-b')
    def test_punctuation_and_spaces(self):
        self.assertEqual(slugify('one , two ; three'), 'one-two-three')
    def test_underscore_runs(self):
        self.assertEqual(slugify('x___y'), 'x-y')
    def test_trailing_separator(self):
        self.assertEqual(slugify('end!'), 'end')
    def test_padded_whitespace(self):
        self.assertEqual(slugify('  padded  '), 'padded')
    def test_leading_trailing_hyphens(self):
        self.assertEqual(slugify('--both--'), 'both')
    def test_parentheses(self):
        self.assertEqual(slugify('(parens)'), 'parens')
    def test_empty_input(self):
        self.assertEqual(slugify(''), '')
    def test_only_separators(self):
        self.assertEqual(slugify('!!!'), '')
    def test_whitespace_only(self):
        self.assertEqual(slugify('   '), '')
    def test_existing_hello_world(self):
        self.assertEqual(slugify('Hello World'), 'hello-world')
    def test_existing_already_slug(self):
        self.assertEqual(slugify('already-a-slug'), 'already-a-slug')
    def test_existing_python_3(self):
        self.assertEqual(slugify('Python 3'), 'python-3')
    def test_existing_mixed_case(self):
        self.assertEqual(slugify('MiXeD CaSe 42'), 'mixed-case-42')
    def test_non_ascii_letters_separators(self):
        self.assertEqual(slugify('caf\u00e9 cr\u00e8me'), 'caf-cr-me')
    def test_non_ascii_only(self):
        self.assertEqual(slugify('\u65e5\u672c\u8a9e'), '')
    def test_result_is_str(self):
        result = slugify('Test')
        self.assertIsInstance(result, str)
    def test_type_error_none(self):
        with self.assertRaises(TypeError):
            slugify(None)
    def test_type_error_int(self):
        with self.assertRaises(TypeError):
            slugify(3)
    def test_type_error_float(self):
        with self.assertRaises(TypeError):
            slugify(2.5)
    def test_type_error_list(self):
        with self.assertRaises(TypeError):
            slugify(['a'])
    def test_type_error_bytes(self):
        with self.assertRaises(TypeError):
            slugify(b'bytes')
