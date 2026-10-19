import unittest

import semver
from semver import Version


class BreakerTests(unittest.TestCase):
    def test_long_leading_zeros_normalize_without_changing_storage(self):
        prerelease = '0' * 5000 + '7.alpha'
        left = Version(0, 0, 0, prerelease=prerelease)
        right = Version(0, 0, 0, prerelease='7.alpha')
        self.assertEqual(left.compare(right), 0)
        self.assertEqual(right.compare(left), 0)
        self.assertEqual(left.prerelease, prerelease)
        self.assertEqual(Version._nat_cmp(prerelease, '7.alpha'), 0)

    def test_long_numeric_tie_continues_to_following_identifier(self):
        prefix = '8' * 5000
        lower = Version(0, 0, 0, prerelease=prefix + '.4')
        higher = Version(0, 0, 0, prerelease=prefix + '.5')
        self.assertEqual(lower.compare(higher), -1)
        self.assertEqual(higher.compare(lower), 1)
        self.assertEqual(Version._nat_cmp(prefix + '.4', prefix), 1)

    def test_mixed_unicode_decimal_identifier_after_long_ascii_part(self):
        prefix = '3' * 5000
        left = Version(0, 0, 0, prerelease=prefix + '.0\u0661\u0662')
        right = Version(0, 0, 0, prerelease=prefix + '.12')
        self.assertEqual(left.compare(right), 0)
        self.assertEqual(right.compare(left), 0)
        self.assertEqual(left.prerelease, prefix + '.0\u0661\u0662')

    def test_invalid_unicode_digit_after_long_numeric_difference_is_eager(self):
        left = Version(0, 0, 0, prerelease='9' * 5000 + '.ok')
        right = Version(0, 0, 0, prerelease='1.bad.\u00b2')
        with self.assertRaises(ValueError):
            left.compare(right)
        with self.assertRaises(ValueError):
            right.compare(left)

    def test_invalid_unicode_digit_after_empty_identifier_is_eager(self):
        left = Version(0, 0, 0, prerelease='a..\u00b2')
        right = Version(0, 0, 0, prerelease='a.0')
        with self.assertRaises(ValueError):
            left.compare(right)
        with self.assertRaises(ValueError):
            right.compare(left)

    def test_core_precedence_skips_conversion_after_tuple_coercion(self):
        left = Version(0, 1, 9, prerelease='\u00b2')
        self.assertEqual(left.compare((0, 2, 0, '\u00b2')), -1)
        self.assertEqual(Version(0, 2, 0, prerelease='\u00b2').compare(left), 1)

    def test_empty_identifier_positions_and_counts(self):
        self.assertEqual(Version._nat_cmp('.a', '0.a'), 1)
        self.assertEqual(Version._nat_cmp('a..', 'a.'), 1)
        self.assertEqual(Version._nat_cmp('1..a', '1.b'), -1)

    def test_strict_parse_rejects_leading_zero_after_long_identifier(self):
        prefix = '4' * 5000
        valid = '0.0.0-' + prefix + '.1'
        invalid = '0.0.0-' + prefix + '.01'
        self.assertEqual(Version.parse(valid).prerelease, prefix + '.1')
        self.assertTrue(Version.is_valid(valid))
        with self.assertRaises(ValueError):
            Version.parse(invalid)
        self.assertFalse(Version.is_valid(invalid))

    def test_long_prerelease_round_trip_preserves_build_independence(self):
        text = '2.3.4-' + '6' * 5000 + '.beta+build.7'
        parsed = Version.parse(text)
        reparsed = Version.parse(str(parsed))
        self.assertEqual(str(parsed), text)
        self.assertEqual(parsed.compare(reparsed), 0)
        self.assertEqual(parsed.compare(reparsed.replace(build='different')), 0)

    def test_module_compare_uses_last_digit_of_long_identifier(self):
        lower = '0.0.0-' + '7' * 4999 + '3'
        higher = '0.0.0-' + '7' * 4999 + '4'
        self.assertEqual(semver.compare(lower, higher), -1)
        self.assertEqual(semver.compare(higher, lower), 1)
