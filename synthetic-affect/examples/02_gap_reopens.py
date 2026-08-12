# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""Example 02 — a gap that closes and reopens, so `reopened` does real work.

Deterministic. Regenerates examples/logs/02_gap_reopens.jsonl.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.loop import Loop  # noqa: E402


def main():
    base = pathlib.Path(__file__).resolve().parent
    loop = Loop(log_path=str(base / "logs" / "02_gap_reopens.jsonl"))

    states = ["pending", "deploy", "rollback", "deploy"]
    for actual in states:
        r = loop.run_cycle(expected="deploy", actual=actual, event={"deploy_state": actual})
        print(
            f"cycle {r['cycle']}  actual={actual:<9} label={r['label']:<10} "
            f"strategy={r['decision'].strategy}"
        )

    rate = loop.closure_success_rate()
    print(f"closure success rate: {rate:.2f}" if rate is not None else "not yet judged")


if __name__ == "__main__":
    main()
