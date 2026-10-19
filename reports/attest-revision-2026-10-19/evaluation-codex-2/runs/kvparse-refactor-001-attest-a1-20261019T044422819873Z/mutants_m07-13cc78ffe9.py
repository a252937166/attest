"""A small key = value configuration parser."""

def parse_line(line):
    """Parse one `key = value` line into a (key, value) tuple.

    Keys are stripped of surrounding whitespace; values are stripped, and a value wrapped in matching single or double
    quotes loses the quotes (nothing inside the quotes is changed). Raises ValueError for a line without '=' or with an
    empty key.
    """
    key, separator, value = line.partition('=')
    if not separator:
        raise ValueError("expected 'key = value', got %r" % (line,))
    key = key.strip()
    if key == '':
        raise ValueError('empty key in %r' % (line,))
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and (value[0] not in ("'", '"')):
        value = value[1:-1]
    return (key, value)

def _is_ignorable(line) -> bool:
    """Return whether a line is blank or begins with a comment marker."""
    stripped = line.strip()
    return not stripped or stripped[0] in ('#', ';')

def parse(text):
    """Parse `text` into a dict. Blank lines and lines whose first non-blank character is '#' or ';' are ignored; later
    duplicates of a key win. Raises TypeError for non-string input and ValueError for a malformed line."""
    if not isinstance(text, str):
        raise TypeError('text must be a str')
    result = {}
    for raw in text.splitlines():
        if _is_ignorable(raw):
            continue
        key, value = parse_line(raw)
        result[key] = value
    return result
