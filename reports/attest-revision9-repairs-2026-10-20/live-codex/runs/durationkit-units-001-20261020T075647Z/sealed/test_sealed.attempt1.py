import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_from_module


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_plain_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_parse_module_import_remains_available(self):
        self.assertEqual(parse_duration_from_module("2m"), 120.0)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0),
                               ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_valid_combinations(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0),
                               ("1m1s", 61.0), ("1s500ms", 1.5),
                               ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected, delta=1e-9)

    def test_skipped_units(self):
        self.assertEqual(parse_duration("1d1s"), 86401.0)

    def test_component_values_need_not_be_normalized(self):
        for text, expected in (("90m", 5400.0), ("1500ms", 1.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_leading_zeros(self):
        for text, expected in (("00090", 90.0), ("01h030m", 5400.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_zero_valued_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_whitespace_around_and_between_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\r", "\u20031h\v30m\f"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_whitespace_between_number_and_unit_is_rejected(self):
        for text in ("1 h", "1\th", "1m s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_all_accepted_forms_return_float(self):
        for text in ("7", "0", "0ms", "1h", "1h30m", "1ms", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_are_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_signed_numbers_are_rejected(self):
        for text in ("-1", "-1h", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_fractional_exponent_and_separator_notation_is_rejected(self):
        for text in ("1.5h", ".5s", "1e3s", "1_000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_unknown_uppercase_and_bare_units_are_rejected(self):
        for text in ("1x", "1H", "1MS", "h", "ms", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_repeated_units_are_rejected_even_when_zero(self):
        for text in ("1h1h", "1ms1ms", "0h0h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_out_of_order_units_are_rejected_even_when_zero(self):
        for text in ("30m1h", "1ms1s", "0s0m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_mixed_unitless_and_unit_components_are_rejected(self):
        for text in ("1h30", "1 30m", "1 2"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_trailing_punctuation_and_garbage_are_rejected(self):
        for text in ("1h,30m", "1h!", "1msx"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_nondecimal_numeric_characters_are_rejected(self):
        for text in ("Ⅳ", "½", "①", "①h", "²s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, 1.5, True, None, b"90"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse_duration(value)
