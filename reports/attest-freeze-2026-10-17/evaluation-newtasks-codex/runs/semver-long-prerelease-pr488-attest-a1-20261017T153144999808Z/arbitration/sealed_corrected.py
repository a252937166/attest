import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo


class TestSealedPrereleaseComparison(unittest.TestCase):
    def test_public_class_alias(self):
        self.assertIs(VersionInfo, Version)
        self.assertIs(semver.Version, Version)

    def test_canonical_5000_digit_prerelease_parses_and_compares(self):
        text = '0.0.0-' + '1' * 5000
        self.assertTrue(Version.is_valid(text))
        version = Version.parse(text)
        self.assertEqual(version.prerelease, '1' * 5000)
        self.assertEqual(version.compare(text), 0)

    def test_deprecated_compare_orders_long_digits_and_warns(self):
        text = '0.0.0-' + '1' * 5000
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', PendingDeprecationWarning)
            self.assertEqual(semver.compare(text, '0.0.0-2'), 1)
            self.assertEqual(semver.compare('0.0.0-2', text), -1)
        self.assertEqual(len(caught), 2)
        self.assertTrue(all(issubclass(w.category, PendingDeprecationWarning) for w in caught))

    def test_long_numeric_and_identifier_precedence(self):
        pairs = (
            ('9' * 4999, '1' + '0' * 4999),
            ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'),
            ('1' * 5000, 'alpha'),
            ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'),
        )
        for low_text, high_text in pairs:
            with self.subTest(low=low_text[:20], high=high_text[:20]):
                low = Version.parse('0.0.0-' + low_text)
                high = Version.parse('0.0.0-' + high_text)
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)
                self.assertEqual(sorted([high, low]), [low, high])

    def test_long_prerelease_release_precedence_and_build_replacement(self):
        version = Version.parse('0.0.0-' + '1' * 5000)
        rebuilt = version.replace(build='other')
        release = Version(0, 0, 0)
        self.assertEqual(version.compare(rebuilt), 0)
        self.assertEqual(rebuilt.compare(version), 0)
        self.assertTrue(version == rebuilt)
        self.assertTrue(version < release)
        self.assertTrue(release > version)
        self.assertEqual(version.compare(release), -1)
        self.assertEqual(release.compare(version), 1)

    def test_direct_constructor_numeric_and_text_identifiers(self):
        cases = (
            ('0001', '1', 0),
            ('000', '0', 0),
            ('02', '10', -1),
            ('01.2', '1.2', 0),
            ('2a', '10a', 1),
            ('01a', '1a', -1),
            ('-1', '0', 1),
            ('', None, 0),
            ('\u0661\u0662', '12', 0),
            ('\uff11\uff12', '13', -1),
            ('1\u0662', '12', 0),
            ('\u0660\u0660\u0661', '1', 0),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, prerelease=left_text)
                right = Version(0, 0, 0, prerelease=right_text)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)

    def test_long_leading_zeros_and_mixed_unicode_numeric_values(self):
        zero = Version(0, 0, 0, prerelease='0' * 5000)
        twelve = Version(0, 0, 0, prerelease='0' * 5000 + '12')
        huge = Version(0, 0, 0, prerelease='1' * 5000)
        self.assertEqual(zero.compare(Version(0, 0, 0, prerelease='0')), 0)
        self.assertEqual(twelve.compare(Version(0, 0, 0, prerelease='12')), 0)
        self.assertEqual(twelve.compare(Version(0, 0, 0, prerelease='\u0661\u0662')), 0)
        self.assertEqual(huge.compare(Version(0, 0, 0, prerelease='\uff11\uff12')), 1)

    def test_identifier_boundaries_and_empty_parts(self):
        self.assertEqual(Version._nat_cmp('', None), 0)
        self.assertEqual(Version._nat_cmp('a', 'a.'), -1)
        self.assertEqual(Version._nat_cmp('a..b', 'a..c'), -1)
        self.assertEqual(Version._nat_cmp('0', ''), -1)
        self.assertEqual(Version(0, 0, 0, prerelease='0').compare(Version(0, 0, 0)), -1)

    def test_parser_rejects_noncanonical_and_unicode_prereleases(self):
        for prerelease in ('01', '01.2', '\u0661\u0662', '\uff11\uff12'):
            text = '0.0.0-' + prerelease
            with self.subTest(prerelease=prerelease):
                with self.assertRaises(ValueError) as cm:
                    Version.parse(text)
                self.assertIsInstance(cm.exception, ValueError)
                self.assertFalse(Version.is_valid(text))

    def test_legacy_digit_conversion_errors_are_eager_in_both_orders(self):
        pairs = (
            ('\u00b2', '2'),
            ('a.\u00b2', 'b.0'),
            ('a.0', 'b.\u00b2'),
            ('a', 'a.\u00b2'),
            ('\u00b2', None),
        )
        for left_text, right_text in pairs:
            for first, second in ((left_text, right_text), (right_text, left_text)):
                with self.subTest(first=first, second=second):
                    left = Version(0, 0, 0, prerelease=first)
                    right = Version(0, 0, 0, prerelease=second)
                    with self.assertRaises(ValueError) as cm:
                        left.compare(right)
                    self.assertIsInstance(cm.exception, ValueError)

    def test_core_precedence_skips_bad_prerelease_conversion(self):
        for smaller, larger in (((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)), ((0, 0, 0), (0, 0, 1))):
            left = Version(*smaller, prerelease='\u00b2')
            right = Version(*larger, prerelease='\u00b2')
            self.assertEqual(left.compare(right), -1)
            self.assertEqual(right.compare(left), 1)
            self.assertTrue(left < right)

    def test_long_ascii_comparison_respects_active_integer_string_limit(self):
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
            huge = Version(0, 0, 0, prerelease='9' * 5000)
            self.assertEqual(huge.compare(Version(0, 0, 0, prerelease='8' * 5000)), 1)
            self.assertEqual(huge.compare(Version(0, 0, 0, prerelease='\u0661\u0662')), 1)
            self.assertEqual(Version._nat_cmp('0' * 5000 + '12', '12'), 0)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_legacy_unicode_digits_keep_integer_conversion_limit(self):
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            bad = Version(0, 0, 0, prerelease='\u0661' * 5000)
            with self.assertRaises(ValueError) as cm:
                bad.compare(Version(0, 0, 0, prerelease='2'))
            self.assertIsInstance(cm.exception, ValueError)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_compare_coerces_supported_operand_types(self):
        left = Version.parse('0.0.0-' + '1' * 5000)
        values = (
            Version(0, 0, 0, prerelease='2'),
            '0.0.0-2',
            b'0.0.0-2',
            {'major': 0, 'minor': 0, 'patch': 0, 'prerelease': '2'},
            (0, 0, 0, '2'),
            [0, 0, 0, '2'],
        )
        for other in values:
            with self.subTest(other_type=type(other).__name__):
                self.assertEqual(left.compare(other), 1)

    def test_comparison_operators_derive_from_long_numeric_compare(self):
        lower = Version.parse('0.0.0-' + '8' * 5000)
        higher = Version.parse('0.0.0-' + '9' * 5000)
        self.assertTrue(lower < higher)
        self.assertTrue(lower <= higher)
        self.assertTrue(higher > lower)
        self.assertTrue(higher >= lower)
        self.assertTrue(lower != higher)
        self.assertFalse(lower == higher)
        self.assertTrue(lower == lower.replace(build='meta'))

    def test_operators_propagate_legacy_conversion_errors(self):
        bad = Version(0, 0, 0, prerelease='\u00b2')
        good = Version(0, 0, 0, prerelease='2')
        for operation in (lambda: bad == good, lambda: bad != good, lambda: bad < good,
                          lambda: bad <= good, lambda: bad > good, lambda: bad >= good):
            with self.assertRaises(ValueError) as cm:
                operation()
            self.assertIsInstance(cm.exception, ValueError)

    def test_unsupported_operands_preserve_compare_and_operator_behavior(self):
        version = Version(0, 0, 0)
        with self.assertRaises(TypeError) as cm:
            version.compare(object())
        self.assertIsInstance(cm.exception, TypeError)
        self.assertIs(version.__lt__(object()), NotImplemented)
        self.assertIs(version.__eq__({}), NotImplemented)
        self.assertIs(version.__lt__((0, 'bad')), NotImplemented)

    def test_constructor_remains_permissive_and_core_errors_remain(self):
        version = Version('0', '0', '0', prerelease='01', build=7)
        self.assertEqual(version.to_tuple(), (0, 0, 0, '01', '7'))
        with self.assertRaises(ValueError) as cm:
            Version(-1)
        self.assertIsInstance(cm.exception, ValueError)
        with self.assertRaises(ValueError) as cm:
            Version('invalid')
        self.assertIsInstance(cm.exception, ValueError)

    def test_parse_bytes_and_optional_components_still_work(self):
        text = b'0.0.0-' + b'1' * 5000
        self.assertEqual(Version.parse(text).prerelease, '1' * 5000)
        self.assertEqual(Version.parse('0', optional_minor_and_patch=True).to_tuple()[:3], (0, 0, 0))
        with self.assertRaises(TypeError) as cm:
            Version.parse(123)
        self.assertIsInstance(cm.exception, TypeError)

    def test_replace_rejects_unknown_parts(self):
        with self.assertRaises(TypeError) as cm:
            Version(0, 0, 0).replace(unknown=1)
        self.assertIsInstance(cm.exception, TypeError)
