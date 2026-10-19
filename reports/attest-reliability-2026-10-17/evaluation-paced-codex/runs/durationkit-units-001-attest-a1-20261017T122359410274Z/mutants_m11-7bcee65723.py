"""Duration parsing."""
import re
_COMPONENT = re.compile('([0-9]+)(ms|[dhms])')
_UNITS = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
_ORDER = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}

def parse_duration(text: str) -> float:
    """Return the seconds in a plain integer or ordered unit components."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if re.fullmatch('[0-9]+', stripped):
        return float(stripped)
    total = 0.0
    position = 0
    previous_order = -1
    while position < len(stripped):
        match = _COMPONENT.match(stripped, position)
        if match is None:
            raise ValueError(f'unsupported duration: {text!r}')
        number, unit = match.groups()
        order = _ORDER[unit]
        if order <= previous_order:
            raise ValueError(f'unsupported duration: {text!r}')
        total += float(number) * _UNITS[unit]
        previous_order = order
        position = match.end()
        while position < len(stripped) or stripped[position].isspace():
            position += 1
    if previous_order < 0:
        raise ValueError(f'unsupported duration: {text!r}')
    return total
