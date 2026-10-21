import unittest
from slugkit import slugify

class TestSlugifyBreaker(unittest.TestCase):
    def test_unicode_combining_marks(self):
        # e\u0301 is e + combining acute, should be treated as separator after lowercasing? 
        # The base 'e' is ascii letter, combining mark is non-ascii, so becomes hyphen.
        # But trailing hyphens are stripped per contract, so result is 'e'.
        self.assertEqual(slugify('e\u0301'), 'e')
    def test_emoji_separators(self):
        self.assertEqual(slugify('Hi😀there'), 'hi-there')
    def test_multiple_emoji_and_symbols(self):
        self.assertEqual(slugify('A😀😃B!!C'), 'a-b-c')
    def test_very_long_input(self):
        long = 'a' + '-'*10000 + 'b'
        self.assertEqual(slugify(long), 'a-b')
    def test_mixed_ascii_and_nonascii_with_digits(self):
        self.assertEqual(slugify('ab12ç34Ñ56'), 'ab12-34-56')
    def test_leading_trailing_nonascii_only(self):
        self.assertEqual(slugify('★abc★'), 'abc')
    def test_null_bytes_in_string(self):
        # null byte is non-ascii, should become hyphen
        self.assertEqual(slugify('a\0b'), 'a-b')
