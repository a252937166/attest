import unittest
from unittest.mock import patch

from kvparse import parse, parse_line
import kvparse.parser as parser_module


class TestParseLine(unittest.TestCase):
    def test_basic_key_value(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        self.assertEqual(parse_line('a='), ('a', ''))

    def test_first_equals_separates_key_and_value(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_key_strips_surrounding_unicode_whitespace(self):
        self.assertEqual(parse_line('\u2003k e y\u00a0= v'), ('k e y', 'v'))

    def test_unquoted_value_strips_only_surrounding_whitespace(self):
        self.assertEqual(parse_line(' a = \u2003b  c\u00a0'), ('a', 'b  c'))

    def test_matching_outer_quotes_are_removed(self):
        cases = [('q = "x"', ('q', 'x')), ("q = 'x'", ('q', 'x')),
                 ("q = ''", ('q', '')), ('q = ""', ('q', ''))]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), expected)

    def test_mismatched_quotes_are_retained(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
        self.assertEqual(parse_line("q = 'x\""), ('q', "'x\""))

    def test_lone_quotes_are_retained(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
        self.assertEqual(parse_line("q = '"), ('q', "'"))

    def test_exactly_one_quote_pair_is_removed_without_changing_interior(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
        self.assertEqual(parse_line('n = ""x""'), ('n', '"x"'))

    def test_quoted_escapes_are_not_decoded(self):
        self.assertEqual(parse_line('q = "a\\nb"'), ('q', 'a\\nb'))

    def test_missing_delimiter_raises_value_error(self):
        for line in ('', 'novalue', '   ', '# comment'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_empty_stripped_key_raises_value_error(self):
        for line in (' = v', '=', '\t= 1', '\u2003= x'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_comment_like_line_is_valid_for_parse_line_when_it_has_equals(self):
        self.assertEqual(parse_line('#=v'), ('#', 'v'))
        self.assertEqual(parse_line(';=v'), (';', 'v'))


class TestIgnorableHelper(unittest.TestCase):
    def test_blank_and_comment_lines_are_ignorable(self):
        for line in ('', ' \t\u2003', '   # c', '\t; c', '\u2003# c'):
            with self.subTest(line=line):
                self.assertIs(parser_module._is_ignorable(line), True)

    def test_assignment_lines_are_not_ignorable(self):
        for line in ('a = 1', 'a = # not a comment',
                     'a = ; not a comment', ' #=v\nvalue'):
            with self.subTest(line=line):
                self.assertIs(parser_module._is_ignorable(line), False)


class TestParse(unittest.TestCase):
    def test_empty_text_returns_empty_dict(self):
        self.assertEqual(parse(''), {})

    def test_blank_and_comment_lines_are_skipped(self):
        self.assertEqual(parse(' \t\n\u2003\n  # c\n\t; c\n'), {})
        self.assertEqual(parse('k = v'), {'k': 'v'})

    def test_parse_uses_module_ignorable_helper(self):
        with patch.object(parser_module, '_is_ignorable', return_value=False) as helper:
            self.assertEqual(parse('#=v'), {'#': 'v'})
        helper.assert_called_once_with('#=v')

    def test_windows_line_endings_and_trailing_break(self):
        self.assertEqual(parse('# comment\r\n\r\n; other\r\nname = x\r\n'), {'name': 'x'})

    def test_all_recognized_line_boundaries_split_assignments(self):
        for boundary in ('\n', '\r', '\r\n', '\v', '\f', '\x1c',
                         '\x1d', '\x1e', '\x85', '\u2028', '\u2029'):
            with self.subTest(boundary=repr(boundary)):
                self.assertEqual(parse('a=1' + boundary + 'b=2' + boundary),
                                 {'a': '1', 'b': '2'})

    def test_duplicate_stripped_keys_overwrite_without_moving(self):
        result = parse('a=1\nb=2\n a =3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_comment_markers_in_values_are_significant(self):
        self.assertEqual(parse('a = # text\nb = ; text'),
                         {'a': '# text', 'b': '; text'})
        self.assertEqual(parse('#=v\n;=w'), {})

    def test_malformed_lines_at_each_position_raise_value_error(self):
        for text in ('bad\na=1\nb=2', 'a=1\nbad\nb=2',
                     'a=1\nb=2\nbad', ' = x\na=1',
                     'a=1\n\t= x\nb=2', 'a=1\nb=2\n= x'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (None, 3, [], b'a=1'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse(value)

    def test_parse_agrees_with_parse_line_on_special_value_characters(self):
        line = '  key\u2003= " #;=  "  '
        key, value = parse_line(line)
        self.assertEqual(parse(line), {key: value})

    def test_package_exports_match_parser_module(self):
        self.assertIs(parse, parser_module.parse)
        self.assertIs(parse_line, parser_module.parse_line)
