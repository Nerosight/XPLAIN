"""Shared token / span helpers used by parsers."""

from __future__ import annotations

from typing import Iterator, Tuple


def chunked(text: str, size: int, start: int = 0) -> Iterator[Tuple[int, str]]:
    """Yield (offset, chunk) pairs of fixed size from text[start:].

    Useful for parsers walking fixed-width fields, e.g. SDDL right codes
    (two chars each) or Linux permission strings (three chars per triplet).
    """
    i = start
    n = len(text)
    while i < n:
        yield i, text[i : i + size]
        i += size
