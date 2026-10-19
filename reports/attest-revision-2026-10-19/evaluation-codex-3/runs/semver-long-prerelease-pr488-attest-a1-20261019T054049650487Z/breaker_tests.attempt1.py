import unittest

from semver import Version


class BreakerTests(unittest.TestCase):
    def test_long_numeric_equalities_with_different_spelling(self):
        pairs = [
            ('0' * 9000, '0'),
            ('0' * 8999 + '7', '7'),
            ('0' * 4500 + '12', '12'),
        ]
        for left, right in pairs:
            with self.subTest(left_length=len(left)):
                a = Version(3, 2, 1, prerelease=left)
                b = Version(3, 2, 1, prerelease=right)
                self.assertEqual(a.compare(b), 0)
                self.assertEqual(b.compare(a), 0)
                self.assertEqual(a.prerelease, left)

    def test_long_numeric_lexicographic_boundary_after_zero_prefix(self):
        prefix = '0' * 4500 + '7' * 100
        low = Version(0, 0, 0, prerelease=prefix + '8')
        high = Version(0, 0, 0, prerelease=prefix + '9')
        self.assertEqual(low.compare(high), -1)
        self.assertEqual(high.compare(low), 1)
        self.assertEqual(Version._nat_cmp('0' * 4500 + '99', '100'), -1)

    def test_unicode_decimal_identifiers_match_ascii_after_normalization(self):
        for unicode_value, ascii_value in [
            ('\u0660\u0660\u0667', '7'),
            ('1\u0662\u0663', '123'),
            ('\uff10\uff10\uff19', '9'),
        ]:
            with self.subTest(unicode_value=unicode_value):
                self.assertEqual(Version._nat_cmp(unicode_value, ascii_value), 0)
                self.assertEqual(
                    Version(0, 0, 0, prerelease=unicode_value).compare(
                        Version(0, 0, 0, prerelease=ascii_value)
                    ),
                    0,
                )

    def test_invalid_unicode_digit_is_eager_in_distant_suffix(self):
        for left, right in [
            ('a.0.0.\u00b2', 'z'),
            ('z', 'a.0.0.\u00b2'),
            ('a', 'a.0.0.\u00b2'),
            ('a.0.0.\u00b2', 'a'),
        ]:
            with self.subTest(left=left, right=right):
                with self.assertRaises(ValueError):
                    Version._nat_cmp(left, right)

    def test_release_comparison_validates_invalid_suffix(self):
        malformed = Version(1, 2, 3, prerelease='alpha.\u00b2')
        for absent in (None, ''):
            release = Version(1, 2, 3, prerelease=absent)
            with self.subTest(absent=absent):
                with self.assertRaises(ValueError):
                    malformed.compare(release)
                with self.assertRaises(ValueError):
                    release.compare(malformed)

    def test_core_precedence_skips_invalid_suffix_in_both_operands(self):
        low = Version(1, 2, 3, prerelease='alpha.\u00b2')
        for high in (
            Version(2, 0, 0, prerelease='beta.\u00b2'),
            Version(1, 3, 0, prerelease='beta.\u00b2'),
            Version(1, 2, 4, prerelease='beta.\u00b2'),
        ):
            with self.subTest(high=(high.major, high.minor, high.patch)):
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)

    def test_numeric_and_text_identifiers_in_nested_lists(self):
        cases = [
            ('alpha.0002', 'alpha.10', -1),
            ('alpha.0002', 'alpha.2', 0),
            ('alpha.2', 'alpha.2.beta', -1),
            ('alpha.2a', 'alpha.2', 1),
            ('alpha..2', 'alpha..10', -1),
            ('alpha.2', 'alpha.', -1),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_long_prerelease_through_supported_operand_coercions(self):
        digits = '4' * 5000
        value = Version(1, 2, 3, prerelease=digits)
        for operand in (
            '1.2.3-' + digits,
            ('1', '2', '3', digits),
            ['1', '2', '3', digits],
            {'major': '1', 'minor': '2', 'patch': '3', 'prerelease': digits},
        ):
            with self.subTest(operand_type=type(operand).__name__):
                self.assertEqual(value.compare(operand), 0)

    def test_parsed_long_numeric_identifier_preserves_text_with_build(self):
        digits = '9' * 5000
        text = '1.2.3-' + digits + '+build.7'
        value = Version.parse(text)
        self.assertEqual(value.prerelease, digits)
        self.assertEqual(str(value), text)
        self.assertEqual(value.compare(Version(1, 2, 3, prerelease=digits, build='other')), 0)
        self.assertTrue(Version.is_valid(text))
