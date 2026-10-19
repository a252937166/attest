import unittest
from slugkit import slugify

class TestSlugifyBreaker(unittest.TestCase):
    def test_soft_hyphen_separator(self):
        self.assertEqual(slugify('a\uadb'), 'a-b')
    def test_null_byte_separator(self):
        self.assertEqual(slugify('a\x00b'), 'a-b')
    def test_multiple_unicode_separators_collapse(self):
        self.assertEqual(slugify('a\u00e9\u00e8b'), 'a-b')
    def test_leading_trailing_mixed_separators(self):
        self.assertEqual(slugify(' !!hello!! '), 'hello')
    def test_only_ascii_digits_returns_same(self):
        self.assertEqual(slugify('123'), '123')
    def test_digits_with_separators(self):
        self.assertEqual(slugify('12!!34!!56'), '12-34-56')
    def test_empty_after_strip_returns_empty(self):
        self.assertEqual(slugify('---'), '')
    def test_very_long_string(self):
        long = 'a' + '-'*10000 + 'b'
        self.assertEqual(slugify(long), 'a-b')
    def test_return_type_is_str(self):
        self.assertIsInstance(slugify('test'), str)
    def test_type_error_on_nonstr_subclasses(self):
        class MyStr(str):
            pass
        # subclass of str should be accepted
        self.assertEqual(slugify(MyStr('Hi')), 'hi')
        # but object that is not str should raise
        with self.assertRaises(TypeError):
            slugify(object())
