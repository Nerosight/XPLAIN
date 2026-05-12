"""ASCII art banner for the CLI.

Shown when the user runs `xplain` with no arguments or `xplain --list`.
Suppressed when stdout is not a TTY (pipes, redirects, CI), so piping into
other tools stays clean.
"""

from __future__ import annotations

from rich.console import Console


# Paste your FIGlet output between the triple-quotes below.
# IMPORTANT: keep the leading `r` so backslashes in the art are preserved.
_ART = r"""██╗  ██╗██████╗ ██╗      █████╗ ██╗███╗   ██╗
╚██╗██╔╝██╔══██╗██║     ██╔══██╗██║████╗  ██║
 ╚███╔╝ ██████╔╝██║     ███████║██║██╔██╗ ██║
 ██╔██╗ ██╔═══╝ ██║     ██╔══██║██║██║╚██╗██║
██╔╝ ██╗██║     ███████╗██║  ██║██║██║ ╚████║
╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝


"""

_TAGLINE = "decode the cryptic"

# Colors. Pick one for WORDMARK_COLOR. Common picks:
#   "bright_cyan"     - electric / hacker
#   "bright_green"    - matrix / terminal classic
#   "bright_magenta"  - cyberpunk
#   "bright_yellow"   - warm / attention
#   "bold blue"       - professional / corporate
#   "bright_red"      - aggressive / offensive-tool
WORDMARK_COLOR = "chartreuse1"
TAGLINE_STYLE = "dim italic"


def print_banner(console: Console | None = None) -> None:
    """Print the colored banner. No-op when stdout is not a real terminal."""
    console = console or Console()
    if not console.is_terminal:
        return

    # Skip if the terminal is too narrow for the art - prevents ugly wrap.
    art_width = max((len(line) for line in _ART.splitlines()), default=0)
    if console.width < art_width:
        return

    console.print(_ART, style=WORDMARK_COLOR, highlight=False)
    console.print(f"  {_TAGLINE}\n", style=TAGLINE_STYLE, highlight=False)
