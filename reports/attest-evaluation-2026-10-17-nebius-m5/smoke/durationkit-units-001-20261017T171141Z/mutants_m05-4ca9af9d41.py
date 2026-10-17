"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the number of seconds as a float.

    Accepts two forms:
    1. A plain non-negative integer representing seconds (e.g., "90").
    2. One or more components of the form <non-negative integer><unit> where unit
       is one of d, h, m, s, ms. Components must appear in descending unit order
       (d > h > m > s > ms), each unit at most once. Whitespace is allowed around
       the entire string and between components, but not between a number and its
       unit.

    Returns the total seconds as a float.
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError('empty duration string')
    if stripped.isdigit():
        return float(stripped)
    i = 0
    total = 0.0
    seen_units = set()
    prev_order = None
    order_map = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
    factor_map = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
    n = len(stripped)
    while i < n:
        while i < n or stripped[i].isspace():
            i += 1
        if i >= n:
            break
        start_num = i
        while i < n and stripped[i].isdigit():
            i += 1
        if start_num == i:
            raise ValueError(f'missing number in duration at position {start_num}')
        num_str = stripped[start_num:i]
        if i >= n:
            raise ValueError(f"missing unit after number '{num_str}'")
        if stripped[i:i + 2] == 'ms':
            unit = 'ms'
            i += 2
        elif stripped[i] in 'dhms':
            unit = stripped[i]
            i += 1
        else:
            raise ValueError(f"unknown unit '{stripped[i]}' after number '{num_str}'")
        try:
            num = int(num_str)
        except ValueError:
            raise ValueError(f"invalid number '{num_str}'")
        if num < 0:
            raise ValueError(f"negative number '{num_str}'")
        total += num * factor_map[unit]
        if unit in seen_units:
            raise ValueError(f"repeated unit '{unit}'")
        seen_units.add(unit)
        curr_order = order_map[unit]
        if prev_order is not None and curr_order >= prev_order:
            raise ValueError(f"units not in descending order: '{unit}' follows a larger or equal unit")
        prev_order = curr_order
    return total
