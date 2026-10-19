import dis
import inspect
import unittest
from typing import get_type_hints
from unittest.mock import patch

import kvparse.parser as parser_module
from kvparse import parse, parse_line


class TestSealedParser(unittest.TestCase):
    def test_parse_line_basic_values_and_whitespace(self):
        cases = [('a=b', ('a', 'b')), (' a = b ', ('a', 'b')), ('a=', ('a', '')), ('k e y = v', ('k e y', 'v'))]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), expected)

    def test_parse_line_partitions_only_first_equals(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_parse_line_removes_one_matching_quote_pair(self):
        cases = [('q = "x"', 'x'), ("q = 'x'", 'x'), ("q = ''", ''), ('q = ""', ''), ('u = "a" "b"', 'a" "b')]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), (line.split('=', 1)[0].strip(), expected))

    def test_parse_line_preserves_mismatched_and_single_quotes(self):
        cases = [('q = "x\'', '"x\''), ('q = "', '"'), ("q = '", "'")]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), ('q', expected))

    def test_parse_line_keeps_quoted_contents_exact(self):
        cases = [('q = " spaced "', ' spaced '), ('q = " \t spaced \t "', ' \t spaced \t '), ('q = "a"b"', 'a"b'), (r'q = "a\b = c"', r'a\b = c'), ('q = ""x""', '"x"')]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), ('q', expected))

    def test_parse_line_rejects_missing_separator_or_empty_key(self):
        for line in ('', 'novalue', ' = v', '   ', '=', '\t= 1', '\u2003= x'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIs(type(cm.exception), ValueError)

    def test_default_strip_handles_unicode_whitespace(self):
        self.assertEqual(parse_line('\u2003k e y\u00a0=\u2007v\u2003'), ('k e y', 'v'))
        self.assertEqual(parse('\u2003# comment\n\u00a0; comment\n\u2003k = v\u00a0'), {'k': 'v'})

    def test_parse_empty_and_fresh_dict(self):
        first = parse('')
        second = parse('')
        self.assertEqual(first, {})
        self.assertEqual(second, {})
        self.assertIsNot(first, second)
        self.assertEqual(parse('k = v'), {'k': 'v'})

    def test_parse_multiline_and_ignorable_lines(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
        self.assertEqual(parse('  \n\t# comment\n  ; comment\na=1'), {'a': '1'})
        self.assertEqual(parse('  \n\t# comment\n  ; comment'), {})

    def test_parse_uses_default_splitlines_separators(self):
        for separator in ('\n', '\r\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029'):
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse('a=1' + separator + 'b=2'), {'a': '1', 'b': '2'})

    def test_comment_markers_are_literal_after_key_or_in_value(self):
        self.assertEqual(parse('a = # not a comment'), {'a': '# not a comment'})
        self.assertEqual(parse('a = ; value'), {'a': '; value'})
        self.assertEqual(parse_line('#k=v'), ('#k', 'v'))
        with self.assertRaises(ValueError) as cm:
            parse_line('# comment')
        self.assertIs(type(cm.exception), ValueError)

    def test_duplicate_keys_replace_value_and_retain_order(self):
        result = parse('a=1\nb=2\n a =3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_parse_rejects_malformed_line_at_each_position(self):
        for text in ('bad\na=1', 'a=1\nbad\nb=2', 'a=1\nbad', 'a=1\n = x', 'a=1\n# bad\n; bad\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse(text)
                self.assertIs(type(cm.exception), ValueError)
        self.assertEqual(parse('# bad\na=1\n; bad'), {'a': '1'})

    def test_parse_rejects_non_string_inputs(self):
        for value in (None, 3, [], {}, b'a=1'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_module_helper_annotation_and_boolean_behavior(self):
        self.assertEqual(parse('  # c\n\t; c\na = 1'), {'a': '1'})
        helper = getattr(parser_module, '_is_ignorable')
        self.assertIs(get_type_hints(helper).get('return'), bool)
        cases = [('', True), ('   ', True), ('   # c', True), ('\t; c', True), ('a = 1', False), ('a = # not a comment', False), ('x; c', False)]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertIs(helper(line), expected)

    def test_parse_delegates_detection_and_passes_original_lines(self):
        original_helper = getattr(parser_module, '_is_ignorable')
        original_parse_line = parse_line
        checked = []
        parsed = []

        def check(line):
            checked.append(line)
            return original_helper(line)

        def read_line(line):
            parsed.append(line)
            return original_parse_line(line)

        with patch.dict(parse.__globals__, {'_is_ignorable': check, 'parse_line': read_line}):
            result = parse('  # c\n a = 1 \n\t; c\n b=2')
        self.assertEqual(result, {'a': '1', 'b': '2'})
        self.assertEqual(checked, ['  # c', ' a = 1 ', '\t; c', ' b=2'])
        self.assertEqual(parsed, [' a = 1 ', ' b=2'])

    def test_parse_line_uses_partition_without_index_loops(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertIn('partition', parse_line.__code__.co_names)
        self.assertNotIn('append', parse_line.__code__.co_names)
        self.assertFalse(any(instruction.opname.startswith('JUMP_BACKWARD') for instruction in dis.get_instructions(parse_line)))

    def test_public_exports_and_signatures(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        self.assertEqual(parse('a=b'), {'a': 'b'})
        self.assertIs(parse_line, parser_module.parse_line)
        self.assertIs(parse, parser_module.parse)
        self.assertEqual(list(inspect.signature(parse_line).parameters), ['line'])
        self.assertEqual(list(inspect.signature(parse).parameters), ['text'])

    def test_existing_test_examples_remain_valid(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
        self.assertEqual(parse_line('title = "Hello World"'), ('title', 'Hello World'))
        self.assertEqual(parse_line("title = 'single'"), ('title', 'single'))
        with self.assertRaises(ValueError) as cm:
            parse('novalue\n')
        self.assertIs(type(cm.exception), ValueError)
        with self.assertRaises(TypeError) as cm:
            parse(None)
        self.assertIs(type(cm.exception), TypeError)
