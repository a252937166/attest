import itertools
import math
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_from_module


class BreakerTests(unittest.TestCase):
    def test_every_descending_unit_subsequence(self):
        units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001)]
        for length in range(1, 6):
            for subset in itertools.combinations(units, length):
                text = ''.join(f'{index + 2}{unit}' for index, (unit, _) in enumerate(subset))
                expected = sum((index + 2) * multiplier for index, (_, multiplier) in enumerate(subset))
                with self.subTest(text=text):
                    result = parse_duration(text)
                    self.assertIs(type(result), float)
                    self.assertTrue(math.isclose(result, expected, rel_tol=0, abs_tol=1e-9))

    def test_all_standard_whitespace_between_components(self):
        for separator in (' ', '\t', '\n', '\r', '\v', '\f', '\u2003'):
            text = separator + '2d' + separator + '3ms' + separator
            with self.subTest(separator=repr(separator)):
                self.assertAlmostEqual(parse_duration(text), 172800.003)

    def test_adjacent_m_s_and_ms_have_distinct_meanings(self):
        cases = {'1m2s': 62.0, '1m2ms': 60.002, '1s2ms': 1.002,
                 '12ms': 0.012, '1m0s2ms': 60.002, '0m0s1ms': 0.001}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_every_pairwise_unit_inversion_is_invalid(self):
        units = ('d', 'h', 'm', 's', 'ms')
        for earlier, later in itertools.combinations(units, 2):
            text = f'0{later} 1{earlier}'
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeats_remain_invalid_with_other_units_between(self):
        for text in ('1d0h2d', '1h0m2h', '1m0s2m', '1s0ms2s', '0ms 0ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_whitespace_cannot_split_a_component(self):
        for gap in (' ', '\t', '\n', '\r', '\v', '\f', '\u2003'):
            for text in ('12' + gap + 'ms', '1' + gap + '2h'):
                with self.subTest(text=repr(text)):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_plain_seconds_cannot_join_components(self):
        for text in ('12 3ms', '12ms 3', '1d 2', '1 2d', '1s\n002'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_entire_input_must_match(self):
        for text in ('1d2h?', '(1h)', '1h/2m', '1d2hh', '1h2m3', '2msx'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_nondecimal_numeric_characters_are_rejected_in_components(self):
        for character in ('\u2167', '\u00be', '\u2469', '\u2075'):
            for text in (character + 'h', '1h' + character + 'ms'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_leading_zeros_and_large_finite_values(self):
        self.assertEqual(parse_duration('0' * 200 + '42'), 42.0)
        self.assertEqual(parse_duration('000123456789d000987654321h'),
                         float(123456789 * 86400 + 987654321 * 3600))

    def test_both_public_imports_agree_on_millisecond_inputs(self):
        for text in ('1ms', '999ms', '1s001ms', '1h0m0s1001ms'):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), parse_from_module(text))

    def test_additional_nonstring_inputs_raise_type_error(self):
        for value in ({}, (), 1 + 2j, bytearray(b'1s'), memoryview(b'1s')):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(TypeError):
                    parse_duration(value)
