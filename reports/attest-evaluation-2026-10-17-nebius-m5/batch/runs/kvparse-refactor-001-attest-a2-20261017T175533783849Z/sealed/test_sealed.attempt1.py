import unittest
from kvparse import parse, parse_line

class TestKVParseAcceptance(unittest.TestCase):
    def test_parse_line_a_eq_b(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
    
    def test_parse_line_spaces_around_eq(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
    
    def test_parse_line_double_eq(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
    
    def test_parse_line_multiple_eq(self):
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))
    
    def test_parse_line_eq_with_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))
    
    def test_parse_line_quoted_double(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
    
    def test_parse_line_quoted_single(self):
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
    
    def test_parse_line_quote_with_escape_inside(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
    
    def test_parse_line_quote_only(self):
        self.assertEqual(parse_line('q = ""'), ('q', '"'))
    
    def test_parse_line_single_quote_only(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
    
    def test_parse_line_spaced_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
    
    def test_parse_line_key_with_spaces(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
    
    def test_parse_line_multiple_quoted_parts(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
    
    def test_parse_line_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_line('')
    
    def test_parse_line_no_equal_raises(self):
        with self.assertRaises(ValueError):
            parse_line('novalue')
    
    def test_parse_line_empty_key_after_strip_raises(self):
        with self.assertRaises(ValueError):
            parse_line(' = v')
    
    def test_parse_line_only_whitespace_raises(self):
        with self.assertRaises(ValueError):
            parse_line('   ')
    
    def test_parse_line_only_equal_raises(self):
        with self.assertRaises(ValueError):
            parse_line('=')
    
    def test_parse_line_tab_then_equal_raises(self):
        with self.assertRaises(ValueError):
            parse_line('\t= 1')
    
    def test_parse_empty_text(self):
        self.assertEqual(parse(''), {})
    
    def test_parse_simple_kv(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})
    
    def test_parse_multiple_lines(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
    
    def test_parse_ignores_comments_and_blanks(self):
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
    
    def test_parse_removes_double_quotes(self):
        self.assertEqual(parse('title = "Hello World"\n'), {'title': 'Hello World'})
    
    def test_parse_removes_single_quotes(self):
        self.assertEqual(parse("title = 'single'\n"), {'title': 'single'})
    
    def test_parse_malformed_line_raises(self):
        with self.assertRaises(ValueError):
            parse('novalue\n')
    
    def test_parse_type_error_non_string(self):
        for val in (None, 3, [], b'bytes'):
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    parse(val)
    
    def test_is_ignorable_comment_hash(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('   # c'))
    
    def test_is_ignorable_blank(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable(''))
    
    def test_is_ignorable_comment_semicolon(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('\t; c'))
    
    def test_is_ignorable_not_comment(self):
        from kvparse.parser import _is_ignorable
        self.assertFalse(_is_ignorable('a = 1'))
    
    def test_is_ignorable_hash_not_first_nonblank(self):
        from kvparse.parser import _is_ignorable
        self.assertFalse(_is_ignorable('a = # not a comment'))
