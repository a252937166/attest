import unittest

from kvparse import parse, parse_line


class TestBreaker(unittest.TestCase):
    def test_first_separator_with_equals_and_quotes_in_value(self):
        self.assertEqual(parse_line(' a\tb =="=x=y" '), ('a\tb', '="=x=y"'))
        self.assertEqual(parse_line('x===y'), ('x', '==y'))
        self.assertEqual(parse_line('x=='), ('x', '='))

    def test_outer_quotes_removed_only_once(self):
        for quote in ('"', "'"):
            with self.subTest(quote=quote):
                self.assertEqual(parse_line('k=' + quote * 4), ('k', quote * 2))
                self.assertEqual(parse_line('k=' + quote * 3), ('k', quote))
                self.assertEqual(parse_line('k=' + quote + ' = # ; ' + quote), ('k', ' = # ; '))

    def test_unicode_whitespace_outside_and_inside_quotes(self):
        line = '\u2003k\u00a0=\u2002" \t=;# \u00a0"\u2003'
        self.assertEqual(parse_line(line), ('k', ' \t=;# \u00a0'))

    def test_backslashes_and_nulls_are_literal(self):
        self.assertEqual(parse_line('k="a\\\\b\\"c"'), ('k', 'a\\\\b\\"c'))
        self.assertEqual(parse_line('a\x00b=\x00x\x00'), ('a\x00b', '\x00x\x00'))

    def test_other_equals_characters_are_not_separators(self):
        for line in ('a\uff1db', 'a\u2261b', 'a\u2250b'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_line(line)
        self.assertEqual(parse_line('a\uff1db=c'), ('a\uff1db', 'c'))

    def test_comment_markers_are_significant_only_at_line_start(self):
        text = ' \t# fake=1\n; fake=2\nx#y = 3\nx;y=4\nx= #v\nz= ;v'
        self.assertEqual(parse(text), {'x#y': '3', 'x;y': '4', 'x': '#v', 'z': ';v'})

    def test_mixed_less_common_splitlines_separators(self):
        text = 'a=1\x1cb=2\x1d#skip\x1ec=3\x85d=4\u2028e=5\u2029f=6\v;skip\fg=7'
        self.assertEqual(parse(text), {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5', 'f': '6', 'g': '7'})

    def test_duplicate_keys_keep_first_insertion_position(self):
        result = parse('a=1\n b=2\n\u2003a\u2003="3"\n# ignored\nb=4\nc=')
        self.assertEqual(result, {'a': '3', 'b': '4', 'c': ''})
        self.assertEqual(list(result), ['a', 'b', 'c'])

    def test_malformed_line_after_ignored_lines_raises(self):
        for text in ('# no equals\nk=v\n\u2003=oops', 'a=1\u2028bad\u2029b=2', '; ignored\r\nkey=ok\r\n\t=bad'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text)

    def test_parse_matches_parse_line_on_single_noncomment_lines(self):
        for line in ('a=="x"', 'k = "  ;#=  "', 'x\ty = \'nested "quote"\'', 'z=\x00'):
            with self.subTest(line=line):
                key, value = parse_line(line)
                self.assertEqual(parse(line), {key: value})
