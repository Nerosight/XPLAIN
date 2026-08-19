"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from wheel.cli import parser

from tests.test_perms import test_cli_accepts_dash_prefixed_input
from xplain import __version__, registry
from xplain.render import render

_Confident = 0.6
_MEHH = 0.3
_TOP_FLAGS = {"--list", "--version", "-h", "--help"}

def _PickOne(ranked):
    if not ranked:
        return None
    best, best_score = ranked[0]
    if best_score < _Confident:
        return None
    if len(ranked) > 1 and best_score - ranked[1][1] < _MEHH:
        return None
    return best

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="xplain",
        description="Annotate and explain cryptic command output.",
    )
    p.add_argument("--version", action="version", version=f"xplain {__version__}")
    p.add_argument(
        "--list",
        action="store_true",
        help="list available parsers and exit",
    )

    sub = p.add_subparsers(dest="parser", metavar="<parser>")
    for parser in registry.all_parsers():
        sp = sub.add_parser(
            parser.name,
            help=parser.description,
            description=f"{parser.description}\n\nExample: xplain {parser.name} '{parser.example}'",
        )
        sp.add_argument(
            "input",
            nargs="?",
            help="input string (or pipe via stdin if omitted)",
        )
    return p


def _read_input(arg: Optional[str]) -> str:
    if arg is not None:
        return arg
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def _preprocess_argv(argv: List[str]) -> List[str]:
    """Insert '--' before a subcommand's input argument when it starts with '-'.

    Without this, argparse interprets things like '-rwsr-xr-x' or '-rw-r--r--'
    as unknown flags. Many of the formats this tool decodes legitimately start
    with '-' (regular-file permission strings, for one), so we accommodate.
    """
    parser_names = set(registry.names())
    for i, arg in enumerate(argv):
        if arg in parser_names and i + 1 < len(argv):
            nxt = argv[i + 1]
            if nxt.startswith("-") and nxt != "--":
                return argv[: i + 1] + ["--"] + argv[i + 1 :]
            break
    return argv

def _run_detected(text: str) -> int:
    text  = text.strip()
    if not text:
        print("No input :O.", file=sys.stderr)
        return 2
    ranked = registry.all_detect(text)
    parser = _PickOne(ranked) ## Decicde which parser is going to be the ONE

    if parser is None:
        _report_candidate(ranked)
        return 4
    print(f"Detected: {parser.description}", file=sys.stderr)
    try:
        annotations = list(parser.parse(text))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    render(text, annotations)
    return 0

##List the parsers that the user wants and explain to them, we couldn't auto-detect
def _report_candidate(ranked) -> None:
    if not ranked:
        print("error: could not identify this format.", file=sys.stderr)
        print("try one explicitly:", file=sys.stderr)
        candidates = registry.all_parsers()
    else:
        print("error: ambiguous input. best guesses:", file=sys.stderr)
        candidates = [p for p, _ in ranked]

    for p in candidates:
        print(f"    xplain {p.name:8} {p.description}", file=sys.stderr)


def main(argv = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] not in registry.names() and argv[0] not in _TOP_FLAGS:
        return _run_detected(" ".join(argv)) ## Will write run detected soon
    argv = _preprocess_argv(argv)
    arg_parser = _build_parser()
    args = arg_parser.parse_args(argv)

    if args.list:
        from xplain.banner import print_banner
        print_banner()
        for parser in registry.all_parsers():
            print(f"  {parser.name:10} {parser.description}")
        return 0

    if not args.parser:
        from xplain.banner import print_banner
        print_banner()
        arg_parser.print_help()
        return 1

    parser = registry.get(args.parser)
    text = _read_input(args.input)
    if not text:
        print(
            f"error: no input given. example: xplain {parser.name} '{parser.example}'",
            file=sys.stderr,
        )
        return 2

    text = text.strip()
    try:
        annotations = list(parser.parse(text))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    render(text, annotations)
    return 0


if __name__ == "__main__":
    sys.exit(main())
