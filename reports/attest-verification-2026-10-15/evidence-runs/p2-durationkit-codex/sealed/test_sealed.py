import inspect
import unittest

from durationkit import parse_duration
from durationkit.parse import parse_duration as module_parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_public_and_module_imports_remain_available(self):
        self.assertIs(parse_duration, module_parse_duration)

    def test_public_signature(self):
        signature = inspect.signature(module_parse_duration)
        self.assertEqual(list(signature.parameters), ["text"])
        self.assertEqual(signature.parameters["text"].kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIn(signature.parameters["text"].annotation, (str, "str"))
        self.assertIn(signature.return_annotation, (float, "float"))
        self.assertEqual(parse_duration(text="2s"), 2.0)

    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("0007", 7.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_combined_components(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_all_units_in_descending_order(self):
        self.assertAlmostEqual(parse_duration("1d1h1m1s1ms"), 90061.001, delta=1e-9)

    def test_units_may_be_skipped(self):
        self.assertAlmostEqual(parse_duration("1d1ms"), 86400.001, delta=1e-9)

    def test_component_values_have_no_clock_bounds(self):
        self.assertEqual(parse_duration("90m"), 5400.0)
        self.assertEqual(parse_duration("1500ms"), 1.5)

    def test_zero_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zeros_in_components(self):
        self.assertEqual(parse_duration("01h030m"), 5400.0)

    def test_surrounding_whitespace(self):
        self.assertEqual(parse_duration(" 1h30m "), 5400.0)

    def test_whitespace_between_complete_components(self):
        for text in (" 1h 30m ", "\t1h\n30m\r", "1h\u200330m"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_whitespace_within_components_is_rejected(self):
        for text in ("1 h", "1m s", "1 m", "1m s1ms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unicode_decimal_digits(self):
        self.assertEqual(parse_duration("\uff11\uff12"), 12.0)
        self.assertEqual(parse_duration("\u0661h\u0663\u0660m"), 5400.0)

    def test_nondecimal_digit_is_rejected(self):
        for text in ("\u00b2", "\u00b2s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_empty_or_whitespace_only_input_is_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_explicit_signs_are_rejected(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_fractional_numbers_are_rejected(self):
        for text in ("1.5", "1.5h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_exponents_and_digit_separators_are_rejected(self):
        for text in ("1e3s", "1_000s", "1e3", "1_000"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_or_uppercase_units_are_rejected(self):
        for text in ("1x", "1H", "1MS", "1sec"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_are_rejected(self):
        for text in ("1h1h", "1ms2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_out_of_order_units_are_rejected(self):
        for text in ("30m1h", "1ms1s", "0s0m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers_are_rejected(self):
        for text in ("h", "ms", "1hms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_bare_numbers_cannot_mix_with_components(self):
        for text in ("1h30", "90 1s", "1 2"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_punctuation_and_trailing_junk_are_rejected(self):
        for text in ("abc", "1h,30m", "1s!"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_non_string_inputs_raise_type_error(self):
        for value in (90, None, 1.5, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)

    def test_every_accepted_form_returns_float(self):
        for text in ("90", "0", "1h", "0s", "0ms", "500ms", "1h30m", "1d1h1m1s1ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_str_subclass_is_accepted(self):
        class DurationText(str):
            pass

        self.assertEqual(parse_duration(DurationText("1h30m")), 5400.0)
