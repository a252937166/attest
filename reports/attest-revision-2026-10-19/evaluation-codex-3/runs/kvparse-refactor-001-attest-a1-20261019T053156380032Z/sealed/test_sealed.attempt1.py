import dis
import unittest

from kvparse import parse, parse_line


class TestSealedParser(unittest.TestCase):
    def test_parse_line_strips_key_and_value(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
        self.assertEqual(parse_line('a='), ('a', ''))

    def test_parse_line_splits_at_first_equals(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))

    def test_parse_line_removes_matching_outer_quotes(self):
        for line, expected in [('q = "x"', 'x'), ("q = 'x'", 'x'), ("q = ''", ''), ('q = ""', '')]:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line), ('q', expected))

    def test_parse_line_preserves_mismatched_and_lone_quotes(self):
        self.assertEqual(parse_line("q = \"x'"), ('q', "\"x'"))
        self.assertEqual(parse_line('q = "'), ('q', '"'))
        self.assertEqual(parse_line("q = '"), ('q', "'"))

    def test_parse_line_preserves_space_inside_outer_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
        self.assertEqual(parse_line('q = "  "'), ('q', '  '))

    def test_parse_line_removes_only_one_outer_pair(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
        self.assertEqual(parse_line('q = ""x""'), ('q', '"x"'))

    def test_parse_line_preserves_internal_key_space_and_literal_escapes(self):
        slash = chr(92)
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
        self.assertEqual(parse_line('q = "a' + slash + 'tb"'), ('q', 'a' + slash + 'tb'))

    def test_parse_line_rejects_missing_equals(self):
        for line in ('', 'novalue', '   '):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIs(type(cm.exception), ValueError)

    def test_parse_line_rejects_empty_stripped_key(self):
        for line in (' = v', '=', '\t= 1', '\u2003= value'):
            with self.subTest(line=line):
                with self.assertRaises(ValueError) as cm:
                    parse_line(line)
                self.assertIs(type(cm.exception), ValueError)

    def test_parse_line_uses_unicode_strip_boundaries(self):
        self.assertEqual(parse_line('\u2003key\u2002=\u00a0value\u2003'), ('key', 'value'))

    def test_parse_line_does_not_split_line_breaks(self):
        self.assertEqual(parse_line(' a\nb = c\nd '), ('a\nb', 'c\nd'))
        self.assertEqual(parse_line('a=\nb'), ('a', 'b'))

    def test_ignorable_helper_matches_stripped_line_rule(self):
        parse('')
        helper = parse.__globals__['_is_ignorable']
        cases = ('', ' \t\u2003 ', '   # c', '\t; c', 'a = 1', 'a = # not a comment', '#', ';', ' x#y', '\u2003; note')
        for line in cases:
            with self.subTest(line=line):
                stripped = line.strip()
                expected = not stripped or stripped.startswith(('#', ';'))
                self.assertIs(helper(line), expected)
                self.assertIs(type(helper(line)), bool)

    def test_parse_skips_blank_and_comment_lines(self):
        self.assertEqual(parse(''), {})
        self.assertEqual(parse('k = v'), {'k': 'v'})
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
        self.assertEqual(parse(' \u2003\n \t# note\n\t; note\n'), {})

    def test_parse_uses_splitlines_boundaries(self):
        self.assertEqual(parse('a=1\r\nb=2\r\n'), {'a': '1', 'b': '2'})
        self.assertEqual(parse('a=1\rb=2\vc=3\fd=4\x1ce=5'), {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5'})

    def test_parse_duplicate_stripped_keys_keep_first_position(self):
        result = parse('a=1\nb=2\n a =3')
        self.assertEqual(result, {'a': '3', 'b': '2'})
        self.assertEqual(list(result), ['a', 'b'])

    def test_comment_markers_inside_values_are_literal(self):
        self.assertEqual(parse('a = # not a comment\nb = ; text'), {'a': '# not a comment', 'b': '; text'})
        self.assertEqual(parse_line('# = ; text'), ('#', '; text'))

    def test_parse_rejects_malformed_line_at_any_position(self):
        for text in ('bad\na=1', 'a=1\nbad\nb=2', 'a=1\nbad', 'a=1\n = invalid'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse(text)
                self.assertIs(type(cm.exception), ValueError)

    def test_parse_requires_string_instance(self):
        for value in (None, 3, [], b'a=1'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse(value)
                self.assertIs(type(cm.exception), TypeError)

    def test_public_exports_come_from_parser_module(self):
        self.assertEqual(parse.__module__, 'kvparse.parser')
        self.assertEqual(parse_line.__module__, 'kvparse.parser')
        self.assertEqual(parse('a=1'), {'a': '1'})
        self.assertEqual(parse_line('a=1'), ('a', '1'))

    def test_parse_line_bytecode_calls_partition_without_a_backward_loop(self):
        self.assertEqual(parse_line('a=b=c'), ('a', 'b=c'))
        instructions = tuple(dis.get_instructions(parse_line))
        self.assertTrue(any(i.opname in ('LOAD_ATTR', 'LOAD_METHOD') and i.argval == 'partition' for i in instructions))
        self.assertFalse(any('JUMP_BACKWARD' in i.opname for i in instructions))

    def test_parse_uses_module_scope_annotated_helper(self):
        self.assertEqual(parse(' # ignored\na=1'), {'a': '1'})
        helper = parse.__globals__.get('_is_ignorable')
        self.assertTrue(callable(helper))
        self.assertEqual(helper.__module__, 'kvparse.parser')
        self.assertIn(helper.__annotations__.get('return'), (bool, 'bool'))
        self.assertIn('_is_ignorable', parse.__code__.co_names)

    def test_original_public_examples(self):
        self.assertEqual(parse('a = 1\nb=2\n'), {'a': '1', 'b': '2'})
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
        self.assertEqual(parse_line('title = "Hello World"'), ('title', 'Hello World'))
        self.assertEqual(parse_line("title = 'single'"), ('title', 'single'))
