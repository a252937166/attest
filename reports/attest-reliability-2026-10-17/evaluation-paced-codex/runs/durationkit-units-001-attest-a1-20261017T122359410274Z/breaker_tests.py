import itertools
import math
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_from_module


class TestBreaker(unittest.TestCase):
    def test_public_imports_agree_on_additional_forms(self):
        for text in ('0000', '0002d', '3h4s5ms', '  7m 8ms  '):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), parse_duration_from_module(text))
                self.assertIs(type(parse_duration(text)), float)

    def test_every_nonempty_ordered_subset_of_units(self):
        units = (('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001))
        for count in range(1, len(units) + 1):
            for subset in itertools.combinations(units, count):
                text = ''.join('2' + unit for unit, _ in subset)
                expected = sum(2 * scale for _, scale in subset)
                with self.subTest(text=text):
                    self.assertTrue(math.isclose(parse_duration(text), expected, rel_tol=0, abs_tol=1e-9))

    def test_all_other_unit_permutations_are_invalid(self):
        units = ('d', 'h', 'm', 's', 'ms')
        for permutation in itertools.permutations(units):
            if permutation == units:
                continue
            text = ''.join('1' + unit for unit in permutation)
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repetition_is_invalid_even_with_zero_and_whitespace(self):
        for unit in ('d', 'h', 'm', 's', 'ms'):
            for separator in ('', ' ', '\n'):
                text = '0' + unit + separator + '00' + unit
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_python_whitespace_between_complete_components(self):
        for separator in ('\r', '\v', '\f', '\u0085', '\u00a0', '\u2003', '\u2028', '\u2029'):
            self.assertTrue(separator.isspace())
            text = separator + '2h' + separator + '3m' + separator
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse_duration(text), 7380.0)

    def test_whitespace_cannot_split_digits_from_unit(self):
        for separator in (' ', '\r', '\v', '\f', '\u00a0', '\u2028'):
            for text in ('12' + separator + 'ms', '1h' + separator + '23' + separator + 's'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_missing_or_bare_numbers_after_complete_components(self):
        for text in ('1d2h3', '1ms0', '1s 0', '1d 2h 3', '1h 2 m', '1h 2'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_partial_or_similar_looking_units_are_invalid(self):
        for text in ('1mm', '1mss', '1sm', '1Ms', '1mS', '1d1D', '1h1minute', '1s1msec'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_decimal_numeric_symbols_are_invalid(self):
        for symbol in ('\u00b2', '\u2153', '\u2167', '\u24f5', '\u3280'):
            for text in (symbol, symbol + 'h', '1m' + symbol + 's'):
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        parse_duration(text)

    def test_large_valid_component_values_and_leading_zeroes(self):
        cases = {
            '0000000000000000000000000000000000000005': 5.0,
            '00000000100000m': 6000000.0,
            '999999ms': 999.999,
            '0002d0000h0003m0004s0005ms': 172984.005,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                result = parse_duration(text)
                self.assertIs(type(result), float)
                self.assertTrue(math.isclose(result, expected, rel_tol=0, abs_tol=1e-9))

    def test_punctuation_and_numeric_syntax_cannot_separate_components(self):
        for text in ('1h,2m', '1h;2m', '1h/2m', '1h_2m', '1h+2m', '1h-2m', '1h.2m', '1h\x002m'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)
