"""Tests for the banner module."""

from __future__ import annotations

import io

from rich.console import Console

from xplain.banner import print_banner, _ART, _TAGLINE


def test_banner_skipped_on_non_tty():
    """When stdout isn't a real terminal, the banner must be silent."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False)
    print_banner(console)
    assert buf.getvalue() == ""


def test_banner_printed_on_tty():
    """When stdout IS a terminal, both wordmark and tagline appear."""
    buf = io.StringIO()
    # force_terminal=True simulates a TTY for testing.
    console = Console(file=buf, force_terminal=True, width=120)
    print_banner(console)
    out = buf.getvalue()
    assert _TAGLINE in out
    # Sanity check that some of the art landed.
    art_first_visible = next(line.strip() for line in _ART.splitlines() if line.strip())
    assert art_first_visible[:3] in out


def test_banner_skipped_when_terminal_too_narrow():
    """If the terminal is narrower than the art, skip rather than wrap ugly."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=10)
    print_banner(console)
    assert buf.getvalue() == ""
