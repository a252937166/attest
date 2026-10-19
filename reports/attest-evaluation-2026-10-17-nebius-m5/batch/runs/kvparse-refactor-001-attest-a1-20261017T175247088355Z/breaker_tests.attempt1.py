import unittest
from kvparse import parse, parse_line, _is_ignorable

class BreakerTests(unittest.TestCase):
    def test_parse_line_unicode_key_value(self):
        self.assertEqual(parse_line('α = β'), ('α', 'β'))
        self.assertEqual(parse_line('😀 = "👍"'), ('😀', '👍'))
    
    def test_parse_line_whitespace_variants(self):
        # tab and spaces mix
        self.assertEqual(parse_line('\tkey\t=\tvalue\t'), ('key', 'value'))
        self.assertEqual(parse_line('\nkey = value\n'), ('key', 'value'))  # leading/trailing newline treated as part of line? Actually line includes newline? splitlines removes newline, so we test via parse.
        # but parse_line receives line without newline.
        self.assertEqual(parse_line('key = value'), ('key', 'value'))
    
    def test_parse_line_quote_not_matching(self):
        self.assertEqual(parse_line('k = "v\''), ('k', '