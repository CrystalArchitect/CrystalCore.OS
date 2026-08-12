# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""The four primitives are the public surface — drive them directly."""
import pytest

from core import crystalcode
from core.affect import AffectModel
from core.closure import ClosurePolicy
from core.crystalcode import Runtime, RuntimeNotInitialised
from core.gap import GapDetector
from core.log import CycleLogger
from core.state import PersistentStateStore


def make_runtime(tmp_path, name="rt"):
    return Runtime(
        state=PersistentStateStore(tmp_path / f"{name}-state.json"),
        gap_detector=GapDetector(),
        affect_model=AffectModel(),
        closure_policy=ClosurePolicy(),
        logger=CycleLogger(tmp_path / f"{name}.jsonl"),
    )


def test_track_records_and_logs(tmp_path):
    rt = make_runtime(tmp_path)
    crystalcode.track({"query": "hello"}, runtime=rt)
    assert rt.state.history == [{"query": "hello"}]
    assert [e["op"] for e in rt.logger.read_all()] == ["track"]


def test_detect_gap_logs_both_outcomes(tmp_path):
    rt = make_runtime(tmp_path)
    assert crystalcode.detect_gap("a", "b", runtime=rt) is not None
    assert crystalcode.detect_gap("a", "a", runtime=rt) is None
    assert [e["op"] for e in rt.logger.read_all()] == ["gap_opened", "gap_none"]


def test_label_affect_and_close_with(tmp_path):
    rt = make_runtime(tmp_path)
    gap = crystalcode.detect_gap("a", "b", runtime=rt)
    assert crystalcode.label_affect([gap], runtime=rt) == "uncertain"
    assert crystalcode.close_with("closed", runtime=rt).strategy == "stop"


def test_unbound_runtime_raises_a_named_error(monkeypatch):
    monkeypatch.setattr(crystalcode, "_default", None)
    with pytest.raises(RuntimeNotInitialised):
        crystalcode.track({"x": 1})


def test_two_runtimes_do_not_share_state(tmp_path):
    a, b = make_runtime(tmp_path, "a"), make_runtime(tmp_path, "b")
    crystalcode.track({"who": "a"}, runtime=a)
    crystalcode.track({"who": "b"}, runtime=b)
    assert a.state.history == [{"who": "a"}]
    assert b.state.history == [{"who": "b"}]
