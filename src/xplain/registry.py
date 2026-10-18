"""Parser registry. All parsers are registered here at import time."""

from __future__ import annotations

from typing import Dict, List

from xplain.core.base import Parser
from xplain.parsers.nmap import NmapParser
from xplain.parsers.perms import PermsParser
from xplain.parsers.sddl import SddlParser


_PARSERS: Dict[str, Parser] = {}


def _register(parser: Parser) -> None:
    if parser.name in _PARSERS:
        raise ValueError(f"duplicate parser name: {parser.name!r}")
    _PARSERS[parser.name] = parser


_register(PermsParser())
_register(SddlParser())
_register(NmapParser())


def get(name: str) -> Parser:
    if name not in _PARSERS:
        raise KeyError(name)
    return _PARSERS[name]


def names() -> List[str]:
    return sorted(_PARSERS.keys())


def all_parsers() -> List[Parser]:
    return [_PARSERS[n] for n in names()]
