# Synthetic Affect Theory™ — v0.1

> **Synthetic = apparent / functional, for design purposes. Not a claim of
> feeling, consciousness, or inner experience.**

**Belt: Vision.** This is a design theory with falsifiable predictions, not a
measured finding. Where something in this repository *has* been measured, it is
in [`CHRONICLE.md`](CHRONICLE.md) with the command that produced it.

---

## The claim

Give a system three things:

- persistent goals and state,
- a way to detect the gap between expected and actual states,
- and a policy for resolving that gap,

and its **observable behaviour** will exhibit functional patterns that look like
affect — urgency, frustration, relief, focus. Those patterns can be modelled and
engineered usefully without asserting anything about inner experience.

The theory is about what a system *does*, and is silent on what, if anything, it
is like to be one. That silence is deliberate and load-bearing.

## Why a new name

| Existing term | What it actually covers |
|---|---|
| Machine Psychology | Mainly tests LLMs with human psychology instruments |
| Robopsychology | Largely fiction, plus some human–robot interaction work |
| Artificial Psychology | A 1999 theoretical proposal, not an engineering stack |

None supplies a practical, buildable vocabulary. This does — four primitives and
a loop you can run.

## The four postulates

**1 — State is primary.** A stateless predictor cannot sustain affect-like
behaviour. Without persistence no gap can persist, and without a persisting gap
there is nothing for urgency to be *about*. Requires a Persistent State Store.

**2 — Affect is a signal, not a feeling.** The Affect Model is a classifier over
gap history. It answers a routing question — is progress stalled, is uncertainty
high, has a closed gap reopened — and its output selects an action. Nothing in
the label implies an experience.

**3 — Gap drives behaviour.** `Gap = Expected − Actual`. A non-zero gap is the
only drive in the system. It is a measurable delta, not an emotion.

**4 — Closure is the action.** A Closure Policy selects the concrete move:
rephrase, ask, switch tool, escalate, stop. Closure is the only thing that
changes state.

Together these give the loop in [Figure 1](docs/figure-1.svg):

```
State → Gap → Affect signal → Closure → LLM Core → State
```

Nothing can be removed without collapsing it. Remove state and no gap persists;
remove the gap and there is no drive; remove the label and closure cannot be
selected; remove closure and nothing changes.

## What CrystalCode™ adds

The theory becomes four language primitives instead of free-form prompting:

```
track(event)                      # commit an observation to state
detect_gap(expected, actual)      # → Gap | None
label_affect(gap_history)         # → closed | reopened | stalled | converging | uncertain
close_with(label, context)        # → ClosureDecision
```

Because each one logs, the loop becomes **measurable**: gap openings, labels,
closure attempts, and — critically — whether each closure attempt actually
worked. See [`crystalcode/SPEC.md`](crystalcode/SPEC.md).

## Falsifiable predictions — and what the harness measured

Each prediction is stated, then what has actually been tested. The tests live
in [`experiments/`](experiments/) and their committed results in
[`experiments/results/RESULTS.md`](experiments/results/RESULTS.md); rerun with
`python3 -m experiments.harness`. **Scope, stated plainly: these are
measurements of a scripted, deterministic environment. No language model is
involved. The predictions as claims about real LLM workloads remain Vision.**

**1. A system with a Gap Detector and a Closure Policy resolves repeated
queries in fewer turns than a stateless baseline on the same task set.**

*Tested in-sim, 12 August 2026 — supported in one precise sense, not
supported in another, and both are stated.* The full aggregate set, in one
place, because quoting only the favourable ones is how a benchmark lies:

- The loop resolves **5/6** with one policy and no task knowledge.
- The best **single** task-agnostic stateless policy resolves **2/6**.
- The per-task **best-stateless portfolio** — a different stateless policy
  allowed per task — also resolves **5/6**, and the loop is strictly faster
  than the best stateless on **zero** tasks.
