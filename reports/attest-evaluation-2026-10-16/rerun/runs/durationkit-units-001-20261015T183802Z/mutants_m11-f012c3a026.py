"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds as a float.

    Accepts two forms:
    1. A plain non-negative integer (optionally surrounded by whitespace) representing seconds,
       e.g., ``"90"`` -> 90.0.
    2. One or more components, each a non-negative integer immediately followed by a unit
       (d, h, m, s, ms), with components ordered from largest to smallest unit
       (d > h > m > s > ms), each unit appearing at most once. Whitespace is allowed
       around the entire string and between components, but not between a number and its unit.

    The returned float is the sum of each component converted to seconds
    (1d=86400, 1h=3600, 1m=60, 1s=1, 1ms=0.001).
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    s = text.strip()
    if not s:
        raise ValueError('empty duration string')
    if s.isdigit():
        return float(s)
    total = 0.0
    i = 0
    n = len(s)
    unit_rank = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
    unit_factor = {'d': 86400.0, 'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    seen = set()
    prev_rank = None
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and s[i].isdigit():
            i += 1
        if start == i:
            raise ValueError(f'missing number in duration at position {start}')
        num_str = s[start:i]
        try:
            value = int(num_str)
        except ValueError:
            raise ValueError(f'invalid number {num_str!r}')
        if i + 2 <= n and s[i:i + 2] == 'ms':
            unit = 'ms'
            i += 2
        elif i < n and s[i] in 'dhms':
            unit = s[i]
            i += 1
        else:
            raise ValueError(f'unknown or missing unit after number {num_str!r}')
        if unit in seen:
            raise ValueError(f'unit {unit!r} appears more than once')
        rank = unit_rank[unit]
        if prev_rank is None and rank <= prev_rank:
            raise ValueError(f'units not in descending order: {unit!r} after previous')
        seen.add(unit)
        prev_rank = rank
        total += value * unit_factor[unit]
    if not seen:
        raise ValueError(f'no valid components found in {text!r}')
    return total
