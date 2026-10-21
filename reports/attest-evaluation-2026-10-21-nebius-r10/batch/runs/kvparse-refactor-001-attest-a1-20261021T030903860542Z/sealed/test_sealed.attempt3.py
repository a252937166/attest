import unittest\nfrom kvparse import parse, parse_line\n\nclass TestKvParseAcceptance(unittest.TestCase):\n    def test_ac1_parse_line_a_eq_b(self):\n        self.assertEqual(parse_line('a=b'), ('a', 'b'))\n    def test_ac2_spaces_around_eq(self):\n        self.assertEqual(parse_line(' a = b '), ('a', 'b'))\n    def test_ac3_double_eq(self):\n        self.assertEqual(parse_line('a==b'), ('a', '=b'))\n    def test_ac3_multiple_eqs(self):\n        self.assertEqual(parse_line('a = b = c'), ('a', 'b = c'))\n    def test_ac5_empty_value(self):\n        self.assertEqual(parse_line('a='), ('a', ''))\n    def test_ac6_double_quoted_value(self):\n        self.assertEqual(parse_line('q = "x"'), ('q', 'x'))\n    def test_ac7_single_quoted_value(self):\n        self.assertEqual(parse_line("q = 'x'"), ('q', 'x'))\n    def test_ac8_mixed_quotes_not_removed(self):\n        self.assertEqual(parse_line('q = "x\''), ('q', "'x'"))\n    def test_ac9_open_quote_only(self):\n        self.assertEqual(parse_line('q = "'), ('q', '"'))\n    def test_ac10_empty_quotes(self):\n        self.assertEqual(parse_line("q = ''"), ('q', ''))\n    def test_ac11_spaced_inside_quotes(self):\n        self.assertEqual(parse_line('q = " spaced "'), ('q', ' spaced '))\n    def test_ac12_key_with_spaces(self):\n        self.assertEqual(parse_line('k e y = v'), ('k e y', 'v'))\n    def test_ac13_adjacent_quoted_strings(self):\n        self.assertEqual(parse_line('u = "a" "b"'), ('u', 'a" "b'))\n    def test_ac14_empty_line_error(self):\n        with self.assertRaises(ValueError):\n            parse_line('')\n    def test_ac15_no_equals_error(self):\n        with self.assertRaises(ValueError):\n            parse_line('novalue')\n    def test_ac16_key_only_spaces_error(self):\n        with self.assertRaises(ValueError):\n            parse_line(' = v')\n    def test_ac17_blank_only_error(self):\n        with self.assertRaises(ValueError):\n            parse_line('   ')\n    def test_ac18_equals_only_error(self):\n        with self.assertRaises(ValueError):\n            parse_line('=')\n    def test_ac19_tab_equals_error(self):\n        with self.assertRaises(ValueError):\n            parse_line('\t= 1')\n    def test_ac20_parse_empty(self):\n        self.assertEqual(parse(''), {})\n    def test_ac21_parse_simple():
        self.assertEqual(parse('k = v'), {'k': 'v'})
    def test_ac22_parse_comments_and_blanks():
        self.assertEqual(parse('# comment\n\n; other\nname = x\n'), {'name': 'x'})
    def test_ac23_parse_windows_line_endings():
        self.assertEqual(parse('a=1\rb=2\r\n'), {'a': '1', 'b': '2'})
    def test_ac24_duplicate_keys_later_wins():
        self.assertEqual(parse('a=1\na=2'), {'a': '2'})
    def test_ac25_parse_malformed_line_raises():
        with self.assertRaises(ValueError):\n            parse('novalue\n')
    def test_ac26_parse_type_error_non_string():
        for bad in (None, 3, [], b'bytes'):\n            with self.subTest(bad=bad):\n                with self.assertRaises(TypeError):\n                    parse(bad)
    def test_ac27_is_ignorable_true_cases():
        from kvparse.parser import _is_ignorable\n        self.assertTrue(_is_ignorable('   # c'))\n        self.assertTrue(_is_ignorable(''))\n        self.assertTrue(_is_ignorable('\t; c'))
    def test_ac28_is_ignorable_false_cases():
        from kvparse.parser import _is_ignorable\n        self.assertFalse(_is_ignorable('a = 1'))\n        self.assertFalse(_is_ignorable('a = # not a comment'))
    def test_ac29_parse_uses_is_ignorable():
        # ensure lines considered ignorable are skipped
        txt = '   # comment\n\n; another\nkey = value\n'
        self.assertEqual(parse(txt), {'key': 'value'})
    def test_ac30_parse_line_no_while_and_uses_partition():
        import inspect, re\n        src = inspect.getsource(parse_line)\n        self.assertNotIn('while', src)\n        self.assertIn('partition', src)
    def test_ac31_existing_tests_pass():
        # This test ensures we don't break the original test suite.
        # We'll import and run the existing test cases via unittest loader.
        loader = unittest.TestLoader()\n        suite = loader.loadTestsFromName('tests.test_parser')\n        runner = unittest.TextTestRunner(verbosity=0)\n        result = runner.run(suite)\n        self.assertTrue(result.wasSuccessful(), 'Existing test suite failed')
    def test_ac32_public_names_exported():
        import kvparse\n        self.assertTrue(hasattr(kvparse, 'parse'))\n        self.assertTrue(hasattr(kvparse, 'parse_line'))\n\n