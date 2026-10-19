import math
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_from_module


class TestBreaker(unittest.TestCase):
    def test_large_millisecond_value_with_finite_seconds(self):
        result = parse_duration('1' + '0' * 309 + 'ms')
        self.assertIs(type(result), float)
        self.assertTrue(math.isfinite(result))
        self.assertTrue(math.isclose(result, 1e306, rel_tol=1e-12))

    def test_large_millisecond_value_in_combination(self):
        result = parse_duration('2s ' + '1' + '0' * 309 + 'ms')
        self.assertIs(type(result), float)
        self.assertTrue(math.isclose(result, 1e306, rel_tol=1e-12))

    def test_module_import_matches_public_import(self):
        for text in ('000', '07d003h', '12m34s005ms'):
            with self.subTest(text=text):
                self.assertEqual(parse_from_module(text), parse_duration(text))

    def test_all_ordered_unit_pairs(self):
        units = ('d', 'h', 'm', 's', 'ms')
        multipliers = (86400, 3600, 60, 1, 0.001)
        for first in range(len(units)):
            for second in range(first + 1, len(units)):
                text = '2' + units[first] + '3' + units[second]
                expected = 2 * multipliers[first] + 3 * multipliers[second]
                with self.subTest(text=text):
                    self.assertAlmostEqual(parse_duration(text), expected)

    def test_all_reversed_unit_pairs(self):
        units = ('d', 'h', 'm', 's', 'ms')
        for first in range(len(units)):
            for second in range(first):
                text = '0' + units[first] + '0' + units[second]
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_repeats_with_intervening_units(self):
        for text in ('1d2h3d', '1h2m3h', '1m2s3m', '1s2ms3s'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_varied_python_whitespace_between_components(self):
        for separator in ('\v', '\f', '\u00a0', '\u2003', '\u2028'):
            self.assertTrue(separator.isspace())
            text = separator + '2d' + separator + '3ms' + separator
            with self.subTest(separator=repr(separator)):
                self.assertAlmostEqual(parse_duration(text), 172800.003)

    def test_whitespace_cannot_split_any_component(self):
        for separator in ('\v', '\f', '\u00a0', '\u2003'):
            for text in ('12' + separator + '3s', '123' + separator + 'ms'):
                with self.subTest(text=repr(text)):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_malformed_millisecond_boundaries(self):
        for text in ('1m s', '1ms2m', '1mss', '1m2', '1s2m s', '1ms0ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_decimal_numeric_characters_inside_numbers(self):
        for character in ('²', 'Ⅳ', '½', '①'):
            for text in ('12' + character + '3', '12' + character + '3s'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)
