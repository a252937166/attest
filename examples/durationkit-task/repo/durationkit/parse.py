"""Duration parsing."""


def parse_duration(text: str) -> float:
    """Parse a duration string and return the number of seconds as a float.

    Only a plain non-negative integer number of seconds is accepted at the
    moment, for example ``"90"``. Surrounding whitespace is ignored.
    """
    if not isinstance(text, str):
        raise TypeError("duration must be a string")
    stripped = text.strip()
    if not stripped.isdigit():
        raise ValueError(f"unsupported duration: {text!r}")
    return float(stripped)
