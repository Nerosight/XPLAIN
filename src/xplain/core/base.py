"""Base classes and shared types for parsers.

Every parser returns a stream of `Annotation` objects pointing back at
character spans in the original input. Parsers do NOT know about colors,
terminals, JSON, or anything else - they just identify and explain spans.
That separation is what keeps adding new parsers cheap.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Annotation:
    """A single annotated span in the input.

    Attributes:
        start: offset into the original input string (inclusive).
        end: offset into the original input string (exclusive).
        label: short canonical name, e.g. "SERVICE_QUERY_CONFIG" or "owner read".
        short_code: the literal token from the input, e.g. "CC" or "r".
        description: full human explanation for the legend table.
        category: grouping used by the renderer to pick a color
            (e.g. "access_right", "principal", "permission", "section").
    """

    start: int
    end: int
    label: str
    short_code: str
    description: str
    category: str

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) < start ({self.start})")
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")


class Parser(ABC):
    """Base class for all format parsers."""

    name: str = ""              # subcommand name, e.g. "sddl"
    description: str = ""       # one-line summary for --list / --help
    example: str = ""           # an example input shown in error messages

    @abstractmethod
    def parse(self, text: str) -> Iterable[Annotation]:
        """Yield annotations for the given input.

        Implementations should yield in the order they discover spans;
        the renderer sorts them before display.
        """
        raise NotImplementedError
    def detect(self, text: str)-> float:
        """Confidence poll from each parser the format is 0.0 1.0"""
        return 0.0