import unittest

from kvparse import parse, parse_line
from kvparse.parser import _is_ignorable


class TestBreaker(unittest.TestCase):
    def test_unicode_whitespace_at_assignment_edges(self):
        self.assertEqual(parse_line('\u00a0\t key \u2003=\u2002 value \u3000'), ('key', 'value'))
        self.assertEqual(parse_line('a\u2003b = x\u00a0y'), ('a\u2003b', 'x\u00a0y'))

    def test_non_whitespace_unicode_is_preserved(self):
        self.assertEqual(parse_line('\u200b = \u200b'), ('\u200b', '\u200b'))
        self.assertEqual(parse_line('k=\u200b value \u200b'), ('k', '\u200b value \u200b'))

    def test_equals_signs_interact_with_outer_quotes(self):
        self.assertEqual(parse_line('k=== '), ('k', '=='))
        self.assertEqual(parse_line("k= 'a=b' "), ('k', 'a=b'))
        self.assertEqual(parse_line("k='a'='b'"), ('k', "a'='b"))

    def test_repeated_outer_quotes_lose_exactly_one_pair(self):
        self.assertEqual(parse_line('k=""x""'), ('k', '"x"'))
        self.assertEqual(parse_line("k='''x'''"), ('k', "''x''"))

    def test_quoted_control_and_unicode_whitespace_is_preserved(self):
        self.assertEqual(parse_line('k = "\t a \u00a0"'), ('k', '\t a \u00a0'))
        self.assertEqual(parse_line("k = '\u2003'"), ('k', '\u2003'))

    def test_helper_distinguishes_leading_comments_from_inline_markers(self):
        cases = {
            '\u00a0# comment': True,
            '\u3000; comment': True,
            '\u2003\t': True,
            '\u200b# comment': False,
            'key= # value': False,
            'key= ; value': False,
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                actual = _is_ignorable(line)
                self.assertIs(type(actual), bool)
                self.assertIs(actual, expected)

    def test_comments_duplicates_and_order_across_mixed_boundaries(self):
        text = 'first=1\r\u00a0# ignored=bad\nsecond=2\x85 first =3\u2028; ignored\u2029third=4'
        result = parse(text)
        self.assertEqual(result, {'first': '3', 'second': '2', 'third': '4'})
        self.assertEqual(list(result), ['first', 'second', 'third'])

    def test_zero_width_key_is_valid_and_distinct(self):
        result = parse('\u200b=one\na=two\n\u200b=three')
        self.assertEqual(result, {'\u200b': 'three', 'a': 'two'})
        self.assertEqual(list(result), ['\u200b', 'a'])

    def test_malformed_lines_after_ignored_lines_still_raise(self):
        for bad_line in ('missing separator', '\u00a0\t=value'):
            with self.subTest(bad_line=bad_line):
                with self.assertRaises(ValueError):
                    parse('# ignored=1\nvalid=2\n' + bad_line + '\n; ignored=3')

    def test_more_non_string_parse_inputs_raise_type_error(self):
        for value in (False, 1.5, {}, (), bytearray(b'a=1'), memoryview(b'a=1')):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    parse(value)
