import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


LONG_ONES = '1' * 5000


class TestLongAsciiPrereleases(unittest.TestCase):
    def test_long_canonical_prerelease_parses_and_compares_equal(self):
        value = '0.0.0-' + LONG_ONES
        self.assertTrue(Version.is_valid(value))
        self.assertEqual(Version.parse(value).compare(value), 0)

    def test_deprecated_compare_orders_long_prerelease_and_warns(self):
        value = '0.0.0-' + LONG_ONES
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', PendingDeprecationWarning)
            self.assertEqual(semver.compare(value, '0.0.0-2'), 1)
            self.assertEqual(semver.compare('0.0.0-2', value), -1)
        self.assertTrue(any(issubclass(item.category, PendingDeprecationWarning)
                            for item in caught))

    def test_long_identifier_precedence_and_sorting(self):
        pairs = (
            ('9' * 4999, '1' + '0' * 4999),
            ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'),
            (LONG_ONES, 'alpha'),
            ('alpha.' + LONG_ONES, 'alpha.' + LONG_ONES + '.1'),
        )
        for low_tag, high_tag in pairs:
            with self.subTest(low=low_tag[:20], high=high_tag[:20]):
                low = Version.parse('0.0.0-' + low_tag)
                high = Version.parse('0.0.0-' + high_tag)
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)
                self.assertEqual(sorted([high, low]), [low, high])

    def test_long_prerelease_ignores_build_and_precedes_release(self):
        version = Version.parse('0.0.0-' + LONG_ONES)
        changed = version.replace(build='other')
        self.assertIsNot(changed, version)
        self.assertEqual(version, changed)
        self.assertEqual(version.compare(changed), 0)
        self.assertLess(version, Version(0, 0, 0))

    def test_comparison_preserves_all_stored_parts(self):
        left = Version(0, 0, 0, LONG_ONES, 'left')
        right = Version(0, 0, 0, '2', 'right')
        before = (left.to_tuple(), right.to_tuple())
        self.assertEqual(left.compare(right), 1)
        self.assertEqual((left.to_tuple(), right.to_tuple()), before)

    def test_long_leading_zeros_normalize_without_changing_storage(self):
        cases = (
            ('0' * 5000, '0', 0),
            ('0' * 5000 + '1', '1', 0),
            ('0' * 5000 + '2', '10', -1),
        )
        for a, b, expected in cases:
            with self.subTest(suffix=a[-10:], other=b):
                left = Version(0, 0, 0, a)
                right = Version(0, 0, 0, b)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, a)
                self.assertEqual(right.prerelease, b)

    def test_long_ascii_number_compares_above_unicode_number(self):
        left = Version(0, 0, 0, LONG_ONES)
        right = Version(0, 0, 0, '١٢')
        self.assertEqual(left.compare(right), 1)
        self.assertEqual(right.compare(left), -1)

    def test_ascii_comparison_preserves_integer_string_limit(self):
        if not hasattr(sys, 'set_int_max_str_digits'):
            self.skipTest('interpreter has no integer-string conversion limit')
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            self.assertEqual(Version._nat_cmp(LONG_ONES, '2'), 1)
            self.assertEqual(Version._nat_cmp('0' * 5000 + '1', '1'), 0)
            self.assertEqual(Version.parse('0.0.0-' + LONG_ONES).compare('0.0.0-2'), 1)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)


