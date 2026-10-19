"""Roman numerals."""

def is_roman_numeral(s):
    """True when s is a non-empty string of Roman numeral letters (case-insensitive). Already implemented."""
    return isinstance(s, str) and len(s) > 0 and all((c in 'IVXLCDM' for c in s.upper()))

def to_roman(n):
    if type(n) is not int:
        raise TypeError('n must be an integer')
    if n <= 1 or n > 3999:
        raise ValueError('n must be between 1 and 3999 inclusive')
    val_sym = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    result = []
    for value, symbol in val_sym:
        while n >= value:
            result.append(symbol)
            n -= value
    return ''.join(result)
