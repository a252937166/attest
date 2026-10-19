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

    def test_empty_and_separator_only_inputs(self):
        for value in ('', '!!!', '   ', '--', '\t\n'):
            with self.subTest(value=value):
                self.assertEqual(slugify(value), '')

    def test_existing_outputs(self):
        cases = {
            'Hello World': 'hello-world',
            'already-a-slug': 'already-a-slug',
            'Python 3': 'python-3',
            'MiXeD CaSe 42': 'mixed-case-42',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_non_ascii_after_lowercase_is_separator(self):
        cases = {
            'café crème': 'caf-cr-me',
            '日本語': '',
            'a１２b': 'a-b',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_lowercase_precedes_ascii_classification(self):
        for value, expected in (('K', 'k'), ('İ', 'i')):
            with self.subTest(value=value):
                self.assertEqual(slugify(value), expected)

    def test_ascii_letters_and_digits_preserve_order(self):
        self.assertEqual(
            slugify('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
            'abcdefghijklmnopqrstuvwxyz0123456789',
        )

    def test_mixed_separator_types_form_one_run(self):
        self.assertEqual(slugify('a \t\n_!é--b'), 'a-b')

    def test_successful_results_are_strings_with_valid_slug_shape(self):
        samples = ('', '!!!', '--Hello, 42!--', 'a \t\n_!é--b', '日本語', 'K', 'İ')
        pattern = re.compile(r'(?:[a-z0-9]+(?:-[a-z0-9]+)*)?\Z')
        for value in samples:
            with self.subTest(value=value):
                result = slugify(value)
                self.assertIsInstance(result, str)
                self.assertIsNotNone(pattern.fullmatch(result))

    def test_non_string_inputs_raise_type_error_with_existing_message(self):
        for value in (None, 3, 2.5, ['a'], b'bytes'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    slugify(value)
                self.assertEqual(str(cm.exception), 'text must be a str')

    def test_string_subclass_is_accepted(self):
        class StringChild(str):
            pass

        result = slugify(StringChild('  Child--42!  '))
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'child-42')

    def test_both_public_import_paths_work(self):
        for function in (slugify, core_slugify):
            with self.subTest(function=function):
                self.assertEqual(function('Hello--World!'), 'hello-world')

    def test_text_keyword_argument(self):
        self.assertEqual(slugify(text='Hello World'), 'hello-world')

    def test_missing_text_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify()

    def test_additional_argument_raises_type_error(self):
        with self.assertRaises(TypeError):
            slugify('hello', 'extra')