class TestIdentifierSemantics(unittest.TestCase):
    def test_constructor_preserves_unvalidated_prerelease_and_build(self):
        version = Version('1', '2', '3', '01..١٢', 42)
        self.assertEqual(version.to_tuple(), (1, 2, 3, '01..١٢', '42'))
        self.assertEqual(Version(0, prerelease='').prerelease, '')
        self.assertIsNone(Version(0).prerelease)

    def test_constructor_prerelease_comparison_matrix(self):
        cases = (
            ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1),
            ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1),
            ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0),
            ('１２', '13', -1), ('1٢', '12', 0), ('٠٠١', '1', 0),
        )
        for a, b, expected in cases:
            with self.subTest(left=a, right=b):
                left = Version(0, 0, 0, prerelease=a)
                right = Version(0, 0, 0, prerelease=b)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, a)
                self.assertEqual(right.prerelease, b)

    def test_nat_cmp_retains_empty_identifiers(self):
        self.assertEqual(Version._nat_cmp('', None), 0)
        self.assertEqual(Version._nat_cmp('a', 'a.'), -1)
        self.assertEqual(Version._nat_cmp('a..b', 'a..c'), -1)
        self.assertEqual(Version._nat_cmp('', '0'), 1)

    def test_empty_and_none_prereleases_have_release_precedence(self):
        empty = Version(0, 0, 0, '')
        absent = Version(0, 0, 0)
        prerelease = Version.parse('0.0.0-alpha')
        self.assertEqual(empty.compare(absent), 0)
        self.assertEqual(absent.compare(empty), 0)
        self.assertEqual(empty.compare(prerelease), 1)
        self.assertEqual(absent.compare(prerelease), 1)
        self.assertEqual(prerelease.compare(empty), -1)
        self.assertEqual(prerelease.compare(absent), -1)

    def test_parser_rejects_leading_zeros_and_unicode_digits(self):
        for tag in ('01', '01.2', '١٢', '１２'):
            value = '0.0.0-' + tag
            with self.subTest(tag=tag):
                with self.assertRaises(ValueError):
                    Version.parse(value)
                self.assertFalse(Version.is_valid(value))

    def test_unicode_conversion_is_eager_after_decisive_pair_or_in_suffix(self):
        pairs = (('²', '2'), ('a.²', 'b.0'), ('a.0', 'b.²'), ('a', 'a.²'))
        for a, b in pairs:
            with self.subTest(left=a, right=b):
                with self.assertRaises(ValueError):
                    Version(0, 0, 0, a).compare(Version(0, 0, 0, b))
                with self.assertRaises(ValueError):
                    Version(0, 0, 0, b).compare(Version(0, 0, 0, a))

    def test_unicode_conversion_is_eager_against_release(self):
        malformed = Version(0, 0, 0, '²')
        release = Version(0, 0, 0)
        with self.assertRaises(ValueError):
            malformed.compare(release)
        with self.assertRaises(ValueError):
            release.compare(malformed)

    def test_unicode_integer_limit_failure_remains_eager(self):
        if not hasattr(sys, 'set_int_max_str_digits'):
            self.skipTest('interpreter has no integer-string conversion limit')
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            with self.assertRaises(ValueError):
                Version._nat_cmp('a', 'b.' + '١' * 5000)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_core_precedence_bypasses_bad_prerelease(self):
        for lower, higher in (((0, 0, 0), (1, 0, 0)),
                              ((1, 0, 0), (1, 1, 0)),
                              ((1, 1, 0), (1, 1, 1))):
            with self.subTest(lower=lower, higher=higher):
                left = Version(*lower, prerelease='²')
                right = Version(*higher, prerelease='²')
                self.assertEqual(left.compare(right), -1)
                self.assertEqual(right.compare(left), 1)
                self.assertLess(left, right)

    def test_operator_propagates_unicode_conversion_error(self):
        bad = Version(0, 0, 0, '²')
        other = Version(0, 0, 0, '2')
        with self.assertRaises(ValueError):
            bad == other
        with self.assertRaises(ValueError):
            bad < other
        with self.assertRaises(ValueError):
            other > bad


