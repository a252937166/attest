import unittest
from unittest.mock import call, patch

from kvparse import parse, parse_line
from kvparse.parser import parse as module_parse, parse_line as module_parse_line
import kvparse.parser as parser_module


class TestParseLine(unittest.TestCase):
    def test_basic_assignment(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))

    def test_first_separator_only(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_empty_value_is_allowed(self):
        self.assertEqual(parse_line('a='), ('a', ''))

    def test_surrounding_whitespace_uses_strip(self):
        self.assertEqual(parse_line('\t\u2003 a \u2003=\u2003 b \t'), ('a', 'b'))

    def test_internal_key_and_value_characters_remain(self):
        self.assertEqual(parse_line('k e y = v  w'), ('k e y', 'v  w'))

    def test_matching_quotes_are_removed(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))

    def test_empty_matching_quotes_are_removed(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
        self.assertEqual(parse_line('q = ""'), ('q', ''))

    def test_mismatched_and_single_quotes_remain(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
        self.assertEqual(parse_line('q = "'), ('q', '"'))

    def test_quoted_interior_whitespace_remains(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))

    def test_only_one_outer_quote_pair_is_removed(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
        self.assertEqual(parse_line('q = ""x""'), ('q', '"x"'))

    def test_quoted_escape_sequences_are_not_decoded(self):
        self.assertEqual(parse_line(r'q = "a\nb"'), ('q', r'a\nb'))

    def test_comment_markers_are_ordinary_key_characters(self):
        self.assertEqual(parse_line('# = v'), ('#', 'v'))
        self.assertEqual(parse_line('; = v'), (';', 'v'))

    def test_missing_separator_raises_value_error(self):
        for line in ('', 'novalue', '   ', '# comment'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_empty_stripped_key_raises_value_error(self):
        for line in (' = v', '=', '\t= 1'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_line_separation_does_not_index_the_input(self):
        class NoIndexString(str):
            def __getitem__(self, index):
                raise AssertionError('input was indexed')

        self.assertEqual(parse_line(NoIndexString(' a = b=c ')), ('a', 'b=c'))


class TestIgnorableLines(unittest.TestCase):
    def test_module_helper_returns_bool_for_blank_comments_and_assignments(self):
        helper = getattr(parser_module, '_is_ignorable')
        cases = (('', True), (' \t\u2003 ', True), ('   # c', True),
                 ('\t; c', True), ('a = 1', False),
                 ('a = # not a comment', False),
                 ('a = ; not a comment', False))
        for line, expected in cases:
            with self.subTest(line=line):
                actual = helper(line)
                self.assertIs(type(actual), bool)
                self.assertEqual(actual, expected)
                if expected:
                    self.assertEqual(parse(line), {})
                else:
                    self.assertEqual(len(parse(line)), 1)

    def test_parse_delegates_ignore_decisions_to_helper(self):
        helper = getattr(parser_module, '_is_ignorable')
        with patch.object(parser_module, '_is_ignorable', wraps=helper) as wrapped:
            self.assertEqual(parse(' \t\n  # c\n k = v \n\t; c'), {'k': 'v'})
        self.assertEqual(wrapped.call_args_list,
                         [call(' \t'), call('  # c'), call(' k = v '), call('\t; c')])


class TestParse(unittest.TestCase):
    def test_empty_text_returns_empty_dict(self):
        self.assertEqual(parse(''), {})

    def test_single_assignment(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})

    def test_blank_and_comment_only_text_returns_empty_dict(self):
        self.assertEqual(parse('\n \t\n # c\n\t; c\n'), {})

    def test_comments_with_separators_or_malformed_assignments_are_ignored(self):
        self.assertEqual(parse('# = ignored\n; bad line\na=1'), {'a': '1'})

    def test_inline_comment_markers_remain_in_values(self):
        self.assertEqual(parse('a = # not a comment\nb = ; not a comment'),
                         {'a': '# not a comment', 'b': '; not a comment'})

    def test_all_splitlines_boundaries_are_supported(self):
        for boundary in ('\n', '\r\n', '\r', '\v', '\f', '\x1c',
                         '\x1d', '\x1e', '\x85', '\u2028', '\u2029'):
            with self.subTest(boundary=repr(boundary)):
                self.assertEqual(parse('a=1' + boundary + 'b=2' + boundary),
                                 {'a': '1', 'b': '2'})

    def test_duplicate_keys_replace_values_without_moving_keys(self):
        result = parse('a=1\nb=2\n a =3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_keys_are_case_sensitive(self):
        self.assertEqual(parse('A=1\na=2'), {'A': '1', 'a': '2'})

    def test_missing_separator_at_any_position_raises_value_error(self):
        for text in ('bad\na=1\nb=2', 'a=1\nbad\nb=2', 'a=1\nb=2\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_empty_key_at_any_position_raises_value_error(self):
        for text in (' =x\na=1', 'a=1\n\t= x\nb=2', 'a=1\n =x'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_non_string_text_raises_type_error(self):
        for text in (None, 3, [], b'a=1'):
            with self.subTest(text=text):
                with self.assertRaises(TypeError):
                    parse(text)

    def test_parse_passes_original_nonignored_line_to_parse_line(self):
        with patch.object(parser_module, 'parse_line', wraps=parser_module.parse_line) as wrapped:
            self.assertEqual(parse('  k = v  '), {'k': 'v'})
        wrapped.assert_called_once_with('  k = v  ')


class TestImports(unittest.TestCase):
    def test_package_and_parser_module_exports_work(self):
        self.assertEqual(parse('a=b'), module_parse('a=b'))
        self.assertEqual(parse_line('a=b'), module_parse_line('a=b'))
