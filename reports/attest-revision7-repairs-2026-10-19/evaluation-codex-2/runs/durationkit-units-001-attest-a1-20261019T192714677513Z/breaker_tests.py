import unittest

from durationkit import parse_duration


class BreakerTests(unittest.TestCase):
    def test_long_leading_zero_component_is_valid(self):
        self.assertEqual(parse_duration('0' * 4301 + '1h'), 3600.0)
        self.assertEqual(parse_duration('0' * 4301 + '1ms'), 0.001)

    def test_long_leading_zero_bare_seconds_is_valid(self):
        self.assertEqual(parse_duration('0' * 4301 + '1'), 1.0)

    def test_every_descending_pair(self):
        units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001)]
        for i, (first, first_value) in enumerate(units):
            for second, second_value in units[i + 1:]:
                with self.subTest(first=first, second=second):
                    result = parse_duration('2' + first + '3' + second)
                    self.assertIs(type(result), float)
                    self.assertAlmostEqual(result, 2 * first_value + 3 * second_value)

    def test_every_reverse_pair_is_rejected(self):
        units = ['d', 'h', 'm', 's', 'ms']
        for i, first in enumerate(units):
            for second in units[i + 1:]:
                with self.subTest(first=first, second=second):
                    with self.assertRaises(ValueError):
                        parse_duration('0' + second + '0' + first)

    def test_ms_is_one_unit_in_long_sequences(self):
        self.assertAlmostEqual(parse_duration('12m34s56ms'), 754.056)
        self.assertAlmostEqual(parse_duration('12m56ms'), 720.056)
        for text in ('1ms2m', '1ms2s', '1m2ms3s', '1s2ms3ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_whitespace_at_component_boundaries(self):
        for separator in ('\v', '\f', '\u2003', '\u2028', '\u001c'):
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse_duration('1h' + separator + '2m'), 3720.0)
                with self.assertRaises(ValueError):
                    parse_duration('1' + separator + 'h2m')

    def test_incomplete_and_embedded_tokens(self):
        for text in ('1d2', '1h2m3', '1m2ms3', '1d 2h x', '1d2h,3m', '1d2hh', '1mss', '1m2MS'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_other_numeric_characters_inside_valid_forms(self):
        for character in ('\u00b2', '\u2469', '\u216b', '\u2153'):
            for text in (character, '1' + character, '1h' + character + '2m', '1' + character + 'ms'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_nonwhitespace_format_characters_are_rejected(self):
        for character in ('\u200b', '\ufeff'):
            for text in (character + '1h', '1h' + character, '1h' + character + '2m'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)
