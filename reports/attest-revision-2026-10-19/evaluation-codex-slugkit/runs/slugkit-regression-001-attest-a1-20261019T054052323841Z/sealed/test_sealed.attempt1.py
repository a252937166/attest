import re
import unittest

from slugkit import slugify
from slugkit.core import slugify as core_slugify


class TestSlugifyAcceptance(unittest.TestCase):
    def test_separator_runs_collapse_to_one_hyphen(self):
        cases = {
            'Hello--World': 'hello-world',
            'a -- b': 'a-b',
            'one , two ; three': 'one-two-three',
            'x___y': 'x-y',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_edge_separators_disappear(self):
        cases = {
            'end!': 'end',
            '  padded  ': 'padded',
            '--both--': 'both',
            '(parens)': 'parens',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_inputs_without_ascii_alphanumerics_return_empty(self):
        for text in ('', '!!!', '   ', '--__\t\n'):
            with self.subTest(text=text):
                self.assertEqual(slugify(text), '')

    def test_existing_normal_cases(self):
        cases = {
            'Hello World': 'hello-world',
            'already-a-slug': 'already-a-slug',
            'Python 3': 'python-3',
            'MiXeD CaSe 42': 'mixed-case-42',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_non_ascii_characters_are_separators(self):
        cases = {
            'café crème': 'caf-cr-me',
            '日本語': '',
            'aé日b': 'a-b',
            '１２٣': '',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_unicode_casing_does_not_make_non_ascii_characters_eligible(self):
        cases = {'K': '', 'İ': '', 'aKb': 'a-b'}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(slugify(text), expected)

    def test_ascii_letters_and_digits_keep_their_order(self):
        self.assertEqual(slugify('AZaz019'), 'azaz019')

    def test_results_are_strings_with_valid_slug_shape(self):
        inputs = ('', 'AZaz019', 'Hello--World', '--__\t\n', 'café crème', 'aKb')
        pattern = re.compile(r'(?:[a-z0-9]+(?:-[a-z0-9]+)*)?')
        for text in inputs:
            with self.subTest(text=text):
                result = slugify(text)
                self.assertIsInstance(result, str)
                self.assertIsNotNone(pattern.fullmatch(result))

    def test_non_string_inputs_raise_typeerror_with_existing_message(self):
        for value in (None, 3, 2.5, ['a'], b'bytes'):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    slugify(value)
                self.assertEqual(str(cm.exception), 'text must be a str')

    def test_string_subclass_is_accepted(self):
        class Text(str):
            pass

        self.assertEqual(slugify(Text('Hello--World')), 'hello-world')

    def test_package_import_accepts_positional_and_text_keyword_arguments(self):
        self.assertEqual(slugify('Hello--World'), 'hello-world')
        self.assertEqual(slugify(text='Hello--World'), 'hello-world')

    def test_core_import_accepts_positional_and_text_keyword_arguments(self):
        self.assertEqual(core_slugify('Hello--World'), 'hello-world')
        self.assertEqual(core_slugify(text='Hello--World'), 'hello-world')
