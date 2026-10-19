import sys
import unittest

import semver
from semver import Version


class BreakerTests(unittest.TestCase):
    def test_ascii_numeric_comparison_under_reduced_integer_limit(self):
        if not hasattr(sys, 'set_int_max_str_digits'):
            self.skipTest('integer string limit is unavailable')
        previous = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            digits = '7' * 900
            low = Version.parse('1.2.3-' + digits)
            high = Version.parse('1.2.3-1' + '0' * 900)
            self.assertTrue(Version.is_valid('1.2.3-' + digits))
            self.assertEqual(low.compare(high), -1)
            self.assertEqual(high.compare(low), 1)
            self.assertEqual(Version(1, 2, 3, '0' * 900 + '7').compare(Version(1, 2, 3, '7')), 0)
        finally:
            sys.set_int_max_str_digits(previous)

    def test_numeric_tie_continues_to_later_identifiers(self):
        padded = '0' * 700 + '42'
        self.assertEqual(Version._nat_cmp(padded + '.z', '42.a'), 1)
        self.assertEqual(Version._nat_cmp('42.a', padded + '.z'), -1)
        self.assertEqual(Version._nat_cmp(padded + '.a.2', '42.a.10'), -1)
        self.assertEqual(Version._nat_cmp(padded + '.a', '42.a.0'), -1)

    def test_unicode_decimal_digits_share_numeric_order(self):
        arabic = chr(0x0660) + chr(0x0667)
        fullwidth = chr(0xFF10) + chr(0xFF17)
        astral = chr(0x1D7D8) + chr(0x1D7DF)
        for identifier in (arabic, fullwidth, astral):
            with self.subTest(identifier=identifier):
                self.assertEqual(Version._nat_cmp(identifier, '0007'), 0)
                self.assertEqual(Version._nat_cmp(identifier + '.2', '7.10'), -1)
                self.assertEqual(Version._nat_cmp('8', identifier), 1)

    def test_invalid_unicode_digit_is_eager_in_unmatched_suffix(self):
        bad = chr(0x00B2)
        cases = [('a', 'a.0.' + bad), ('a.1', 'b.0.' + bad), ('a.0.' + bad, 'b.1')]
        for left, right in cases:
            with self.subTest(left=left, right=right):
                with self.assertRaises(ValueError):
                    Version._nat_cmp(left, right)
                with self.assertRaises(ValueError):
                    Version._nat_cmp(right, left)

    def test_each_core_component_short_circuits_both_bad_prereleases(self):
        bad = chr(0x00B2)
        for lower, higher in (((0, 9, 9), (1, 0, 0)), ((0, 0, 9), (0, 1, 0)), ((0, 0, 0), (0, 0, 1))):
            with self.subTest(lower=lower, higher=higher):
                a = Version(*lower, prerelease=bad)
                b = Version(*higher, prerelease='a.' + bad)
                self.assertEqual(a.compare(b), -1)
                self.assertEqual(b.compare(a), 1)

    def test_empty_components_and_length_after_equal_prefix(self):
        self.assertEqual(Version._nat_cmp('a..9', 'a..10'), -1)
        self.assertEqual(Version._nat_cmp('a.', 'a..'), -1)
        self.assertEqual(Version._nat_cmp('a..', 'a.'), 1)
        self.assertEqual(Version._nat_cmp('a..0', 'a..'), 1)
        self.assertEqual(Version(0, 0, 0, '').compare(Version(0, 0, 0, None)), 0)
        self.assertEqual(Version(0, 0, 0, 'a.').compare(Version(0, 0, 0, 'a')), 1)

    def test_nonnumeric_identifiers_keep_python_string_order(self):
        self.assertEqual(Version._nat_cmp('12x', '2x'), -1)
        self.assertEqual(Version._nat_cmp('x-2', 'x.2'), 1)
        self.assertEqual(Version._nat_cmp('3', '3x'), -1)
        self.assertEqual(Version._nat_cmp('3x', '3'), 1)

    def test_coerced_operands_use_corrected_comparison_and_ignore_build(self):
        left = Version(2, 3, 4, '0' * 700 + '12', 'first')
        self.assertEqual(left.compare({'major': 2, 'minor': 3, 'patch': 4, 'prerelease': '12', 'build': 'second'}), 0)
        self.assertEqual(left.compare((2, 3, 4, '13', 'other')), -1)
        self.assertEqual(left.compare([2, 3, 4, '11']), 1)
        self.assertEqual(left.compare(b'2.3.4-12+third'), 0)
        self.assertEqual((left.prerelease, left.build), ('0' * 700 + '12', 'first'))

    def test_strict_parse_rejects_mixed_unicode_and_long_leading_zero(self):
        invalid = ('0' * 700 + '1', '1' + chr(0x0662), chr(0xFF11) + '2')
        for prerelease in invalid:
            with self.subTest(prerelease=prerelease):
                value = '0.0.0-' + prerelease
                with self.assertRaises(ValueError):
                    Version.parse(value)
                self.assertFalse(Version.is_valid(value))
                self.assertEqual(Version(0, 0, 0, prerelease).prerelease, prerelease)

    def test_is_valid_preserves_non_valueerror_exception(self):
        with self.assertRaises(TypeError):
            Version.is_valid(123)
