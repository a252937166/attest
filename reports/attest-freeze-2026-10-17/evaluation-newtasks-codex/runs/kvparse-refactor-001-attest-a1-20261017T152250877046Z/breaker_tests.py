import unittest

from kvparse import parse, parse_line


class BreakerTests(unittest.TestCase):
    def test_integer_keyed_mapping_preserves_indexed_input(self):
        self.assertEqual(parse_line({0: 'a', 1: '=', 2: 'b'}), ('a', 'b'))

    def test_mapping_insertion_order_does_not_change_indexed_input(self):
        line = {2: ' b ', 0: ' a ', 1: '='}
        self.assertEqual(parse_line(line), ('a', 'b'))

    def test_mapping_missing_zero_preserves_key_error(self):
        with self.assertRaises(KeyError):
            parse_line({1: '=', 2: 'b'})

    def test_mapping_noncharacter_key_preserves_type_error(self):
        with self.assertRaises(TypeError):
            parse_line({0: 7, 1: '=', 2: 'b'})

    def test_unicode_whitespace_and_quoted_content(self):
        self.assertEqual(parse_line('\u2003key\u00a0=\u2002" a = b "\u2009'), ('key', ' a = b '))

    def test_less_common_splitlines_boundaries(self):
        self.assertEqual(parse('a=1\x1cb=2\x1da=3\x85c=4'), {'a': '3', 'b': '2', 'c': '4'})

    def test_comment_markers_inside_values_across_line_boundaries(self):
        self.assertEqual(parse(' \u2003# ignored\r\nk=# value\r\u2002; ignored\nv=; value'), {'k': '# value', 'v': '; value'})

    def test_other_non_string_parse_inputs_raise_type_error(self):
        for value in (True, bytearray(), memoryview(b'a=b'), {'a': 'b'}):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    parse(value)
