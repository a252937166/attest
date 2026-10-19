"""Duration parsing."""
_UNITS = {'d': 86400.0, 'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
_ORDER = {unit: index for index, unit in enumerate(_UNITS)}

def parse_duration(text: str) -> float:
    """Parse integer seconds or ordered duration components into seconds."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError('duration is empty')

    def is_ascii_digit(char: str) -> bool:
        return '0' <= char <= '9'
    if all((is_ascii_digit(char) for char in stripped)):
        return float(stripped)
    total = 0.0
    position = 0
    previous_order = -1
    while position < len(stripped):
        start = position
        while position < len(stripped) and is_ascii_digit(stripped[position]):
            position += 1
        if position == start:
            raise ValueError(f'invalid duration: {text!r}')
        if stripped.startswith('ms', position):
            unit = 'ms'
        elif position < len(stripped) and stripped[position] in 'dhms':
            unit = stripped[position]
        else:
            raise ValueError(f'invalid duration: {text!r}')
        order = _ORDER[unit]
        if order <= previous_order:
            raise ValueError(f'duration units out of order: {text!r}')
        previous_order = order
        total += int(stripped[start:position]) / _UNITS[unit]
        position += len(unit)
        while position < len(stripped) and stripped[position].isspace():
            position += 1
    return float(total)
