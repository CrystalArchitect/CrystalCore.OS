# Synthetic Affect Theory™ — public v0.1

> **Synthetic = apparent / functional, for design purposes. Not a claim of
> feeling, consciousness, or inner experience.**

A design theory and a runnable reference loop. Give a system persistent state, a
way to detect the gap between expected and actual, and a policy for closing it,
and its observable behaviour starts to look like affect — without any claim about
inner experience.

![Figure 1 — the Synthetic Affect Theory stack](docs/figure-1.svg)

- **[THEORY.md](THEORY.md)** — the four postulates, the falsifiable predictions,
  and what is deliberately not claimed
- **[crystalcode/SPEC.md](crystalcode/SPEC.md)** — the four primitives
- **[CHRONICLE.md](CHRONICLE.md)** — dated record: evidence → interpretation →
  experiment → record

## Prove it

```bash
cd synthetic-affect
python3 -m core.selftest                  # exact assertions, exit 0
python3 -m pytest tests -q                # 30 tests
python3 examples/01_repeated_query.py     # regenerates its own log
python3 examples/02_gap_reopens.py
git diff --stat examples/logs/            # empty — the logs are outputs
```

That last line is the check that matters. `examples/logs/*.jsonl` are committed
outputs of an actual run, and they are byte-reproducible because nothing in the
log carries a wall clock. If a fresh run changes them, they were never outputs.

## What runs, and what does not

**Belt: Science — checkable by running the commands above.**

- The loop: `track → detect_gap → label_affect → close_with`, with the persistent
  state store reloading from disk across processes
- Five affect labels, every one reachable and asserted so by the test suite
- Closure decisions judged by the *following* cycle, so closure success rate is a
  measurement rather than a self-report

**Belt: Vision — designed, not built.**

- The hardware column of Figure 1. No sensors, no actuators, no homeostatic loops
- The claim that this beats a stateless baseline on real tasks. The comparison
  harness is not written; until it is, that is a prediction, not a result

**Stated plainly so the figure does not overclaim:** the LLM Core in v0.1 is a
**deterministic offline stub**. No model, no network. It is what makes the logs
reproducible — and it means this release demonstrates the control loop, not a
language model driven by one.

## The loop, in one example

```
$ python3 examples/01_repeated_query.py
cycle 1  gap=0.67  label=uncertain  strategy=ask
cycle 2  gap=0.33  label=converging strategy=rephrase
cycle 3  gap=   -  label=closed     strategy=stop
closure success rate: 0.50
```

The gap narrows, the label tracks it, the policy changes move, and the rate is
0.50 rather than 1.00 because the first attempt did not work and the log says so.

## Layout

```
core/          state · gap · affect · closure · loop · crystalcode · log · selftest
crystalcode/   SPEC.md — the primitive contract
docs/          figure-1.svg · FIGURE-1.md · GLOSSARY.md
examples/      two runnable scenarios, with their committed logs
tests/         30 tests
```

## Licence

CC BY-NC-ND 4.0. **All rights reserved.**
TerAustralis Incognita™ — ABN 70 741 068 059

Implementation: CrystalCore.OS™ · Language: CrystalCode™
See [ATTRIBUTION.md](ATTRIBUTION.md) for who built what.
