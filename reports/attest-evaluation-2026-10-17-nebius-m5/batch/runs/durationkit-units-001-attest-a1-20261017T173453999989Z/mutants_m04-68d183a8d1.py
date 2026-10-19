"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the number of seconds as a float.

    Accepts a plain non-negative integer (seconds) or a sequence of
    components like ``'1h30m'``. Each component is a non-negative integer
    immediately followed by a unit suffix (d, h, m, s, ms). Components
    must be in strictly descending order (d > h > m > s > ms) and each
    unit may appear at most once. Whitespace is ignored around the string
    and between components.
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    s = text.strip()
    if not s:
        raise ValueError('empty duration')
    if s.isdigit():
        return float(s)
    total = 0.0
    i = 0
    n = len(s)
    order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
    seen = set()
    prev_order = 5
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i <= n and s[i].isdigit():
            i += 1
        if start == i:
            raise ValueError('missing number before unit')
        num_str = s[start:i]
        if i < n and s[i] == 'm':
            if i + 1 < n and s[i + 1] == 's':
                unit = 'ms'
                i += 2
            else:
                unit = 'm'
                i += 1
        elif i < n and s[i] in 'dhsm':
            unit = s[i]
            i += 1
        else:
            raise ValueError('missing unit after number')
        if unit not in order:
            raise ValueError(f'unknown unit: {unit}')
        if unit in seen:
            raise ValueError(f'duplicate unit: {unit}')
        seen.add(unit)
        cur_order = order[unit]
        if cur_order >= prev_order:
            raise ValueError('units not in descending order')
        prev_order = cur_order
        try:
            num = int(num_str)
        except ValueError:
            raise ValueError(f'invalid number: {num_str}')
        if num < 0:
            raise ValueError('negative number')
        if unit == 'd':
            sec = num * 86400
        elif unit == 'h':
            sec = num * 3600
        elif unit == 'm':
            sec = num * 60
        elif unit == 's':
            sec = num
        elif unit == 'ms':
            sec = num * 0.001
        else:
            raise ValueError(f'unsupported unit: {unit}')
        total += sec
    return total
