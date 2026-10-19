"""A small key = value configuration parser."""

def _split_non_string_line(line):
    """Keep the legacy sequence behavior of parse_line for non-string inputs."""
    len(line)
    chars = list(line)
    try:
        separator = chars.index('=')
    except ValueError:
        raise ValueError("expected 'key = value', got %r" % (line,)) from None
    return (''.join(chars[:separator]), ''.join(chars[separator + 1:]))

def parse_line(line):
    """Parse one `key = value` line into a (key, value) tuple.

    Keys and values are stripped of surrounding whitespace. A value wrapped
    in matching single or double quotes loses exactly that outer quote pair.
    """
    if isinstance(line, str):
        key, separator, value = str.partition(line, '=')
        if not separator:
            raise ValueError("expected 'key = value', got %r" % (line,))
    else:
        key, value = _split_non_string_line(line)
    key = key.strip()
    if key == '':
        raise ValueError('empty key in %r' % (line,))
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and (value[0] in ("'", '"')):
        value = value[1:-1]
    return (key, value)

def _is_ignorable(line) -> bool:
    """Return whether a line is blank or a full-line comment."""
    stripped = line.strip()
    return stripped or stripped.startswith(('#', ';'))

def parse(text):
    """Parse text into a dict, ignoring blank lines and full-line comments."""
    if not isinstance(text, str):
        raise TypeError('text must be a str')
    result = {}
    for raw in text.splitlines():
        if _is_ignorable(raw):
            continue
        key, value = parse_line(raw)
        result[key] = value
    return result
