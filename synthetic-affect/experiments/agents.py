# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""The agents under comparison.

Fairness rules, stated up front because they are the experiment:

- Every agent sees exactly the same observation each turn: `(expected, actual)`.
  Nobody sees environment internals.
- Every agent draws from the same strategy vocabulary.
- A **stateless** agent is a pure function of the current observation. It may be
  as clever as it likes about *now* — it may compute the gap and its magnitude —
  but it may not remember what it tried before. Purity is asserted by test, not
  assumed.
- The baseline registry includes every constant policy, one per strategy. That
  makes the comparison maximally adversarial to the theory: for any single
  task, some constant policy may be pre-tuned to it by accident. The honest
  aggregate compares the one stateful loop against the *best* stateless policy
  per task, and reports where the loop loses.
"""
from __future__ import annotations

import pathlib
import tempfile
from typing import Any, List, Optional

from core.closure import STRATEGIES
from core.gap import GapDetector
from core.loop import Loop


def gap_magnitude(expected: Any, actual: Any) -> Optional[float]:
    """Pure helper: the magnitude of the current gap, or None when closed.

    A fresh detector per call, so no identity state leaks between turns —
    stateless agents must stay stateless.
    """
    gap = GapDetector().detect(expected, actual)
    return None if gap is None else gap.magnitude


class ConstantPolicy:
    """gap → the one strategy this policy knows; no gap → stop.

    Stateless: `decide` reads nothing but its arguments and a frozen constant.
    """

    stateful = False

    def __init__(self, strategy: str):
        if strategy not in STRATEGIES:
            raise ValueError(f"unknown strategy {strategy!r}")
        self.name = f"always_{strategy}"
        self._strategy = strategy

    def decide(self, expected: Any, actual: Any) -> str:
        if gap_magnitude(expected, actual) is None:
            return "stop"
        return self._strategy


class MagnitudeReactivePolicy:
    """The strongest task-agnostic stateless policy in the registry.

    It uses everything the current observation offers — full mismatch reads as
    a question to ask, partial mismatch as something to refine — and nothing
    historical. This is also the ablation for prediction 3: it is the loop's
    per-observation knowledge with the state store removed.
    """

    stateful = False
    name = "magnitude_reactive"

    def decide(self, expected: Any, actual: Any) -> str:
        magnitude = gap_magnitude(expected, actual)
        if magnitude is None:
            return "stop"
        if magnitude < 1.0:
            return "rephrase"
        return "ask"


class LoopAgent:
    """The stateful agent: the shipped v0.1 Loop, unmodified.

    It receives the same observation as everyone else; its only extra input is
    its own history — which is the thing under test.
    """

    stateful = True
    name = "loop"

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.loop = Loop(
            store_path=str(pathlib.Path(self._tmp.name) / "state.json"),
            log_path=str(pathlib.Path(self._tmp.name) / "run.jsonl"),
            bind_default=False,
        )
        self.labels: List[str] = []

    def decide(self, expected: Any, actual: Any) -> str:
        result = self.loop.run_cycle(expected=expected, actual=actual)
        self.labels.append(result["label"])
        return result["decision"].strategy

    def observe_final(self, expected: Any, actual: Any) -> None:
        """Show the agent the resolved state so its last decision gets judged.

        Not an environment step and not charged as a turn — every run ends with
        the world in some state, and a stateful agent is entitled to see it.
        """
        result = self.loop.run_cycle(expected=expected, actual=actual)
        self.labels.append(result["label"])

    def closure_success_rate(self) -> Optional[float]:
        return self.loop.closure_success_rate()

    def close(self) -> None:
        self._tmp.cleanup()


class StallBlindLoopAgent(LoopAgent):
    """Ablation for prediction 2: the loop with a classifier that cannot see
    progress during a same-goal run — the pre-fix ordering, where stalled is
    checked before converging. Everything else is identical.
    """

    name = "loop_stall_blind"

    def __init__(self) -> None:
        super().__init__()
        model = self.loop.runtime.affect_model
        original = model.classify

        def stall_blind_classify(history):
            from core.affect import STALL_RUN

            if not history:
                return "closed"
            current = history[-1]
            previous = history[-2] if len(history) > 1 else None
            if current is None:
                return "closed"
            if previous is None and len(history) > 1:
                return "reopened"
            tail = history[-STALL_RUN:]
            if len(tail) == STALL_RUN and all(g is not None for g in tail):
                if len({repr(g.expected) for g in tail}) == 1:
                    return "stalled"
            if previous is not None and current.magnitude < previous.magnitude:
                return "converging"
            return "uncertain"

        model.classify = stall_blind_classify  # type: ignore[method-assign]
        self._original_classify = original


def stateless_registry() -> List[Any]:
    """Every stateless baseline, freshly constructed."""
    return [ConstantPolicy(s) for s in STRATEGIES] + [MagnitudeReactivePolicy()]


def all_agents() -> List[Any]:
    return [LoopAgent(), StallBlindLoopAgent()] + stateless_registry()
