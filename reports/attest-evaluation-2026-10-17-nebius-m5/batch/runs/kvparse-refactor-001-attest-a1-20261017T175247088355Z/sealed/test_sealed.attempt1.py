import unittest
from kvparse import parse, parse_line

class TestKVParseAcceptance(unittest.TestCase):
    def test_parse_line_simple(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
    
    def test_parse_line_spaces(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
    
    def test_parse_line_double_eq(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
    
    def test_parse_line_multiple_eq(self):
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))
    
    def test_parse_line_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))
    
    def test_parse_line_double_quoted(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
    
    def test_parse_line_single_quoted(self):
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
    
    def test_parse_line_quote_with_escape(self):
        self.assertEqual(parse_line('q = "x\'''), ('q', '"x\''))
    
    def test_parse_line_only_quote(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
    
    def test_parse_line_empty_quotes(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
    
    def test_parse_line_spaced_inside_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
    
    def test_parse_line_key_with_spaces(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
    
    def test_parse_line_quotes_not_matching(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
    
    def test_parse_line_no_equal(self):
        with self.assertRaises(ValueError):
            parse_line('')
    
    def test_parse_line_novalue(self):
        with self.assertRaises(ValueError):
            parse_line('novalue')
    
    def test_parse_line_empty_key_space(self):
        with self.assertRaises(ValueError):
            parse_line(' = v')
    
    def test_parse_line_whitespace_only(self):
        with self.assertRaises(ValueError):
            parse_line('   ')
    
    def test_parse_line_only_equal(self):
        with self.assertRaises(ValueError):
            parse_line('=')
    
    def test_parse_line_tab_equal(self):
        with self.assertRaises(ValueError):
            parse_line('\t= 1')
    
    def test_parse_empty_text(self):
        self.assertEqual(parse(''), {})
    
    def test_parse_single_kv(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})
    
    def test_parse_multiple_lines(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
    
    def test_parse_ignore_comments_and_blank(self):
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
    
    def test_parse_title_double_quote(self):
        self.assertEqual(parse_line('title = "Hello World"'), ('title', 'Hello World'))
    
    def test_parse_title_single_quote(self):
        self.assertEqual(parse_line("title = 'single'"), ('title', 'single'))
    
    def test_parse_error_propagation(self):
        with self.assertRaises(ValueError):
            parse('novalue\n')
    
    def test_parse_type_error_none(self):
        with self.assertRaises(TypeError):
            parse(None)
    
    def test_parse_type_error_int(self):
        with self.assertRaises(TypeError):
            parse(3)
    
    def test_parse_type_error_list(self):
        with self.assertRaises(TypeError):
            parse([])
    
    def test_parse_type_error_bytes(self):
        with self.assertRaises(TypeError):
            parse(b'text')
    
    def test_is_ignorable_comment_hash(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('   # c'))
    
    def test_is_ignorable_empty(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable(''))
    
    def test_is_ignorable_comment_semicolon(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('\t; c'))
    
    def test_is_ignorable_false_normal(self):
        from kvparse.parser import _is_ignorable
        self.assertFalse(_is_ignorable('a = 1'))
    
    def test_is_ignorable_false_inline_comment(self):
        from kvparse.parser import _is_ignorable
        self.assertFalse(_is_ignorable('a = # not a comment'))
    
    def test_parse_line_uses_partition_no_while(self):
        import inspect
        src = inspect.getsource(parse_line)
        self.assertNotIn('while', src)
        self.assertIn('str.partition', src.replace(' ', ''))

