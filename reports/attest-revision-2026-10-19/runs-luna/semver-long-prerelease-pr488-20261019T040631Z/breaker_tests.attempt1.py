import unittest

from semver import Version


class TestBreaker(unittest.TestCase):
    def test_zero_padding_across_multiple_identifiers(self):
        left = Version(2, 3, 4, prerelease='0' * 5000 + '7.000.00012')
        right = Version(2, 3, 4, prerelease='7.0.12')
        self.assertEqual(left.compare(right), 0)
        self.assertEqual(right.compare(left), 0)
        self.assertEqual(left.prerelease, '0' * 5000 + '7.000.00012')

    def test_large_numeric_length_takes_priority_over_lexical_order(self):
        shorter = Version(0, 0, 0, prerelease='9' * 4500)
        longer = Version(0, 0, 0, prerelease='1' + '0' * 4500)
        self.assertEqual(shorter.compare(longer), -1)
        self.assertEqual(longer.compare(shorter), 1)

    def test_dot_components_after_long_equal_numeric_identifier(self):
        prefix = '7' * 4500
        left = Version.parse('1.2.3-' + prefix + '.alpha.9')
        right = Version.parse('1.2.3-' + prefix + '.alpha.10')
        self.assertEqual(left.compare(right), -1)
        self.assertEqual(right.compare(left), 1)
        self.assertEqual(left.prerelease, prefix + '.alpha.9')

    def test_numeric_identifier_count_after_normalization(self):
        self.assertEqual(Version._nat_cmp('0001', '1.0'), -1)
        self.assertEqual(Version._nat_cmp('1.000', '0001'), 1)
        self.assertEqual(Version._nat_cmp('a.', 'a..'), -1)

    def test_non_digit_unicode_numeral_is_text(self):
        numeral = '\u216b'
        self.assertFalse(numeral.isdigit())
        self.assertEqual(Version._nat_cmp('1', numeral), -1)
        self.assertEqual(Version._nat_cmp(numeral, '1'), 1)

    def test_invalid_legacy_digit_after_early_difference(self):
        for left, right in (('0.\u2082', '1'), ('1', '0.\u2082'), ('a.\u00b3', 'z'), ('z', 'a.\u00b3')):
            with self.subTest(left=left, right=right):
                with self.assertRaises(ValueError):
                    Version._nat_cmp(left, right)

    def test_invalid_legacy_digit_with_empty_absent_prerelease(self):
        bad = Version(1, 0, 0, prerelease='\u2082')
        empty = Version(1, 0, 0, prerelease='')
        with self.assertRaises(ValueError):
            bad.compare(empty)
        with self.assertRaises(ValueError):
            empty.compare(bad)

    def test_core_precedence_skips_conversion_for_collection_operand(self):
        bad = Version(1, 2, 3, prerelease='\u00b3')
        self.assertEqual(bad.compare({'major': 1, 'minor': 2, 'patch': 4, 'prerelease': '\u2082'}), -1)
        self.assertEqual(bad.compare((1, 2, 2, '\u2082')), 1)

    def test_all_rich_operators_for_normalized_numeric_equality(self):
        left = Version(0, 0, 0, prerelease='0' * 5000 + '42', build='first')
        right = Version(0, 0, 0, prerelease='42', build='second')
        self.assertTrue(left == right)
        self.assertFalse(left != right)
        self.assertFalse(left < right)
        self.assertTrue(left <= right)
        self.assertFalse(left > right)
        self.assertTrue(left >= right)
