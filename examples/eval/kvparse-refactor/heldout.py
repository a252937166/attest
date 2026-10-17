import inspect
import unittest

import kvparse.parser as parser_module
from kvparse import parse, parse_line


class HeldOut(unittest.TestCase):
    def test_parse_line_behaviour_is_unchanged(self):
        cases = {
            "a=b": ("a", "b"), " a = b ": ("a", "b"), "a==b": ("a", "=b"), "a = b = c": ("a", "b = c"), "a=": ("a", ""),
            "a =   ": ("a", ""), 'q = "x"': ("q", "x"), "q = 'x'": ("q", "x"), 'q = "x\'': ("q", "\"x'"), 'q = "': ("q", '"'),
            "q = ''": ("q", ""), 'q = " spaced "': ("q", " spaced "), "k e y = v": ("k e y", "v"), "tab\t=\tv": ("tab", "v"),
            'u = "a" "b"': ("u", 'a" "b'), "n = 42": ("n", "42"),
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), expected)

    def test_parse_line_errors_are_unchanged(self):
        for line in ("", "novalue", " = v", "   ", "=", "\t= 1"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_line(line)

    def test_parse_behaviour_is_unchanged(self):
        text = "# top\n  ; note\n\na = 1\n b = 'two' \n# a = 9\nc=\na = 3\r\n   # indented comment\nd = \"x = y\"\n"
        self.assertEqual(parse(text), {"a": "3", "b": "two", "c": "", "d": "x = y"})
        self.assertEqual(parse(""), {})
        self.assertEqual(parse("\n\n# only comments\n;\n"), {})
        self.assertEqual(parse("k = v"), {"k": "v"})

    def test_parse_errors_are_unchanged(self):
        for text in ("broken\n", "a = 1\nbroken\n", " = 1\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text)
        for bad in (None, 3, ["a = 1"], b"a = 1"):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                parse(bad)

    def test_requested_structure(self):
        self.assertTrue(callable(getattr(parser_module, "_is_ignorable", None)), "_is_ignorable(line) helper is required")
        self.assertTrue(parser_module._is_ignorable("   # c"))
        self.assertTrue(parser_module._is_ignorable(""))
        self.assertTrue(parser_module._is_ignorable("\t; c"))
        self.assertFalse(parser_module._is_ignorable("a = 1"))
        self.assertFalse(parser_module._is_ignorable("a = # not a comment"))
        source = inspect.getsource(parse_line)
        self.assertNotIn("while ", source, "parse_line must not use an index loop")
        self.assertIn("partition", source, "parse_line must split with str.partition")
