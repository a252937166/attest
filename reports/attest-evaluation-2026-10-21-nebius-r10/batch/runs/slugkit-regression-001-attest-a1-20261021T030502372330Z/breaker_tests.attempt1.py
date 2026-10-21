import unittest
from slugkit import slugify

class TestSlugifyBreaker(unittest.TestCase):
    def test_unicode_combining_accents(self):
        self.assertEqual(slugify('e\u0301'), '')  # e + combining acute => no ascii alnum
    def test_multiple_internal_non_alnum_runs(self):
        self.assertEqual(slugify('a!!!b???c'), 'a-b-c')
    def test_leading_trailing_mix(self):
        self.assertEqual(slugify('---abc---def---'), 'abc-def')
    def test_digits_only(self):
        self.assertEqual(slugify('123!!!456'), '123-456')
    def test_long_string_performance(self):
        s = 'a' * 5000 + '!' * 5000 + 'b' * 5000
        self.assertEqual(slugify(s), 'a' + '-'*1 + 'b')
    def test_return_type_is_str(self):
        self.assertIsInstance(slugify('Hello'), str)
    def test_non_ascii_letter_separator(self):
        self.assertEqual(slugify('na\u00efve'), 'na-ve')  # ï treated as separator
