# Chronicle — Synthetic Affect Theory™

Dated record, in the project's own form: **Evidence → Interpretation →
Experiment → Record.** Belt labels apply here as everywhere.

---

## 2026-08-12 — public v0.1

**Evidence.** A reference implementation of the loop was drafted with assistance
from Meta AI and delivered as a ~20-file package. It was read in full and run
before anything was changed. Measured on this machine:

- `python3 -m core.selftest` — passed, exit 0
- `python3 -m pytest tests -q` — 5 passed
- `examples/logs/*.jsonl` — 779 and 1536 bytes, byte-reproducible across reruns

Those three claims were made about the draft and all three held. The logs are
genuine outputs, not hand-authored.

**Interpretation.** What the logs *recorded*, however, was a broken classifier.
`AffectModel.classify` asked whether any gap had ever existed rather than whether
one exists now:

```python
gaps = [g for g in hist if g is not None]
if not gaps: return "closed"
```

So `closed` became unreachable the moment a first gap opened. Confirmed by
running it: `classify([gap, None])` → `uncertain`. Both example logs show a gap
being resolved and the system still reporting `uncertain` / `ask`. A theory whose
central act is closure had an implementation that could not express closure.

The draft's selftest passed anyway, because it asserted only that a gap was
present or absent and never checked the label. It printed `PASS — uncertain`.

Four further findings, all confirmed by reading or running:

- `PersistentStateStore` accepted a path, stored it, and never read or wrote it.
  Postulate 1 — *state is primary* — had no implementation at all.
- `ClosureDecision.outcome` was stamped at decision time (`"asked"`, `"closed"`).
  A closure-success-rate computed from that field reads 100% forever — the
  Goodhart failure this theory is supposed to guard against, present in the
  guard itself.
- `crystalcode` bound its primitives to module-level globals, so a second `Loop`
  in one process would silently hijack the first one's store and logger.
- `docs/figure-1.svg` placed two boxes below a 400-unit `viewBox`; they were
  clipped in every renderer. The LLM Core box was absent entirely.

**Experiment.** Rebuild keeping the draft's design and fixing what the run
exposed. Classifier reads the tail of history, not the whole of it. State store
writes JSON and reloads. Decisions are judged by the *following* cycle. Runtime
is an explicit object. Figure redrawn at 900×560 with the LLM Core box and the
feedback arrow present.

**Record.** Measured on this machine, 12 August 2026:

- `python3 -m core.selftest` — PASS: 3 cycles, 12 log lines, closure success rate
  0.50, state survived being reopened
- `python3 -m pytest tests -q` — **30 passed**
- Example 01 — `0.67 → 0.33 → closed`, labels `uncertain → converging → closed`
- Example 02 — `uncertain → closed → reopened → closed`
- Logs byte-reproducible; `git diff --stat examples/logs/` empty after a rerun

The closure success rates are 0.50 and 0.67, not 1.00, because failed attempts
are now recorded as failures.

**Still Vision, still unbuilt.** The hardware column. The stateless-baseline
comparison harness — until it exists, "fewer turns than a stateless baseline"
is a prediction and is labelled one in `THEORY.md`.

---

**All rights reserved.**
TerAustralis Incognita™ — ABN 70 741 068 059
