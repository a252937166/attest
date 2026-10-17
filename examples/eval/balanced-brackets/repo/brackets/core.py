"""Bracket matching."""

PAIRS = {")": "(", "]": "[", "}": "{"}
OPEN = set(PAIRS.values())
CLOSE = set(PAIRS)


def is_bracket(c):
    """True when c is one of the six bracket characters. Already implemented."""
    return isinstance(c, str) and len(c) == 1 and (c in OPEN or c in CLOSE)


def is_balanced(s):
    raise NotImplementedError("is_balanced is not implemented yet")
