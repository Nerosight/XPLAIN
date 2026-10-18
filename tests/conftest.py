"""Hypothesis profiles.

Locally, Hypothesis explores new random examples on every run. CI sets
HYPOTHESIS_PROFILE=ci so the same examples run every time and a PR can't fail
by chance. Pin anything Hypothesis finds as a corpus file or an @example.
"""

from __future__ import annotations

import os

from hypothesis import settings

settings.register_profile("ci", derandomize=True, max_examples=300)
settings.register_profile("default", max_examples=300)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))
