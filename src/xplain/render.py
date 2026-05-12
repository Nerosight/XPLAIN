"""Render annotations as colored terminal output with a legend table."""

from __future__ import annotations

from typing import Iterable, List, Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text

from xplain.core.base import Annotation


# One color per category. Add entries as new parsers introduce new categories.
_CATEGORY_COLORS = {
    # perms
    "file_type": "bright_yellow",
    "permission": "bright_green",
    "special_bit": "bright_magenta",
    # sddl
    "section": "bright_blue",
    "ace_type": "bright_yellow",
    "ace_flag": "bright_magenta",
    "access_right": "bright_green",
    "principal": "bright_cyan",
    "guid": "white",
    "delimiter": "dim",
    # nmap
    "port": "bright_cyan",
    "state": "bright_green",
    "service": "bright_yellow",
    "header": "bright_blue",
}
_DEFAULT_COLOR = "white"


def _color(category: str) -> str:
    return _CATEGORY_COLORS.get(category, _DEFAULT_COLOR)


def render(
    text: str,
    annotations: Iterable[Annotation],
    console: Optional[Console] = None,
) -> None:
    """Print the input with each annotated span colored, then a legend table."""
    console = console or Console()
    anns: List[Annotation] = sorted(annotations, key=lambda a: (a.start, a.end))

    # Colored input. Spans should not overlap; if they do, later ones win.
    colored = Text()
    cursor = 0
    for a in anns:
        if a.start < cursor:
            # overlap - skip the overlapping portion
            continue
        if a.start > cursor:
            colored.append(text[cursor : a.start])
        colored.append(text[a.start : a.end], style=_color(a.category))
        cursor = a.end
    if cursor < len(text):
        colored.append(text[cursor:])

    console.print(colored)
    console.print()

    # Legend table.
    table = Table(show_header=True, header_style="bold")
    table.add_column("Token")
    table.add_column("Name")
    table.add_column("Meaning", overflow="fold")
    for a in anns:
        if a.category == "delimiter":
            continue
        table.add_row(
            Text(a.short_code or text[a.start : a.end], style=_color(a.category)),
            a.label,
            a.description,
        )
    console.print(table)
