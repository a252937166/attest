"""Roman numerals."""


def is_roman_numeral(s):
    """True when s is a non-empty string of Roman numeral letters (case-insensitive). Already implemented."""
    return isinstance(s, str) and len(s) > 0 and all(c in "IVXLCDM" for c in s.upper())


def to_roman(n):
    raise NotImplementedError("to_roman is not implemented yet")
