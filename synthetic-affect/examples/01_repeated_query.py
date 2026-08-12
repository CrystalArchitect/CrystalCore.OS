# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Example 01 — a repeated query that narrows, then closes.

Deterministic. Regenerates examples/logs/01_repeated_query.jsonl.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.loop import Loop  # noqa: E402


def main():
    base = pathlib.Path(__file__).resolve().parent
    loop = Loop(log_path=str(base / "logs" / "01_repeated_query.jsonl"))

    goal = {"topic": "SAT", "definition": "functional affect signal", "scope": "design"}
    attempts = [
        {"topic": "SAT"},
        {"topic": "SAT", "definition": "functional affect signal"},
        goal,
    ]
    for actual in attempts:
        r = loop.run_cycle(expected=goal, actual=actual, event={"query": "what is SAT?"})
        magnitude = "-" if r["gap"] is None else f"{r['gap'].magnitude:.2f}"
        print(
            f"cycle {r['cycle']}  gap={magnitude:>4}  label={r['label']:<10} "
            f"strategy={r['decision'].strategy}"
        )

    rate = loop.closure_success_rate()
    print(f"closure success rate: {rate:.2f}" if rate is not None else "not yet judged")


if __name__ == "__main__":
    main()
