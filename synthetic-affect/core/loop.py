# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""The loop: track → detect_gap → label_affect → close_with → LLM Core → state.

What is actually wired here, stated plainly so Figure 1 does not overclaim:
the LLM Core is a **deterministic offline stub**. No model, no network. It makes
the logs reproducible, which is the point — but it means v0.1 demonstrates the
control loop, not a language model driven by one.

The one honesty mechanism worth naming: a closure decision is recorded as
`pending`, and the *following* cycle judges it. `worked` if the gap shut,
`failed` if it did not. Nothing in this file lets a decision grade itself.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from . import crystalcode
from .affect import AffectModel
from .closure import ClosureDecision, ClosurePolicy
from .crystalcode import Runtime
from .gap import Gap, GapDetector
from .log import CycleLogger
from .state import MEMORY, PersistentStateStore


def _stub_llm(prompt: str) -> str:
    """Deterministic stand-in for the LLM Core. No model, no network."""
    canned = (
        "Let me rephrase that step.",
        "Could you clarify the expected output?",
        "Switching tool.",
        "Closing loop, gap resolved.",
    )
    return canned[sum(ord(c) for c in prompt) % len(canned)]


class Loop:
    def __init__(
        self,
        store_path: str = MEMORY,
        log_path: str = "examples/logs/loop.jsonl",
        llm_core: Optional[Callable[[str], str]] = None,
        bind_default: bool = True,
    ):
        self.runtime = Runtime(
            state=PersistentStateStore(store_path),
            gap_detector=GapDetector(),
            affect_model=AffectModel(),
            closure_policy=ClosurePolicy(),
            logger=CycleLogger(log_path),
        )
        if bind_default:
            crystalcode.init_runtime(self.runtime)
        self.gap_history: List[Optional[Gap]] = []
        self.llm_core = llm_core or _stub_llm
        self._pending: Optional[ClosureDecision] = None

    @property
    def store(self) -> PersistentStateStore:
        return self.runtime.state

    @property
    def logger(self) -> CycleLogger:
        return self.runtime.logger

    def _judge_pending(self, gap: Optional[Gap]) -> None:
        """Score the previous cycle's decision against what actually happened."""
        if self._pending is None:
            return
        self._pending.outcome = "worked" if gap is None else "failed"
        self.runtime.logger.log(
            "closure_outcome",
            {"strategy": self._pending.strategy, "outcome": self._pending.outcome},
        )
        self._pending = None

    def run_cycle(
        self, expected: Any, actual: Any, event: Optional[dict] = None
    ) -> Dict[str, Any]:
        self.runtime.logger.begin_cycle()
        if event:
            crystalcode.track(event, runtime=self.runtime)

        gap = crystalcode.detect_gap(expected, actual, runtime=self.runtime)
        self._judge_pending(gap)
        self.gap_history.append(gap)

        self.runtime.state.set_expected({"value": expected})
        self.runtime.state.update_actual({"value": actual})

        label = crystalcode.label_affect(self.gap_history, runtime=self.runtime)
        decision = crystalcode.close_with(
            label, {"expected": expected, "actual": actual}, runtime=self.runtime
        )
        self._pending = decision

        llm_out = self.llm_core(f"{label}:{decision.strategy}:{expected}")
        return {
            "gap": gap,
            "label": label,
            "decision": decision,
            "llm": llm_out,
            "cycle": self.runtime.logger.cycle,
        }

    def closure_success_rate(self) -> Optional[float]:
        """Share of judged decisions that actually shut the gap.

        `None` while nothing has been judged yet — an unmeasured rate is not
        zero, and must not be reported as one.
        """
        judged = [
            e for e in self.runtime.logger.read_all() if e["op"] == "closure_outcome"
        ]
        if not judged:
            return None
        worked = sum(1 for e in judged if e["data"]["outcome"] == "worked")
        return worked / len(judged)
