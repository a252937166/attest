"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the number of seconds as a float.

    Accepts either a plain non-negative integer (seconds) or a sequence of
    components. A component is a non-negative integer immediately followed by a
    unit suffix: 'd' (days), 'h' (hours), 'm' (minutes), 's' (seconds), or
    'ms' (milliseconds). Components must appear in descending unit order (d >
    h > m > s > ms), each unit at most once. Whitespace is allowed around the
    entire string and between components, but not between a number and its unit.
    The function computes the total seconds (1d = 86400s, 1h = 3600s, 1m = 60s,
    1s = 1s, 1ms = 0.001s) and returns the sum as a float.
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    s = text.strip()
    if not s:
        raise ValueError('empty duration')
    if s.isdigit():
        return float(s)
    i = 0
    total = 0.0
    seen_units = set()
    prev_rank = -1
    rank = {'d': 1, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
    multipliers = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
    while i < len(s):
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            break
        start_num = i
        while i < len(s) and s[i].isdigit():
            i += 1
        if start_num == i:
            raise ValueError('missing number in duration')
        num_str = s[start_num:i]
        if i < len(s) and s[i] == '.':
            raise ValueError('fractional number not allowed')
        if i >= len(s):
            raise ValueError('missing unit after number')
        unit = None
        if s[i] == 'm' and i + 1 < len(s) and (s[i + 1] == 's'):
            unit = 'ms'
            i += 2
        elif s[i] in 'dhms':
            unit = s[i]
            i += 1
        else:
            raise ValueError(f"unknown unit '{s[i]}'")
        try:
            num = int(num_str)
        except ValueError:
            raise ValueError('invalid number')
        if num < 0:
            raise ValueError('negative number')
        total += num * multipliers[unit]
        r = rank[unit]
        if unit in seen_units:
            raise ValueError('repeated unit')
        if r <= prev_rank:
            raise ValueError('units out of order')
        seen_units.add(unit)
        prev_rank = r
    if i != len(s):
        raise ValueError('invalid duration format')
    return total
