# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""F6 (ported from Synthetic-Affect-Theory-, 2026-08-14): windowed classifier.

`classify()` looks only at the last `window` gaps, so the stalled rule sees
the same-shaped input at cycle 3 and cycle 300 rather than being able to
see all the way back to a run's start. `tests/test_affect.py` already
covers every label and the ordering fix; this file covers the one thing
that only shows up once a history is longer than the window.
"""
from core.affect import AffectModel
from core.gap import Gap


def _gap(i, expected, magnitude):
    return Gap(id=i, expected=expected, actual=f"not-{expected}", magnitude=magnitude, kind="mismatch")


def test_default_window_is_ten():
    assert AffectModel().window == 10


def test_window_rejects_less_than_one():
    import pytest

    with pytest.raises(ValueError):
        AffectModel(window=0)


def test_window_sees_same_shape_at_cycle_3_and_cycle_300():
    am = AffectModel(window=10)
    stalled_tail = [_gap(1, "X", 1.0), _gap(2, "X", 1.0), _gap(3, "X", 1.0)]

    short_history = list(stalled_tail)
    long_history = [_gap(100 + i, f"old-{i % 7}", 1.0) for i in range(297)] + stalled_tail

    assert am.classify(short_history) == "stalled"
    # Window of ten, not forever — ancient history cannot drown the stalled rule.
    assert am.classify(long_history) == am.classify(short_history) == "stalled"


def test_a_smaller_window_can_change_the_label():
    # With window=2, only the last two entries are visible. A tail of three
    # same-expected gaps can only read as stalled if all three are in view —
    # shrink the window below that and the same history reads uncertain
    # instead, demonstrating the window is actually being applied, not just
    # accepted and ignored.
    default_window = AffectModel(window=10)
    narrow_window = AffectModel(window=2)
    run = [_gap(1, "X", 1.0), _gap(2, "X", 1.0), _gap(3, "X", 1.0)]
    assert default_window.classify(run) == "stalled"
    assert narrow_window.classify(run) == "uncertain"
