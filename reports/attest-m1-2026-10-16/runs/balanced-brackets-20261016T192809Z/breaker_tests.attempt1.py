import itertools
import unittest

from brackets import is_balanced, is_bracket


class TestBreaker(unittest.TestCase):
    def test_all_short_ascii_bracket_sequences(self):
        # Adjacent matching pairs can be removed in any order exactly when
        # the original sequence is correctly nested.
        for length in range(6):
            for chars in itertools.product("()[]{}", repeat=length):
                s = "".join(chars)
                reduced = s
                while True:
                    next_reduced = reduced.replace("()", "").replace("[]", "").replace("{}", "")
                    if next_reduced == reduced:
                        break
                    reduced = next_reduced
                with self.subTest(s=s):
                    self.assertIs(is_balanced(s), reduced == "")

    def test_deep_mixed_nesting_with_adjacent_groups(self):
        group = "(" * 1024 + "[" * 1024 + "{" * 1024 + "}" * 1024 + "]" * 1024 + ")" * 1024
        self.assertIs(is_balanced("α" + group + "x[]y" + group + "ω"), True)

    def test_deep_outer_mismatch(self):
        s = "(" * 1024 + "[" * 1024 + "]" * 1024 + ")" * 1023 + "]"
        self.assertIs(is_balanced(s), False)

    def test_premature_closer_before_valid_suffix(self):
        self.assertIs(is_balanced("text } " + "({[]})" * 100), False)

    def test_unmatched_opener_after_valid_prefix(self):
        self.assertIs(is_balanced("({[]})" * 100 + " ignored ["), False)

    def test_unicode_bracket_lookalikes_are_ignored(self):
        lookalikes = "（ ） ［ ］ ｛ ｝ ❨ ❩ ⟦ ⟧"
        self.assertIs(is_balanced(lookalikes + "{[()]}"), True)
        self.assertIs(is_balanced("（[］"), False)

    def test_str_subclass_uses_its_string_contents(self):
        class MisleadingString(str):
            def __str__(self):
                return "()"

        self.assertIs(is_balanced(MisleadingString("([)]")), False)
        self.assertIs(is_balanced(MisleadingString("{text[]} ")), True)

    def test_deceptive_non_string_objects_raise_type_error(self):
        class StringLike:
            def __str__(self):
                return "()"

            def __iter__(self):
                return iter("()")

        for value in (StringLike(), bytearray(b"()"), memoryview(b"()"), range(0)):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError):
                    is_balanced(value)

    def test_is_bracket_remains_ascii_single_character_only(self):
        class BracketString(str):
            pass

        self.assertIs(is_bracket(BracketString("{")), True)
        for value in ("（", "⟦", "{ ", "()", b"(", None):
            with self.subTest(value=value):
                self.assertIs(is_bracket(value), False)
