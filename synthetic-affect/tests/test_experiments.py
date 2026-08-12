# Copyright (c) 2026 TerAustralis Incognita™ — ABN 70 741 068 059
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""The harness's own honesty checks.

Numbers pinned here are the measured results of 2026-08-12, hand-traced first
and then confirmed by running. If a change to core/ moves any of them, that is
a *finding* — the test failing is the harness noticing — and the change belongs
in CHRONICLE.md, not in a quiet edit to these assertions.
"""
import json
import pathlib

from experiments.agents import (
    LoopAgent,
    StallBlindLoopAgent,
    stateless_registry,
)
from experiments.harness import run_one, run_suite
from experiments.tasks import SUITE, TURN_CAP, TaskEnv

TASKS = {t.name: t for t in SUITE}


def test_suite_is_deterministic():
    assert run_suite() == run_suite()


def test_committed_results_are_outputs_of_a_real_run():
    # The committed results.json must equal a fresh run — the same check the
    # examples' logs get, applied to the experiment.
    committed_path = (
        pathlib.Path(__file__).resolve().parents[1]
        / "experiments" / "results" / "results.json"
    )
    committed = json.loads(committed_path.read_text(encoding="utf-8"))
    assert committed == run_suite()


def test_stateless_policies_are_pure():
    # Same observation, any number of times, fresh instance or not: same
    # strategy. This is the definition of stateless, enforced rather than
    # assumed.
    observations = [
        ({"answer": "42"}, {"answer": None}),
        ({"result": "found"}, {"result": "missing"}),
        ({"a": 1, "b": 2, "c": 3}, {"a": 1}),
        ({"status": "deployed"}, {"status": "deployed"}),
    ]
    for agent in stateless_registry():
        for expected, actual in observations:
            first = agent.decide(expected, actual)
            assert agent.decide(expected, actual) == first
            assert type(agent)(*(
                [agent._strategy] if hasattr(agent, "_strategy") else []
            )).decide(expected, actual) == first


def test_loop_resolves_the_repeated_query_in_three_turns():
    record = run_one(TASKS["repeated_query_needs_tool"], LoopAgent())
    assert record["resolved"] and record["turns"] == 3
    assert record["strategies"] == ["ask", "ask", "switch_tool"]
    assert record["labels"] == ["uncertain", "uncertain", "stalled", "closed"]


def test_repeated_query_defeats_every_stateless_policy_but_the_pretuned_one():
    task = TASKS["repeated_query_needs_tool"]
    for agent in stateless_registry():
        record = run_one(task, agent)
        if agent.name == "always_switch_tool":
            assert record["resolved"] and record["turns"] == 1
        else:
            assert not record["resolved"]


def test_deploy_rollback_is_unsolvable_by_any_stateless_policy():
    task = TASKS["deploy_rollback"]
    for agent in stateless_registry():
        assert not run_one(task, agent)["resolved"], agent.name


def test_deploy_rollback_impossibility_is_structural():
    # The two decision points where different strategies are required present
    # byte-identical observations. Any function of the observation therefore
    # answers both the same way — the impossibility is a construction, not an
    # empirical accident of which baselines were tried.
    task = TASKS["deploy_rollback"]
    env = TaskEnv(task)
    first_decision_obs = env.observe()
    env.step("ask")                      # clears stage 1
    assert env.observe() == task.goal    # closure is observable
    env.arm_transition_if_due()
    env.step("stop")                     # the world regresses
    second_decision_obs = env.observe()
    assert second_decision_obs == first_decision_obs
    # ...and the loop resolves it anyway, in 3 turns, via its history.
    record = run_one(task, LoopAgent())
    assert record["resolved"] and record["turns"] == 3
    assert record["labels"] == ["uncertain", "closed", "reopened", "closed"]


def test_strict_interview_is_an_honest_loss_for_the_loop():
    # Kept failing on purpose: a v0.1 closure-policy limitation, measured.
    # If a future policy change makes the loop pass this task, that is a real
    # improvement — record it in CHRONICLE.md and update this pin.
    loop_record = run_one(TASKS["strict_interview"], LoopAgent())
    assert not loop_record["resolved"]
    ask = next(a for a in stateless_registry() if a.name == "always_ask")
    ask_record = run_one(TASKS["strict_interview"], ask)
    assert ask_record["resolved"] and ask_record["turns"] == 2


def test_stall_blind_ablation_is_measurably_worse():
    # Prediction 2 in miniature: a classifier that cannot tell converging from
    # stalled loses the converging task outright.
    blind = run_one(TASKS["converging_refinement"], StallBlindLoopAgent())
    sighted = run_one(TASKS["converging_refinement"], LoopAgent())
    assert sighted["resolved"] and sighted["turns"] == 3
    assert not blind["resolved"]


def test_headline_numbers():
    # The suite-level result, pinned exactly. Measured 2026-08-12.
    results = run_suite()
    assert results["turn_cap"] == TURN_CAP
    assert results["summary"]["resolved_counts"] == {
        "loop": 5,
        "loop_stall_blind": 4,
        "always_stop": 0,
        "always_ask": 2,
        "always_rephrase": 0,
        "always_switch_tool": 1,
        "always_escalate": 1,
        "magnitude_reactive": 2,
    }
    assert results["summary"]["loop_vs_best_stateless"] == {
        "single_question": "tie",
        "repeated_query_needs_tool": "stateless_faster",
        "escalation_ladder": "stateless_faster",
        "converging_refinement": "tie",
        "deploy_rollback": "loop_only",
        "strict_interview": "stateless_only",
    }
