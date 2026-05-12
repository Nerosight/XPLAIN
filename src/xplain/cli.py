"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from xplain import __version__, registry
from xplain.render import render


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


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
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
