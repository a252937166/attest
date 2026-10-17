import itertools
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as module_parse_duration


class TestBreakerDurationParsing(unittest.TestCase):
    def test_every_descending_unit_subsequence(self):
        units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001)]
        for size in range(1, 6):
            for chosen in itertools.combinations(units, size):
                text = ''.join('2' + unit for unit, _ in chosen)
                expected = sum(2 * factor for _, factor in chosen)
                with self.subTest(text=text):
                    self.assertIsInstance(parse_duration(text), float)
                    self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    # Corrected 17 Oct 2026. The original test fed mixed Arabic-Indic, Devanagari and fullwidth digits ('١२h３४m') and
    # expected 58440.0; 12h34m is 45240.0, so the expectation was wrong (the arbiter corrected the value). The clarified
    # contract leaves non-ASCII decimal digits unspecified, so the test now covers multi-digit ASCII components instead.
    def test_multi_digit_ascii_components(self):
        cases = {'12h34m': 45240.0, '45': 45.0, '7ms': 0.007, '120m': 7200.0, '001h': 3600.0}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)
                self.assertAlmostEqual(module_parse_duration(text), expected, delta=1e-9)

    def test_unusual_python_whitespace_between_components(self):
        for separator in ('\u001c', '\u00a0', '\u2028', '\u3000'):
            text = separator + '2h' + separator + '3m' + separator
            with self.subTest(separator=repr(separator)):
                self.assertEqual(parse_duration(text), 7380.0)
                with self.assertRaises(ValueError):
                    parse_duration('2' + separator + 'h3m')

    def test_ms_is_one_unit_after_m_or_s(self):
        cases = {'2m3ms': 120.003, '2s3ms': 2.003, '2m3s4ms': 123.004}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_nonadjacent_repeats_and_reversals(self):
        for text in ('1d2h3d', '1h2s3h', '1m2ms3m', '1d2ms3s', '1h2m3h', '1s2ms3ms'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text)

    def test_whitespace_cannot_split_digits_or_units(self):
        for text in ('1 2h', '1h2 3m', '1m s', '1m\ts', '1m\ns', '1\u00a0ms'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text)

    def test_partial_tokens_and_trailing_text(self):
        for text in ('1d2h3', '1h2m3', '1ms2', '1msec', '1msx', 'x1h', '1h\x002m', '1h#2m'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text)

    def test_other_numeric_characters_are_not_decimal_digits(self):
        for token in ('Ⅻ', '①', '四', '½', '−1', '1٫5'):
            for text in (token, token + 's', '1h' + token + 'ms'):
                with self.subTest(text=text), self.assertRaises(ValueError):
                    parse_duration(text)

    def test_string_subclass_and_other_object_types(self):
        class DurationText(str):
            pass

        self.assertEqual(parse_duration(DurationText(' 2h3m ')), 7380.0)
        for value in (bytearray(b'2h'), memoryview(b'2h'), 2 + 0j, object()):
            with self.subTest(type=type(value).__name__), self.assertRaises(TypeError):
                parse_duration(value)

    def test_large_finite_component_values(self):
        number = '12345678901234567890'
        for text, expected in ((number, float(number)), (number + 's', float(number)), (number + 'ms', float(number) * 0.001)):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)
                self.assertEqual(parse_duration(text), expected)
