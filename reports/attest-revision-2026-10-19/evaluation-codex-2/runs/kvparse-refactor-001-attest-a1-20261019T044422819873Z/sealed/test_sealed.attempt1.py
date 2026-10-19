import dis
import importlib
import unittest
from unittest.mock import patch

from kvparse import parse, parse_line


class TestParseLine(unittest.TestCase):
    def test_basic_assignment_and_surrounding_whitespace(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))

    def test_split_at_first_equals(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))

    def test_matching_outer_quotes(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
        self.assertEqual(parse_line("q = ''"), ('q', ''))
        self.assertEqual(parse_line('q = ""'), ('q', ''))

    def test_mismatched_outer_quotes_remain(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
        self.assertEqual(parse_line("q = 'x\""), ('q', "'x\""))

    def test_lone_quote_remains(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
        self.assertEqual(parse_line("q = '"), ('q', "'"))

    def test_quote_removal_happens_once_without_stripping_inside(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
        self.assertEqual(parse_line('q = "\"x\""'), ('q', '"x"'))
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))

    def test_missing_equals_raises_value_error(self):
        for line in ('', 'novalue', '   ', '\tno value'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIs(type(cm.exception), ValueError)

    def test_empty_stripped_key_raises_value_error(self):
        for line in (' = v', '=', '\t= 1', '\u2003= value'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIs(type(cm.exception), ValueError)

    def test_unicode_surrounding_whitespace_is_stripped(self):
        self.assertEqual(parse_line('\u2003k\u00a0=\u2002v\u3000'), ('k', 'v'))

    def test_internal_key_and_value_characters_remain(self):
        self.assertEqual(parse_line(' "k e y" = a  b=c\\n#;'), ('"k e y"', 'a  b=c\\n#;'))
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))

    def test_comment_marker_in_key_is_not_skipped(self):
        self.assertEqual(parse_line('#k=v'), ('#k', 'v'))
        self.assertEqual(parse_line(';k=v'), (';k', 'v'))

    def test_embedded_line_separator_is_not_split(self):
        self.assertEqual(parse_line('a=one\ntwo'), ('a', 'one\ntwo'))
        self.assertEqual(parse_line('a=one\rtwo'), ('a', 'one\rtwo'))

    def test_partition_without_index_scanning(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        instructions = tuple(dis.get_instructions(parse_line))
        self.assertTrue(any(i.opname in ('LOAD_METHOD', 'LOAD_ATTR') and i.argval == 'partition' for i in instructions))
        self.assertFalse(any('JUMP_BACKWARD' in i.opname for i in instructions))


class TestParse(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(parse(''), {})

    def test_single_assignment(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})

    def test_blank_and_whitespace_only_lines_are_ignored(self):
        self.assertEqual(parse('\n   \n\t\n\u2003\na=1'), {'a': '1'})

    def test_whitespace_prefixed_comments_are_ignored_even_with_equals(self):
        self.assertEqual(parse('   # x=y\n\t; a=b\n# comment\n; other\nname = x\n'), {'name': 'x'})

    def test_comment_markers_after_equals_are_values(self):
        self.assertEqual(parse('a = # not a comment\nb = ; also a value'), {'a': '# not a comment', 'b': '; also a value'})

    def test_splitlines_recognizes_python_line_separators(self):
        text = 'a=1\r\nb=2\rc=3\nd=4\ve=5\ff=6\x1cg=7\x1dh=8\x1ei=9\x85j=10\u2028k=11\u2029l=12'
        self.assertEqual(parse(text), {chr(97 + i): str(i + 1) for i in range(12)})

    def test_duplicate_stripped_keys_replace_values_without_moving_position(self):
        result = parse(' a = 1\nb=2\na=3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_keys_are_case_sensitive(self):
        self.assertEqual(parse('a=1\nA=2'), {'a': '1', 'A': '2'})

    def test_malformed_non_ignored_line_raises_at_any_position(self):
        for text in ('bad\na=1', 'a=1\nbad\nb=2', 'a=1\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse(text)
                self.assertIs(type(cm.exception), ValueError)

    def test_non_string_input_raises_type_error(self):
        for value in (None, 3, [], b'a=b'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_str_subclass_is_accepted(self):
        class Text(str):
            pass

        self.assertEqual(parse(Text('a=1')), {'a': '1'})

    def test_helper_is_module_level_and_bool_annotated(self):
        self.assertEqual(parse('a=1'), {'a': '1'})
        helper = parse.__globals__.get('_is_ignorable')
        self.assertTrue(callable(helper))
        self.assertEqual(helper.__qualname__, '_is_ignorable')
        self.assertEqual(helper.__module__, 'kvparse.parser')
        self.assertIn(helper.__annotations__.get('return'), (bool, 'bool'))

    def test_parse_calls_helper_on_raw_lines(self):
        seen = []

        def recording_helper(line):
            seen.append(line)
            stripped = line.strip()
            return not stripped or stripped.startswith(('#', ';'))

        with patch.dict(parse.__globals__, {'_is_ignorable': recording_helper}):
            self.assertEqual(parse('  # x=y\n\t\na = # value'), {'a': '# value'})
        self.assertEqual(seen, ['  # x=y', '\t', 'a = # value'])

    def test_public_exports_are_parser_functions(self):
        parser_module = importlib.import_module('kvparse.parser')
        self.assertEqual(parse('a=1'), {'a': '1'})
        self.assertEqual(parse_line('a=1'), ('a', '1'))
        self.assertIs(parse, parser_module.parse)
        self.assertIs(parse_line, parser_module.parse_line)
