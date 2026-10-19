import inspect
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as parse_duration_module


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_public_imports_and_signature(self):
        for parser in (parse_duration, parse_duration_module):
            with self.subTest(parser=parser.__module__):
                signature = inspect.signature(parser, eval_str=True)
                parameters = list(signature.parameters.values())
                self.assertEqual(len(parameters), 1)
                self.assertEqual(parameters[0].name, "text")
                self.assertIs(parameters[0].annotation, str)
                self.assertIs(signature.return_annotation, float)
                self.assertEqual(parser("90"), 90.0)

    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("0007", 7.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_combined_components(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5), ("1d1h1m1s1ms", 90061.001)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_duration(text), expected)

    def test_skipped_units(self):
        self.assertEqual(parse_duration("1d1s"), 86401.0)
        self.assertAlmostEqual(parse_duration("1h1ms"), 3600.001)

    def test_whitespace_between_complete_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\r", "\v1h\f30m\u2003"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_leading_zeros_in_components(self):
        self.assertEqual(parse_duration("01h030m"), 5400.0)

    def test_zero_valued_components(self):
        self.assertEqual(parse_duration("0s"), 0.0)
        self.assertEqual(parse_duration("0d0h0m0s0ms"), 0.0)

    def test_component_values_can_exceed_clock_ranges(self):
        self.assertEqual(parse_duration("90m"), 5400.0)
        self.assertEqual(parse_duration("1500ms"), 1.5)

    def test_valid_results_are_floats(self):
        for text in ("90", "0", "2d", "0s", "0d0h0m0s0ms", "500ms", "1h30m", "1d1h1m1s1ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_strings(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_unsupported_number_syntax(self):
        for text in ("-1", "-1h", "+1", "+1h", "1.5h", ".5s", "1e3s", "1_000s", "1,000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_unknown_uppercase_and_numberless_units(self):
        for text in ("1x", "1H", "1MS", "h", "ms", "abc"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_repeated_units(self):
        for text in ("1h1h", "1h 0h", "0s0s", "1ms1ms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_units_out_of_descending_order(self):
        for text in ("30m1h", "1ms1s", "1s1d", "0s0h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_whitespace_inside_number_or_component(self):
        for text in ("1 h", "500 ms", "1\th", "1 0"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_mixed_bare_values_and_unmatched_trailing_text(self):
        for text in ("1h30", "1 30m", "1h!", "1h,30m", "1mss"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_non_decimal_numeric_characters(self):
        for text in ("Ⅰ", "Ⅰh", "½", "½s", "①", "①m", "²s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as cm:
                    parse_duration(text)

    def test_non_string_inputs(self):
        for value in (90, 0.5, None, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    parse_duration(value)

    def test_str_subclass_is_accepted(self):
        class DurationText(str):
            pass

        self.assertEqual(parse_duration(DurationText("1h30m")), 5400.0)

    def test_unicode_decimal_digits_may_be_accepted_or_rejected(self):
        for text, expected in (("١٢h", 43200.0), ("１２", 12.0)):
            with self.subTest(text=text):
                try:
                    result = parse_duration(text)
                except ValueError:
                    continue
                self.assertIsInstance(result, float)
                self.assertEqual(result, expected)
