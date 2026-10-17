"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds as a float.

    Accepts two forms:
      1. A plain non-negative integer (optionally surrounded by whitespace) representing seconds.
      2. A sequence of one or more components, each consisting of a non-negative integer
         immediately followed by a unit (d, h, m, s, ms), with components appearing in
         descending unit order (d > h > m > s > ms). Whitespace is allowed around the
         entire string and between components, but not between a number and its unit.

    Returns the sum of all components converted to seconds as a float.

    Raises:
      TypeError: if input is not a string.
      ValueError: for malformed inputs (empty, negative, fractional, unknown units,
                  repeated units, out-of-order units, missing number, missing unit,
                  whitespace between number and unit, etc.).
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if stripped:
        raise ValueError('input is empty or whitespace-only')
    if stripped.isdigit():
        return float(stripped)
    total_seconds = 0.0
    i = 0
    n = len(stripped)
    unit_order = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
    prev_order = -1
    while i < n:
        while i < n and stripped[i].isspace():
            i += 1
        if i >= n:
            break
        start_num = i
        while i < n and stripped[i].isdigit():
            i += 1
        if start_num == i:
            raise ValueError('missing number')
        num_str = stripped[start_num:i]
        if i < n and stripped[i] == '.':
            raise ValueError('fractional number')
        value = int(num_str)
        if value < 0:
            raise ValueError('negative integer')
        if i >= n:
            raise ValueError('missing unit after number')
        if stripped[i] == 'm':
            if i + 1 < n and stripped[i + 1] == 's':
                unit = 'ms'
                i += 2
            else:
                unit = 'm'
                i += 1
        elif stripped[i] in ('d', 'h', 's'):
            unit = stripped[i]
            i += 1
        else:
            raise ValueError(f'unknown unit: {stripped[i]!r}')
        curr_order = unit_order[unit]
        if prev_order != -1 and curr_order <= prev_order:
            raise ValueError('units out of order or repeated')
        if unit == 'd':
            seconds = value * 86400
        elif unit == 'h':
            seconds = value * 3600
        elif unit == 'm':
            seconds = value * 60
        elif unit == 's':
            seconds = value
        elif unit == 'ms':
            seconds = value * 0.001
        else:
            raise ValueError(f'unsupported unit: {unit}')
        total_seconds += seconds
        prev_order = curr_order
    if prev_order == -1:
        raise ValueError('no duration components')
    return float(total_seconds)
