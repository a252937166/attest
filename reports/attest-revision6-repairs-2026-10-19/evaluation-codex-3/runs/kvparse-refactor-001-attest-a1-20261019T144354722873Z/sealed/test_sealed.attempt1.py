import dis
import unittest
from unittest.mock import patch

from kvparse import parse, parse_line
from kvparse.parser import parse as module_parse, parse_line as module_parse_line


class TestParseLine(unittest.TestCase):
    def test_first_separator_and_surrounding_spaces(self):
        cases = [
            ('a=b', ('a', 'b')),
            (' a = b ', ('a', 'b')),
            ('a==b', ('a', '=b')),
            ('a = b = c', ('a', 'b = c')),
            ('a=', ('a', '')),
            ('k e y = v', ('k e y', 'v')),
        ]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), expected)

    def test_one_matching_outer_quote_pair_is_removed(self):
        cases = [
            ('q = "x"', ('q', 'x')),
            ("q = 'x'", ('q', 'x')),
            ("q = ''", ('q', '')),
            ('q = ""', ('q', '')),
            ('q = " spaced "', ('q', ' spaced ')),
            ('u = "a" "b"', ('u', 'a" "b')),
        ]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), expected)

    def test_unmatched_mismatched_and_nested_quotes(self):
        cases = [
            ('q = "x\'', '"x\''),
            ('q = "', '"'),
            ("q = '", "'"),
            ('q = ""x""', '"x"'),
            ("q = ''x''", "'x'"),
        ]
        for line, expected_value in cases:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), ('q', expected_value))

    def test_strip_uses_python_whitespace_semantics(self):
        self.assertEqual(parse_line('\t\u2003key\u00a0=\u3000value\t'), ('key', 'value'))
        self.assertEqual(parse_line('a\tb = c\u2003d'), ('a\tb', 'c\u2003d'))

    def test_literal_value_content_is_preserved(self):
        self.assertEqual(parse_line(r'path = C:\dir\file=one#two;three'), ('path', r'C:\dir\file=one#two;three'))
        self.assertEqual(parse_line(r'q = "\n=;#"'), ('q', r'\n=;#'))

    def test_missing_separator_raises_value_error(self):
        for line in ('', 'novalue', '   ', '# comment', 'a b c'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIsInstance(cm.exception, ValueError)

    def test_empty_stripped_key_raises_value_error(self):
        for line in (' = v', '=', '\t= 1', '\u2003=anything'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIsInstance(cm.exception, ValueError)

    def test_comment_markers_are_ordinary_line_characters(self):
        self.assertEqual(parse_line('#k=v'), ('#k', 'v'))
        self.assertEqual(parse_line(';k=v'), (';k', 'v'))
        with self.assertRaises(ValueError) as cm:
            parse_line('# comment')
        self.assertIsInstance(cm.exception, ValueError)

    def test_partition_is_used_without_index_loops(self):
        instructions = tuple(dis.get_instructions(parse_line))
        self.assertTrue(any(i.argval == 'partition' and i.opname in ('LOAD_ATTR', 'LOAD_METHOD') for i in instructions))
        self.assertFalse(any('JUMP_BACKWARD' in i.opname for i in instructions))


class TestParse(unittest.TestCase):
    def test_empty_and_single_line_text(self):
        self.assertEqual(parse(''), {})
        self.assertEqual(parse('k = v'), {'k': 'v'})

    def test_blank_and_full_line_comments_are_ignored(self):
        text = '\n  \t\n   # no equals\n\t; also no equals\n\u2003# ignored\n'
        self.assertEqual(parse(text), {})

    def test_all_splitlines_boundaries_are_processed(self):
        separators = ('\n', '\r\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029')
        for separator in separators:
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse(separator + 'a=1' + separator + 'b=2' + separator), {'a': '1', 'b': '2'})

    def test_duplicate_key_overwrites_without_moving_its_position(self):
        result = parse('a=1\nb=2\na=3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_inline_comment_markers_remain_in_values(self):
        self.assertEqual(parse('a = # not a comment\nb = ; not a comment'), {'a': '# not a comment', 'b': '; not a comment'})

    def test_malformed_non_ignorable_lines_raise_at_every_position(self):
        for bad_line in ('missing', ' = empty key'):
            for lines in ((bad_line, 'a=1'), ('a=1', bad_line, 'b=2'), ('a=1', bad_line)):
                with self.subTest(lines=lines):
                    with self.assertRaises(ValueError) as cm:
                        parse('\n'.join(lines))
                    self.assertIsInstance(cm.exception, ValueError)

    def test_non_string_text_raises_type_error(self):
        for text in (None, 3, [], {}, b'a=1'):
            with self.subTest(text=text):
                with self.assertRaises(TypeError) as cm:
                    parse(text)
                self.assertIsInstance(cm.exception, TypeError)

    def test_str_subclass_is_accepted(self):
        class Text(str):
            pass

        self.assertEqual(parse(Text('a=1')), {'a': '1'})

    def test_module_level_helper_follows_strip_and_prefix_rule(self):
        helper = parse.__globals__.get('_is_ignorable')
        self.assertTrue(callable(helper))
        self.assertEqual(helper.__module__, 'kvparse.parser')
        self.assertEqual(helper.__qualname__, '_is_ignorable')
        cases = [
            ('', True), (' \t\u2003', True), ('   # c', True), ('\t; c', True),
            ('a = 1', False), ('a = # not a comment', False),
            ('a = ; not a comment', False), ('#k=v', True),
        ]
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertIs(helper(line), expected)
        self.assertEqual(parse('a = # not a comment'), {'a': '# not a comment'})

    def test_parse_calls_helper_for_each_input_line(self):
        seen = []

        def traced(line):
            seen.append(line)
            stripped = line.strip()
            return not stripped or stripped.startswith(('#', ';'))

        with patch.dict(parse.__globals__, {'_is_ignorable': traced}):
            result = parse('  # comment\na=1\n \nb=; literal')
        self.assertEqual(result, {'a': '1', 'b': '; literal'})
        self.assertEqual(seen, ['  # comment', 'a=1', ' ', 'b=; literal'])

    def test_package_and_parser_module_exports_match(self):
        self.assertIs(parse, module_parse)
        self.assertIs(parse_line, module_parse_line)
        self.assertEqual(module_parse('a=1'), {'a': '1'})
        self.assertEqual(module_parse_line('a=1'), ('a', '1'))
