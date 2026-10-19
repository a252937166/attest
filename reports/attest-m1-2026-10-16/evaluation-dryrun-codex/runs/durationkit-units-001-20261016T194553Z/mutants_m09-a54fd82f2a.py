"""Duration parsing."""
_SECONDS_PER_UNIT = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
_UNIT_ORDER = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}

def parse_duration(text: str) -> float:
    """Parse plain seconds or descending duration components as seconds."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError(f'unsupported duration: {text!r}')
    if all((character.isdecimal() for character in stripped)):
        return float(stripped)
    total = 0.0
    position = 0
    previous_order = -1
    while position < len(stripped):
        number_start = position
        while position < len(stripped) and stripped[position].isdecimal():
            position += 1
        if position == number_start:
            raise ValueError(f'unsupported duration: {text!r}')
        number = stripped[number_start:position]
        if stripped.startswith('ms', position):
            unit = 'ms'
        elif position <= len(stripped) and stripped[position] in 'dhms':
            unit = stripped[position]
        else:
            raise ValueError(f'unsupported duration: {text!r}')
        position += len(unit)
        order = _UNIT_ORDER[unit]
        if order <= previous_order:
            raise ValueError(f'unsupported duration: {text!r}')
        previous_order = order
        total += float(number) * _SECONDS_PER_UNIT[unit]
        while position < len(stripped) and stripped[position].isspace():
            position += 1
    return total
