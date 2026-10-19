import unittest
from kvparse import parse, parse_line
# Attempt to access the private helper; will fail if not present
try:
    from kvparse.parser import _is_ignorable
except Exception:
    _is_ignorable = None

class TestSealedAcceptance(unittest.TestCase):
    def test_parse_line_basic(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
    def test_parse_line_spaces(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
    def test_parse_line_first_eq(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
    def test_parse_line_multiple_eq(self):
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))
    def test_parse_line_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))
    def test_parse_line_double_quotes(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
    def test_parse_line_single_quotes(self):
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
    def test_parse_line_quotes_with_inner_quote(self):
        self.assertEqual(parse_line('q = "x\'') , ('q', '"x\''))
    def test_parse_line_quote_only(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
    def test_parse_line_empty_quotes(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
    def test_parse_line_spaced_inside_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
    def test_parse_line_key_with_spaces(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
    def test_parse_line_extra_quotes(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
    def test_parse_line_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_line('')
    def test_parse_line_no_equal_raises(self):
        with self.assertRaises(ValueError):
            parse_line('novalue')
    def test_parse_line_empty_key_raises(self):
        with self.assertRaises(ValueError):
            parse_line(' = v')
    def test_parse_line_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            parse_line('   ')
    def test_parse_line_only_equal_raises(self):
        with self.assertRaises(ValueError):
            parse_line('=')
    def test_parse_line_tab_equal_raises(self):
        with self.assertRaises(ValueError):
            parse_line('\t= 1')
    def test_parse_empty_text(self):
        self.assertEqual(parse(''), {})
    def test_parse_simple(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})
    def test_parse_multiple_lines(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
    def test_parse_ignores_comments_and_blanks(self):
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
    def test_parse_line_title_double_quotes(self):
        self.assertEqual(parse_line('title = "Hello World"'), ('title', 'Hello World'))
    def test_parse_line_title_single_quotes(self):
        self.assertEqual(parse_line("title = 'single'"), ('title', 'single'))
    def test_parse_malformed_line_raises(self):
        with self.assertRaises(ValueError):
            parse('novalue\n')
    def test_parse_type_error_nonstr(self):
        for bad in (None, 3, [], b'bytes'):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    parse(bad)
    def test_is_ignorable_whitespace(self):
        self.assertTrue(_is_ignorable(''))
    def test_is_ignorable_spaces(self):
        self.assertTrue(_is_ignorable('   '))
    def test_is_ignorable_hash_comment(self):
        self.assertTrue(_is_ignorable('   # c'))
    def test_is_ignorable_semicolon_comment(self):
        self.assertTrue(_is_ignorable('\t; c'))
    def test_is_ignorable_not_ignorable(self):
        self.assertFalse(_is_ignorable('a = 1'))
    def test_is_ignorable_hash_not_comment(self):
        self.assertFalse(_is_ignorable('a = # not a comment'))
