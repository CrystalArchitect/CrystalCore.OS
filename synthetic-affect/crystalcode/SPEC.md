# CrystalCode™ — Operator Spec v0.1

> Synthetic = apparent / functional, for design purposes. Not a claim of
> feeling, consciousness, or inner experience.

Four primitives. Each one logs, which is what makes the loop measurable rather
than merely describable.

Every primitive takes an optional `runtime`. Omit it and the module's default
runtime is used; pass one and the call is isolated — two loops in one process
cannot overwrite each other's store or log.

---

## `track(event: dict, runtime=None) -> None`

**Postulate 1.** Commits an observation to the Persistent State Store and logs
`op: "track"`.

The store is only persistent when constructed with a path. `":memory:"` is
available and is named honestly — `store.is_persistent` reports `False`.

## `detect_gap(expected, actual, runtime=None) -> Gap | None`

**Postulate 3.** `Gap = Expected − Actual`.

Equality returns `None` and logs `gap_none`. Difference returns a `Gap` and logs
`gap_opened`. Scalars are all-or-nothing (`magnitude == 1.0`); dicts are scored
per differing key, so a partially-correct state reads as a partial gap and the
classifier can see it narrowing.

`Gap(id, expected, actual, magnitude, kind)` — `id` increments per gap opened.

## `label_affect(gap_history, runtime=None) -> str`

**Postulate 2.** Classifies the *current* situation from the tail of history.
`gap_history` is the per-cycle record: a `Gap` where one was open, `None` where
none was.

| Label | Condition |
|---|---|
| `closed` | no gap this cycle, or no history at all |
| `reopened` | a gap this cycle, none last cycle |
| `converging` | this gap's magnitude is smaller than last cycle's |
| `stalled` | three consecutive gaps against the same expectation, with no progress this cycle |
| `uncertain` | a gap that is not narrowing and not yet a run |

The rows above are in check order — precedence reads top to bottom.

Order matters: `closed` → `reopened` → `converging` → `stalled` → `uncertain`.
Converging is checked before stalled, deliberately: a same-goal run whose
magnitude is falling is progress, and labelling it stalled would route the
policy away from a strategy that is working. The experiment harness caught an
earlier ordering doing exactly that — `CHRONICLE.md`, 2026-08-12.

**Every label must be reachable.** `tests/test_affect.py` asserts the set of
labels the model can actually emit equals `LABELS`, so a dead branch fails the
suite instead of hiding in it.

## `close_with(label, context=None, runtime=None) -> ClosureDecision`

**Postulate 4.** Selects the concrete move.

| Label | Strategy |
|---|---|
| `closed` | `stop` |
| `reopened` | `rephrase` |
| `converging` | `rephrase` |
| `stalled` | `switch_tool`, then `escalate` on the second consecutive stall |
| `uncertain` | `ask` |

The stall counter resets on any non-stalled label, so a session that stalls,
recovers, and stalls again later gets `switch_tool` first rather than escalating
forever after two stalls in its whole history.

### The rule that matters most

`ClosureDecision.outcome` is **`pending`** when the decision is made. The
*following* cycle sets it to `worked` or `failed` by observing whether the gap
actually shut, and logs `closure_outcome`.

Nothing lets a decision record its own success. A closure-success-rate computed
from a self-reported outcome would read 100% forever, which is precisely the
cosmetic-closure failure this theory has to guard against.

`Loop.closure_success_rate()` returns `None` before anything has been judged — an
unmeasured rate is not zero and must not be reported as one.

---

## Log schema

One JSONL line per event. No wall clock anywhere, so logs are byte-reproducible.

```json
{"cycle": 2, "seq": 7, "op": "closure_outcome",
 "data": {"strategy": "ask", "outcome": "failed"}}
```

- `cycle` — the loop cycle, incremented once per `run_cycle`
- `seq` — the line's position in the file
- `op` — `track` · `gap_opened` · `gap_none` · `label` · `closure` · `closure_outcome`

---

**All rights reserved.**
TerAustralis Incognita™ — ABN 70 741 068 059
