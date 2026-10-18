"""Tests for format detection: the rules that turn Confidences into an outcome."""

from __future__ import annotations

from typing import Iterable

import pytest

from xplain.core.base import Annotation, Parser
from xplain.detection import Ambiguous, Candidate, Chosen, Unknown, resolve


class FixedScore(Parser):
    """A fake parser that gives every input the same Confidence."""

    def __init__(self, name: str, confidence: float) -> None:
        self.name = name
        self.description = f"fake {name}"
        self._confidence = confidence

    def detect(self, text: str) -> float:
        return self._confidence

    def parse(self, text: str) -> Iterable[Annotation]:
        return []


def test_no_candidates_is_unknown():
    outcome = resolve("anything", parsers=[FixedScore("a", 0.0), FixedScore("b", 0.0)])
    assert outcome == Unknown()


def test_lone_candidate_at_the_floor_is_chosen():
    a = FixedScore("a", 0.3)
    outcome = resolve("755", parsers=[a, FixedScore("b", 0.0)])
    assert outcome == Chosen(a, (Candidate(a, 0.3),))


def test_lone_candidate_below_the_floor_is_ambiguous():
    a = FixedScore("a", 0.2)
    outcome = resolve("(A;;GA;;;SY)", parsers=[a])
    assert outcome == Ambiguous((Candidate(a, 0.2),))


def test_clear_winner_at_exactly_the_margin_is_chosen():
    # The margin is inclusive: a lead of exactly 0.3 is enough.
    a, b = FixedScore("a", 0.9), FixedScore("b", 0.6)
    outcome = resolve("x", parsers=[b, a])
    assert outcome == Chosen(a, (Candidate(a, 0.9), Candidate(b, 0.6)))


@pytest.mark.parametrize(
    "best, runner_up, expected",
    [
        (0.7, 0.4, Chosen),      # lead of exactly 0.3; 0.7 - 0.4 rounds below 0.3
        (0.6, 0.3, Chosen),      # exactly at the confidence bar
        (0.8, 0.6, Ambiguous),   # confident, but lead too small
        (0.5, 0.1, Ambiguous),   # big lead, but below the confidence bar
        (0.9, 0.9, Ambiguous),   # a tie at the top
        (0.3, 0.3, Ambiguous),   # two weak Candidates
    ],
)
def test_rules_with_rival_candidates(best, runner_up, expected):
    outcome = resolve("x", parsers=[FixedScore("a", best), FixedScore("b", runner_up)])
    assert type(outcome) is expected


def test_equal_confidences_rank_by_parser_name():
    a, b, c = FixedScore("a", 0.5), FixedScore("b", 0.5), FixedScore("c", 0.9)
    outcome = resolve("x", parsers=[b, a, c])
    assert [cand.parser.name for cand in outcome.candidates] == ["c", "a", "b"]


def test_parsers_receive_stripped_text():
    seen = []

    class Recording(FixedScore):
        def detect(self, text: str) -> float:
            seen.append(text)
            return 0.0

    resolve("  drwxr-xr-x\n", parsers=[Recording("a", 0.0)])
    assert seen == ["drwxr-xr-x"]


@pytest.mark.parametrize("bad", [1.5, -0.1])
def test_out_of_range_confidence_raises(bad):
    with pytest.raises(ValueError, match="'broken'"):
        resolve("x", parsers=[FixedScore("broken", bad)])


def test_defaults_to_the_registered_parsers():
    outcome = resolve("D:(A;;GA;;;SY)")
    assert isinstance(outcome, Chosen)
    assert outcome.parser.name == "sddl"


def test_bare_ace_is_ambiguous_with_sddl_as_the_only_candidate():
    # sddl cannot parse an ACE without a section yet (#7), so it must not be Chosen.
    outcome = resolve("(A;;GA;;;SY)")
    assert isinstance(outcome, Ambiguous)
    assert [c.parser.name for c in outcome.candidates] == ["sddl"]
