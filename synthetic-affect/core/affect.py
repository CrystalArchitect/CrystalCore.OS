# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Affect Model — a classifier over gap history. Postulate 2.

The label is a routing signal, not a feeling. It answers one question about the
present: what kind of gap situation is this, right now?

The classifier reads the *tail* of history, not the whole of it. An earlier
draft asked "has any gap ever existed?" and so could never return `closed`
once one had — every resolved gap still reported `uncertain`. A theory whose
central act is closure has to be able to say the gap is shut.

Windowed (F6, ported from Synthetic-Affect-Theory- 2026-08-14): `classify()`
looks only at the last `window` entries (default 10), so the stalled rule
sees the same-shaped input at cycle 3 and cycle 300 — a long-running loop's
memory of the classifier's own inputs doesn't grow without bound. Backward
compatible: every existing check here already only ever reads `history[-1]`,
`history[-2]`, and `history[-STALL_RUN:]`, so windowing changes nothing for
any run shorter than `window` — every test, example and harness run in this
package is. `git diff --stat examples/logs/ experiments/results/` after this
change is empty, and the harness's pinned numbers are unchanged, confirming
it by measurement rather than by this argument alone.
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
    def __init__(self, window: int = 10) -> None:
        if window < 1:
            raise ValueError(f"window must be >= 1, got {window}")
        self.window = window

    def classify(self, history: List[Optional[Gap]]) -> str:
        """Classify the current state from the tail of `history`.

        `history` is the per-cycle record: a `Gap` where one was open that
        cycle, `None` where none was.
        """
        recent = history[-self.window:]
        if not recent:
            return "closed"

        current = recent[-1]
        previous = recent[-2] if len(recent) > 1 else None

        # No gap right now — closed, regardless of what came before. This is
        # the case the earlier draft got wrong.
        if current is None:
            return "closed"

        # A gap now, none last cycle: it reopened.
        if previous is None and len(recent) > 1:
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
        tail = recent[-STALL_RUN:]
        if len(tail) == STALL_RUN and all(g is not None for g in tail):
            if len({repr(g.expected) for g in tail}) == 1:
                return "stalled"

        return "uncertain"
