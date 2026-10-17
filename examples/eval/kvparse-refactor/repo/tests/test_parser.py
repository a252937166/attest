import unittest
from kvparse import parse, parse_line


class TestParse(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse("a = 1\nb=2\n"), {"a": "1", "b": "2"})

    def test_comments_and_blank_lines(self):
        self.assertEqual(parse("# comment\n\n; other\nname = x\n"), {"name": "x"})

    def test_quotes_removed(self):
        self.assertEqual(parse_line('title = "Hello World"'), ("title", "Hello World"))
        self.assertEqual(parse_line("title = 'single'"), ("title", "single"))

    def test_errors(self):
        with self.assertRaises(ValueError):
            parse("novalue\n")
        with self.assertRaises(TypeError):
            parse(None)
