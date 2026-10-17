import unittest
from brackets import is_balanced


class HeldOut(unittest.TestCase):
    def test_simple_balanced(self):
        for s in ("", "()", "[]", "{}", "()[]{}", "([{}])"):
            self.assertTrue(is_balanced(s))

    def test_nested(self):
        self.assertTrue(is_balanced("(a[b]{c})"))
        self.assertTrue(is_balanced("code = f(x[0], y[1])"))

    def test_unbalanced(self):
        for s in ("(", ")", "([)]", "(]", "{[}", "())"):
            self.assertFalse(is_balanced(s))

    def test_ignores_non_bracket_chars(self):
        self.assertTrue(is_balanced("a + b - c"))
        self.assertFalse(is_balanced("a ) b"))

    def test_returns_bool(self):
        self.assertIsInstance(is_balanced("()"), bool)

    def test_non_string_raises_typeerror(self):
        for bad in (123, None, ["("]):
            with self.assertRaises(TypeError):
                is_balanced(bad)
