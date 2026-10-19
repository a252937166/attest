import itertools
import unittest

from durationkit import parse_duration


class TestBreakerDurationParsing(unittest.TestCase):
    def test_every_descending_unit_subsequence(self):
        units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001)]
        for length in range(1, 6):
            for selected in itertools.combinations(units, length):
                text = ''.join('2' + unit for unit, _ in selected)
                with self.subTest(text=text):
                    result = parse_duration(text)
                    self.assertIsInstance(result, float)
                    self.assertAlmostEqual(result, sum(2 * multiplier for _, multiplier in selected), places=8)

    def test_every_reversed_unit_pair_is_rejected(self):
        units = ['d', 'h', 'm', 's', 'ms']
        for later in range(1, len(units)):
            for earlier in range(later):
                text = '7' + units[later] + '3' + units[earlier]
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_zero_values_do_not_reset_order_or_uniqueness(self):
        for text in ('0ms0d', '4h0d', '0m0m', '2d0s3m', '0d1h0h', '0s 0ms 0ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_millisecond_unit_is_indivisible(self):
        self.assertAlmostEqual(parse_duration('2m3s4ms'), 123.004)
        self.assertAlmostEqual(parse_duration('2m 3ms'), 120.003)
        for text in ('2ms3s', '2ms3m', '2mss', '2m3sm', '2m3mss'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_python_unicode_whitespace_at_component_boundaries(self):
        for separator in ('\x1c', '\u2007', '\u2028', '\u202f', '\u3000'):
            self.assertTrue(separator.isspace())
            text = separator + '1d' + separator + '2h' + separator + '3ms' + separator
            with self.subTest(separator=repr(separator)):
                self.assertAlmostEqual(parse_duration(text), 93600.003)

    def test_whitespace_cannot_split_any_component(self):
        for unit in ('d', 'h', 'm', 's', 'ms'):
            for text in ('12 3' + unit, '12\u2003' + unit, '12' + unit + ' 3 4ms'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_malformed_numeric_syntax_in_later_components(self):
        for text in ('1d+2h', '1d-2h', '1h2.5m', '1h2e3m', '1h2_000m', '1h0x10m'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_no_unmatched_prefix_middle_or_suffix(self):
        for text in ('x1h', '1h?2m', '1h2m?', '1h2', '1h2m3', '12 34', '1h ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_long_leading_zero_runs_keep_plain_seconds_behavior(self):
        for text, expected in (('0' * 200 + '17', 17.0), ('0' * 200, 0.0)):
            with self.subTest(length=len(text)):
                result = parse_duration(text)
                self.assertIsInstance(result, float)
                self.assertEqual(result, expected)

    def test_equivalent_component_expressions_with_seconds_and_milliseconds(self):
        pairs = (('2m1500ms', '121s500ms'), ('1h120s', '62m'), ('3d48h', '5d'))
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertAlmostEqual(parse_duration(left), parse_duration(right), places=8)

    def test_other_nondecimal_numeric_characters_are_rejected(self):
        for character in ('²', 'Ⅷ', '⑨'):
            for text in (character, character + 'h', '1m' + character + 's'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)
