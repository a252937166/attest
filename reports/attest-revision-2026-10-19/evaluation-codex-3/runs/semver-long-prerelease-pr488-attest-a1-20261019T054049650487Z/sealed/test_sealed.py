import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo


class TestSealedPrereleaseComparison(unittest.TestCase):
    def test_long_parsed_identifier_is_valid_and_compares_with_itself(self):
        text = '0.0.0-' + '1' * 5000
        self.assertTrue(Version.is_valid(text))
        version = Version.parse(text)
        self.assertEqual(version.prerelease, '1' * 5000)
        self.assertEqual(version.compare(text), 0)

    def test_deprecated_compare_orders_long_identifiers_and_warns(self):
        text = '0.0.0-' + '1' * 5000
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', PendingDeprecationWarning)
            self.assertEqual(semver.compare(text, '0.0.0-2'), 1)
            self.assertEqual(semver.compare('0.0.0-2', text), -1)
        self.assertEqual(len(caught), 2)
        self.assertTrue(all(issubclass(w.category, PendingDeprecationWarning) for w in caught))

    def test_long_parsed_identifier_ordering_and_sorting(self):
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

    def test_long_prerelease_ignores_build_and_precedes_release(self):
        text = '1' * 5000
        version = Version.parse('0.0.0-' + text)
        changed_build = version.replace(build='other')
        self.assertEqual(version.compare(changed_build), 0)
        self.assertEqual(version, changed_build)
        self.assertLess(version, Version(0, 0, 0))
        self.assertEqual(version.prerelease, text)
        self.assertEqual(changed_build.prerelease, text)

    def test_constructor_identifier_ordering_and_spelling(self):
        cases = (
            ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1),
            ('01.2', '1.2', 0), ('2a', '10a', 1),
            ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0),
            ('١٢', '12', 0), ('１２', '13', -1),
            ('1٢', '12', 0), ('٠٠١', '1', 0),
        )
        for left_text, right_text, expected in cases:
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, 0, 0, prerelease=left_text)
                right = Version(0, 0, 0, prerelease=right_text)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, left_text)
                self.assertEqual(right.prerelease, right_text)

    def test_long_zero_identifiers_normalize_without_changing_storage(self):
        long_zero = Version(0, prerelease='0' * 5000)
        short_zero = Version(0, prerelease='0')
        self.assertEqual(long_zero.compare(short_zero), 0)
        self.assertEqual(short_zero.compare(long_zero), 0)
        self.assertEqual(long_zero.prerelease, '0' * 5000)

    def test_long_leading_zeros_equal_ascii_and_unicode_values(self):
        long_twelve = Version(0, prerelease='0' * 5000 + '12')
        for text in ('12', '١٢'):
            with self.subTest(text=text):
                other = Version(0, prerelease=text)
                self.assertEqual(long_twelve.compare(other), 0)
                self.assertEqual(other.compare(long_twelve), 0)
        self.assertEqual(long_twelve.prerelease, '0' * 5000 + '12')

    def test_long_ascii_number_exceeds_short_unicode_number(self):
        long_number = Version(0, prerelease='1' * 5000)
        unicode_number = Version(0, prerelease='١٢')
        self.assertEqual(long_number.compare(unicode_number), 1)
        self.assertEqual(unicode_number.compare(long_number), -1)

    def test_parser_rejects_noncanonical_and_unicode_prereleases(self):
        for prerelease in ('01', '01.2', '١٢', '１２'):
            with self.subTest(prerelease=prerelease):
                text = '0.0.0-' + prerelease
                with self.assertRaises(ValueError):
                    Version.parse(text)
                self.assertFalse(Version.is_valid(text))

    def test_legacy_digit_errors_are_eager_in_both_directions(self):
        cases = (('²', '2'), ('a.²', 'b.0'), ('a.0', 'b.²'),
                 ('a', 'a.²'), ('²', None))
        for left_text, right_text in cases:
            with self.subTest(left=left_text, right=right_text):
                left = Version(0, prerelease=left_text)
                right = Version(0, prerelease=right_text)
                with self.assertRaises(ValueError):
                    left.compare(right)
                with self.assertRaises(ValueError):
                    right.compare(left)

    def test_identity_and_equality_do_not_skip_digit_validation(self):
        version = Version(0, prerelease='²')
        with self.assertRaises(ValueError):
            version.compare(version)
        with self.assertRaises(ValueError):
            version == version

    def test_core_precedence_bypasses_prerelease_validation(self):
        for low_core, high_core in (((0, 0, 0), (1, 0, 0)),
                                    ((1, 0, 0), (1, 1, 0)),
                                    ((1, 1, 0), (1, 1, 1))):
            with self.subTest(low=low_core, high=high_core):
                low = Version(*low_core, prerelease='²')
                high = Version(*high_core, prerelease='²')
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)
                self.assertTrue(low < high)

    def test_helper_preserves_empty_identifiers_and_list_length(self):
        cases = (('', None, 0), ('a.', 'a', 1),
                 ('a..1', 'a..2', -1), ('0', '', -1))
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_release_precedence_overrides_empty_helper_ordering(self):
        numeric = Version(0, prerelease='0')
        release = Version(0)
        empty = Version(0, prerelease='')
        self.assertEqual(numeric.compare(release), -1)
        self.assertEqual(numeric.compare(empty), -1)
        self.assertEqual(empty.compare(release), 0)

    def test_ascii_comparison_preserves_integer_conversion_limit(self):
        if not hasattr(sys, 'get_int_max_str_digits'):
            self.skipTest('interpreter has no integer string conversion limit')
        original = sys.get_int_max_str_digits()
        if original == 0 or original > 5000:
            self.skipTest('integer string conversion limit does not cover 5000 digits')
        try:
            self.assertEqual(Version._nat_cmp('1' * 5000, '2'), 1)
            self.assertEqual(Version._nat_cmp('0' * 5000 + '12', '12'), 0)
            self.assertEqual(sys.get_int_max_str_digits(), original)
        finally:
            if sys.get_int_max_str_digits() != original:
                sys.set_int_max_str_digits(original)

    def test_legacy_unicode_conversion_keeps_enabled_digit_limit_error(self):
        if not hasattr(sys, 'get_int_max_str_digits'):
            self.skipTest('interpreter has no integer string conversion limit')
        limit = sys.get_int_max_str_digits()
        if limit == 0 or limit > 5000:
            self.skipTest('integer string conversion limit does not cover 5000 digits')
        with self.assertRaises(ValueError):
            Version(0, prerelease='١' * 5000).compare(Version(0, prerelease='2'))
        self.assertEqual(sys.get_int_max_str_digits(), limit)

    def test_all_comparison_operators_use_long_numeric_precedence(self):
        low = Version(0, prerelease='9' * 4999)
        high = Version(0, prerelease='1' + '0' * 4999)
        equal = Version(0, prerelease='0' * 5000 + '12')
        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
        self.assertTrue(equal == Version(0, prerelease='12'))
        self.assertFalse(equal != Version(0, prerelease='١٢'))

    def test_compare_accepts_existing_operand_forms(self):
        version = Version(1, 2, 3, 'rc.2')
        operands = ('1.2.3-rc.2', b'1.2.3-rc.2',
                    {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': 'rc.2'},
                    (1, 2, 3, 'rc.2'), [1, 2, 3, 'rc.2'])
        for operand in operands:
            with self.subTest(type=type(operand).__name__):
                self.assertEqual(version.compare(operand), 0)
                self.assertTrue(version == operand)

    def test_unsupported_operands_and_invalid_collections(self):
        version = Version(1)
        with self.assertRaises(TypeError):
            version.compare(object())
        with self.assertRaises(ValueError):
            version.compare('not-a-version')
        self.assertFalse(version == object())
        self.assertFalse(version == [])
        self.assertTrue(version != [])
        with self.assertRaises(TypeError):
            version < object()
        with self.assertRaises(TypeError):
            version < []

    def test_parse_bytes_subclass_and_optional_core_parts(self):
        class SubVersion(Version):
            pass

        parsed = SubVersion.parse(b'1.2.3-rc.2+meta')
        self.assertIsInstance(parsed, SubVersion)
        self.assertEqual(parsed.to_tuple(), (1, 2, 3, 'rc.2', 'meta'))
        self.assertEqual(SubVersion.parse('1.2', optional_minor_and_patch=True).to_tuple(),
                         (1, 2, 0, None, None))
        with self.assertRaises(TypeError):
            Version.parse(None)
        with self.assertRaises(TypeError):
            Version.is_valid(None)

    def test_constructor_storage_and_core_conversion_remain_permissive(self):
        version = Version('1', '2', '3', prerelease='a..01', build=42)
        self.assertEqual(version.to_tuple(), (1, 2, 3, 'a..01', '42'))
        self.assertIs(VersionInfo, Version)
        with self.assertRaises(ValueError):
            Version(-1)
        with self.assertRaises(ValueError):
            Version('not-an-integer')
        with self.assertRaises(TypeError):
            Version(None)
