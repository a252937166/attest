import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo


class SealedPrereleaseComparisonTests(unittest.TestCase):
    def test_long_numeric_prerelease_is_valid_and_self_equal(self):
        text = '0.0.0-' + '1' * 5000
        self.assertTrue(Version.is_valid(text))
        parsed = Version.parse(text)
        self.assertEqual(parsed.prerelease, '1' * 5000)
        self.assertEqual(parsed.compare(text), 0)

    def test_module_compare_orders_long_numeric_identifiers_both_ways(self):
        long_version = '0.0.0-' + '1' * 5000
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', PendingDeprecationWarning)
            self.assertEqual(semver.compare(long_version, '0.0.0-2'), 1)
            self.assertEqual(semver.compare('0.0.0-2', long_version), -1)

    def test_long_prerelease_pairs_compare_and_sort(self):
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

    def test_build_metadata_does_not_change_long_prerelease_precedence(self):
        version = Version.parse('0.0.0-' + '1' * 5000)
        replacement = version.replace(build='other')
        self.assertIsNot(version, replacement)
        self.assertIsNone(version.build)
        self.assertEqual(replacement.build, 'other')
        self.assertEqual(version.compare(replacement), 0)
        self.assertTrue(version == replacement)
        self.assertTrue(version < Version(0, 0, 0))

    def test_constructor_identifiers_keep_legacy_order_and_text(self):
        cases = (
            ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1),
            ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1),
            ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0),
            ('１２', '13', -1), ('1٢', '12', 0), ('٠٠١', '1', 0),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, prerelease=left_text)
                right = Version(0, 0, 0, prerelease=right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)

    def test_constructor_long_ascii_normalization_and_unicode_comparison(self):
        cases = (
            ('0' * 5000, '0', 0),
            ('0' * 5000 + '12', '12', 0),
            ('0' * 5000 + '12', '١٢', 0),
            ('1' * 5000, '１２', 1),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left_length=len(left_text), right=right_text):
                left = Version(0, 0, 0, prerelease=left_text)
                right = Version(0, 0, 0, prerelease=right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)

    def test_nat_cmp_preserves_empty_identifiers(self):
        cases = (('', None, 0), ('a.', 'a', 1),
                 ('a..1', 'a..01', 0), ('', '0', 1))
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_public_comparison_treats_empty_prerelease_as_release(self):
        empty = Version(0, 0, 0, prerelease='')
        release = Version(0, 0, 0)
        prerelease = Version(0, 0, 0, prerelease='0')
        self.assertEqual(empty.compare(release), 0)
        self.assertEqual(release.compare(empty), 0)
        self.assertEqual(empty.compare(prerelease), 1)
        self.assertEqual(prerelease.compare(empty), -1)

    def test_strict_parse_rejects_noncanonical_prereleases(self):
        for identifier in ('01', '01.2', '١٢', '１２'):
            with self.subTest(identifier=identifier):
                text = '0.0.0-' + identifier
                with self.assertRaises(ValueError):
                    Version.parse(text)
                self.assertFalse(Version.is_valid(text))

    def test_unicode_conversion_errors_survive_earlier_identifier_difference(self):
        for left_text, right_text in (('²', '2'), ('a.²', 'b.0'),
                                      ('a.0', 'b.²')):
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, prerelease=left_text)
                right = Version(0, 0, 0, prerelease=right_text)
                with self.assertRaises(ValueError):
                    left.compare(right)
                with self.assertRaises(ValueError):
                    right.compare(left)

    def test_unicode_conversion_errors_survive_length_release_and_equality(self):
        for left_text, right_text in (('a', 'a.²'), ('²', None), ('²', '²')):
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, prerelease=left_text)
                right = Version(0, 0, 0, prerelease=right_text)
                with self.assertRaises(ValueError):
                    left.compare(right)
                with self.assertRaises(ValueError):
                    right.compare(left)

    def test_all_comparison_operators_propagate_unicode_conversion_errors(self):
        left = Version(0, 0, 0, prerelease='a.²')
        right = Version(0, 0, 0, prerelease='b.0')
        for operation in (
            lambda: left == right, lambda: left != right,
            lambda: left < right, lambda: left <= right,
            lambda: left > right, lambda: left >= right,
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    operation()

    def test_core_precedence_skips_invalid_prerelease_conversion(self):
        for low_core, high_core in (((0, 0, 0), (1, 0, 0)),
                                    ((0, 0, 0), (0, 1, 0)),
                                    ((0, 0, 0), (0, 0, 1))):
            with self.subTest(high_core=high_core):
                low = Version(*low_core, prerelease='²')
                high = Version(*high_core, prerelease='²')
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)
                self.assertTrue(low < high)

    def test_cpython_digit_limit_remains_enabled_for_long_ascii_comparisons(self):
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            with self.assertRaises(ValueError):
                int('1' * 5000)
            long_version = Version.parse('0.0.0-' + '1' * 5000)
            self.assertEqual(long_version.compare('0.0.0-2'), 1)
            self.assertEqual(Version._nat_cmp('0' * 6000 + '12', '12'), 0)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_long_unicode_digits_keep_legacy_integer_conversion_limit(self):
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            long_unicode = '١' * 5000
            with self.assertRaises(ValueError):
                Version._nat_cmp(long_unicode, '2')
            with self.assertRaises(ValueError):
                Version(0, 0, 0, prerelease=long_unicode).compare(
                    Version(0, 0, 0, prerelease='2'))
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_parse_preserves_bytes_optional_components_and_subclasses(self):
        class ChildVersion(Version):
            pass

        parsed = ChildVersion.parse(b'1-rc.2', optional_minor_and_patch=True)
        self.assertIsInstance(parsed, ChildVersion)
        self.assertEqual(parsed.to_tuple(), (1, 0, 0, 'rc.2', None))
        with self.assertRaises(ValueError):
            Version.parse('1-rc.2')

    def test_constructor_storage_and_core_conversion_remain_permissive(self):
        version = Version('2', '3', '4', prerelease='²', build=19)
        self.assertEqual(version.to_tuple(), (2, 3, 4, '²', '19'))
        self.assertIs(VersionInfo, Version)
        with self.assertRaises(ValueError):
            Version(-1)
        with self.assertRaises(ValueError):
            Version('invalid')

    def test_compare_coerces_supported_operand_forms(self):
        version = Version(0, 0, 0, prerelease='1' * 5000)
        operands = (
            '0.0.0-2', b'0.0.0-2',
            {'major': 0, 'minor': 0, 'patch': 0, 'prerelease': '2'},
            (0, 0, 0, '2'), [0, 0, 0, '2'],
        )
        for operand in operands:
            with self.subTest(operand_type=type(operand)):
                self.assertEqual(version.compare(operand), 1)

    def test_compare_propagates_operand_errors(self):
        version = Version(0, 0, 0)
        with self.assertRaises(TypeError):
            version.compare(object())
        with self.assertRaises(ValueError):
            version.compare('not-a-version')
        with self.assertRaises(ValueError):
            version.compare({'major': 'invalid'})
        with self.assertRaises(TypeError):
            version.compare(())

    def test_operators_preserve_notimplemented_for_invalid_operands(self):
        version = Version(0, 0, 0)
        self.assertIs(version.__eq__(object()), NotImplemented)
        self.assertIs(version.__lt__({}), NotImplemented)
        self.assertFalse(version == {})
        with self.assertRaises(TypeError):
            version < {}
        with self.assertRaises(ValueError):
            version < 'not-a-version'

    def test_all_six_operators_derive_from_long_numeric_comparison(self):
        low = Version.parse('0.0.0-' + '9' * 4999)
        high = Version.parse('0.0.0-' + '1' + '0' * 4999)
        self.assertFalse(low == high)
        self.assertTrue(low != high)
        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertFalse(low > high)
        self.assertFalse(low >= high)

    def test_replace_rejects_unknown_parts(self):
        with self.assertRaises(TypeError):
            Version(0, 0, 0).replace(unknown=1)

    def test_is_valid_propagates_non_value_errors(self):
        with self.assertRaises(TypeError):
            Version.is_valid(None)
