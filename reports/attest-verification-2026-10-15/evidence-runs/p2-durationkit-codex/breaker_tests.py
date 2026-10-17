import math
import unittest

from durationkit import parse_duration


class TestDurationBreaker(unittest.TestCase):
    def test_very_long_zero_component_is_valid(self):
        self.assertEqual(parse_duration('0' * 5000 + 'h1s'), 1.0)

    def test_every_ordered_subset_of_units(self):
        units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001)]
        for mask in range(1, 1 << len(units)):
            selected = [item for index, item in enumerate(units) if mask & (1 << index)]
            value = '  '.join('2' + unit for unit, _ in selected)
            expected = sum(2 * seconds for _, seconds in selected)
            with self.subTest(value=value):
                actual = parse_duration(value)
                self.assertIs(type(actual), float)
                self.assertTrue(math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9))

    def test_every_reversed_unit_pair_is_rejected(self):
        units = ['d', 'h', 'm', 's', 'ms']
        for higher_index in range(len(units)):
            for lower_index in range(higher_index + 1, len(units)):
                value = '1' + units[lower_index] + '2' + units[higher_index]
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        parse_duration(value)

    def test_unicode_whitespace_between_components(self):
        for separator in ('\u2003', '\u2028', '\x85', '\u3000'):
            self.assertTrue(separator.isspace())
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse_duration(separator + '1h' + separator + '2m' + separator), 3720.0)

    def test_mixed_unicode_decimal_scripts(self):
        self.assertEqual(parse_duration('\u0968\u0663\uff14'), 234.0)
        self.assertEqual(parse_duration('\u0968h\u0663\uff14m\U0001d7d9s'), 9241.0)

    def test_nondecimal_numeric_characters_are_rejected(self):
        for value in ('\u2163s', '\u2460ms', '1h\u00b2m', '\u00b9', '1\u2153s'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_format_controls_are_not_whitespace(self):
        for control in ('\u200b', '\ufeff', '\u2060'):
            self.assertFalse(control.isspace())
            for value in (control + '1s', '1h' + control + '2m', '1s' + control):
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        parse_duration(value)

    def test_whitespace_never_splits_a_number_from_its_unit(self):
        for value in ('12\tms', '1h 2\nm', '1d\u20033h 4\ts'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_bare_number_after_complete_component_is_rejected(self):
        for value in ('1ms 0', '1d2h 3', '1s\n000'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)

    def test_unit_prefixes_and_trailing_text_are_rejected(self):
        for value in ('1msec', '1milliseconds', '1sms', '2d3hours', '4s5msec'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_duration(value)
