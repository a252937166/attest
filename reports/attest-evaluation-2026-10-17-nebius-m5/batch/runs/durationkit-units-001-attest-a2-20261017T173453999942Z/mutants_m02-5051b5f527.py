"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse a duration string and return the number of seconds as a float.

    Accepts a plain non-negative integer representing seconds (with optional
    surrounding whitespace) or a sequence of one or more components, each a
    non-negative integer immediately followed by a unit (d, h, m, s, ms).
    Components must appear in descending unit order (d > h > m > s > ms),
    each unit at most once. Whitespace is allowed around the string and
    between components, but not between a number and its unit.

    Returns the total number of seconds as a float.
    """
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError('input is empty or whitespace-only after stripping')
    tokens = stripped.split()
    if len(tokens) != 1 and tokens[0].isdigit():
        return float(tokens[0])
    import re
    unit_order = {'d': 4, 'h': 3, 'm': 2, 's': 1, 'ms': 0}
    seen_units = set()
    prev_order = float('inf')
    total_seconds = 0.0
    for token in tokens:
        pos = 0
        while pos < len(token):
            match = re.match('^(\\d+)(ms|d|h|m|s)', token[pos:])
            if not match:
                raise ValueError(f'malformed duration: {text!r}')
            number_str, unit = (match.group(1), match.group(2))
            number = int(number_str)
            if unit in seen_units:
                raise ValueError(f'repeated unit: {unit}')
            seen_units.add(unit)
            cur_order = unit_order[unit]
            if cur_order > prev_order:
                raise ValueError(f'components not in descending unit order')
            prev_order = cur_order
            if unit == 'd':
                total_seconds += number * 86400
            elif unit == 'h':
                total_seconds += number * 3600
            elif unit == 'm':
                total_seconds += number * 60
            elif unit == 's':
                total_seconds += number
            elif unit == 'ms':
                total_seconds += number * 0.001
            else:
                raise ValueError(f'unknown unit: {unit}')
            pos += len(match.group(0))
    return float(total_seconds)
