# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Selftest — `python3 -m core.selftest`, matching the crystalcore convention.

Every assertion names an exact expected value. A selftest that accepts three of
five possible labels can pass while the classifier is wrong, which is how the
`closed`-unreachable defect survived an earlier build's "PASS".

Uses `check()` rather than bare `assert` so `python -O` cannot strip the proof
out of the file whose only job is to prove.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from .loop import Loop


class SelftestFailure(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SelftestFailure(message)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        loop = Loop(
            store_path=str(Path(td) / "state.json"),
            log_path=str(Path(td) / "selftest.jsonl"),
        )

        r1 = loop.run_cycle("answer", "no answer", event={"q": "what is SAT?"})
        check(r1["gap"] is not None, "cycle 1: a gap should have opened")
        check(r1["label"] == "uncertain", f"cycle 1: expected uncertain, got {r1['label']}")
        check(r1["decision"].strategy == "ask", "cycle 1: expected strategy ask")

        r2 = loop.run_cycle("answer", "answer")
        check(r2["gap"] is None, "cycle 2: the gap should have closed")
        check(r2["label"] == "closed", f"cycle 2: expected closed, got {r2['label']}")
        check(r2["decision"].strategy == "stop", "cycle 2: expected strategy stop")

        r3 = loop.run_cycle("answer", "wrong again")
        check(r3["label"] == "reopened", f"cycle 3: expected reopened, got {r3['label']}")

        entries = loop.logger.read_all()
        ops = [e["op"] for e in entries]
        check("closure_outcome" in ops, "decisions must be judged by a later cycle")
        # 4 + 4 + 4: cycle 1 logs track, gap_opened, label, closure; cycles 2
        # and 3 have no event to track but each judge the prior decision.
        check(
            len(entries) == 12,
            f"expected exactly 12 log lines, got {len(entries)}",
        )
        check(
            max(e["cycle"] for e in entries) == 3,
            "cycle numbers must count loop cycles, not log lines",
        )

        rate = loop.closure_success_rate()
        check(rate is not None, "closure success rate should be measured by now")

        check(loop.store.is_persistent, "store should be persistent when given a path")
        loop.store.set_goal("prove state is primary")
        reopened = type(loop.store)(loop.store.path)
        check(
            "prove state is primary" in reopened.goals,
            "postulate 1: state must survive being reopened",
        )

    print(
        f"[selftest] PASS — 3 cycles, {len(entries)} log lines, "
        f"closure success rate {rate:.2f}, state survived reopen"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
