# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""The prediction-1 harness: the stateful loop against stateless baselines.

Run with:

    python3 -m experiments.harness

It executes every agent against every task in the suite, then writes
`experiments/results/results.json` and a generated `experiments/results/
RESULTS.md`. Both are deterministic — no wall clock appears anywhere — so the
committed results are byte-reproducible and `git diff` on them is a real check
that they are outputs rather than prose. The date of the committed run lives in
CHRONICLE.md, where dates belong.

This file decides nothing about who wins. It runs the runs and reports the
numbers, including the ones that go against the theory.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.closure import STRATEGIES

from .agents import ConstantPolicy, LoopAgent, MagnitudeReactivePolicy, StallBlindLoopAgent
from .tasks import SUITE, TURN_CAP, ScriptedTask, TaskEnv

RESULTS_DIR = pathlib.Path(__file__).resolve().parent / "results"

#: Construction order fixes report order. A fresh agent per (agent, task) run.
AGENT_FACTORIES: Tuple[Tuple[str, Callable[[], Any]], ...] = tuple(
    [("loop", LoopAgent), ("loop_stall_blind", StallBlindLoopAgent)]
    + [(f"always_{s}", (lambda s=s: ConstantPolicy(s))) for s in STRATEGIES]
    + [("magnitude_reactive", MagnitudeReactivePolicy)]
)

STATEFUL_AGENTS = ("loop", "loop_stall_blind")


def run_one(task: ScriptedTask, agent: Any) -> Dict[str, Any]:
    """One agent, one task, one deterministic run."""
    env = TaskEnv(task)
    strategies: List[str] = []
    resolved = False
    turns = 0

    while True:
        observation = env.observe()
        if env.resolved():
            resolved = True
            break
        if turns >= TURN_CAP:
            break
        env.arm_transition_if_due()
        strategy = agent.decide(task.goal, observation)
        strategies.append(strategy)
        env.step(strategy)
        turns += 1

    record: Dict[str, Any] = {
        "resolved": resolved,
        "turns": turns if resolved else None,
        "strategies": strategies,
    }
    if getattr(agent, "stateful", False):
        if resolved:
            agent.observe_final(task.goal, env.observe())
        record["labels"] = list(agent.labels)
        record["closure_success_rate"] = agent.closure_success_rate()
        agent.close()
    return record


def run_suite() -> Dict[str, Any]:
    runs: Dict[str, Dict[str, Any]] = {}
    for task in SUITE:
        runs[task.name] = {}
        for agent_name, factory in AGENT_FACTORIES:
            runs[task.name][agent_name] = run_one(task, factory())

    agent_names = [name for name, _ in AGENT_FACTORIES]
    stateless_names = [n for n in agent_names if n not in STATEFUL_AGENTS]

    resolved_counts = {
        name: sum(1 for task in SUITE if runs[task.name][name]["resolved"])
        for name in agent_names
    }

    # Per task, the best stateless result — the maximally adversarial
    # comparator, since any constant policy may be pre-tuned to any one task.
    best_stateless: Dict[str, Optional[Dict[str, Any]]] = {}
    for task in SUITE:
        candidates = [
            {"agent": n, "turns": runs[task.name][n]["turns"]}
            for n in stateless_names
            if runs[task.name][n]["resolved"]
        ]
        best_stateless[task.name] = (
            min(candidates, key=lambda c: (c["turns"], c["agent"]))
            if candidates
            else None
        )

    loop_vs_best: Dict[str, str] = {}
    for task in SUITE:
        loop_run = runs[task.name]["loop"]
        best = best_stateless[task.name]
        if loop_run["resolved"] and best is None:
            loop_vs_best[task.name] = "loop_only"
        elif loop_run["resolved"] and best is not None:
            if loop_run["turns"] < best["turns"]:
                loop_vs_best[task.name] = "loop_faster"
            elif loop_run["turns"] == best["turns"]:
                loop_vs_best[task.name] = "tie"
            else:
                loop_vs_best[task.name] = "stateless_faster"
        elif best is not None:
            loop_vs_best[task.name] = "stateless_only"
        else:
            loop_vs_best[task.name] = "nobody"

    return {
        "turn_cap": TURN_CAP,
        "agents": agent_names,
        "tasks": {t.name: {"note": t.note, "goal": t.goal} for t in SUITE},
        "runs": runs,
        "summary": {
            "resolved_counts": resolved_counts,
            "best_stateless_per_task": best_stateless,
            "loop_vs_best_stateless": loop_vs_best,
        },
    }


