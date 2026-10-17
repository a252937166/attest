"""URL slugs."""

import re

_NOT_ALNUM = re.compile(r"[^a-z0-9]")


def slugify(text):
    """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    return _NOT_ALNUM.sub("-", text.lower())
