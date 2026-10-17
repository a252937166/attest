import unittest
from brackets import is_bracket


class TestHelper(unittest.TestCase):
    def test_true(self):
        for c in "()[]{}":
            self.assertTrue(is_bracket(c))

    def test_false(self):
        for c in ("a", "", "((", 1):
            self.assertFalse(is_bracket(c))
