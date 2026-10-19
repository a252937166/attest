import dis
import sys
import unittest

from kvparse import parse, parse_line


class TestParseLine(unittest.TestCase):
    def test_first_equals_is_separator(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_surrounding_whitespace_is_stripped(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))

    def test_empty_values_are_valid(self):
        self.assertEqual(parse_line('a='), ('a', ''))
        self.assertEqual(parse_line('a=   '), ('a', ''))

    def test_matching_quote_pairs_are_removed(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
        self.assertEqual(parse_line("q = ''"), ('q', ''))
        self.assertEqual(parse_line('q = ""'), ('q', ''))

    def test_mismatched_quotes_remain(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
        self.assertEqual(parse_line('q = \'x"'), ('q', 'x"'))

    def test_lone_quotes_remain(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
        self.assertEqual(parse_line("q = '"), ('q', "'"))

    def test_quoted_interior_whitespace_remains(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))

    def test_internal_key_and_value_characters_remain(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))

    def test_only_one_nested_quote_pair_is_removed(self):
        self.assertEqual(parse_line('q = ""x""'), ('q', '"x"'))

    def test_backslashes_are_not_processed(self):
        self.assertEqual(parse_line('q = "a\\nb"'), ('q', 'a\\nb'))

    def test_missing_separator_raises_value_error(self):
        for line in ('', 'novalue', '   '):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_empty_stripped_key_raises_value_error(self):
        for line in (' = v', '=', '\t= 1'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    def test_comment_markers_have_no_special_meaning_in_parse_line(self):
        self.assertEqual(parse_line('# key = value'), ('# key', 'value'))
        self.assertEqual(parse_line('; key = value'), ('; key', 'value'))

    def test_unicode_whitespace_uses_strip_semantics(self):
        self.assertEqual(parse_line('\u2003k\u00a0=\u202fv\u2003'), ('k', 'v'))
        self.assertEqual(parse_line(' q\u00a0x = a\u00a0b '), ('q\u00a0x', 'a\u00a0b'))

    def test_parse_line_does_not_split_lines(self):
        self.assertEqual(parse_line('a=1\nb=2'), ('a', '1\nb=2'))


class TestParse(unittest.TestCase):
    def test_empty_and_basic_input(self):
        self.assertEqual(parse(''), {})
        self.assertEqual(parse('k = v'), {'k': 'v'})
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})

    def test_blank_and_full_line_comments_are_ignored(self):
        self.assertEqual(parse(' \n\t\n  # comment\n\t; comment\na=1'), {'a': '1'})

    def test_entirely_ignorable_input_is_empty(self):
        self.assertEqual(parse('\n  \n # comment\n\t; comment\n'), {})

    def test_splitlines_separators(self):
        for separator in ('\n', '\r\n', '\r', '\v', '\f', '\x1c', '\u2028'):
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse('a=1' + separator + 'b=2' + separator), {'a': '1', 'b': '2'})

    def test_duplicates_overwrite_without_reordering(self):
        result = parse(' a =1\nb=2\na=3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_inline_comment_characters_are_values(self):
        self.assertEqual(parse('a = # not a comment\nb = ; also a value'), {'a': '# not a comment', 'b': '; also a value'})

    def test_malformed_line_at_any_position_raises_value_error(self):
        for text in ('bad\na=1', '# comment\na=1\nbad\nb=2', 'a=1\n; comment\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse(text)

    def test_empty_key_in_parse_raises_value_error(self):
        with self.assertRaises(ValueError):
            parse('a=1\n  =2')

    def test_non_string_input_raises_type_error(self):
        for value in (None, 3, [], b'a=b'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse(value)

    def test_str_subclass_is_accepted(self):
        class Text(str):
            pass

        self.assertEqual(parse(Text('a=1')), {'a': '1'})


class TestStructureAndExports(unittest.TestCase):
    def test_module_level_ignorable_helper(self):
        self.assertEqual(parse(''), {})
        module = sys.modules[parse.__module__]
        helper = getattr(module, '_is_ignorable')
        cases = (('   # c', True), ('', True), ('\t; c', True), (' \u2003\t', True), ('a = 1', False), ('a = # not a comment', False), ('x; comment', False))
        for line, expected in cases:
            with self.subTest(line=line):
                self.assertIs(type(helper(line)), bool)
                self.assertIs(helper(line), expected)

    def test_parse_line_bytecode_uses_partition(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        instructions = tuple(dis.get_instructions(parse_line))
        self.assertIn('partition', [instruction.argval for instruction in instructions if instruction.opname in ('LOAD_METHOD', 'LOAD_ATTR')])
        self.assertIn('=', parse_line.__code__.co_consts)

    def test_parse_line_has_no_backward_loop_jump(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        self.assertFalse(any('BACKWARD' in instruction.opname for instruction in dis.get_instructions(parse_line)))

    def test_parse_references_ignorable_helper(self):
        self.assertEqual(parse(' # comment\na=1'), {'a': '1'})
        self.assertIn('_is_ignorable', parse.__code__.co_names)

    def test_package_exports_parser_functions(self):
        self.assertEqual(parse('a=1'), {'a': '1'})
        self.assertEqual(parse_line('a=1'), ('a', '1'))
        self.assertIs(parse, sys.modules['kvparse.parser'].parse)
        self.assertIs(parse_line, sys.modules['kvparse.parser'].parse_line)
