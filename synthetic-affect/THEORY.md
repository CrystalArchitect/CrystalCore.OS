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

## Falsifiable predictions

**Belt: Vision. None of these has been tested here.** They are written to be
refutable, and a fair test could refute them.

1. A system with a Gap Detector and a Closure Policy resolves repeated queries
   in **fewer turns** than a stateless baseline on the same task set.
2. Closure success rate **rises** when the Affect Model can distinguish
   `converging` from `stalled`, because the policy stops retrying a route that
   is not narrowing the gap.
3. Removing the Persistent State Store collapses prediction 1 entirely — the
   advantage is a function of state, not of the labels.

The harness for prediction 1 is not written. Until it is, prediction 1 is a
prediction.

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
- Lead with the falsifiable predictions, and concede that they are untested.
- Concede prior art directly. A narrow claim that survives scrutiny beats a broad
  one that dies on contact.
- Keep the ethical requirement in the text, not in a footnote: if the behaviour
  looks affective, label it synthetic.

---

**All rights reserved.**
TerAustralis Incognita™ — ABN 70 741 068 059
