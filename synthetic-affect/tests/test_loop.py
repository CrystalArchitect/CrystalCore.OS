# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

from core.loop import Loop


def test_full_cycle_opens_then_closes(tmp_path):
    loop = Loop(
        store_path=str(tmp_path / "state.json"),
        log_path=str(tmp_path / "loop.jsonl"),
    )
    opened = loop.run_cycle("expected", "actual", event={"test": True})
    assert opened["gap"] is not None
    assert opened["label"] == "uncertain"

    closed = loop.run_cycle("expected", "expected")
    assert closed["gap"] is None
    assert closed["label"] == "closed"
    assert closed["decision"].strategy == "stop"


def test_cycle_numbers_count_cycles_not_log_lines(tmp_path):
    loop = Loop(log_path=str(tmp_path / "loop.jsonl"))
    loop.run_cycle("a", "b", event={"e": 1})
    loop.run_cycle("a", "a")
    assert max(e["cycle"] for e in loop.logger.read_all()) == 2


def test_decision_is_judged_by_the_following_cycle(tmp_path):
    loop = Loop(log_path=str(tmp_path / "loop.jsonl"))
    loop.run_cycle("a", "b")          # gap opens, decision pending
    loop.run_cycle("a", "a")          # gap shuts — the prior decision worked
    judged = [e for e in loop.logger.read_all() if e["op"] == "closure_outcome"]
    assert [e["data"]["outcome"] for e in judged] == ["worked"]


def test_closure_success_rate_is_none_before_anything_is_judged(tmp_path):
    loop = Loop(log_path=str(tmp_path / "loop.jsonl"))
    assert loop.closure_success_rate() is None


def test_failed_closure_is_recorded_as_failed(tmp_path):
    loop = Loop(log_path=str(tmp_path / "loop.jsonl"))
    loop.run_cycle("a", "b")
    loop.run_cycle("a", "c")          # still open — the decision did not work
    judged = [e for e in loop.logger.read_all() if e["op"] == "closure_outcome"]
    assert judged[0]["data"]["outcome"] == "failed"
    assert loop.closure_success_rate() == 0.0
