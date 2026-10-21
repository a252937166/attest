import unittest
from kvparse import parse, parse_line

class TestParseLine(unittest.TestCase):
    def test_ac1_simple(self):
        self.assertEqual(parse_line('a=b'), ('a', 'b'))
    def test_ac2_spaces(self):
        self.assertEqual(parse_line(' a = b '), ('a', 'b'))
    def test_ac3_double_eq(self):
        self.assertEqual(parse_line('a==b'), ('a', '=b'))
    def test_ac3_multiple_eq(self):
        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))
    def test_ac5_empty_value(self):
        self.assertEqual(parse_line('a='), ('a', ''))
    def test_ac6_double_quoted(self):
        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))
    def test_ac7_single_quoted(self):
        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))
    def test_ac8_mixed_quotes_no_remove(self):
        self.assertEqual(parse_line('q = "x\''), ('q', '"x\''))
    def test_ac9_open_quote_only(self):
        self.assertEqual(parse_line('q = "'), ('q', '"'))
    def test_ac10_empty_quotes(self):
        self.assertEqual(parse_line("q = ''"), ('q', ''))
    def test_ac11_spaced_inside_quotes(self):
        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))
    def test_ac12_key_with_spaces(self):
        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))
    def test_ac13_extra_quotes_inside(self):
        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))
    def test_ac14_empty_line(self):
        with self.assertRaises(ValueError):
            parse_line('')
    def test_ac15_no_equals(self):
        with self.assertRaises(ValueError):
            parse_line('novalue')
    def test_ac16_empty_key_before_eq(self):
        with self.assertRaises(ValueError):
            parse_line(' = v')
    def test_ac17_only_spaces(self):
        with self.assertRaises(ValueError):
            parse_line('   ')
    def test_ac18_only_eq(self):
        with self.assertRaises(ValueError):
            parse_line('=')
    def test_ac19_tab_eq(self):
        with self.assertRaises(ValueError):
            parse_line('	= 1')
    def test_ac20_no_while_loop(self):
        import inspect
        src = inspect.getsource(parse_line)
        self.assertNotIn('while', src)
        self.assertIn('partition', src)

class TestParse(unittest.TestCase):
    def test_ac21_empty_text(self):
        self.assertEqual(parse(''), {})
    def test_ac22_simple_kv(self):
        self.assertEqual(parse('k = v'), {'k': 'v'})
    def test_ac23_comments_and_blanks(self):
        self.assertEqual(parse('# comment

; other
name = x
'), {'name': 'x'})
    def test_ac24_windows_line_endings(self):
        self.assertEqual(parse('a=1
b=2
'), {'a': '1', 'b': '2'})
    def test_ac25_duplicate_keys_later_win(self):
        self.assertEqual(parse('a=1
a=2'), {'a': '2'})
    def test_ac26_value_error_propagates(self):
        with self.assertRaises(ValueError):
            parse('novalue
')
    def test_ac27_type_error_nonstr(self):
        for bad in (None, 3, [], b'bytes'):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    parse(bad)
    def test_ac28_is_ignorable_true(self):
        from kvparse.parser import _is_ignorable
        self.assertTrue(_is_ignorable('   # c'))
        self.assertTrue(_is_ignorable(''))
        self.assertTrue(_is_ignorable('	; c'))
    def test_ac29_is_ignorable_false(self):
        from kvparse.parser import _is_ignorable
        self.assertFalse(_is_ignorable('a = 1'))
        self.assertFalse(_is_ignorable('a = # not a comment'))
    def test_ac30_existing_tests_pass(self):
        # Run the existing test suite via import
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('tests.test_parser')
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        self.assertEqual(result.failures, [])
        self.assertEqual(result.errors, [])

