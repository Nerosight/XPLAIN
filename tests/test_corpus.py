"""Detection corpus: real-world samples on disk, one input per file.

- tests/corpus/<parser>/*.txt must be Chosen as that parser, and parse cleanly.
- tests/corpus/unknown/*.txt must be Unknown.
- tests/corpus/known-gaps/<parser>/*.txt should be Chosen as that parser but
  aren't yet. They run as strict xfail: when one starts passing, move it into
  tests/corpus/<parser>/.

Adding a sample needs no code: drop a file in the right folder.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from xplain import registry
from xplain.detection import Chosen, Unknown, resolve


CORPUS = Path(__file__).parent / "corpus"


def _samples(*parts: str):
    folder = CORPUS.joinpath(*parts)
    return sorted(folder.glob("*.txt")) if folder.is_dir() else []


def _id(path: Path) -> str:
    return path.relative_to(CORPUS).as_posix()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_CHOSEN = [(name, p) for name in registry.names() for p in _samples(name)]
_UNKNOWN = _samples("unknown")
_KNOWN_GAPS = [(name, p) for name in registry.names() for p in _samples("known-gaps", name)]


@pytest.mark.parametrize("name, path", _CHOSEN, ids=[_id(p) for _, p in _CHOSEN])
def test_sample_is_chosen_and_parses(name, path):
    text = _read(path)
    outcome = resolve(text)
    assert isinstance(outcome, Chosen), outcome
    assert outcome.parser.name == name
    list(outcome.parser.parse(text.strip()))


@pytest.mark.parametrize("path", _UNKNOWN, ids=[_id(p) for p in _UNKNOWN])
def test_sample_is_unknown(path):
    assert resolve(_read(path)) == Unknown()


@pytest.mark.xfail(strict=True, reason="known gap: move the file into tests/corpus/<parser>/ once fixed")
@pytest.mark.parametrize("name, path", _KNOWN_GAPS, ids=[_id(p) for _, p in _KNOWN_GAPS])
def test_known_gap_is_chosen(name, path):
    outcome = resolve(_read(path))
    assert isinstance(outcome, Chosen) and outcome.parser.name == name
