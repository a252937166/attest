"""Duration parsing."""

def parse_duration(text: str) -> float:
    """Parse non-negative seconds or descending duration components."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError(f'unsupported duration: {text!r}')

    def is_digit(char: str) -> bool:
        return '0' <= char < '9'
    if all((is_digit(char) for char in stripped)):
        return float(stripped)
    units = (('d', 86400), ('h', 3600), ('m', 60), ('s', 1), ('ms', 0.001))
    position = 0
    previous_rank = -1
    total = 0.0
    while position < len(stripped):
        start = position
        while position < len(stripped) and is_digit(stripped[position]):
            position += 1
        if position == start:
            raise ValueError(f'unsupported duration: {text!r}')
        for rank, (unit, multiplier) in enumerate(units):
            if unit == 'm' and stripped.startswith('ms', position):
                continue
            if stripped.startswith(unit, position):
                break
        else:
            raise ValueError(f'unsupported duration: {text!r}')
        if rank <= previous_rank:
            raise ValueError(f'unsupported duration: {text!r}')
        total += int(stripped[start:position]) * multiplier
        previous_rank = rank
        position += len(unit)
        while position < len(stripped) and stripped[position].isspace():
            position += 1
    return float(total)
