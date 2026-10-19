import inspect
import re
import unittest

from slugkit import slugify
from slugkit.core import slugify as core_slugify


class TestSealedSlugify(unittest.TestCase):
    def test_separator_runs_collapse(self):
        cases = {
            'Hello--World': 'hello-world',
            'a -- b': 'a-b',
            'one , two ; three': 'one-two-three',
            'x___y': 'x-y',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_edge_separators_disappear(self):
        cases = {
            'end!': 'end',
            '  padded  ': 'padded',
            '--both--': 'both',
            '(parens)': 'parens',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(slugify(''), '')

    def test_separator_only_inputs_return_empty_string(self):
        for value in ('!!!', '   ', '--', '\t\n'):
            with self.subTest(value=value):
                self.assertEqual(slugify(value), '')

    def test_existing_normal_examples(self):
        cases = {
            'Hello World': 'hello-world',
            'already-a-slug': 'already-a-slug',
            'Python 3': 'python-3',
            'MiXeD CaSe 42': 'mixed-case-42',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_non_ascii_characters_are_separators(self):
        cases = {
            'café crème': 'caf-cr-me',
            '日本語': '',
            'a１２b': 'a-b',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_kelvin_sign_lowercases_to_ascii(self):
        self.assertEqual(slugify('K'), 'k')

    def test_dotted_capital_i_lowercases_before_filtering(self):
        self.assertEqual(slugify('İ'), 'i')

    def test_tabs_and_newlines_form_one_separator(self):
        self.assertEqual(slugify('a\t\n b'), 'a-b')

    def test_all_ascii_digits_remain(self):
        self.assertEqual(slugify('0123456789'), '0123456789')

    def test_successful_results_are_strings_with_valid_slug_shape(self):
        pattern = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
        for value in ('', '!!!', '--Hello___World--', 'İ', 'café crème', '日本語', 'a１２b', '0123456789'):
            with self.subTest(value=value):
                result = slugify(value)
                self.assertIsInstance(result, str)
                self.assertTrue(result == '' or pattern.fullmatch(result) is not None)

    def test_non_string_inputs_raise_type_error_with_exact_message(self):
        for value in (None, 3, 2.5, ['a'], b'bytes'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    slugify(value)
                self.assertIs(type(cm.exception), TypeError)
                self.assertEqual(str(cm.exception), 'text must be a str')

    def test_string_subclasses_are_accepted(self):
        class Text(str):
            pass

        self.assertEqual(slugify(Text('Hello--World')), 'hello-world')

    def test_both_public_import_paths_work(self):
        self.assertEqual(slugify('a -- b'), 'a-b')
        self.assertEqual(core_slugify('a -- b'), 'a-b')

    def test_both_public_import_paths_have_text_signature(self):
        for public_slugify in (slugify, core_slugify):
            with self.subTest(public_slugify=public_slugify):
                self.assertEqual(str(inspect.signature(public_slugify)), '(text)')
                self.assertEqual(public_slugify(text='Python 3'), 'python-3')