def render_markdown(results: Dict[str, Any]) -> str:
    """RESULTS.md, generated. Carries no date — CHRONICLE.md holds that."""
    agents = results["agents"]
    runs = results["runs"]
    task_names = list(results["tasks"].keys())

    def cell(task: str, agent: str) -> str:
        run = runs[task][agent]
        return str(run["turns"]) if run["resolved"] else "DNF"

    lines: List[str] = []
    lines.append("# Results — prediction 1 harness")
    lines.append("")
    lines.append(
        "> Synthetic = apparent / functional, for design purposes. Not a claim"
        " of feeling, consciousness, or inner experience."
    )
    lines.append("")
    lines.append(
        "**Generated by `python3 -m experiments.harness`.** Do not edit by"
        " hand — a fresh run must reproduce this file byte for byte. The date"
        " of the committed run is recorded in `CHRONICLE.md`."
    )
    lines.append("")
    lines.append("**Belt: Science, with stated scope.** These numbers are real"
                 " and reproducible, and they are measurements of a scripted,"
                 " deterministic environment — not of live LLM workloads. The"
                 " prediction for real workloads remains Vision.")
    lines.append("")
    lines.append("## Method, in one paragraph")
    lines.append("")
    lines.append(
        "Every agent sees the same observation each turn — expected state and"
        " actual state — and submits one strategy from the shared vocabulary."
        f" A run ends at resolution or at the {results['turn_cap']}-turn cap"
        " (DNF). Stateless agents are pure functions of the current"
        " observation, asserted by test. The stateless registry contains every"
        " constant policy, one per strategy, plus a magnitude-reactive policy"
        " that uses everything the current observation offers; the comparison"
        " below is against the **best stateless result per task**, which is"
        " maximally adversarial to the loop, since a constant policy may be"
        " pre-tuned to any single task."
    )
    lines.append("")
    lines.append("## Turns to resolution")
    lines.append("")
    lines.append("| task | " + " | ".join(agents) + " |")
    lines.append("|---|" + "---|" * len(agents))
    for task in task_names:
        lines.append(
            f"| {task} | " + " | ".join(cell(task, a) for a in agents) + " |"
        )
    lines.append("")
    resolved = results["summary"]["resolved_counts"]
    lines.append(
        "**Tasks resolved:** "
        + " · ".join(f"{a} {resolved[a]}/{len(task_names)}" for a in agents)
    )
    lines.append("")
    lines.append("## Loop vs best stateless, per task")
    lines.append("")
    lines.append("| task | loop | best stateless | verdict |")
    lines.append("|---|---|---|---|")
    for task in task_names:
        best = results["summary"]["best_stateless_per_task"][task]
        best_text = f"{best['agent']} ({best['turns']})" if best else "none resolves it"
        lines.append(
            f"| {task} | {cell(task, 'loop')} |"
            f" {best_text} |"
            f" {results['summary']['loop_vs_best_stateless'][task]} |"
        )
    lines.append("")
    lines.append("## What the loop actually did")
    lines.append("")
    for task in task_names:
        run = runs[task]["loop"]
        lines.append(f"**{task}** — strategies `{' → '.join(run['strategies']) or '—'}`,"
                     f" labels `{' → '.join(run['labels'])}`,"
                     f" closure success rate"
                     f" {run['closure_success_rate'] if run['closure_success_rate'] is not None else 'unjudged'}")
        lines.append("")
    lines.append("## Findings that cut against the theory")
    lines.append("")
    lines.append(
        "- **strict_interview:** the loop DNFs where `always_ask` resolves in"
        " 2. After the first answer the shrinking gap reads as converging, the"
        " v0.1 policy moves to rephrase, and no route back to ask exists. A"
        " measured limitation of the shipped closure policy, in the suite on"
        " purpose."
    )
    lines.append(
        "- **Per-task pre-tuned constants win their own task:**"
        " `always_switch_tool` and `always_escalate` beat the loop on the one"
        " task each is tuned to, then resolve almost nothing else. State buys"
        " adaptivity across the suite, not victory on every task."
    )
    lines.append("")
    lines.append("## The construction, not just a measurement")
    lines.append("")
    lines.append(
        "`deploy_rollback` is unsolvable by **any** stateless policy, tuned or"
        " not: the observation before the first ask and the observation after"
        " the rollback are byte-identical, and the correct strategies differ."
        " A function of the current observation returns the same strategy both"
        " times, so it clears at most one of the two obstacles. The loop"
        " resolves it because its history distinguishes the two moments. That"
        " is postulate 1 operationalised."
    )
    lines.append("")
    lines.append("## Caveats, stated rather than buried")
    lines.append("")
    lines.append(
        "- The task suite is experimenter-chosen. It includes controls, ties,"
        " and a task the loop loses, but the selection is still part of the"
        " design. Criticism of the suite is invited; add a task and rerun."
    )
    lines.append(
        "- Stateless baselines are task-agnostic. A lookup table tuned to one"
        " task can solve any deterministic task **except** deploy_rollback,"
        " where identical observations require different actions."
    )
    lines.append(
        "- Nothing here involves a language model. The LLM Core remains a"
        " deterministic stub; these are properties of the control loop."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**All rights reserved.**")
    lines.append("TerAustralis Incognita™ — ABN 70 741 068 059")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    results = run_suite()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (RESULTS_DIR / "RESULTS.md").write_text(render_markdown(results), encoding="utf-8")

    resolved = results["summary"]["resolved_counts"]
    print(f"[harness] {len(SUITE)} tasks × {len(results['agents'])} agents, cap {TURN_CAP}")
    for agent in results["agents"]:
        per_task = " ".join(
            (str(results["runs"][t][agent]["turns"])
             if results["runs"][t][agent]["resolved"] else "DNF").rjust(4)
            for t in results["tasks"]
        )
        print(f"[harness] {agent:>20}  resolved {resolved[agent]}/{len(SUITE)}  {per_task}")
    print(f"[harness] wrote {RESULTS_DIR / 'results.json'} and RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
