import inspect
import re
import unittest

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class CompatibilityAcceptanceTests(unittest.TestCase):
    def test_public_access_and_signature(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        self.assertIs(semver.Version, Version)
        method = Version.is_compatible
        self.assertIs(semver.Version.is_compatible, method)
        self.assertIs(VersionInfo.is_compatible, method)
        parameters = list(inspect.signature(method).parameters.values())
        self.assertEqual([p.name for p in parameters], ["self", "other"])
        self.assertIs(parameters[1].default, inspect.Parameter.empty)
        self.assertEqual(parameters[1].kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIn(inspect.signature(method).return_annotation, (bool, "bool"))
        old = Version(1, 2, 3)
        new = Version(1, 3, 0)
        self.assertIs(old.is_compatible(new), old.is_compatible(other=new))

    def test_equal_versions_and_patch_changes_are_compatible_for_nonzero_major(self):
        self.assertIs(Version(1, 2, 3).is_compatible(Version(1, 2, 3)), True)
        self.assertIs(Version(1, 2, 3).is_compatible(Version(1, 2, 4)), True)
        self.assertIs(Version(1, 2, 4).is_compatible(Version(1, 2, 3)), True)

    def test_nonzero_major_minor_may_increase_but_not_decrease(self):
        self.assertIs(Version(1, 2, 9).is_compatible(Version(1, 3, 0)), True)
        self.assertIs(Version(1, 3, 0).is_compatible(Version(1, 2, 9)), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible_in_both_directions(self):
        for left, right in ((Version(1, 5, 0), Version(2, 0, 0)),
                            (Version(0, 1, 0), Version(1, 1, 0))):
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_matching_prerelease_allows_patch_or_minor_change(self):
        old = Version(1, 2, 3, "rc.0")
        self.assertIs(old.is_compatible(Version(1, 2, 4, "rc.0")), True)
        self.assertIs(old.is_compatible(Version(1, 3, 0, "rc.0")), True)

    def test_different_prerelease_values_are_incompatible(self):
        cases = (("rc.0", "rc.1"), ("rc.0", "Rc.0"),
                 (None, "rc.0"), ("rc.0", None))
        for old_pre, new_pre in cases:
            with self.subTest(old_pre=old_pre, new_pre=new_pre):
                self.assertIs(Version(1, 2, 3, old_pre).is_compatible(
                    Version(1, 3, 0, new_pre)), False)

    def test_empty_prerelease_is_distinct_from_absent_prerelease(self):
        absent = Version(1, 2, 3)
        empty = Version(1, 2, 3, "")
        self.assertIs(absent.is_compatible(empty), False)
        self.assertIs(empty.is_compatible(absent), False)
        self.assertIs(empty.is_compatible(Version(1, 3, 0, "")), True)

    def test_major_zero_requires_exact_core_version(self):
        old = Version(0, 1, 0)
        self.assertIs(old.is_compatible(Version(0, 1, 0)), True)
        for candidate in (Version(0, 1, 1), Version(0, 1, 2),
                          Version(0, 2, 0), Version(0, 0, 0)):
            with self.subTest(candidate=candidate):
                self.assertIs(old.is_compatible(candidate), False)
        self.assertIs(Version(0, 1, 1).is_compatible(Version(0, 1, 0)), False)
        self.assertIs(Version(0, 2, 0).is_compatible(Version(0, 1, 0)), False)

    def test_major_zero_requires_exact_prerelease(self):
        old = Version(0, 1, 0, "rc.0")
        self.assertIs(old.is_compatible(Version(0, 1, 0, "rc.0")), True)
        self.assertIs(old.is_compatible(Version(0, 1, 0, "rc.1")), False)
        self.assertIs(old.is_compatible(Version(0, 1, 0)), False)
        self.assertIs(Version(0, 1, 0).is_compatible(old), False)
        self.assertIs(old.is_compatible(Version(0, 1, 1, "rc.0")), False)

    def test_build_metadata_is_ignored_in_both_major_regimes(self):
        for major, minor, patch in ((1, 2, 3), (0, 1, 0)):
            with self.subTest(major=major):
                a = Version(major, minor, patch, build="a")
                b = Version(major, minor, patch, build="b")
                self.assertIs(a.is_compatible(b), True)
                self.assertIs(b.is_compatible(a), True)

    def test_absent_and_present_build_metadata_are_equivalent(self):
        for major in (0, 1):
            with self.subTest(major=major):
                plain = Version(major, 1, 0)
                built = Version(major, 1, 0, build="build.1")
                self.assertIs(plain.is_compatible(built), True)
                self.assertIs(built.is_compatible(plain), True)

    def test_non_version_arguments_raise_typeerror_for_both_major_regimes(self):
        wrong_values = ("wrongtype", "1.2.3", b"1.2.3", {"a": 2},
                        {"major": 1, "minor": 2, "patch": 3}, [],
                        (1, 2, 3), None, 7, object())
        for major in (0, 1):
            for wrong in wrong_values:
                with self.subTest(major=major, wrong=wrong):
                    with self.assertRaises(TypeError) as cm:
                        Version(major, 2, 3).is_compatible(wrong)
                    self.assertTrue(str(cm.exception).startswith("Expected a Version type"))

    def test_python_argument_binding_errors(self):
        old = Version(1, 2, 3)
        new = Version(1, 2, 4)
        with self.assertRaises(TypeError):
            old.is_compatible()
        with self.assertRaises(TypeError):
            old.is_compatible(new, new)
        with self.assertRaises(TypeError):
            old.is_compatible(candidate=new)
        with self.assertRaises(TypeError):
            old.is_compatible(new, other=new)

    def test_base_and_subclass_operands_are_accepted_in_both_directions(self):
        class CustomVersion(Version):
            pass

        base = Version(1, 0, 0)
        custom = CustomVersion(1, 0, 0)
        self.assertIs(base.is_compatible(custom), True)
        self.assertIs(custom.is_compatible(base), True)
        self.assertIs(custom.is_compatible(CustomVersion(1, 0, 1)), True)

    def test_major_zero_accepts_base_and_subclass_operands(self):
        class CustomVersion(Version):
            pass

        base = Version(0, 1, 0)
        custom = CustomVersion(0, 1, 0)
        self.assertIs(base.is_compatible(custom), True)
        self.assertIs(custom.is_compatible(base), True)
        self.assertIs(custom.is_compatible(CustomVersion(0, 1, 0)), True)

    def test_distinct_version_subclasses_are_accepted(self):
        class FirstVersion(Version):
            pass

        class SecondVersion(Version):
            pass

        self.assertIs(FirstVersion(1, 0, 0).is_compatible(
            SecondVersion(1, 1, 0)), True)
        self.assertIs(SecondVersion(0, 1, 0).is_compatible(
            FirstVersion(0, 1, 0)), True)

    def test_results_are_builtin_bool_and_operands_are_unchanged(self):
        cases = ((Version(1, 2, 3, "rc.0", "a"),
                  Version(1, 3, 0, "rc.0", "b"), True),
                 (Version(0, 1, 0, "rc.0", "a"),
                  Version(0, 1, 1, "rc.0", "b"), False))
        for old, new, expected in cases:
            with self.subTest(old=old, new=new):
                old_before = (old.major, old.minor, old.patch, old.prerelease, old.build)
                new_before = (new.major, new.minor, new.patch, new.prerelease, new.build)
                result = old.is_compatible(new)
                self.assertIs(type(result), bool)
                self.assertIs(result, expected)
                self.assertEqual((old.major, old.minor, old.patch,
                                  old.prerelease, old.build), old_before)
                self.assertEqual((new.major, new.minor, new.patch,
                                  new.prerelease, new.build), new_before)

    def test_method_docstring_describes_rules_and_contains_two_examples(self):
        self.assertIs(Version(1, 0, 0).is_compatible(Version(1, 0, 0)), True)
        doc = Version.is_compatible.__doc__ or ""
        lower = doc.lower()
        for term in ("major", "minor", "patch", "prerelease", "build", "typeerror"):
            with self.subTest(term=term):
                self.assertIn(term, lower)
        self.assertRegex(lower, r"\b(?:zero|0)\b")
        self.assertRegex(lower, r"\b(?:self|receiver|old|current)\b")
        self.assertRegex(lower, r"\b(?:other|candidate|new)\b")
        self.assertRegex(lower, r"\breplac(?:e|es|ement|ing)\b")
        examples = re.findall(
            r"(?m)^\s*>>>\s+[^\n]*\.is_compatible\([^\n]*\)\s*\n\s*(?:True|False)\s*$",
            doc,
        )
        self.assertGreaterEqual(len(examples), 2)
