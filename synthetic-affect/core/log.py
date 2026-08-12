# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Structured JSONL cycle log.

Deterministic by construction: `cycle` is the loop cycle the line belongs to and
`seq` is its position in the file. No wall-clock timestamp appears anywhere, so
a committed log is byte-reproducible and `git diff` on it is a real check that
the logs are outputs rather than prose.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List


class CycleLogger:
    def __init__(self, path: str | pathlib.Path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.cycle = 0
        self.seq = 0
        self.path.write_text("", encoding="utf-8")

    def begin_cycle(self) -> int:
        """Advance the loop-cycle counter. Called once per `run_cycle`."""
        self.cycle += 1
        return self.cycle

    def log(self, op: str, data: Dict[str, Any]) -> None:
        self.seq += 1
        entry = {"cycle": self.cycle, "seq": self.seq, "op": op, "data": data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines if line.strip()]
