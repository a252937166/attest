import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo


class SealedPrereleaseComparisonTests(unittest.TestCase):
    def test_long_numeric_public_entry_points(self):
        value = '0.0.0-' + '1' * 5000
        self.assertTrue(Version.is_valid(value))
        self.assertEqual(Version.parse(value).compare(value), 0)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', PendingDeprecationWarning)
            self.assertEqual(semver.compare(value, '0.0.0-2'), 1)
            self.assertEqual(semver.compare('0.0.0-2', value), -1)

    def test_long_numeric_precedence_and_sorting(self):
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

    def test_integer_string_limit_is_unchanged(self):
        original = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            long_number = '1' * 5000
            with_zeros = '0' * 5000 + '1'
            parsed = Version.parse('0.0.0-' + long_number)
            self.assertTrue(Version.is_valid('0.0.0-' + long_number))
            self.assertEqual(parsed.compare('0.0.0-2'), 1)
            self.assertEqual(Version._nat_cmp(with_zeros, '1'), 0)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(original)

    def test_replace_build_preserves_long_prerelease_precedence(self):
        text = '1' * 5000
        original = Version.parse('0.0.0-' + text)
        replaced = original.replace(build='other')
        self.assertEqual(original, replaced)
        self.assertLess(original, Version(0, 0, 0))
        self.assertEqual(original.prerelease, text)
        self.assertEqual(original.build, None)
        self.assertEqual(replaced.prerelease, text)
        self.assertEqual(replaced.build, 'other')

    def test_constructor_prerelease_compatibility_table(self):
        cases = (
            ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1),
            ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1),
            ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0),
            ('１２', '13', -1), ('1٢', '12', 0), ('٠٠١', '1', 0),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, left_text)
                right = Version(0, 0, 0, right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)

    def test_arbitrary_length_leading_zero_normalization(self):
        self.assertEqual(Version._nat_cmp('0' * 5000, '0'), 0)
        self.assertEqual(Version._nat_cmp('0' * 5000 + '1', '1'), 0)
        self.assertEqual(Version(0, prerelease='0' * 5000).compare(Version(0, prerelease='0')), 0)
        self.assertEqual(Version(0, prerelease='0' * 5000 + '1').compare(Version(0, prerelease='1')), 0)

    def test_long_ascii_compares_with_unicode_number(self):
        long_number = Version(0, prerelease='9' * 5000)
        unicode_number = Version(0, prerelease='١٢')
        self.assertEqual(long_number.compare(unicode_number), 1)
        self.assertEqual(unicode_number.compare(long_number), -1)

    def test_empty_dot_identifiers(self):
        self.assertEqual(Version._nat_cmp('', None), 0)
        self.assertEqual(Version._nat_cmp('a', 'a.'), -1)
        self.assertEqual(Version._nat_cmp('a..1', 'a.0.1'), 1)
        self.assertEqual(Version._nat_cmp('', '0'), 1)

    def test_absent_prereleases(self):
        empty = Version(0, prerelease='')
        absent = Version(0, prerelease=None)
        present = Version(0, prerelease='0')
        self.assertEqual(empty.compare(absent), 0)
        self.assertEqual(absent.compare(empty), 0)
        self.assertEqual(empty.compare(present), 1)
        self.assertEqual(present.compare(absent), -1)

    def test_parse_rejects_noncanonical_prereleases(self):
        for prerelease in ('01', '01.2', '١٢', '１２'):
            value = '0.0.0-' + prerelease
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Version.parse(value)
                self.assertFalse(Version.is_valid(value))

    def test_eager_legacy_conversion_in_both_lists(self):
        for left_text, right_text in (('²', '2'), ('a.²', 'b.0'), ('a.0', 'b.²')):
            for first, second in ((left_text, right_text), (right_text, left_text)):
                with self.subTest(first=first, second=second):
                    with self.assertRaises(ValueError):
                        Version(0, prerelease=first).compare(Version(0, prerelease=second))

    def test_eager_legacy_conversion_in_unmatched_components(self):
        for first, second in (('a.²', 'a'), ('a', 'a.²'), ('²', None), (None, '²')):
            with self.subTest(first=first, second=second):
                with self.assertRaises(ValueError):
                    Version(0, prerelease=first).compare(Version(0, prerelease=second))

    def test_unequal_cores_skip_prerelease_conversion(self):
        for lower_core, higher_core in (((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)), ((0, 0, 0), (0, 0, 1))):
            with self.subTest(cores=(lower_core, higher_core)):
                lower = Version(*lower_core, prerelease='²')
                higher = Version(*higher_core, prerelease='²')
                self.assertEqual(lower.compare(higher), -1)
                self.assertEqual(higher.compare(lower), 1)
                self.assertTrue(lower < higher)

    def test_rich_operators_match_compare(self):
        low = Version.parse('0.0.0-' + '9' * 4999)
        high = Version.parse('0.0.0-' + '1' + '0' * 4999)
        self.assertEqual(low.compare(high), -1)
        self.assertFalse(low == high)
        self.assertTrue(low != high)
        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertFalse(low > high)
        self.assertFalse(low >= high)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
        self.assertFalse(high < low)
        self.assertFalse(high <= low)

    def test_rich_equality_ignores_build_metadata(self):
        text = '1' * 5000
        left = Version(0, prerelease=text, build='one')
        right = Version(0, prerelease=text, build='two')
        self.assertEqual(left.compare(right), 0)
        self.assertTrue(left == right)
        self.assertFalse(left != right)
        self.assertTrue(left <= right)
        self.assertTrue(left >= right)
        self.assertFalse(left < right)
        self.assertFalse(left > right)

    def test_compare_accepts_supported_operands(self):
        version = Version(1, 2, 3, 'rc.2')
        operands = (
            '1.2.3-rc.2', b'1.2.3-rc.2',
            {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': 'rc.2'},
            (1, 2, 3, 'rc.2'), [1, 2, 3, 'rc.2'],
            VersionInfo(1, 2, 3, 'rc.2'),
        )
        for operand in operands:
            with self.subTest(type=type(operand).__name__):
                self.assertEqual(version.compare(operand), 0)
                self.assertTrue(version == operand)

    def test_compare_rejects_unsupported_operand(self):
        with self.assertRaises(TypeError):
            Version(1).compare(object())

    def test_rich_operators_reject_invalid_collections(self):
        version = Version(1)
        self.assertIs(version.__eq__({}), NotImplemented)
        self.assertIs(version.__lt__([]), NotImplemented)
        self.assertIs(version.__gt__(('bad',)), NotImplemented)
        with self.assertRaises(TypeError):
            version < []

    def test_accepted_rich_operands_propagate_prerelease_errors(self):
        version = Version(0, prerelease='²')
        with self.assertRaises(ValueError):
            version == (0, 0, 0, '2')
        with self.assertRaises(ValueError):
            version < {'major': 0, 'prerelease': '2'}

    def test_constructor_preserves_noncanonical_values(self):
        version = Version('2', '3', '4', prerelease='a..01', build=7)
        self.assertEqual(version.to_tuple(), (2, 3, 4, 'a..01', '7'))
        self.assertEqual(Version(0, prerelease='').prerelease, '')
        self.assertIsNone(Version(0, prerelease=None).prerelease)

    def test_constructor_core_validation(self):
        with self.assertRaises(ValueError):
            Version(-1)
        with self.assertRaises(ValueError):
            Version(0, -1)
        with self.assertRaises(ValueError):
            Version(0, 0, -1)
        with self.assertRaises(ValueError):
            Version('invalid')
        with self.assertRaises(TypeError):
            Version(None)

    def test_parse_bytes_optional_parts_and_subclass(self):
        class DerivedVersion(Version):
            pass

        parsed = DerivedVersion.parse(b'1.2.3-rc.4+build')
        self.assertIsInstance(parsed, DerivedVersion)
        self.assertEqual(parsed.to_tuple(), (1, 2, 3, 'rc.4', 'build'))
        self.assertEqual(DerivedVersion.parse('1.2', optional_minor_and_patch=True).to_tuple(), (1, 2, 0, None, None))

    def test_parse_type_and_decode_errors(self):
        with self.assertRaises(TypeError):
            Version.parse(123)
        with self.assertRaises(UnicodeDecodeError):
            Version.parse(b'\xff')

    def test_deprecated_compare_emits_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', PendingDeprecationWarning)
            self.assertEqual(semver.compare('0.0.0-1', '0.0.0-2'), -1)
        self.assertTrue(any(issubclass(item.category, PendingDeprecationWarning) for item in caught))

    def test_replace_rejects_unknown_keyword(self):
        with self.assertRaises(TypeError):
            Version(1).replace(unknown=2)
