# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Persistent State Store — postulate 1, the one the whole theory rests on.

A store that discards its contents at process exit cannot demonstrate that
state is primary. This one writes to disk when given a path, and reloads from
it. `:memory:` is still available for tests and examples that want isolation,
and it is named honestly: in-memory, not persistent.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

MEMORY = ":memory:"


class PersistentStateStore:
    """Goals, expected state, actual state and an event history.

    With a path, every mutation is flushed to JSON, so a second process opening
    the same path sees what the first one wrote. Without one, the store is
    explicitly ephemeral.
    """

    def __init__(self, path: str | pathlib.Path = MEMORY):
        self.path: Optional[pathlib.Path] = (
            None if str(path) == MEMORY else pathlib.Path(path)
        )
        self.goals: List[Any] = []
        self.expected: Dict[str, Any] = {}
        self.actual: Dict[str, Any] = {}
        self.history: List[Any] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                self.load()
            else:
                self.save()

    @property
    def is_persistent(self) -> bool:
        return self.path is not None

    def set_goal(self, goal: Any) -> None:
        self.goals.append(goal)
        self.save()

    def set_expected(self, expected: Dict[str, Any]) -> None:
        self.expected = expected
        self.save()

    def update_actual(self, actual: Dict[str, Any]) -> None:
        self.actual = actual
        self.save()

    def record(self, event: Any) -> None:
        self.history.append(event)
        self.save()

    def save(self) -> None:
        if self.path is None:
            return
        payload = {
            "goals": self.goals,
            "expected": self.expected,
            "actual": self.actual,
            "history": self.history,
        }
        self.path.write_text(
            json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8"
        )

    def load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.goals = payload.get("goals", [])
        self.expected = payload.get("expected", {})
        self.actual = payload.get("actual", {})
        self.history = payload.get("history", [])
