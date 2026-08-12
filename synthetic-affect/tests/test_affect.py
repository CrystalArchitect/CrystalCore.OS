# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Every label in LABELS must be reachable — a dead branch fails here."""
from core.affect import LABELS, AffectModel
from core.gap import Gap


def g(magnitude=1.0, expected="a", gid=1):
    return Gap(id=gid, expected=expected, actual="b", magnitude=magnitude, kind="mismatch")


def test_empty_history_is_closed():
    assert AffectModel().classify([]) == "closed"


def test_no_current_gap_is_closed():
    assert AffectModel().classify([None, None]) == "closed"


def test_closed_after_a_gap_actually_closes():
    # The defect this suite exists for: a resolved gap must read as closed,
    # not as uncertain because a gap once existed.
    assert AffectModel().classify([g(), None]) == "closed"


def test_reopened():
    assert AffectModel().classify([None, g()]) == "reopened"


def test_reopened_after_a_real_close():
    assert AffectModel().classify([g(), None, g()]) == "reopened"


def test_stalled_on_a_run_of_same_goal_gaps():
    assert AffectModel().classify([g(gid=i) for i in range(1, 4)]) == "stalled"


def test_converging_when_magnitude_shrinks():
    assert AffectModel().classify([g(1.0), g(0.5, gid=2)]) == "converging"


def test_uncertain_when_gap_is_not_narrowing():
    assert AffectModel().classify([g(0.5), g(1.0, gid=2)]) == "uncertain"


def test_every_label_is_reachable():
    m = AffectModel()
    reached = {
        m.classify([]),
        m.classify([g(), None]),
        m.classify([None, g()]),
        m.classify([g(gid=i) for i in range(1, 4)]),
        m.classify([g(1.0), g(0.5, gid=2)]),
        m.classify([g(0.5), g(1.0, gid=2)]),
    }
    assert reached == set(LABELS)
