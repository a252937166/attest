import unittest

from kvparse import parse, parse_line


class TestBreaker(unittest.TestCase):
    def test_multiple_equals_remain_in_value(self):
        self.assertEqual(parse_line(" \tname\t=== 'a=b'== "), ("name", "== 'a=b'=="))
        self.assertEqual(parse_line("key===="), ("key", "==="))

    def test_only_one_outer_quote_pair_is_removed(self):
        self.assertEqual(parse_line("q = ''''"), ("q", "''"))
        self.assertEqual(parse_line('q = """"'), ("q", '""'))
        self.assertEqual(parse_line("q = '"), ("q", "'"))

    def test_unicode_whitespace_inside_quotes_and_keys_is_preserved(self):
        line = '\u3000a\u2003b\u00a0 = \u2003" \u2003x\u2003 "\u3000'
        self.assertEqual(parse_line(line), ('a\u2003b', ' \u2003x\u2003 '))

    def test_parse_line_treats_internal_line_boundaries_as_characters(self):
        self.assertEqual(parse_line('key=first\rsecond\u2028third'), ('key', 'first\rsecond\u2028third'))
        self.assertEqual(parse_line('\u2028key\u2029=\x85value\x1c'), ('key', 'value'))

    def test_parse_uses_all_splitlines_boundaries(self):
        boundaries = ['\n', '\r', '\r\n', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029']
        text = ''.join(f'k{i}=v{i}{boundary}' for i, boundary in enumerate(boundaries))
        expected = {f'k{i}': f'v{i}' for i in range(len(boundaries))}
        self.assertEqual(parse(text), expected)

    def test_unicode_indented_comments_and_literal_markers(self):
        text = '\u2003# ignored=bad\n\u00a0; ignored=bad\na=#;=\nb=;#=\nc= value # ; ='
        self.assertEqual(parse(text), {'a': '#;=', 'b': ';#=', 'c': 'value # ; ='})

    def test_comment_marker_after_noncomment_prefix_does_not_hide_error(self):
        with self.assertRaises(ValueError):
            parse('good=1\n x # still malformed\nmore=2')
        with self.assertRaises(ValueError):
            parse('# ignored\n; ignored\n\u2003=missing key')

    def test_duplicate_keys_preserve_first_insertion_position(self):
        text = ' \u2003alpha = first\nbeta=one\nalpha=second\ngamma=three\n\t beta \t=two\nalpha=last'
        result = parse(text)
        self.assertEqual(result, {'alpha': 'last', 'beta': 'two', 'gamma': 'three'})
        self.assertEqual(list(result), ['alpha', 'beta', 'gamma'])

    def test_single_line_parse_agrees_with_parse_line_for_special_values(self):
        lines = ["k=##;;==", "quoted = 'a=#;b'", 'double = "a=;#b"', "lonely = '", "mixed = 'x\"", 'inner = """"']
        for line in lines:
            with self.subTest(line=line):
                key, value = parse_line(line)
                self.assertEqual(parse(line), {key: value})

    def test_only_line_boundaries_and_unicode_whitespace_are_ignored(self):
        self.assertEqual(parse('\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029\u2003\u00a0'), {})