- A **task-informed** stateless lookup (`tuned_lookup`, built from each
  task's definition) resolves **5/6**, faster-or-equal to the loop on every
  task both resolve, and fails only `deploy_rollback`.

So the supported claim is adaptivity, not speed: one stateful policy matches
the entire stateless portfolio without task knowledge, and wins outright only
where no stateless policy can exist at all. On the repeated-query task the
loop closes in 3 turns; of the six task-agnostic baselines, five never close
it, and the sixth — the constant whose fixed strategy happens to be the
answer — closes it in 1 turn and resolves nothing else in the suite. One
suite task, `strict_interview`, defeats the v0.1 closure policy outright
where plain `always_ask` resolves it in 2 — a measured limitation, kept in
the suite and pinned by a test. And one result is a construction rather than
a statistic: `deploy_rollback` presents byte-identical observations that
require different strategies, so **no** function of the current observation
can solve it, tuned or not — verified by exhausting all 25 observation→
strategy tables; the loop resolves it in 3 turns through its history. That is
postulate 1 operationalised.

**2. Closure success rate rises when the Affect Model can distinguish
`converging` from `stalled`, because the policy stops retrying a route that is
not narrowing the gap.**

*Tested in-sim by ablation — supported.* The `loop_stall_blind` ablation runs
the identical loop with a classifier that checks stalled before converging, so
a same-goal run with falling magnitude reads as stalled. It resolves 4/6 to
the loop's 5/6, failing the converging task outright (closure rate 0.0 where
the sighted loop measures 0.33). Building this ablation is also how a real
ordering defect in the shipped classifier was found and fixed — see
CHRONICLE.md, 2026-08-12.

**3. Removing the Persistent State Store collapses prediction 1 entirely — the
advantage is a function of state, not of the labels.**

*Tested in-sim — supported.* The `magnitude_reactive` baseline is exactly the
loop's per-observation knowledge with the history removed: it reads the current
gap and its magnitude, and nothing else. It resolves 2/6 — the control task and
the one task where progress is visible in the observation itself — and fails
every task where the signal lives in the history.

## Two failure modes the theory has to guard against

**Anthropomorphising.** Users read closure as caring, and grant the system
feelings it does not have. The mitigation is the label: if the behaviour looks
affective, it must be described as synthetic, every time. That is why the ethics
line opens every document here.

**Cosmetic closure.** If closure success rate is the metric, a system can learn
to *appear* to close gaps. The mitigation is structural rather than moral, and it
is implemented: a closure decision is recorded as `pending`, and the **following
cycle** judges it against whether the gap actually shut. Nothing in this codebase
lets a decision grade its own outcome.

## Hardware future

The right-hand column of Figure 1 is **Vision, and unbuilt.** The argument is
that the theory stops being pure simulation once a system has real physical
variables to regulate — power, heat, balance, sensor continuity. At that point
gaps become grounded drives rather than modelled ones. Until sensors exist and
produce evidence, that column stays labelled as what it is.

## For a thesis defence

- Define Synthetic Affect explicitly as apparent / functional affect, for design
  purposes only.
- Lead with the falsifiable predictions, and concede exactly what has been
  tested: a scripted, deterministic environment. On real LLM workloads they
  remain untested — and concede the adverse results too, by name: the loop is
  never strictly faster than the best stateless policy per task, and one task
  defeats it.
- Concede prior art directly. A narrow claim that survives scrutiny beats a broad
  one that dies on contact.
- Keep the ethical requirement in the text, not in a footnote: if the behaviour
  looks affective, label it synthetic.

### Dated note — 2026-08-13

Parked here as **method**, not as a fifth postulate. The four postulates
above are unchanged.

**What a defence can say**

1. Synthetic = functional, never inner.
2. Left column of Figure 1: 5/6 vs 2/6, adaptivity not speed. Concede
   `strict_interview`, and that the loop is never strictly faster than the
   per-task best stateless. `deploy_rollback` is the construction only
   history can solve.
3. Right column: Vision. Unbuilt.
4. The method of writing is load-bearing: Belt-Three, chronicle form,
   pending-then-judge, logs with no wall clock.
5. Prior art conceded (machine psychology, robopsychology, artificial
   psychology).

**What it cannot say:** hardware drives as measured; the predictions as
claims about real LLM workloads; SAT as feeling or consciousness;
Country; a partnership with any model vendor.

**Why the figure needs the stub label.** The LLM Core box is a
deterministic offline stub. Its output is not fed into the next `actual`.
The return arrow is architecture; reading it as Science overclaims. See
[`docs/FIGURE-1.md`](docs/FIGURE-1.md).

**Why `PASS — uncertain` was a scandal.** An earlier classifier asked
whether a gap had *ever* existed, so `closed` was unreachable and a
selftest could still print PASS. The rebuild classifies the tail,
persists state, and lets the next cycle judge. The harness then caught
stalled-before-converging. That order (converging first) is law on this
tree.

**Not this thesis.** `mythos/art` has its own catalogue. SAT classifies
gap history, not images. *Official* here means the public artefact
(this page, the figure, the committed logs) written so it can be
defended — not a grading of the visual canon.

---

**All rights reserved.**
TerAustralis Incognita™ — ABN 70 741 068 059
