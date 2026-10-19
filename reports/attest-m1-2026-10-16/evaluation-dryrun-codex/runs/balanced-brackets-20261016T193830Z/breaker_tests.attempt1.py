import unittest

from brackets import is_balanced, is_bracket


class TestBreaker(unittest.TestCase):
    def test_deep_mixed_nesting(self):
        s = "([{" * 2000 + "}])" * 2000
        self.assertIs(is_balanced(s), True)
        self.assertIs(is_balanced(s[:-1]), False)

    def test_late_mismatch_after_many_valid_pairs(self):
        prefix = "()[]{}" * 2000
        self.assertIs(is_balanced(prefix + "([)]"), False)
        self.assertIs(is_balanced(prefix + "([{}])"), True)

    def test_every_wrong_single_pair(self):
        matching = {"(": ")", "[": "]", "{": "}"}
        for opening, correct_closing in matching.items():
            for closing in ")]}":
                if closing != correct_closing:
                    with self.subTest(opening=opening, closing=closing):
                        self.assertIs(is_balanced(opening + closing), False)

    def test_balanced_suffix_cannot_repair_bad_prefix(self):
        for s in (")(", "][", "}{", ")()(", "([)]()", "())(()"):
            with self.subTest(s=s):
                self.assertIs(is_balanced(s), False)

    def test_non_ascii_lookalikes_are_not_ascii_brackets(self):
        self.assertIs(is_balanced("（［｛）］｝"), True)
        self.assertIs(is_balanced("（[］"), False)
        self.assertIs(is_bracket("（"), False)

    def test_brackets_inside_comment_and_string_syntax_count(self):
        self.assertIs(is_balanced("# [\n"), False)
        self.assertIs(is_balanced("'('"), False)
        self.assertIs(is_balanced("\\}"), False)
        self.assertIs(is_balanced("'[]' # {}"), True)

    def test_nonstring_objects_are_never_coerced(self):
        class LooksLikeBrackets:
            def __str__(self):
                return "()"

            def __iter__(self):
                return iter("()")

        for value in (LooksLikeBrackets(), bytearray(b"()"), memoryview(b"()")):
            with self.subTest(value_type=type(value)):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_str_subclass_uses_its_string_contents(self):
        class MisleadingIteration(str):
            def __iter__(self):
                return iter("()" if str.__str__(self) == "(" else "(")

        self.assertIs(is_balanced(MisleadingIteration("(")), False)
        self.assertIs(is_balanced(MisleadingIteration("()")), True)
