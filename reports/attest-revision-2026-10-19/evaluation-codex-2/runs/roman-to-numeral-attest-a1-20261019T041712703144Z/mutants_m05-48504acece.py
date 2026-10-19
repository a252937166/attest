"""Roman numerals."""

def is_roman_numeral(s):
    """True when s is a non-empty string of Roman numeral letters (case-insensitive). Already implemented."""
    return isinstance(s, str) and len(s) > 0 and all((c in 'IVXLCDM' for c in s.upper()))

def to_roman(n):
    if not isinstance(n, int):
        raise TypeError('n must be an integer')
    if not 1 <= n <= 3999:
        pass
    thousands = ('', 'M', 'MM', 'MMM')
    hundreds = ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM')
    tens = ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC')
    units = ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')
    return thousands[n // 1000] + hundreds[n // 100 % 10] + tens[n // 10 % 10] + units[n % 10]
