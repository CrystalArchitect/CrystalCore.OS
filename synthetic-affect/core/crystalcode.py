# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""CrystalCode™ — the four primitives, and the runtime they bind to.

    track(event) · detect_gap(expected, actual) · label_affect(history)
    · close_with(label, context)

These are the public surface: the vocabulary the theory offers to anyone who
wants to build the loop themselves. Each one logs, so a run leaves an auditable
trail of gap openings, labels and closure attempts.

Every primitive takes an explicit `Runtime`. The module-level functions are a
convenience over one default runtime — but two `Loop`s in one process each get
their own `Runtime`, so they cannot silently overwrite each other's store and
logger the way a module-global wiring would.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from .affect import AffectModel
from .closure import ClosureDecision, ClosurePolicy
from .gap import Gap, GapDetector
from .log import CycleLogger
from .state import PersistentStateStore


class RuntimeNotInitialised(RuntimeError):
    """Raised when a primitive is called before a runtime is bound."""


@dataclass
class Runtime:
    state: PersistentStateStore
    gap_detector: GapDetector
    affect_model: AffectModel
    closure_policy: ClosurePolicy
    logger: CycleLogger


_default: Optional[Runtime] = None


def init_runtime(runtime: Runtime) -> Runtime:
    """Bind `runtime` as the default for the module-level primitives."""
    global _default
    _default = runtime
    return runtime


def _resolve(runtime: Optional[Runtime]) -> Runtime:
    active = runtime or _default
    if active is None:
        raise RuntimeNotInitialised(
            "no runtime bound — pass one explicitly or call init_runtime() first"
        )
    return active


def track(event: dict, runtime: Optional[Runtime] = None) -> None:
    """Postulate 1 — commit an observation to the persistent state store."""
    rt = _resolve(runtime)
    rt.state.record(event)
    rt.logger.log("track", event)


def detect_gap(
    expected: Any, actual: Any, runtime: Optional[Runtime] = None
) -> Optional[Gap]:
    """Postulate 3 — Gap = Expected − Actual."""
    rt = _resolve(runtime)
    gap = rt.gap_detector.detect(expected, actual)
    if gap is None:
        rt.logger.log("gap_none", {"expected": expected, "actual": actual})
    else:
        rt.logger.log("gap_opened", gap.to_dict())
    return gap


def label_affect(
    gap_history: List[Optional[Gap]], runtime: Optional[Runtime] = None
) -> str:
    """Postulate 2 — classify the gap situation. A signal, not a feeling."""
    rt = _resolve(runtime)
    label = rt.affect_model.classify(gap_history)
    rt.logger.log("label", {"label": label, "history_len": len(gap_history)})
    return label


def close_with(
    label: str, context: Optional[dict] = None, runtime: Optional[Runtime] = None
) -> ClosureDecision:
    """Postulate 4 — select the concrete move that attempts closure."""
    rt = _resolve(runtime)
    decision = rt.closure_policy.decide(label, context or {})
    rt.logger.log("closure", decision.to_dict())
    return decision
