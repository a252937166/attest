import unittest
from roman import is_roman_numeral


class TestHelper(unittest.TestCase):
    def test_true(self):
        self.assertTrue(is_roman_numeral("XIV"))
        self.assertTrue(is_roman_numeral("mmxxiv"))

    def test_false(self):
        self.assertFalse(is_roman_numeral(""))
        self.assertFalse(is_roman_numeral("ABC"))
        self.assertFalse(is_roman_numeral(14))
