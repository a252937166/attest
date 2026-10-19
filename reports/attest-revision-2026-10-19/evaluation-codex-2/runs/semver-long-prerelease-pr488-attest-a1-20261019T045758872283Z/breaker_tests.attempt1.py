import sys
import unittest

from semver import Version


class TestBreaker(unittest.TestCase):
    def test_ascii_limit_boundary_and_restoration(self):
        if not hasattr(sys, 'set_int_max_str_digits'):
            self.skipTest('integer string limit unavailable')
        original = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            a = Version(0, prerelease='9' * 641)
            b = Version(0, prerelease='1' + '0' * 641)
            self.assertEqual(a.compare(b), -1)
            self.assertEqual(b.compare(a), 1)
            self.assertEqual(Version._nat_cmp('0' * 7000 + '7', '7'), 0)
            self.assertEqual(sys.get_int_max_str_digits(), 640)
        finally:
            sys.set_int_max_str_digits(original)

    def test_mixed_unicode_digits_and_leading_zeros(self):
        pairs = [
            ('٠٠1', '1', 0),
            ('０٠2', '3', -1),
            ('٠9', '10', -1),
            ('0009', '٠٠9', 0),
        ]
        for left, right, expected in pairs:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_normalized_identifiers_before_and_after_empty_parts(self):
        self.assertEqual(Version._nat_cmp('a.0001..2', 'a.1..10'), -1)
        self.assertEqual(Version._nat_cmp('a.01.', 'a.1'), 1)
        self.assertEqual(Version._nat_cmp('a..001', 'a..1'), 0)
        self.assertEqual(Version._nat_cmp('a..1', 'a.1'), 1)

    def test_bad_unicode_suffix_is_eager_after_long_decisive_number(self):
        bad = '9' * 5000 + '.²'
        with self.assertRaises(ValueError):
            Version._nat_cmp(bad, '1')
        with self.assertRaises(ValueError):
            Version._nat_cmp('1', bad)
        with self.assertRaises(ValueError):
            Version(0, prerelease=bad).compare(Version(0, prerelease='1'))

    def test_empty_prerelease_still_eagerly_checks_other_operand(self):
        release = Version(0, prerelease='')
        invalid = Version(0, prerelease='²')
        with self.assertRaises(ValueError):
            release.compare(invalid)
        with self.assertRaises(ValueError):
            invalid.compare(release)
        with self.assertRaises(ValueError):
            _ = release > invalid

    def test_long_numeric_prerelease_with_supported_operand_forms(self):
        left = Version(1, 2, 3, prerelease='0' * 5000 + '2', build='left')
        equivalents = [
            Version(1, 2, 3, prerelease='2', build='right'),
            '1.2.3-2',
            b'1.2.3-2',
            {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': '2'},
            (1, 2, 3, '2'),
            [1, 2, 3, '2'],
        ]
        for other in equivalents:
            with self.subTest(type=type(other).__name__):
                self.assertEqual(left.compare(other), 0)
        self.assertEqual(left.prerelease, '0' * 5000 + '2')
        self.assertEqual(left.build, 'left')

    def test_numeric_equivalence_preserves_order_across_suffixes(self):
        versions = [
            Version(0, prerelease='0002.a'),
            Version(0, prerelease='2.a.0'),
            Version(0, prerelease='2.b'),
            Version(0, prerelease='10'),
            Version(0),
        ]
        for lower, higher in zip(versions, versions[1:]):
            self.assertEqual(lower.compare(higher), -1)
            self.assertEqual(higher.compare(lower), 1)
        self.assertEqual(sorted(reversed(versions)), versions)
        self.assertEqual(versions[0], versions[0].replace(build='metadata'))

    def test_parser_restrictions_with_long_compound_identifiers(self):
        digits = '7' * 7000
        valid = '1.2.3-' + digits + '.alpha'
        self.assertTrue(Version.is_valid(valid))
        self.assertEqual(Version.parse(valid).compare(valid.encode('utf-8')), 0)
        for prerelease in (digits + '.01', '01.' + digits, digits + '.١', digits + '.²'):
            value = '1.2.3-' + prerelease
            with self.subTest(prerelease=prerelease[-10:]):
                self.assertFalse(Version.is_valid(value))
                with self.assertRaises(ValueError):
                    Version.parse(value)
