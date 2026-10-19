import unittest
from kvparse import parse, parse_line

class TestParseLine(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
    def test_spaces(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
    def test_multiple_eq(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
    def test_multiple_eq_spaces(self):
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))
    def test_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))
    def test_double_quotes(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
    def test_single_quotes(self):
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
    def test_quote_with_escape(self):
        self.assertEqual(parse_line('q = "x\\\''), ('q', '"x\\\''))
    def test_quote_only(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
    def test_empty_quotes(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
    def test_spaced_inside_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
    def test_key_with_spaces(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
    def test_multiple_quotes(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
    def test_error_no_eq(self):
        with self.assertRaises(ValueError):
            parse_line('')
    def test_error_novalue(self):
        with self.assertRaises(ValueError):
            parse_line('novalue')
    def test_error_empty_key_space(self):
        with self.assertRaises(ValueError):
            parse_line(' = v')
    def test_error_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_line('   ')
    def test_error_eq_only(self):
        with self.assertRaises(ValueError):
            parse_line('=')
    def test_error_tab_eq(self):
        with self.assertRaises(ValueError):
            parse_line('\t= 1')

class TestParse(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse(''), {})
    def test_simple(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})
    def test_multiline(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
    def test_comments_blank(self):
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
    def test_title_double(self):
        self.assertEqual(parse_line('title = "Hello World"'), ('title', 'Hello World'))
    def test_title_single(self):
        self.assertEqual(parse_line("title = 'single'"), ('title', 'single'))
    def test_parse_error_novalue(self):
        with self.assertRaises(ValueError):
            parse('novalue\n')
    def test_parse_typeerror_none(self):
        with self.assertRaises(TypeError):
            parse(None)
    def test_parse_typeerror_int(self):
        with self.assertRaises(TypeError):
            parse(3)
    def test_parse_typeerror_list(self):
        with self.assertRaises(TypeError):
            parse([])
    def test_parse_typeerror_bytes(self):
        with self.assertRaises(TypeError):
            parse(b'abc')

# Note: Direct testing of private _is_ignorable is omitted to comply with import restrictions;
# its behavior is exercised via parse tests for ignorable lines.
