import itertools
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_module_duration


class TestBreaker(unittest.TestCase):
    def test_every_nonempty_ordered_unit_subset(self):
        units = (('d', 2, 86400), ('h', 3, 3600), ('m', 4, 60), ('s', 5, 1), ('ms', 125, 0.001))
        for count in range(1, 6):
            for subset in itertools.combinations(units, count):
                text = ''.join(f'{value}{unit}' for unit, value, _ in subset)
                expected = sum(value * factor for _, value, factor in subset)
                with self.subTest(text=text):
                    actual = parse_duration(text)
                    self.assertIs(type(actual), float)
                    self.assertAlmostEqual(actual, expected, delta=1e-9)

    def test_milliseconds_follow_seconds_without_separator(self):
        for text, expected in (('2s3ms', 2.003), ('7m8ms', 420.008), ('9h10ms', 32400.01), ('11d12ms', 950400.012)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_python_whitespace_between_complete_components(self):
        for separator in (chr(9), chr(10), chr(11), chr(12), chr(13), chr(0x85), chr(0x2003), chr(0x2028), chr(0x3000)):
            text = separator + '2h' + separator + '3m' + separator + '4ms' + separator
            with self.subTest(separator=repr(separator)):
                self.assertAlmostEqual(parse_duration(text), 7380.004, delta=1e-9)

    def test_whitespace_cannot_split_number_from_unit(self):
        for text in ('1 d', '1\tms', '1\nms', '1' + chr(0x2003) + 'h', '2m 3 s', '2m 3\nms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_all_other_permutations_of_zero_units_are_invalid(self):
        units = ('d', 'h', 'm', 's', 'ms')
        for ordering in itertools.permutations(units):
            if ordering == units:
                continue
            text = ''.join('0' + unit for unit in ordering)
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_after_intervening_components(self):
        for text in ('1d2h3d', '1h2m3h', '1m2s3m', '1s2ms3s', '1d0ms0ms'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_partial_components_and_mixed_forms_are_invalid(self):
        for text in ('1d2', '1h2m3', '1ms2', '1 2ms', '1d 2', '1d2h ms', '1m s', '1m2ms3'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_malformed_numbers_inside_valid_sequences(self):
        for text in ('1h+2m', '1h-2m', '1h2.5m', '1h.5m', '1h2e3m', '1h2_000m', '1h0x10m'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_nondecimal_numeric_characters_embedded_in_components(self):
        for text in ('1h²m', '1m½s', '1s①ms', 'Ⅳms', '2hⅣm'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_container_and_numeric_inputs(self):
        for value in ([], (), {}, 0, 0.0, False, complex(1, 0), bytearray(b'1s')):
            with self.subTest(value=repr(value)):
                with self.assertRaises(TypeError):
                    parse_duration(value)

    def test_long_leading_zero_component(self):
        text = '0' * 100 + '1s'
        self.assertEqual(parse_duration(text), 1.0)
        self.assertEqual(parse_module_duration(text), 1.0)
