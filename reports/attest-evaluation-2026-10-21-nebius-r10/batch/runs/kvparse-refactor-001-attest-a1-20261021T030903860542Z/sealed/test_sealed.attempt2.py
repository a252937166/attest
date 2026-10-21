import unittest
from kvparse import parse, parse_line

class TestKvParse(unittest.TestCase):
    def test_ac1_parse_line_a_eq_b(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
    def test_ac2_spaces_around_eq(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
    def test_ac3_double_eq(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
    def test_ac4_multiple_eq(self):
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))
    def test_ac5_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))
    def test_ac6_quoted_double(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
    def test_ac7_quoted_single(self):
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
    def test_ac8_mixed_quote_inside(self):
        self.assertEqual(parse_line('q = "x\'"'), ('q', "'x'"))
    def test_ac9_open_quote_only(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
    def test_ac10_empty_quotes(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
    def test_ac11_spaced_inside_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
    def test_ac12_key_with_spaces(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
    def test_ac13_extra_quotes_after_first_pair(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
    def test_ac14_empty_line_error(self):
        with self.assertRaises(ValueError):
            parse_line('')
    def test_ac15_no_equal_sign(self):
        with self.assertRaises(ValueError):
            parse_line('novalue')
    def test_ac16_key_empty_before_eq(self):
        with self.assertRaises(ValueError):
            parse_line(' = v')
    def test_ac17_only_spaces(self):
        with self.assertRaises(ValueError):
            parse_line('   ')
    def test_ac18_only_eq(self):
        with self.assertRaises(ValueError):
            parse_line('=')
    def test_ac19_tab_before_eq(self):
        with self.assertRaises(ValueError):
            parse_line('	= 1')
    def test_ac20_parse_empty_string(self):
        self.assertEqual(parse(''), {})
    def test_ac21_simple_kv(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})
    def test_ac22_comments_and_blanks(self):
        self.assertEqual(parse('# comment

; other
name = x
'), {'name': 'x'})
    def test_ac23_windows_newlines(self):
        self.assertEqual(parse('a=1\rb=2
'), {'a': '1', 'b': '2'})
    def test_ac24_duplicate_keys_later_wins(self):
        self.assertEqual(parse('a=1
a=2'), {'a': '2'})
    def test_ac25_malformed_line_raises(self):
        with self.assertRaises(ValueError):
            parse('novalue
')
    def test_ac26_type_error_nonstr(self):
        for bad in (None, 3, [], b'bytes'):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    parse(bad)
    def test_ac27_is_ignorable_true_cases(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('   # c'))
        self.assertTrue(_is_ignorable(''))
        self.assertTrue(_is_ignorable('	; c'))
    def test_ac28_is_ignorable_false_cases(self):
        from kvparse.parser import _is_ignorable
        self.assertFalse(_is_ignorable('a = 1'))
        self.assertFalse(_is_ignorable('a = # not a comment'))
    def test_ac29_parse_uses_is_ignorable(self):
        # ensure lines starting with ; after spaces are ignored
        txt = '
   ; comment
key=val
'
        self.assertEqual(parse(txt), {'key': 'val'})
    def test_ac30_parse_line_no_while_and_uses_partition(self):
        import inspect, re
        src = inspect.getsource(parse_line)
        self.assertNotIn('while', src)
        self.assertIn('partition', src)
    def test_ac31_existing_tests_pass(self):
        # Run the existing test suite via import
        import tests.test_parser as tp
        suite = unittest.TestLoader().loadTestsFromModule(tp)
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        self.assertEqual(result.wasSuccessful(), True, 'Existing tests should pass')
    def test_ac32_public_names_exported(self):
        import kvparse
        self.assertTrue(hasattr(kvparse, 'parse'))
        self.assertTrue(hasattr(kvparse, 'parse_line'))

