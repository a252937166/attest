import math
import unittest

from durationkit import parse_duration


class BreakerTests(unittest.TestCase):
    def test_every_skipped_unit_pair(self):
        units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001)]
        for i, (first_unit, first_value) in enumerate(units):
            for second_unit, second_value in units[i + 1:]:
                with self.subTest(first=first_unit, second=second_unit):
                    result = parse_duration(f'2{first_unit}3{second_unit}')
                    self.assertIs(type(result), float)
                    self.assertTrue(math.isclose(result, 2 * first_value + 3 * second_value, rel_tol=0, abs_tol=1e-9))

    def test_milliseconds_follow_minutes_and_seconds(self):
        cases = {'2m3ms': 120.003, '2s3ms': 2.003, '2m3s4ms': 123.004, '00120ms': 0.12}
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertTrue(math.isclose(parse_duration(source), expected, rel_tol=0, abs_tol=1e-10))

    def test_full_sequence_with_mixed_separators(self):
        result = parse_duration(' \t1d\u20032h3m\n4s\u20285ms\t')
        self.assertTrue(math.isclose(result, 93784.005, rel_tol=0, abs_tol=1e-9))

    def test_python_whitespace_around_plain_seconds(self):
        for source in ('\u200390\u2003', '\x1c90\x1f', '\u202890\u2029'):
            with self.subTest(source=source):
                self.assertEqual(parse_duration(source), 90.0)

    def test_whitespace_between_quantity_and_unit_is_invalid(self):
        for source in ('1\u2003h', '1\nm', '1\tms', '2d 3\u2028h'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    parse_duration(source)

    def test_repetitions_with_separators_and_zero_values(self):
        for source in ('1d\t0d', '0h\n2h', '2m 0m', '1s\u20030s', '0ms 0ms'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    parse_duration(source)

    def test_ascending_units_with_intervening_whitespace(self):
        for source in ('0ms 0s', '1s\t0m', '2m\n3h', '0h 1d', '1ms 2d'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    parse_duration(source)

    def test_bare_numbers_cannot_join_components(self):
        for source in ('2d 3', '2d3h 4', '2 3ms', '2ms 3', '2d\n3h\n4'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    parse_duration(source)

    def test_millisecond_suffix_requires_complete_consumption(self):
        for source in ('1mss', '1msx', '1ms.', '1ms,2s', '1ms 2'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    parse_duration(source)

    def test_punctuation_cannot_separate_components(self):
        for source in ('1d,2h', '1h:2m', '1m/2s', '1s;2ms'):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    parse_duration(source)

    def test_other_nondecimal_numeric_characters(self):
        for character in ('\u216c', '\u2155', '\u24ea', '\u2074'):
            for source in (character, character + 'ms', '1h' + character + 'm'):
                with self.subTest(source=source):
                    with self.assertRaises(ValueError):
                        parse_duration(source)

    def test_large_clock_fields_and_leading_zeroes(self):
        cases = {'000123456m': 7407360.0, '0000024h00090m': 91800.0, '0000d0000h0000m0000s0000ms': 0.0}
        for source, expected in cases.items():
            with self.subTest(source=source):
                result = parse_duration(source)
                self.assertIs(type(result), float)
                self.assertEqual(result, expected)
