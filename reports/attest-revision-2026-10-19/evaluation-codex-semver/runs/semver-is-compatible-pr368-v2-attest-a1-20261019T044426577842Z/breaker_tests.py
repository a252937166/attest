import unittest

import semver
from semver.version import Version


class TestCompatibilityBreaker(unittest.TestCase):
    def test_nonzero_major_truth_table(self):
        for major in (1, 17):
            for receiver_minor in (0, 2, 9):
                for candidate_minor in (0, 2, 9):
                    for receiver_patch, candidate_patch in ((0, 99), (99, 0)):
                        receiver = Version(major, receiver_minor, receiver_patch, "rc.2", "left")
                        candidate = Version(major, candidate_minor, candidate_patch, "rc.2", "right")
                        result = receiver.is_compatible(candidate)
                        self.assertIs(type(result), bool)
                        self.assertEqual(result, candidate_minor >= receiver_minor)

    def test_zero_major_truth_table(self):
        for receiver_minor in (0, 2, 9):
            for receiver_patch in (0, 5, 99):
                for candidate_minor in (0, 2, 9):
                    for candidate_patch in (0, 5, 99):
                        receiver = Version(0, receiver_minor, receiver_patch, "rc.2", "left")
                        candidate = Version(0, candidate_minor, candidate_patch, "rc.2", "right")
                        result = receiver.is_compatible(candidate)
                        self.assertIs(type(result), bool)
                        self.assertEqual(
                            result,
                            receiver_minor == candidate_minor and receiver_patch == candidate_patch,
                        )

    def test_major_mismatch_cannot_be_rescued_by_other_fields(self):
        for receiver_major, candidate_major in ((0, 1), (1, 0), (1, 2), (17, 1)):
            receiver = Version(receiver_major, 0, 99, "rc.2", "same")
            candidate = Version(candidate_major, 99, 0, "rc.2", "same")
            self.assertIs(receiver.is_compatible(candidate), False)
            self.assertIs(candidate.is_compatible(receiver), False)

    def test_prerelease_equality_is_exact_across_minor_changes(self):
        values = (None, "", "rc.1", "RC.1")
        for receiver_prerelease in values:
            for candidate_prerelease in values:
                receiver = Version(3, 1, 99, receiver_prerelease, "left")
                candidate = Version(3, 2, 0, candidate_prerelease, "right")
                self.assertIs(
                    receiver.is_compatible(candidate),
                    receiver_prerelease == candidate_prerelease,
                )

    def test_build_changes_never_change_the_answer(self):
        cases = (
            (Version(0, 4, 7, "rc.1"), Version(0, 4, 7, "rc.1"), True),
            (Version(0, 4, 7, "rc.1"), Version(0, 4, 8, "rc.1"), False),
            (Version(5, 4, 99, "rc.1"), Version(5, 5, 0, "rc.1"), True),
            (Version(5, 4, 99, "rc.1"), Version(5, 3, 0, "rc.1"), False),
        )
        for receiver, candidate, expected in cases:
            self.assertIs(receiver.is_compatible(candidate), expected)
            with_build = Version(
                candidate.major, candidate.minor, candidate.patch,
                candidate.prerelease, "changed.build",
            )
            self.assertIs(receiver.is_compatible(with_build), expected)

    def test_additional_invalid_types_have_exact_error(self):
        invalid = (True, 1.5, 2j, set(), frozenset(), range(3), Version, NotImplemented, Ellipsis)
        for receiver in (Version(0, 1, 2), Version(8, 1, 2)):
            for other in invalid:
                with self.assertRaises(TypeError) as caught:
                    receiver.is_compatible(other)
                self.assertEqual(
                    str(caught.exception),
                    "Expected a Version type but got " + str(type(other)),
                )

    def test_public_class_calls_and_subclass_membership(self):
        class First(Version):
            pass

        class Second(Version):
            pass

        receiver = First(0, 2, 3, "rc", "one")
        candidate = Second(0, 2, 3, "rc", "two")
        for public_class in (semver.Version, semver.VersionInfo, Version):
            self.assertIs(public_class.is_compatible(receiver, other=candidate), True)
            self.assertIs(public_class.is_compatible(candidate, receiver), True)
        self.assertIs(type(receiver.is_compatible(Version(0, 2, 4, "rc"))), bool)
        self.assertIs(receiver.is_compatible(Version(0, 2, 4, "rc")), False)

    def test_calls_preserve_every_stored_component(self):
        receiver = Version(7, 2, 9, "rc.1", "left")
        compatible = Version(7, 3, 0, "rc.1", "right")
        incompatible = Version(7, 1, 0, "rc.1", "other")
        zero = Version(0, 2, 9, "rc.1", "zero")
        operands = (receiver, compatible, incompatible, zero)
        before = tuple(
            (v.major, v.minor, v.patch, v.prerelease, v.build) for v in operands
        )
        self.assertIs(receiver.is_compatible(compatible), True)
        self.assertIs(receiver.is_compatible(incompatible), False)
        self.assertIs(zero.is_compatible(receiver), False)
        with self.assertRaises(TypeError):
            receiver.is_compatible(compatible.to_dict())
        after = tuple(
            (v.major, v.minor, v.patch, v.prerelease, v.build) for v in operands
        )
        self.assertEqual(after, before)
