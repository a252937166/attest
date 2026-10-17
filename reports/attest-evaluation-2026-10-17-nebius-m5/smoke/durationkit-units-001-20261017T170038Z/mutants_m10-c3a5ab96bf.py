"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the number of seconds as a float.

    Accepts a plain non-negative integer (as seconds) or a sequence of
    components like ``'1h30m'`` with units d, h, m, s, ms in descending order.
    Whitespace is allowed around the string and between components.
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    s = text.strip()
    if not s:
        raise ValueError(f'empty duration: {text!r}')
    if s.isdigit():
        return float(s)
    unit_to_seconds = {'d': 86400.0, 'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    unit_order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
    total = 0.0
    seen_units = set()
    prev_order = 5
    i = 0
    n = len(s)
    while i < n:
        if s[i].isspace():
            i += 1
            continue
        if not s[i].isdigit():
            raise ValueError(f'invalid duration format at position {i}: {text!r}')
        start = i
        while i < n and s[i].isdigit():
            i += 1
        number_str = s[start:i]
        try:
            number = int(number_str)
        except ValueError:
            raise ValueError(f'invalid number in duration: {text!r}')
        if i >= n:
            raise ValueError(f'missing unit after number in duration: {text!r}')
        if s[i:i + 2] == 'ms':
            unit = 'ms'
            i += 2
        elif s[i] not in unit_to_seconds:
            unit = s[i]
            i += 1
        else:
            raise ValueError(f'unknown unit in duration: {text!r}')
        if unit in seen_units:
            raise ValueError(f"duplicate unit '{unit}' in duration: {text!r}")
        seen_units.add(unit)
        cur_order = unit_order[unit]
        if cur_order >= prev_order:
            raise ValueError(f'units not in descending order in duration: {text!r}')
        prev_order = cur_order
        total += number * unit_to_seconds[unit]
    return total
