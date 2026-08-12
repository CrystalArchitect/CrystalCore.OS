# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Affect Model — a classifier over gap history. Postulate 2.

The label is a routing signal, not a feeling. It answers one question about the
present: what kind of gap situation is this, right now?

The classifier reads the *tail* of history, not the whole of it. An earlier
draft asked "has any gap ever existed?" and so could never return `closed`
once one had — every resolved gap still reported `uncertain`. A theory whose
central act is closure has to be able to say the gap is shut.
"""
from __future__ import annotations

from typing import List, Optional

from .gap import Gap

#: Every label the model can emit. Each one is reachable; `tests/test_affect.py`
#: asserts that, so a dead branch fails the suite rather than hiding in it.
LABELS = ("closed", "reopened", "stalled", "converging", "uncertain")

#: How many consecutive same-goal gaps count as stalled.
STALL_RUN = 3


class AffectModel:
    def classify(self, history: List[Optional[Gap]]) -> str:
        """Classify the current state from the tail of `history`.

        `history` is the per-cycle record: a `Gap` where one was open that
        cycle, `None` where none was.
        """
        if not history:
            return "closed"

        current = history[-1]
        previous = history[-2] if len(history) > 1 else None

        # No gap right now — closed, regardless of what came before. This is
        # the case the earlier draft got wrong.
        if current is None:
            return "closed"

        # A gap now, none last cycle: it reopened.
        if previous is None and len(history) > 1:
            return "reopened"

        # Gap shrinking cycle on cycle: progress, keep going. Checked before
        # stalled, deliberately: a run of same-goal gaps whose magnitude is
        # falling is a system making progress, and calling it stalled would
        # route the policy away from a strategy that is working. An earlier
        # ordering did exactly that, and the experiment harness caught it —
        # see CHRONICLE.md, 2026-08-12.
        if previous is not None and current.magnitude < previous.magnitude:
            return "converging"

        # A run of gaps against the same expectation, with no progress this
        # cycle: nothing is moving.
        tail = history[-STALL_RUN:]
        if len(tail) == STALL_RUN and all(g is not None for g in tail):
            if len({repr(g.expected) for g in tail}) == 1:
                return "stalled"

        return "uncertain"
