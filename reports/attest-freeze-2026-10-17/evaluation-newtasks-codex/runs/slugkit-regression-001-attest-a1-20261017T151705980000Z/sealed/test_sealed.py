import re
import unittest

from slugkit import slugify
from slugkit.core import slugify as core_slugify


class TestSealedSlugify(unittest.TestCase):
    def test_repeated_hyphens_collapse(self):
        self.assertEqual(slugify('Hello--World'), 'hello-world')

    def test_mixed_separator_runs_collapse(self):
        for source, expected in (
            ('a -- b', 'a-b'),
            ('one , two ; three', 'one-two-three'),
        ):
            with self.subTest(source=source):
                self.assertEqual(slugify(source), expected)

    def test_underscore_runs_collapse(self):
        self.assertEqual(slugify('x___y'), 'x-y')

    def test_edge_punctuation_disappears(self):
        for source, expected in (('end!', 'end'), ('(parens)', 'parens')):
            with self.subTest(source=source):
                self.assertEqual(slugify(source), expected)

    def test_edge_whitespace_and_hyphens_disappear(self):
        for source, expected in (('  padded  ', 'padded'), ('--both--', 'both')):
            with self.subTest(source=source):
                self.assertEqual(slugify(source), expected)

    def test_inputs_without_ascii_alphanumerics_return_empty(self):
        for source in ('', '!!!', '   ', '--', '日本語'):
            with self.subTest(source=source):
                self.assertEqual(slugify(source), '')

    def test_existing_normal_examples(self):
        for source, expected in (
            ('Hello World', 'hello-world'),
            ('already-a-slug', 'already-a-slug'),
            ('Python 3', 'python-3'),
            ('MiXeD CaSe 42', 'mixed-case-42'),
        ):
            with self.subTest(source=source):
                self.assertEqual(slugify(source), expected)

    def test_accented_characters_are_separators(self):
        self.assertEqual(slugify('café crème'), 'caf-cr-me')

    def test_unicode_lowercasing_does_not_make_characters_eligible(self):
        self.assertEqual(slugify('K'), '')
        self.assertEqual(slugify('aKb'), 'a-b')

    def test_ascii_letters_and_digits_keep_their_order(self):
        self.assertEqual(slugify('AZaz09'), 'azaz09')

    def test_tabs_and_line_breaks_are_separators(self):
        self.assertEqual(slugify('\tA\n\r B\t'), 'a-b')

    def test_successful_results_are_strings_with_slug_shape(self):
        for source in ('', '!!!', '--both--', 'A___9', ' café K B ', 'AZaz09'):
            with self.subTest(source=source):
                result = slugify(source)
                self.assertIsInstance(result, str)
                self.assertTrue(result == '' or re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', result) is not None)

    def test_non_string_inputs_raise_type_error_with_exact_message(self):
        for bad in (None, 3, 2.5, ['a'], b'bytes'):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError) as cm:
                    slugify(bad)
                self.assertEqual(str(cm.exception), 'text must be a str')

    def test_string_subclasses_are_accepted(self):
        class Text(str):
            pass

        self.assertEqual(slugify(Text(' --A___BK9-- ')), 'a-b-9')

    def test_both_public_import_paths_expose_slugify(self):
        self.assertEqual(slugify('A -- B'), 'a-b')
        self.assertEqual(core_slugify('A -- B'), 'a-b')
