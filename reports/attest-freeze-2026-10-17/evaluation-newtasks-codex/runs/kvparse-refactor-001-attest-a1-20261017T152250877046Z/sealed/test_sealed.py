import unittest
from unittest.mock import call, patch

from kvparse import parse, parse_line
import kvparse.parser as parser_module


class TestParseLine(unittest.TestCase):
    def test_basic_assignment(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))

    def test_first_equals_is_the_separator(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_empty_value_is_allowed(self):
        self.assertEqual(parse_line('a='), ('a', ''))

    def test_surrounding_whitespace_is_stripped(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
        self.assertEqual(parse_line('\tkey\u2003=\u00a0value\t'), ('key', 'value'))

    def test_interior_whitespace_is_preserved(self):
        self.assertEqual(parse_line('k e y = a  b'), ('k e y', 'a  b'))

    def test_matching_single_and_double_quotes_are_removed(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))

    def test_empty_matching_quotes_are_removed(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
        self.assertEqual(parse_line('q = ""'), ('q', ''))

    def test_unmatched_and_lone_quotes_are_preserved(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
        self.assertEqual(parse_line('q = "'), ('q', '"'))
        self.assertEqual(parse_line("q = '"), ('q', "'"))

    def test_whitespace_inside_quotes_is_preserved(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))

    def test_only_one_outer_quote_pair_is_removed(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
        self.assertEqual(parse_line('q = """"'), ('q', '""'))

    def test_backslashes_are_not_interpreted(self):
        self.assertEqual(parse_line(r'k = "a\"b"'), ('k', 'a\\"b'))

    def test_missing_separator_raises_value_error(self):
        for line in ('', 'novalue', '   ', '# c'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_empty_stripped_key_raises_value_error(self):
        for line in (' = v', '=', '\t= 1'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_comment_markers_are_ordinary_line_content(self):
        self.assertEqual(parse_line('#=v'), ('#', 'v'))
        self.assertEqual(parse_line('a = # not a comment'), ('a', '# not a comment'))

    def test_legacy_non_string_error_types(self):
        for line, error in ((None, TypeError), (3, TypeError), (b'a=b', ValueError)):
            with self.subTest(line=line):
                with self.assertRaises(error):
                    parse_line(line)

    def test_legacy_character_sequences(self):
        self.assertEqual(parse_line(['a', '=', 'b']), ('a', 'b'))
        self.assertEqual(parse_line(('a', '=', 'b')), ('a', 'b'))


class TestIgnorableLines(unittest.TestCase):
    def test_helper_has_bool_return_annotation(self):
        helper = getattr(parser_module, '_is_ignorable')
        self.assertIn(helper.__annotations__.get('return'), (bool, 'bool'))

    def test_helper_recognizes_blank_and_full_line_comments(self):
        helper = getattr(parser_module, '_is_ignorable')
        for line in ('', ' \t\u2003 ', '   # c', '\t; c'):
            with self.subTest(line=line):
                self.assertIs(helper(line), True)

    def test_helper_keeps_assignments_with_comment_markers(self):
        helper = getattr(parser_module, '_is_ignorable')
        for line in ('a = 1', 'a = # not a comment', 'a = ; not a comment'):
            with self.subTest(line=line):
                self.assertIs(helper(line), False)


class TestParse(unittest.TestCase):
    def test_empty_text_returns_empty_dict(self):
        self.assertEqual(parse(''), {})

    def test_single_assignment(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})

    def test_blank_lines_and_full_line_comments_are_skipped(self):
        self.assertEqual(parse(' \t\n  # invalid = \n\t; also invalid\n\u2003'), {})

    def test_splitlines_boundaries(self):
        self.assertEqual(parse('a=1\nb=2\r\nc=3\rd=4\u2028e=5'),
                         {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5'})

    def test_later_duplicate_wins_without_moving_key(self):
        result = parse('a=1\nb=2\na=3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_keys_are_stripped_and_case_sensitive(self):
        self.assertEqual(parse(' A =1\na=2\nA=3'), {'A': '3', 'a': '2'})

    def test_malformed_line_at_any_position_raises_value_error(self):
        for text in ('bad\na=1', 'a=1\nbad\nb=2', 'a=1\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_inline_comment_markers_remain_values(self):
        self.assertEqual(parse('a = # not a comment\nb = ; not a comment'),
                         {'a': '# not a comment', 'b': '; not a comment'})

    def test_invalid_text_types_raise_type_error(self):
        for value in (None, 3, [], b'', b'a=1'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse(value)

    def test_str_subclass_is_accepted(self):
        class Text(str):
            pass

        self.assertEqual(parse(Text('a=1')), {'a': '1'})

    def test_parse_delegates_ignore_decisions_to_helper(self):
        with patch.object(parser_module, '_is_ignorable', side_effect=lambda line: line == 'skip') as helper:
            with patch.object(parser_module, 'parse_line', return_value=('k', 'v')) as line_parser:
                self.assertEqual(parse('skip\nkept'), {'k': 'v'})
        self.assertEqual(helper.call_args_list, [call('skip'), call('kept')])
        line_parser.assert_called_once_with('kept')

    def test_parse_passes_original_non_ignored_line_to_parse_line(self):
        with patch.object(parser_module, 'parse_line', return_value=('k', 'v')) as line_parser:
            self.assertEqual(parse('  k = v  '), {'k': 'v'})
        line_parser.assert_called_once_with('  k = v  ')

    def test_package_exports_reference_parser_functions(self):
        self.assertIs(parse, parser_module.parse)
        self.assertIs(parse_line, parser_module.parse_line)
