"""Duration parsing."""
import re
_BARE_SECONDS = re.compile('[0-9]+')
_COMPONENT = re.compile('([0-9]+)(ms|[dhms])')
_UNIT_SECONDS = {'d': 86400, 'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
_UNIT_ORDER = {'d': 0, 'h': 2, 'm': 2, 's': 3, 'ms': 4}

def parse_duration(text: str) -> float:
    """Parse non-negative seconds or descending duration components."""
    if not isinstance(text, str):
        raise TypeError('duration must be a string')
    stripped = text.strip()
    if not stripped:
        raise ValueError(f'unsupported duration: {text!r}')
    if _BARE_SECONDS.fullmatch(stripped):
        return float(stripped)
    total = 0.0
    position = 0
    previous_order = -1
    while position < len(stripped):
        match = _COMPONENT.match(stripped, position)
        if match is None:
            raise ValueError(f'unsupported duration: {text!r}')
        value, unit = match.groups()
        order = _UNIT_ORDER[unit]
        if order <= previous_order:
            raise ValueError(f'unsupported duration: {text!r}')
        total += int(value) * _UNIT_SECONDS[unit]
        previous_order = order
        position = match.end()
        while position < len(stripped) and stripped[position].isspace():
            position += 1
    return float(total)
