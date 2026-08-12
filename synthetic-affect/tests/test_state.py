# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Postulate 1 — state is primary. If it does not survive, nothing else holds."""
from core.state import MEMORY, PersistentStateStore


def test_memory_store_is_honest_about_not_persisting():
    store = PersistentStateStore(MEMORY)
    assert store.is_persistent is False
    assert store.path is None


def test_state_survives_being_reopened(tmp_path):
    path = tmp_path / "state.json"
    first = PersistentStateStore(path)
    first.set_goal("close the gap")
    first.set_expected({"value": "answer"})
    first.record({"query": "what is SAT?"})

    second = PersistentStateStore(path)
    assert second.goals == ["close the gap"]
    assert second.expected == {"value": "answer"}
    assert second.history == [{"query": "what is SAT?"}]


def test_nested_directories_are_created(tmp_path):
    store = PersistentStateStore(tmp_path / "deep" / "nested" / "state.json")
    store.set_goal("x")
    assert store.path.exists()