class TestCompatibility(unittest.TestCase):
    def test_public_aliases_and_subclass_parse(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)

        class Derived(Version):
            pass

        parsed = Derived.parse('1.2.3-rc.1')
        self.assertIsInstance(parsed, Derived)
        self.assertEqual(parsed.compare(Derived(1, 2, 3, 'rc.2')), -1)
        with self.assertRaises(TypeError):
            parsed.compare(Version(1, 2, 3, 'rc.2'))

        previous = None
        if hasattr(sys, 'set_int_max_str_digits'):
            previous = sys.get_int_max_str_digits()
            sys.set_int_max_str_digits(4300)
        try:
            long_parsed = Derived.parse('1.2.3-rc.' + LONG_ONES)
            self.assertIsInstance(long_parsed, Derived)
            smaller = Derived(1, 2, 3, 'rc.2')
            self.assertEqual(long_parsed.compare(smaller), 1)
            self.assertEqual(smaller.compare(long_parsed), -1)
        finally:
            if previous is not None:
                sys.set_int_max_str_digits(previous)

    def test_compare_accepts_supported_operand_forms(self):
        value = Version(1, 2, 3, 'rc.1', 'local')
        operands = (
            Version(1, 2, 3, 'rc.1'),
            '1.2.3-rc.1',
            b'1.2.3-rc.1',
            {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': 'rc.1'},
            (1, 2, 3, 'rc.1'),
            [1, 2, 3, 'rc.1'],
        )
        for operand in operands:
            with self.subTest(type=type(operand).__name__):
                self.assertEqual(value.compare(operand), 0)
                self.assertEqual(value.to_tuple(), (1, 2, 3, 'rc.1', 'local'))

    def test_invalid_compare_and_operator_operands(self):
        value = Version(1)
        with self.assertRaises(TypeError):
            value.compare(object())
        with self.assertRaises(ValueError):
            value.compare('invalid')
        with self.assertRaises(TypeError):
            value.compare({})
        self.assertIs(value.__eq__(object()), NotImplemented)
        self.assertIs(value.__lt__({}), NotImplemented)
        self.assertIs(value.__eq__(['invalid']), NotImplemented)
        with self.assertRaises(TypeError):
            value < object()

    def test_parse_bytes_optional_parts_and_input_errors(self):
        self.assertEqual(Version.parse(b'1.2.3-rc.1').to_tuple(),
                         (1, 2, 3, 'rc.1', None))
        self.assertEqual(Version.parse('1.2', optional_minor_and_patch=True).to_tuple(),
                         (1, 2, 0, None, None))
        with self.assertRaises(ValueError):
            Version.parse('1.2')
        with self.assertRaises(TypeError):
            Version.parse(123)
        with self.assertRaises(UnicodeDecodeError):
            Version.parse(b'\xff')
        with self.assertRaises(TypeError):
            Version.is_valid(123)

    def test_constructor_core_conversion_and_negative_error(self):
        self.assertEqual(Version('2', '3', '4').to_tuple(), (2, 3, 4, None, None))
        with self.assertRaises(ValueError):
            Version(-1)
        with self.assertRaises(ValueError):
            Version('not an integer')
        with self.assertRaises(TypeError):
            Version(object())

    def test_replace_preserves_original_and_rejects_unknown_part(self):
        original = Version(1, 2, 3, 'rc.1', 'old')
        updated = original.replace(build='new')
        self.assertEqual(updated.to_tuple(), (1, 2, 3, 'rc.1', 'new'))
        self.assertEqual(original.to_tuple(), (1, 2, 3, 'rc.1', 'old'))
        self.assertEqual(original.compare(updated), 0)
        with self.assertRaises(TypeError):
            original.replace(unknown=1)
        with self.assertRaises(ValueError):
            original.replace(major=-1)

    def test_all_comparison_operators_follow_compare(self):
        low = Version.parse('1.0.0-alpha')
        equal = Version.parse('1.0.0-alpha+build')
        high = Version.parse('1.0.0')
        self.assertTrue(low == equal)
        self.assertFalse(low != equal)
        self.assertTrue(low < high)
        self.assertTrue(low <= equal)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
