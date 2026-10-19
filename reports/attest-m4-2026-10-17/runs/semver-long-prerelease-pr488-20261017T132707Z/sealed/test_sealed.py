import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo


class PrereleaseComparisonAcceptanceTests(unittest.TestCase):
    def test_long_ascii_identifier_parses_and_compares_equal(self):
        text = '0.0.0-' + '1' * 5000
        self.assertTrue(Version.is_valid(text))
        version = Version.parse(text)
        self.assertEqual(version.prerelease, '1' * 5000)
        self.assertEqual(version.compare(text), 0)

    def test_deprecated_compare_orders_long_ascii_identifier(self):
        text = '0.0.0-' + '1' * 5000
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', PendingDeprecationWarning)
            self.assertEqual(semver.compare(text, '0.0.0-2'), 1)
            self.assertEqual(semver.compare('0.0.0-2', text), -1)
        self.assertTrue(any(issubclass(w.category, PendingDeprecationWarning) for w in caught))

    def test_long_numeric_and_identifier_list_ordering(self):
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

    def test_all_comparison_operators_derive_from_long_identifier_order(self):
        low = Version.parse('0.0.0-' + '1' * 5000)
        high = Version(0, 0, 0)
        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
        self.assertTrue(low != high)
        self.assertFalse(low == high)
        self.assertTrue(low == low.replace(build='other'))
        self.assertTrue(low <= low.replace(build='other'))
        self.assertTrue(low >= low.replace(build='other'))

    def test_ascii_zero_normalization_with_legacy_numeric_identifiers(self):
        cases = (
            ('0' * 5000, '0', 0),
            ('0' * 5000 + '12', '12', 0),
            ('0' * 5000 + '12', '١٢', 0),
            ('1' * 5000, '١٢', 1),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left=left_text[:20], right=right_text):
                left = Version(0, 0, 0, left_text)
                right = Version(0, 0, 0, right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)

    def test_constructor_prereleases_keep_legacy_comparison_and_original_text(self):
        cases = (
            ('0001', '1', 0),
            ('000', '0', 0),
            ('02', '10', -1),
            ('01.2', '1.2', 0),
            ('2a', '10a', 1),
            ('01a', '1a', -1),
            ('-1', '0', 1),
            ('', None, 0),
            ('١٢', '12', 0),
            ('１２', '13', -1),
            ('1٢', '12', 0),
            ('٠٠١', '1', 0),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, left_text)
                right = Version(0, 0, 0, right_text)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)

    def test_natural_comparison_preserves_empty_identifiers_and_boundaries(self):
        cases = (('', None, 0), ('a', 'a.', -1), ('a..b', 'a.b', -1), ('0', '', -1))
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_release_precedence_and_empty_prerelease_equivalence(self):
        release = Version(0, 0, 0)
        empty = Version(0, 0, 0, '')
        prerelease = Version(0, 0, 0, '0')
        self.assertEqual(release.compare(empty), 0)
        self.assertEqual(empty.compare(release), 0)
        self.assertEqual(prerelease.compare(release), -1)
        self.assertEqual(release.compare(prerelease), 1)

    def test_strict_parser_rejects_noncanonical_prereleases(self):
        for prerelease in ('01', '01.2', '١٢', '１２'):
            text = '0.0.0-' + prerelease
            with self.subTest(prerelease=prerelease):
                with self.assertRaises(ValueError):
                    Version.parse(text)
                self.assertFalse(Version.is_valid(text))

    def test_legacy_conversion_errors_are_eager_across_decisive_identifiers(self):
        pairs = (('²', '2'), ('a.²', 'b.0'), ('a.0', 'b.²'))
        for left_text, right_text in pairs:
            for a, b in ((left_text, right_text), (right_text, left_text)):
                with self.subTest(left=a, right=b):
                    with self.assertRaises(ValueError):
                        Version(0, 0, 0, a).compare(Version(0, 0, 0, b))

    def test_legacy_conversion_errors_survive_matching_prefix_and_release_absence(self):
        pairs = (('a', 'a.²'), ('²', '²'), ('²', None))
        for left_text, right_text in pairs:
            with self.subTest(left=left_text, right=right_text):
                with self.assertRaises(ValueError):
                    Version(0, 0, 0, left_text).compare(Version(0, 0, 0, right_text))
                with self.assertRaises(ValueError):
                    Version._nat_cmp(left_text, right_text)

    def test_comparison_operator_propagates_legacy_conversion_error(self):
        left = Version(0, 0, 0, 'a.²')
        right = Version(0, 0, 0, 'b.0')
        with self.assertRaises(ValueError):
            _ = left < right
        with self.assertRaises(ValueError):
            _ = left == right

    def test_core_components_decide_before_prerelease_conversion(self):
        bad = Version(0, 0, 0, '²')
        for core in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            with self.subTest(core=core):
                higher = Version(*core, prerelease='²')
                self.assertEqual(bad.compare(higher), -1)
                self.assertEqual(higher.compare(bad), 1)
                self.assertTrue(bad < higher)
                self.assertTrue(higher > bad)

    def test_compare_preserves_operand_coercion_and_ignores_build(self):
        version = Version(1, 2, 3, 'rc.2', 'first')
        operands = (
            '1.2.3-rc.2+second',
            b'1.2.3-rc.2+second',
            {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': 'rc.2', 'build': 'second'},
            (1, 2, 3, 'rc.2', 'second'),
            [1, 2, 3, 'rc.2', 'second'],
        )
        for operand in operands:
            with self.subTest(operand=type(operand).__name__):
                self.assertEqual(version.compare(operand), 0)
                self.assertTrue(version == operand)

    def test_compare_rejects_unsupported_operands(self):
        version = Version(1, 2, 3)
        with self.assertRaises(TypeError):
            version.compare(object())
        with self.assertRaises(ValueError):
            version.compare('1.2.3-01')

    def test_invalid_collection_operators_return_not_implemented(self):
        version = Version(1, 2, 3)
        for operand in ({}, (), [], {'unknown': 1}):
            with self.subTest(operand=operand):
                self.assertIs(version.__lt__(operand), NotImplemented)
                self.assertIs(version.__eq__(operand), NotImplemented)

    def test_non_ascii_integer_conversion_limit_remains_effective(self):
        previous = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(4300)
        try:
            bad = Version(0, 0, 0, '١' * 4301)
            with self.assertRaises(ValueError):
                bad.compare(Version(0, 0, 0, '2'))
        finally:
            sys.set_int_max_str_digits(previous)

    def test_long_ascii_comparison_works_with_active_integer_conversion_limit(self):
        previous = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(4300)
        try:
            low = Version.parse('0.0.0-' + '9' * 4999)
            high = Version.parse('0.0.0-' + '1' + '0' * 4999)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
            self.assertEqual(low.compare(high), -1)
            self.assertEqual(high.compare(low), 1)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_constructor_and_parser_keep_existing_input_behavior(self):
        version = Version('1', '2', '3', 4, 5)
        self.assertEqual(version.to_tuple(), (1, 2, 3, '4', '5'))
        self.assertEqual(Version(0, prerelease='²').prerelease, '²')
        self.assertEqual(Version.parse(b'1.2.3-rc.1').prerelease, 'rc.1')
        self.assertEqual(Version.parse('1.2', optional_minor_and_patch=True).patch, 0)
        with self.assertRaises(TypeError):
            Version.parse(123)
        with self.assertRaises(ValueError):
            Version(-1)

    def test_replace_preserves_long_prerelease_and_rejects_unknown_key(self):
        version = Version.parse('0.0.0-' + '1' * 5000)
        replaced = version.replace(build='other')
        self.assertEqual(replaced.prerelease, version.prerelease)
        self.assertEqual(version.compare(replaced), 0)
        with self.assertRaises(TypeError):
            version.replace(unknown=1)

    def test_version_info_alias_is_preserved(self):
        self.assertIs(VersionInfo, Version)
