import unittest

import semver
from semver import Version


class TestBreaker(unittest.TestCase):
    def test_long_leading_zeros_preserve_decimal_value(self):
        pairs = [
            ('0' * 4500 + '37', '37', 0),
            ('0' * 4500 + '37', '36', 1),
            ('0' * 4500 + '37', '38', -1),
            ('0' * 4500, '0' * 4600, 0),
        ]
        for left, right, expected in pairs:
            with self.subTest(expected=expected, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)
                self.assertEqual(Version(1, prerelease=left).compare(Version(1, prerelease=right)), expected)

    def test_equal_length_long_values_compare_lexicographically(self):
        prefix = '7' * 4700
        low = Version(0, prerelease=prefix + '4')
        high = Version(0, prerelease=prefix + '5')
        self.assertEqual(low.compare(high), -1)
        self.assertEqual(high.compare(low), 1)
        self.assertTrue(low < high)
        self.assertFalse(low >= high)

    def test_numeric_parts_after_long_equal_prefix(self):
        prefix = '0' * 4500 + '12'
        left = Version(2, prerelease=prefix + '.8')
        right = Version(2, prerelease='12.10')
        self.assertEqual(left.compare(right), -1)
        self.assertEqual(right.compare(left), 1)
        self.assertEqual(left.prerelease, prefix + '.8')

    def test_mixed_unicode_decimal_digits_keep_integer_values(self):
        cases = [
            ('٠٠١٢', '12', 0),
            ('０２', '3', -1),
            ('1٢', '11', 1),
            ('१२', '13', -1),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)
                self.assertEqual(Version(0, prerelease=left).compare(Version(0, prerelease=right)), expected)

    def test_numeric_identifiers_precede_text_with_empty_parts(self):
        cases = [
            ('a..0', 'a..x', -1),
            ('a.00', 'a.', -1),
            ('a.9', 'a.9.', -1),
            ('.1', '.alpha', -1),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_unconvertible_unicode_digit_in_distant_identifier_is_eager(self):
        pairs = [
            ('a.1.2.²', 'z'),
            ('a', 'a.1.2.²'),
            ('a.1.2.²', None),
            ('x.²', 'x.²'),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                with self.assertRaises(ValueError):
                    Version._nat_cmp(left, right)
                with self.assertRaises(ValueError):
                    Version._nat_cmp(right, left)
                with self.assertRaises(ValueError):
                    Version(0, prerelease=left).compare(Version(0, prerelease=right))

    def test_unequal_core_skips_unconvertible_prerelease(self):
        invalid = Version(4, 5, 6, prerelease='a.²')
        earlier = Version(4, 5, 5, prerelease='b')
        later = Version(4, 5, 7, prerelease='b')
        self.assertEqual(invalid.compare(earlier), 1)
        self.assertEqual(invalid.compare(later), -1)
        self.assertTrue(earlier < invalid < later)

    def test_long_numeric_comparison_through_supported_operands(self):
        digits = '8' * 4500
        version = Version(3, 2, 1, prerelease=digits, build='first')
        self.assertEqual(version.compare({'major': 3, 'minor': 2, 'patch': 1, 'prerelease': digits, 'build': 'second'}), 0)
        self.assertEqual(version.compare((3, 2, 1, digits, 'third')), 0)
        self.assertEqual(version.compare([3, 2, 1, digits, 'fourth']), 0)
        self.assertEqual(version.compare(('3.2.1-' + digits).encode('ascii')), 0)

    def test_unsupported_operator_fallback(self):
        version = Version(1)
        operand = object()
        self.assertFalse(version == operand)
        self.assertTrue(version != operand)
        with self.assertRaises(TypeError):
            version < operand
        with self.assertRaises(TypeError):
            version.compare(operand)

    def test_parsed_long_prerelease_and_build_metadata(self):
        digits = '6' * 4500
        plain = Version.parse('1.2.3-' + digits)
        built = Version.parse('1.2.3-' + digits + '+build.7')
        self.assertEqual(plain.prerelease, digits)
        self.assertEqual(plain.compare(built), 0)
        self.assertEqual(semver.compare('1.2.3-' + digits, '1.2.3-' + digits + '+build.7'), 0)
