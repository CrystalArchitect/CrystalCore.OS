# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

from core.closure import ClosurePolicy


def test_label_to_strategy():
    p = ClosurePolicy()
    assert p.decide("closed").strategy == "stop"
    assert p.decide("uncertain").strategy == "ask"
    assert p.decide("converging").strategy == "rephrase"
    assert p.decide("reopened").strategy == "rephrase"


def test_escalates_after_two_consecutive_stalls():
    p = ClosurePolicy()
    assert p.decide("stalled").strategy == "switch_tool"
    assert p.decide("stalled").strategy == "escalate"


def test_stall_counter_resets_on_any_other_label():
    p = ClosurePolicy()
    p.decide("stalled")
    p.decide("converging")
    assert p.decide("stalled").strategy == "switch_tool"


def test_decision_does_not_grade_itself():
    # outcome stays pending until a later cycle observes what happened.
    assert ClosurePolicy().decide("closed").outcome == "pending"
