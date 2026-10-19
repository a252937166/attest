import unittest
from slugkit import slugify

class TestBreaker(unittest.TestCase):
    def test_unicode_combining_marks(self):
        # e\u0301 is e + combining acute, still non-ascii alnum after lower? e is ascii, combining mark is not alnum -> hyphen
        self.assertEqual(slugify('e\u0301'), 'e')
    def test_emoji_separator(self):
        self.assertEqual(slugify('Hi😀there'), 'hi-there')
    def test_multiple_emoji_runs(self):
        self.assertEqual(slugify('A😀😃B😄C'), 'a-b-c')
    def test_mixed_ascii_and_nonascii_with_digits(self):
        self.assertEqual(slugify('ab12çÃ©34'), 'ab12-34')
    def test_very_long_input(self):
        s = 'a' + '-'*10000 + 'b'
        self.assertEqual(slugify(s), 'a-b')
    def test_null_bytes_in_string(self):
        # null byte is not ascii alnum -> hyphen
        self.assertEqual(slugify('a\0b'), 'a-b')
    def test_preserve_ascii_digits_only(self):
        self.assertEqual(slugify('123!!!456'), '123-456')
    def test_type_error_for_subclass_of_str(self):
        class MyStr(str): pass
        # Should accept because isinstance(MyStr('', ...), str) True
        self.assertIsInstance(slugify(MyStr('Hello')), str)
