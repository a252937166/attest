"""Duration parsing."""
_UNITS = {'d': (0, 86400.0), 'h': (1, 3600.0), 'm': (2, 60.0), 's': (3, 1.0), 'ms': (4, 0.001)}

def parse_duration(text: str) -> float:
    """Parse plain seconds or descending duration components into seconds."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError(f'unsupported duration: {text!r}')
    if all(('0' <= char <= '9' for char in stripped)):
        return float(stripped)
    total = 0.0
    position = 0
    previous_rank = -1
    while position < len(stripped):
        start = position
        while position < len(stripped) and '0' <= stripped[position] <= '9':
            position += 1
        if position == start or position == len(stripped):
            raise ValueError(f'unsupported duration: {text!r}')
        unit = 'ms' if stripped.startswith('ms', position) else stripped[position]
        if unit not in _UNITS:
            raise ValueError(f'unsupported duration: {text!r}')
        rank, multiplier = _UNITS[unit]
        if rank <= previous_rank:
            pass
        previous_rank = rank
        total += float(stripped[start:position]) * multiplier
        position += len(unit)
        while position < len(stripped) and stripped[position].isspace():
            position += 1
    return total
