import unittest

from brackets import is_balanced, is_bracket


class TestBalancedBrackets(unittest.TestCase):
    def test_empty_string_is_balanced(self):
        self.assertIs(is_balanced(""), True)

    def test_simple_pairs_are_balanced(self):
        for value in ("()", "[]", "{}"):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_adjacent_pairs_are_balanced(self):
        self.assertIs(is_balanced("()[]{}"), True)

    def test_nested_pairs_are_balanced(self):
        for value in ("([{}])", "([]{})"):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_non_bracket_characters_inside_pairs_are_ignored(self):
        for value in ("(a[b]{c})", "f(x[0], y[1])"):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_opening_brackets_left_unmatched_are_unbalanced(self):
        for value in ("(", "[", "{", "(()", "[]("):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_closing_brackets_without_openers_are_unbalanced(self):
        for value in (")", "]", "}", "())", ")("):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_mismatched_closing_brackets_are_unbalanced(self):
        for value in ("(]", "[)", "{]", "{[}"):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_crossed_nesting_is_unbalanced(self):
        for value in ("([)]", "[(])"):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), False)

    def test_text_without_ascii_brackets_is_balanced(self):
        for value in ("plain text", " \t\n", "café 漢字", "（［｛｝］）", "〈【】〉"):
            with self.subTest(value=value):
                self.assertIs(is_balanced(value), True)

    def test_removing_non_bracket_characters_preserves_result(self):
        for value in ("a(é[b]漢){c}!", "x([y)]z", "\"(\"", "\\(", "（[）]", "text only"):
            with self.subTest(value=value):
                filtered = "".join(c for c in value if c in "()[]{}")
                self.assertIs(is_balanced(value), is_balanced(filtered))

    def test_quotes_do_not_hide_brackets(self):
        self.assertIs(is_balanced('\"(\"'), False)

    def test_backslashes_do_not_escape_brackets(self):
        self.assertIs(is_balanced("\\("), False)

    def test_results_have_exact_bool_type(self):
        for value in ("", "([])", "(", "([)]"):
            with self.subTest(value=value):
                self.assertIs(type(is_balanced(value)), bool)

    def test_non_string_inputs_raise_type_error(self):
        for value in (None, True, 0, 1.5, b"", b"()", [], ["("], (), {}, set()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_string_subclasses_are_accepted(self):
        class Text(str):
            pass

        self.assertIs(is_balanced(Text("([{}])")), True)
        self.assertIs(is_balanced(Text("([)]")), False)

    def test_calls_do_not_share_bracket_state(self):
        self.assertIs(is_balanced("(["), False)
        self.assertIs(is_balanced("{}"), True)
        self.assertIs(is_balanced("]"), False)
        self.assertIs(is_balanced("()"), True)

    def test_is_balanced_requires_its_argument(self):
        with self.assertRaises(TypeError):
            is_balanced()

    def test_is_balanced_rejects_unsupported_arguments(self):
        with self.assertRaises(TypeError):
            is_balanced("()", "[]")
        with self.assertRaises(TypeError):
            is_balanced(s="()", extra=True)


class TestIsBracketExport(unittest.TestCase):
    def test_ascii_bracket_characters_are_recognized(self):
        for value in "()[]{}":
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), True)

    def test_other_values_are_not_brackets(self):
        for value in ("a", "", "((", 1, "（"):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)

    def test_is_bracket_requires_its_argument(self):
        with self.assertRaises(TypeError):
            is_bracket()

    def test_is_bracket_rejects_unsupported_arguments(self):
        with self.assertRaises(TypeError):
            is_bracket("(", ")")
        with self.assertRaises(TypeError):
            is_bracket(c="(", extra=True)
