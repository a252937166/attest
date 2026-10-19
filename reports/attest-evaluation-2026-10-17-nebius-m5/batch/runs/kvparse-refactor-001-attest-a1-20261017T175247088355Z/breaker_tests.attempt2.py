import unittest
from kvparse import parse, parse_line

class BreakerTests(unittest.TestCase):
    def test_parse_line_quote_strip_only_one_pair(self):
        # value with matching quotes but extra quotes inside should keep outer stripped only
        self.assertEqual(parse_line('k = ""hello""'), ('k', '"hello"'))
        self.assertEqual(parse_line("k = ''hello''"), ("k", "'hello'"))
        # mismatched quotes should not be stripped
        self.assertEqual(parse_line('k = "\''), ("k", "'\'"))
        self.assertEqual(parse_line("k = '\""), ("k", '\"'))
    def test_parse_line_value_exactly_two_chars_quotes(self):
        self.assertEqual(parse_line('k = ""'), ('k', ''))
        self.assertEqual(parse_line("k = ''"), ('k', ''))
        # non-quote two chars should stay
        self.assertEqual(parse_line('k = ab'), ('k', 'ab'))
    def test_parse_line_key_with_tabs_and_spaces(self):
        self.assertEqual(parse_line('\tkey\t = \tvalue\t'), ('key', 'value'))
    def test_parse_line_value_contains_newline_impossible_as_str? skip
    def test_parse_preserves_order_of_overwrite(self):
        # dict order preserved (Python 3.7+)
        txt = 'a=1\nb=2\na=3'
        self.assertEqual(parse(txt), {'a': '3', 'b': '2'})
    def test_parse_line_raises_ValueError_on_empty_key_after_strip_even_with_spaces_before_eq(self):
        with self.assertRaises(ValueError):
            parse_line('   =value')
        with self.assertRaises(ValueError):
            parse_line('\t\t =value')
    def test_parse_line_raises_ValueError_on_no_eq_even_with_quotes(self):
        with self.assertRaises(ValueError):
            parse_line('noeq')
        with self.assertRaises(ValueError):
            parse_line('"quoted"')
    def test_parse_ignorable_function_detects_unicode_whitespace(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('\u00a0; comment'))  # NBSP then ;
        self.assertTrue(_is_ignorable('\u2003# hash'))      # EM SPACE then #
        self.assertFalse(_is_ignorable('\u00a0key=val'))    # NBSP then key
    def test_parse_handles_large_input_without_degradation(self):
        line = 'k=' + 'v'*10000
        self.assertEqual(parse(line), {'k': 'v'*10000})
    def test_parse_line_does_not_strip_inner_spaces_when_quotes_present(self):
        self.assertEqual(parse_line('k = "  hello  "'), ('k', '  hello  '))
        self.assertEqual(parse_line("k = '  hello  '"), ('k', '  hello  '))
