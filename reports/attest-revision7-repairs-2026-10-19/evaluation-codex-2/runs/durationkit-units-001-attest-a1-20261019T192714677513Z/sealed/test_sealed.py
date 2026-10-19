import inspect
import unittest

from durationkit import parse_duration


class ParseDurationAcceptanceTests(unittest.TestCase):
    def test_public_import_and_signature(self):
        self.assertEqual(parse_duration(text="90"), 90.0)
        signature = inspect.signature(parse_duration)
        self.assertEqual(list(signature.parameters), ["text"])
        self.assertIn(signature.parameters["text"].annotation, (str, "str"))
        self.assertIn(signature.return_annotation, (float, "float"))

    def test_plain_integer_seconds(self):
        for text, expected in (("90", 90.0), ("  42 ", 42.0), ("0", 0.0), ("00090", 90.0)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_single_components(self):
        for text, expected in (("2d", 172800.0), ("3h", 10800.0), ("15m", 900.0), ("45s", 45.0), ("500ms", 0.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_descending_component_pairs(self):
        for text, expected in (("1h30m", 5400.0), ("2d4h", 187200.0), ("1m1s", 61.0), ("1s500ms", 1.5)):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), expected)

    def test_all_units_in_descending_order(self):
        self.assertAlmostEqual(parse_duration("1d1h1m1s1ms"), 90061.001, places=9)

    def test_skipped_units(self):
        self.assertAlmostEqual(parse_duration("1d1ms"), 86400.001, places=9)
        self.assertEqual(parse_duration("1h1s"), 3601.0)

    def test_surrounding_and_intercomponent_whitespace(self):
        for text in (" 1h 30m ", "\t1h\n30m\r"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 5400.0)

    def test_unicode_whitespace_between_components(self):
        self.assertEqual(parse_duration("1h\u200330m"), 5400.0)

    def test_whitespace_between_number_and_unit_is_rejected(self):
        for text in ("1 h", "500 ms", "1h 30 m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_zero_components(self):
        for text in ("0s", "0ms", "0d0h0m0s0ms"):
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), 0.0)

    def test_leading_zero_components(self):
        self.assertEqual(parse_duration("001h030m"), 5400.0)

    def test_component_values_exceeding_clock_ranges(self):
        self.assertEqual(parse_duration("90m"), 5400.0)
        self.assertEqual(parse_duration("1500ms"), 1.5)

    def test_every_accepted_form_returns_float(self):
        for text in ("0", "00090", "0s", "0ms", "2d", "1h30m", "1s500ms"):
            with self.subTest(text=text):
                self.assertIsInstance(parse_duration(text), float)

    def test_empty_and_whitespace_only_inputs_are_rejected(self):
        for text in ("", "   ", "\t\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_signed_numbers_are_rejected(self):
        for text in ("-1", "-1h", "+1", "+1h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_fractional_numbers_are_rejected(self):
        for text in ("1.5", "1.5h", ".5s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_exponential_numbers_are_rejected(self):
        for text in ("1e3", "1e3s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_embedded_numeric_separators_are_rejected(self):
        for text in ("1_000", "1_000s", "1,000", "1,000s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_unknown_units_are_rejected(self):
        for text in ("1x", "1w"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_uppercase_units_are_rejected(self):
        for text in ("1H", "1MS"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_units_without_numbers_are_rejected(self):
        for text in ("h", "ms", "1hms"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_repeated_units_are_rejected_even_when_zero(self):
        for text in ("1h1h", "1ms2ms", "0s0s"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_out_of_order_units_are_rejected_even_when_zero(self):
        for text in ("30m1h", "1ms1s", "1s1d", "0m0h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_partial_component_matches_are_rejected(self):
        for text in ("1h30", "1s500m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_bare_seconds_cannot_be_mixed_with_components(self):
        for text in ("1 30m", "1h 30"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_extraneous_text_is_rejected(self):
        for text in ("abc", "1h,30m", "x1h", "1h!", "1h!30m"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_nondecimal_numeric_characters_are_rejected(self):
        for text in ("①", "①h", "Ⅳ", "Ⅳs", "½", "½h"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)

    def test_nonstring_inputs_raise_type_error(self):
        for value in (90, 0.5, None, True, b"90", []):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_duration(value)

    def test_str_subclass_is_accepted(self):
        class DurationText(str):
            pass

        self.assertEqual(parse_duration(DurationText("1m30s")), 90.0)
