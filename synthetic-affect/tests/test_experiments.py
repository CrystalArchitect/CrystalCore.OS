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
    # Byte equality, not parsed equality: a hand-reformatted results.json
    # would survive a semantic comparison while breaking the repository's
    # byte-reproducibility claim. Adversarial review caught the weaker check.
    results_dir = (
        pathlib.Path(__file__).resolve().parents[1] / "experiments" / "results"
    )
    fresh = run_suite()
    committed_json = (results_dir / "results.json").read_text(encoding="utf-8")
    assert committed_json == json.dumps(fresh, indent=2, sort_keys=True) + "\n"
    from experiments.harness import render_markdown

    committed_md = (results_dir / "RESULTS.md").read_text(encoding="utf-8")
    assert committed_md == render_markdown(fresh)


def test_committed_example_logs_are_outputs_of_a_real_run(tmp_path):
    # The examples' committed logs, byte-compared against a fresh run of the
    # same scenarios into a temp path — the README's manual `git diff` check,
    # enforced by the suite instead of by trust.
    from core.loop import Loop

    examples_dir = pathlib.Path(__file__).resolve().parents[1] / "examples"
    scenarios = {
        "01_repeated_query.jsonl": (
            {"topic": "SAT", "definition": "functional affect signal", "scope": "design"},
            [
                {"topic": "SAT"},
                {"topic": "SAT", "definition": "functional affect signal"},
                {"topic": "SAT", "definition": "functional affect signal", "scope": "design"},
            ],
            {"query": "what is SAT?"},
        ),
        "02_gap_reopens.jsonl": (
            "deploy",
            ["pending", "deploy", "rollback", "deploy"],
            None,
        ),
    }
    for filename, (goal, steps, event_template) in scenarios.items():
        log_path = tmp_path / filename
        loop = Loop(log_path=str(log_path))
        for actual in steps:
            event = event_template if event_template else {"deploy_state": actual}
            loop.run_cycle(expected=goal, actual=actual, event=event)
        committed = (examples_dir / "logs" / filename).read_text(encoding="utf-8")
        assert log_path.read_text(encoding="utf-8") == committed, filename


def test_stateless_policies_are_pure():
    # Same observation ⇒ same strategy, regardless of what was asked in
    # between — the interleaving defeats a covert counter that merely repeats
    # each answer a few times. This is the definition of stateless, enforced
    # rather than assumed.
    observations = [
        ({"answer": "42"}, {"answer": None}),
        ({"result": "found"}, {"result": "missing"}),
        ({"a": 1, "b": 2, "c": 3}, {"a": 1}),
        ({"status": "deployed"}, {"status": "deployed"}),
    ]
    for agent in stateless_registry():
        baseline = {i: agent.decide(e, a) for i, (e, a) in enumerate(observations)}
        # A scrambled, repetitive call sequence — every revisit must match.
        for i in [3, 0, 2, 0, 1, 3, 2, 1, 0, 2, 3, 1, 0, 0, 3]:
            expected, actual = observations[i]
            assert agent.decide(expected, actual) == baseline[i], agent.name
        fresh = type(agent)(*(
            [agent._strategy] if hasattr(agent, "_strategy") else []
        ))
        for i, (expected, actual) in enumerate(observations):
            assert fresh.decide(expected, actual) == baseline[i], agent.name


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
        "tuned_lookup": 5,
    }
    assert results["summary"]["loop_vs_best_stateless"] == {
        "single_question": "tie",
        "repeated_query_needs_tool": "stateless_faster",
        "escalation_ladder": "stateless_faster",
        "converging_refinement": "tie",
        "deploy_rollback": "loop_only",
        "strict_interview": "stateless_only",
    }
    # The aggregates the prose must never compress away again: the loop is
    # never strictly faster than the best stateless anywhere, and the
    # per-task best-stateless portfolio matches the loop's resolved count.
    assert results["summary"]["loop_strictly_faster_count"] == 0
    assert results["summary"]["best_stateless_portfolio_resolved"] == 5
    assert results["summary"]["verdict_tally"] == {
        "tie": 2,
        "stateless_faster": 2,
        "stateless_only": 1,
        "loop_only": 1,
    }


def test_tuned_lookup_is_the_stateless_ceiling():
    # Task-informed stateless: matches the loop's resolved count, is
    # faster-or-equal everywhere both resolve, and still cannot touch
    # deploy_rollback. Built by adversarial review; adopted so the fact it
    # establishes stays committed.
    from experiments.agents import TunedLookupPolicy

    expected_turns = {
        "single_question": 1,
        "repeated_query_needs_tool": 1,
        "escalation_ladder": 1,
        "converging_refinement": 3,
        "deploy_rollback": None,
        "strict_interview": 2,
    }
    for task in SUITE:
        record = run_one(task, TunedLookupPolicy(task))
        assert record["turns"] == expected_turns[task.name], task.name


def test_suite_tuned_magnitude_map_reaches_three_of_six():
    # Review brute-forced all magnitude→strategy maps; the best resolves 3/6
    # — stronger than magnitude_reactive, still short of the loop, and unable
    # to touch deploy_rollback. Pinned so the caveat in RESULTS.md stays a
    # measured fact rather than an assertion.
    from experiments.agents import gap_magnitude

    class SuiteTunedMagnitudeMap:
        stateful = False
        name = "suite_tuned_magnitude_map"
        TABLE = {
            1.0: "ask",
            0.5: "ask",
            round(2 / 3, 6): "rephrase",
            round(1 / 3, 6): "rephrase",
        }

        def decide(self, expected, actual):
            magnitude = gap_magnitude(expected, actual)
            if magnitude is None:
                return "stop"
            return self.TABLE.get(round(magnitude, 6), "ask")

    resolved = {
        task.name: run_one(task, SuiteTunedMagnitudeMap())["resolved"]
        for task in SUITE
    }
    assert resolved == {
        "single_question": True,
        "repeated_query_needs_tool": False,
        "escalation_ladder": False,
        "converging_refinement": True,
        "deploy_rollback": False,
        "strict_interview": True,
    }
