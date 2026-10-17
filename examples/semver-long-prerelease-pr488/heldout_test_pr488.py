import pytest

from semver import Version, compare


# Held-out suite for the Attest task semver-long-prerelease-pr488: the tests that upstream pull request #488
# (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3) added to tests/test_compare.py, verbatim. Never shown to the implementer.



def test_should_compare_long_numeric_prerelease():
    value = "0.0.0-" + "1" * 5000
    assert Version.is_valid(value)
    version = Version.parse(value)
    assert version.compare(value) == 0
    assert compare(value, "0.0.0-2") == 1
    assert compare("0.0.0-2", value) == -1


@pytest.mark.parametrize(
    "lower,higher",
    [
        pytest.param("9" * 4999, "1" + "0" * 4999, id="digit-count"),
        pytest.param(
            "1" + "0" * 4998 + "1",
            "1" + "0" * 4998 + "2",
            id="equal-length",
        ),
        pytest.param("1" * 5000, "alpha", id="numeric-before-text"),
        pytest.param("alpha." + "1" * 5000, "alpha." + "1" * 5000 + ".1", id="prefix"),
    ],
)
def test_should_order_long_numeric_prereleases(lower, higher):
    low = Version.parse("0.0.0-" + lower)
    high = Version.parse("0.0.0-" + higher)
    assert low.compare(high) == -1
    assert high.compare(low) == 1
    assert sorted([high, low]) == [low, high]


def test_should_ignore_build_and_preserve_release_order_with_long_prerelease():
    version = Version.parse("0.0.0-" + "1" * 5000)
    assert version == version.replace(build="other")
    assert version < Version(0, 0, 0)


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ("0001", "1", 0),
        ("000", "0", 0),
        ("02", "10", -1),
        ("01.2", "1.2", 0),
        ("2a", "10a", 1),
        ("01a", "1a", -1),
        ("-1", "0", 1),
        ("", None, 0),
        ("\u0661\u0662", "12", 0),
        ("\uff11\uff12", "13", -1),
        ("1\u0662", "12", 0),
        ("\u0660\u0660\u0661", "1", 0),
    ],
)
def test_should_preserve_constructor_prerelease_comparison(left, right, expected):
    first = Version(0, 0, 0, prerelease=left)
    second = Version(0, 0, 0, prerelease=right)
    assert first.compare(second) == expected
    assert second.compare(first) == -expected
    assert first.prerelease == left
    assert second.prerelease == right


@pytest.mark.parametrize("prerelease", ["01", "01.2", "\u0661\u0662", "\uff11\uff12"])
def test_should_reject_noncanonical_prerelease_when_parsing(prerelease):
    with pytest.raises(ValueError):
        Version.parse("0.0.0-" + prerelease)


@pytest.mark.parametrize(
    "left,right", [("\u00b2", "2"), ("a.\u00b2", "b.0"), ("a.0", "b.\u00b2")]
)
def test_should_preserve_eager_invalid_unicode_digit_error(left, right):
    with pytest.raises(ValueError):
        Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right))


def test_should_compare_core_before_invalid_prerelease():
    assert Version(0, 0, 0, prerelease="\u00b2") < Version(1, 0, 0, prerelease="\u00b2")
