import unittest

from slugkit import slugify


class SlugifyBreakerTests(unittest.TestCase):
    def test_lowercase_expansion_creates_internal_separators(self):
        self.assertEqual(slugify("AİB"), "ai-b")
        self.assertEqual(slugify("İİ"), "i-i")
        self.assertEqual(slugify("KİK"), "ki-k")

    def test_lower_is_not_casefold(self):
        self.assertEqual(slugify("Straße"), "stra-e")
        self.assertEqual(slugify("ﬃ"), "")
        self.assertEqual(slugify("ſ"), "")

    def test_unicode_is_not_normalized_or_transliterated(self):
        self.assertEqual(slugify("e\u0301"), "e")
        self.assertEqual(slugify("é"), "")
        self.assertEqual(slugify("A\u030ab"), "a-b")
        self.assertEqual(slugify("Å"), "")

    def test_non_ascii_numeric_characters_are_separators(self):
        self.assertEqual(slugify("A١१Ⅳ①B"), "a-b")
        self.assertEqual(slugify("١१Ⅳ①"), "")

    def test_ascii_controls_and_delete_are_separators(self):
        self.assertEqual(slugify("a\x00\x1f\x7f b"), "a-b")
        self.assertEqual(slugify("\x00A\x7f"), "a")
        self.assertEqual(slugify("\x00\x1f\x7f"), "")

    def test_mixed_unicode_separator_run_collapses_once(self):
        self.assertEqual(slugify("A_💡\u200d\u00a0—_B"), "a-b")
        self.assertEqual(slugify("💡\u200dA_💡\u200dB\u00a0"), "a-b")

    def test_long_runs_at_edges_and_between_letters(self):
        run = "- \t\n\u200b_" * 500
        self.assertEqual(slugify(run + "A" + run + "B" + run), "a-b")

    def test_slugification_is_idempotent_for_special_inputs(self):
        for value in ("İK--Straße", "A_💡B", "١AⅣB", "\x00İ\u0301Z\x7f", "ﬃ"):
            with self.subTest(value=value):
                self.assertEqual(slugify(slugify(value)), slugify(value))

    def test_plain_string_subclass_uses_string_contents(self):
        class Text(str):
            pass

        result = slugify(Text("_İK_"))
        self.assertEqual(result, "i-k")
        self.assertIsInstance(result, str)

    def test_additional_non_strings_raise_exact_type_error(self):
        for value in (False, (), {}, bytearray(b"a"), memoryview(b"a")):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError) as cm:
                    slugify(value)
                self.assertEqual(str(cm.exception), "text must be a str")
