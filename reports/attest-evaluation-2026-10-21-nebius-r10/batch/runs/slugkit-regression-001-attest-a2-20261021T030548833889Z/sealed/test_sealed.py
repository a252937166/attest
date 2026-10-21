import unittest
from slugkit import slugify

class TestSlugifyAcceptance(unittest.TestCase):
    def test_ac1_hello_world_double_hyphen(self):
        self.assertEqual(slugify('Hello--World'), 'hello-world')
    def test_ac2_space_hyphen_space(self):
        self.assertEqual(slugify('a -- b'), 'a-b')
    def test_ac3_comma_semicolon(self):
        self.assertEqual(slugify('one , two ; three'), 'one-two-three')
    def test_ac4_underscore_run(self):
        self.assertEqual(slugify('x___y'), 'x-y')
    def test_ac5_trailing_exclam(self):
        self.assertEqual(slugify('end!'), 'end')
    def test_ac6_padded_spaces(self):
        self.assertEqual(slugify('  padded  '), 'padded')
    def test_ac7_both_ends_hyphen(self):
        self.assertEqual(slugify('--both--'), 'both')
    def test_ac8_parens(self):
        self.assertEqual(slugify('(parens)'), 'parens')
    def test_ac9_empty_string(self):
        self.assertEqual(slugify(''), '')
    def test_ac10_only_separators(self):
        self.assertEqual(slugify('!!!'), '')
    def test_ac11_only_spaces(self):
        self.assertEqual(slugify('   '), '')
    def test_ac12_hello_world(self):
        self.assertEqual(slugify('Hello World'), 'hello-world')
    def test_ac13_already_slug(self):
        self.assertEqual(slugify('already-a-slug'), 'already-a-slug')
    def test_ac14_python_3(self):
        self.assertEqual(slugify('Python 3'), 'python-3')
    def test_ac15_mixed_case_42(self):
        self.assertEqual(slugify('MiXeD CaSe 42'), 'mixed-case-42')
    def test_ac16_non_ascii_letters_separators(self):
        self.assertEqual(slugify('café crème'), 'caf-cr-me')
    def test_ac17_japanese_no_ascii(self):
        self.assertEqual(slugify('日本語'), '')
    def test_ac18_result_is_str(self):
        result = slugify('Test')
        self.assertIsInstance(result, str)
    def test_ac19_type_error_non_string(self):
        for bad in (None, 3, 2.5, ['a'], b'bytes'):
            with self.assertRaises(TypeError):
                slugify(bad)
