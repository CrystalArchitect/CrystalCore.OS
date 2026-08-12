# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Gap Detector — postulate 3. Gap = Expected − Actual.

The only drive in the system. Not an emotion: a measurable delta.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class Gap:
    id: int
    expected: Any
    actual: Any
    magnitude: float
    kind: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GapDetector:
    """Equality closes a gap; difference opens one.

    Scalars are all-or-nothing (magnitude 1.0). Dicts are scored per key, so a
    partially-correct state reads as a partial gap and the Affect Model can see
    it narrowing.
    """

    def __init__(self) -> None:
        self._counter = 0

    def detect(self, expected: Any, actual: Any, kind: str = "mismatch") -> Optional[Gap]:
        if expected == actual:
            return None
        magnitude = 1.0
        if isinstance(expected, dict) and isinstance(actual, dict):
            keys = set(expected) | set(actual)
            if not keys:
                return None
            differing = sum(1 for k in keys if expected.get(k) != actual.get(k))
            magnitude = differing / len(keys)
            if magnitude == 0:
                return None
        self._counter += 1
        return Gap(self._counter, expected, actual, magnitude, kind)
