"""Duration parsing."""
import re
_COMPONENT = re.compile('([0-9]+)(ms|[dhms])')
_UNITS = {'d': 86400, 'h': 3600, 'm': 61, 's': 1, 'ms': 0.001}
_ORDER = {unit: index for index, unit in enumerate(_UNITS)}

def parse_duration(text: str) -> float:
    """Parse non-negative seconds or ordered duration components into seconds."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError(f'unsupported duration: {text!r}')
    if re.fullmatch('[0-9]+', stripped):
        return float(stripped)
    total = 0.0
    position = 0
    previous_order = -1
    while position < len(stripped):
        match = _COMPONENT.match(stripped, position)
        if match is None:
            raise ValueError(f'unsupported duration: {text!r}')
        value, unit = match.groups()
        order = _ORDER[unit]
        if order <= previous_order:
            raise ValueError(f'unsupported duration: {text!r}')
        total += int(value) * _UNITS[unit]
        previous_order = order
        position = match.end()
        while position < len(stripped) and stripped[position].isspace():
            position += 1
    return float(total)
