#!/usr/bin/env python3
"""Write the frozen evaluation task suite under examples/eval/. Each task has a small repo with a working helper
(so the existing suite passes on the unmodified code) and a target stub (so the independent held-out suite fails on
the unmodified code). The held-out file is the objective judge used for BOTH the plain baseline and Attest."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "examples" / "eval"


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


TASKS = {}

# ---------------------------------------------------------------- roman numerals
TASKS["roman-to-numeral"] = {
    "core": '''"""Roman numerals."""


def is_roman_numeral(s):
    """True when s is a non-empty string of Roman numeral letters (case-insensitive). Already implemented."""
    return isinstance(s, str) and len(s) > 0 and all(c in "IVXLCDM" for c in s.upper())


def to_roman(n):
    raise NotImplementedError("to_roman is not implemented yet")
''',
    "basic": '''import unittest
from roman import is_roman_numeral


class TestHelper(unittest.TestCase):
    def test_true(self):
        self.assertTrue(is_roman_numeral("XIV"))
        self.assertTrue(is_roman_numeral("mmxxiv"))

    def test_false(self):
        self.assertFalse(is_roman_numeral(""))
        self.assertFalse(is_roman_numeral("ABC"))
        self.assertFalse(is_roman_numeral(14))
''',
    "heldout": '''import unittest
from roman import to_roman


class HeldOut(unittest.TestCase):
    def test_units(self):
        for n, r in [(1, "I"), (2, "II"), (3, "III"), (4, "IV"), (5, "V"), (9, "IX")]:
            self.assertEqual(to_roman(n), r)

    def test_tens_and_subtractive(self):
        for n, r in [(10, "X"), (40, "XL"), (49, "XLIX"), (90, "XC"), (99, "XCIX")]:
            self.assertEqual(to_roman(n), r)

    def test_hundreds_thousands(self):
        for n, r in [(400, "CD"), (900, "CM"), (1000, "M"), (2024, "MMXXIV"), (3999, "MMMCMXCIX"), (1994, "MCMXCIV")]:
            self.assertEqual(to_roman(n), r)

    def test_returns_str(self):
        self.assertIsInstance(to_roman(1), str)

    def test_out_of_range_raises_valueerror(self):
        for bad in (0, -1, 4000, 10000):
            with self.assertRaises(ValueError):
                to_roman(bad)

    def test_non_int_raises_typeerror(self):
        for bad in ("5", 5.0, None, [1]):
            with self.assertRaises(TypeError):
                to_roman(bad)
''',
    "statement": ("The roman package exposes is_roman_numeral (already implemented) and a stub to_roman(n). Implement "
                  "to_roman(n) so that it converts an integer n in the range 1..3999 inclusive to its standard Roman "
                  "numeral string using subtractive notation (4='IV', 9='IX', 40='XL', 90='XC', 400='CD', 900='CM'). "
                  "Return a str. Raise ValueError when n is an int outside 1..3999. Raise TypeError when n is not an int "
                  "(bool counts as non-int for this task is not required; treat only real ints as valid). Do not change "
                  "is_roman_numeral or the tests."),
    "criteria": ["to_roman(1)=='I', to_roman(4)=='IV', to_roman(9)=='IX'",
                 "to_roman(40)=='XL', to_roman(90)=='XC', to_roman(400)=='CD', to_roman(900)=='CM'",
                 "to_roman(2024)=='MMXXIV', to_roman(3999)=='MMMCMXCIX', to_roman(1994)=='MCMXCIV'",
                 "to_roman returns a str",
                 "ValueError for ints outside 1..3999 (0, -1, 4000)",
                 "TypeError for non-int input ('5', 5.0, None, [1])"],
    "import_hint": "from roman import to_roman",
    "pkg": "roman",
}

# ---------------------------------------------------------------- run-length encoding
TASKS["rle-encode"] = {
    "core": '''"""Run-length encoding."""


def decode(s):
    """Decode a run-length string like 'a3b1' back to 'aaab'. Already implemented."""
    if not isinstance(s, str):
        raise TypeError("decode expects a string")
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        j = i + 1
        while j < len(s) and s[j].isdigit():
            j += 1
        if j == i + 1:
            raise ValueError("missing count")
        out.append(ch * int(s[i + 1:j]))
        i = j
    return "".join(out)


def encode(s):
    raise NotImplementedError("encode is not implemented yet")
''',
    "basic": '''import unittest
from rle import decode


class TestDecode(unittest.TestCase):
    def test_decode(self):
        self.assertEqual(decode("a3b1"), "aaab")
        self.assertEqual(decode(""), "")

    def test_decode_type(self):
        with self.assertRaises(TypeError):
            decode(123)
''',
    "heldout": '''import unittest
from rle import encode, decode


class HeldOut(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(encode("aaabbc"), "a3b2c1")
        self.assertEqual(encode("a"), "a1")

    def test_empty(self):
        self.assertEqual(encode(""), "")

    def test_single_runs(self):
        self.assertEqual(encode("abc"), "a1b1c1")

    def test_long_run(self):
        self.assertEqual(encode("x" * 12), "x12")

    def test_roundtrip(self):
        for text in ("", "a", "aaabbc", "mississippi", "xxxxxxxxxxyz"):
            self.assertEqual(decode(encode(text)), text)

    def test_returns_str(self):
        self.assertIsInstance(encode("aa"), str)

    def test_non_string_raises_typeerror(self):
        for bad in (123, None, ["a"]):
            with self.assertRaises(TypeError):
                encode(bad)
''',
    "statement": ("The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that "
                  "it run-length encodes a string: each maximal run of one character becomes that character followed by the "
                  "decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') "
                  "is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip "
                  "with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not "
                  "change decode or the tests."),
    "criteria": ["encode('aaabbc')=='a3b2c1' and encode('a')=='a1'",
                 "encode('')==''",
                 "encode('abc')=='a1b1c1' (count written even when 1)",
                 "encode('x'*12)=='x12' (multi-digit counts)",
                 "decode(encode(x))==x for every string x",
                 "encode returns a str",
                 "TypeError when s is not a string"],
    "import_hint": "from rle import encode",
    "pkg": "rle",
}

# ---------------------------------------------------------------- balanced brackets
TASKS["balanced-brackets"] = {
    "core": '''"""Bracket matching."""

PAIRS = {")": "(", "]": "[", "}": "{"}
OPEN = set(PAIRS.values())
CLOSE = set(PAIRS)


def is_bracket(c):
    """True when c is one of the six bracket characters. Already implemented."""
    return isinstance(c, str) and len(c) == 1 and (c in OPEN or c in CLOSE)


def is_balanced(s):
    raise NotImplementedError("is_balanced is not implemented yet")
''',
    "basic": '''import unittest
from brackets import is_bracket


class TestHelper(unittest.TestCase):
    def test_true(self):
        for c in "()[]{}":
            self.assertTrue(is_bracket(c))

    def test_false(self):
        for c in ("a", "", "((", 1):
            self.assertFalse(is_bracket(c))
''',
    "heldout": '''import unittest
from brackets import is_balanced


class HeldOut(unittest.TestCase):
    def test_simple_balanced(self):
        for s in ("", "()", "[]", "{}", "()[]{}", "([{}])"):
            self.assertTrue(is_balanced(s))

    def test_nested(self):
        self.assertTrue(is_balanced("(a[b]{c})"))
        self.assertTrue(is_balanced("code = f(x[0], y[1])"))

    def test_unbalanced(self):
        for s in ("(", ")", "([)]", "(]", "{[}", "())"):
            self.assertFalse(is_balanced(s))

    def test_ignores_non_bracket_chars(self):
        self.assertTrue(is_balanced("a + b - c"))
        self.assertFalse(is_balanced("a ) b"))

    def test_returns_bool(self):
        self.assertIsInstance(is_balanced("()"), bool)

    def test_non_string_raises_typeerror(self):
        for bad in (123, None, ["("]):
            with self.assertRaises(TypeError):
                is_balanced(bad)
''',
    "statement": ("The brackets package exposes is_bracket (already implemented) and a stub is_balanced(s). Implement "
                  "is_balanced(s) so that it returns True when the three kinds of brackets (), [] and {} in the string s "
                  "are correctly matched and nested, and False otherwise. Characters that are not brackets are ignored. "
                  "The empty string is balanced. is_balanced must return a bool. Raise TypeError when s is not a string. "
                  "Do not change is_bracket or the tests."),
    "criteria": ["'', '()', '[]', '{}', '()[]{}', '([{}])' are all balanced (True)",
                 "nested mixed brackets with other characters are balanced: '(a[b]{c})', 'f(x[0], y[1])'",
                 "'(', ')', '([)]', '(]', '{[}', '())' are not balanced (False)",
                 "non-bracket characters are ignored",
                 "is_balanced returns a bool",
                 "TypeError when s is not a string"],
    "import_hint": "from brackets import is_balanced",
    "pkg": "brackets",
}


def main() -> None:
    manifest = []
    for task_id, t in TASKS.items():
        pkg = t["pkg"]
        base = f"{task_id}/repo"
        write(f"{base}/{pkg}/__init__.py", f"from .core import *  # noqa: F401,F403\n")
        write(f"{base}/{pkg}/core.py", t["core"])
        write(f"{base}/tests/__init__.py", "")
        write(f"{base}/tests/test_basic.py", t["basic"])
        write(f"{task_id}/heldout.py", t["heldout"])
        task = {
            "id": task_id, "title": task_id, "repo_dir": "repo", "language": "python",
            "base_image": "python:3.12-slim", "test_runner": "unittest", "import_hint": t["import_hint"],
            "test_command": ["/usr/local/bin/python", "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"],
            "allowed_write_globs": [f"{pkg}/**"], "protected_globs": ["tests/**"],
            "heldout_tests": {"tests/test_heldout.py": "heldout.py"},
            "statement": t["statement"], "acceptance_criteria": t["criteria"],
        }
        write(f"{task_id}/task.json", json.dumps(task, indent=2) + "\n")
        manifest.append({"id": task_id, "path": f"examples/eval/{task_id}/task.json", "heldout": f"examples/eval/{task_id}/heldout.py"})
    # Reference the two existing multi-file tasks too (they already carry independent held-out tests).
    manifest.append({"id": "durationkit-units-001", "path": "examples/durationkit-task/task.json", "heldout": "examples/eval/durationkit-task/heldout.py"})
    manifest.append({"id": "semver-is-compatible-pr368-v2", "path": "examples/semver-is-compatible-v2/task.json", "heldout": "examples/semver-is-compatible/heldout_test_pr368.py"})
    (ROOT / "SUITE.json").write_text(json.dumps({"tasks": manifest}, indent=2) + "\n", encoding="utf-8")
    print("wrote", len(manifest), "tasks to", ROOT)
    for m in manifest:
        print(" -", m["id"])


if __name__ == "__main__":
    main()
