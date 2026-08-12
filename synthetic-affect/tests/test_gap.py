# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

from core.gap import GapDetector


def test_scalars_differ_is_total_gap():
    gap = GapDetector().detect("a", "b")
    assert gap is not None
    assert gap.magnitude == 1.0


def test_equal_dicts_close():
    assert GapDetector().detect({"x": 1}, {"x": 1}) is None


def test_dict_partial_gap_is_proportional():
    gap = GapDetector().detect({"x": 1, "y": 2}, {"x": 1, "y": 3})
    assert gap is not None
    assert gap.magnitude == 0.5


def test_ids_increment_per_gap():
    d = GapDetector()
    first, second = d.detect("a", "b"), d.detect("c", "d")
    assert (first.id, second.id) == (1, 2)
