"""Format detection: work out which parser should handle unlabelled input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple, Optional, Sequence, Tuple, Union

from xplain import registry
from xplain.core.base import Parser


# A lone Candidate is Chosen at or above this Confidence.
_LONE_FLOOR = 0.3
# With rivals, the best Candidate needs this Confidence and this lead.
_CONFIDENT = 0.6
_MARGIN = 0.3
# Absorbs float error so a lead of exactly _MARGIN counts (0.7 - 0.4 < 0.3).
_TOLERANCE = 1e-9


class Candidate(NamedTuple):
    """A parser that gave the input a Confidence above zero."""

    parser: Parser
    confidence: float


@dataclass(frozen=True)
class Chosen:
    """One Candidate is clearly the input's format."""

    parser: Parser
    candidates: Tuple[Candidate, ...]


@dataclass(frozen=True)
class Ambiguous:
    """Candidates exist, but none is clear enough to pick."""

    candidates: Tuple[Candidate, ...]


@dataclass(frozen=True)
class Unknown:
    """No parser recognised the input at all."""

    candidates: Tuple[Candidate, ...] = ()


def resolve(
    text: str, parsers: Optional[Sequence[Parser]] = None
) -> Union[Chosen, Ambiguous, Unknown]:
    """Work out which parser should handle `text`.

    Every parser's `detect()` gets the stripped text and returns a Confidence.
    Candidates (Confidence above zero) are ranked by Confidence, then by name.

    - A lone Candidate is Chosen at a Confidence of 0.3 or more.
    - With rivals, the best Candidate is Chosen at 0.6 or more if it leads the
      runner-up by at least 0.3.
    - Otherwise the outcome is Ambiguous, or Unknown if there are no Candidates.

    `parsers` defaults to every registered parser. Errors raised by `detect()`
    propagate, and a Confidence outside 0.0-1.0 raises ValueError.
    """
    if parsers is None:
        parsers = registry.all_parsers()
    text = text.strip()
    candidates = tuple(
        sorted(
            (Candidate(p, c) for p in parsers if (c := _confidence(p, text)) > 0.0),
            key=lambda cand: (-cand.confidence, cand.parser.name),
        )
    )
    if not candidates:
        return Unknown()
    best = candidates[0]
    if len(candidates) == 1:
        if best.confidence >= _LONE_FLOOR:
            return Chosen(best.parser, candidates)
        return Ambiguous(candidates)
    if (
        best.confidence >= _CONFIDENT
        and best.confidence - candidates[1].confidence >= _MARGIN - _TOLERANCE
    ):
        return Chosen(best.parser, candidates)
    return Ambiguous(candidates)


def _confidence(parser: Parser, text: str) -> float:
    confidence = parser.detect(text)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"parser {parser.name!r} returned Confidence {confidence}, expected 0.0-1.0"
        )
    return confidence
