import unittest

from kvparse import parse, parse_line


class BreakerTests(unittest.TestCase):
    def test_quotes_and_comment_markers_are_literal_key_characters(self):
        self.assertEqual(parse_line("  '#tag; x' = value  "), ("'#tag; x'", 'value'))
        self.assertEqual(parse("  '#tag; x' = value\n"), {"'#tag; x'": 'value'})

    def test_matching_outer_quotes_can_also_appear_inside(self):
        self.assertEqual(parse_line("q='a'b'"), ('q', "a'b"))
        self.assertEqual(parse_line('q="a"b"'), ('q', 'a"b'))

    def test_quote_removal_does_not_repeat(self):
        self.assertEqual(parse_line("q=''''"), ('q', "''"))
        self.assertEqual(parse_line("q='\"x\"'"), ('q', '"x"'))

    def test_unicode_whitespace_inside_quotes_is_preserved(self):
        line = "\u3000key\u00a0=\u2003'\u2003 x \u2003'\u3000"
        self.assertEqual(parse_line(line), ('key', '\u2003 x \u2003'))
        self.assertEqual(parse(line), {'key': '\u2003 x \u2003'})

    def test_zero_width_space_is_not_stripped(self):
        self.assertEqual(parse_line('\u200bk\u200b=\u200bv\u200b'), ('\u200bk\u200b', '\u200bv\u200b'))
        self.assertEqual(parse('\u200bk\u200b=\u200bv\u200b'), {'\u200bk\u200b': '\u200bv\u200b'})

    def test_quote_pair_requires_both_outer_characters(self):
        self.assertEqual(parse_line("q='x' # tail"), ('q', "'x' # tail"))
        self.assertEqual(parse_line('q=prefix"x"'), ('q', 'prefix"x"'))
        self.assertEqual(parse_line("q='x\""), ('q', "'x\""))

    def test_equals_signs_inside_quoted_and_unquoted_values(self):
        self.assertEqual(parse_line('q="a=b=c"'), ('q', 'a=b=c'))
        self.assertEqual(parse_line('q==='), ('q', '=='))
        self.assertEqual(parse('q="a=b=c"\nr==='), {'q': 'a=b=c', 'r': '=='})

    def test_unicode_whitespace_only_key_is_invalid(self):
        for line in ('\u2003=1', '\u3000\u00a0=2', '\u2028=3'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_line(line)

    def test_comments_with_equals_after_unicode_indentation(self):
        text = '\u3000# invalid=ignored\n\u2003; also=ignored\nkey=ok'
        self.assertEqual(parse(text), {'key': 'ok'})

    def test_duplicates_across_distinct_line_separators_keep_order(self):
        text = 'first=old\x85second=middle\u2029first=new\x0bthird=end'
        result = parse(text)
        self.assertEqual(result, {'first': 'new', 'second': 'middle', 'third': 'end'})
        self.assertEqual(list(result), ['first', 'second', 'third'])
