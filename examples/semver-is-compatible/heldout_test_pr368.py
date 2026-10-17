"""Held-out tests: the upstream tests added by python-semver PR #368 (merge 467ea0c7), unchanged."""
import pytest

from semver import Version


@pytest.mark.parametrize(
    "old, new",
    [
        ((1, 2, 3), (1, 2, 3)),
        ((1, 2, 3), (1, 2, 4)),
        ((1, 2, 4), (1, 2, 3)),
        ((1, 2, 3, "rc.0"), (1, 2, 4, "rc.0")),
        ((0, 1, 0), (0, 1, 0)),
    ],
)
def test_should_succeed_compatible_match(old, new):
    old = Version(*old)
    new = Version(*new)
    assert old.is_compatible(new)


@pytest.mark.parametrize(
    "old, new",
    [
        ((1, 1, 0), (1, 0, 0)),
        ((2, 0, 0), (1, 5, 0)),
        ((1, 2, 3, "rc.1"), (1, 2, 3, "rc.0")),
        ((1, 2, 3, "rc.1"), (1, 2, 4, "rc.0")),
        ((0, 1, 0), (0, 1, 1)),
        ((1, 0, 0), (1, 0, 0, "rc1")),
        ((1, 0, 0, "rc1"), (1, 0, 0)),
    ],
)
def test_should_fail_compatible_match(old, new):
    old = Version(*old)
    new = Version(*new)
    assert not old.is_compatible(new)


@pytest.mark.parametrize(
    "wrongtype",
    [
        "wrongtype",
        dict(a=2),
        list(),
    ],
)
def test_should_fail_with_incompatible_type_for_compatible_match(wrongtype):
    with pytest.raises(TypeError, match="Expected a Version type .*"):
        v = Version(1, 2, 3)
        v.is_compatible(wrongtype)


def test_should_succeed_with_compatible_subclass_for_is_compatible():
    class CustomVersion(Version):
        ...

    assert CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0))
