# Examples

Both scripts are deterministic and write their own log into `logs/`.

```bash
python3 examples/01_repeated_query.py    # a gap that narrows, then closes
python3 examples/02_gap_reopens.py       # a gap that closes and reopens
```

**The logs in `logs/` are committed outputs of an actual run**, produced by the
commands above on 12 August 2026. They contain no wall-clock timestamp, so a
fresh run reproduces them byte for byte:

```bash
python3 examples/01_repeated_query.py && python3 examples/02_gap_reopens.py
git diff --stat examples/logs/     # must be empty
```

If that diff is not empty, the logs are not outputs and should not be trusted as
evidence of anything. **Belt: Science** — this is the check that earns the label.

---

**All rights reserved.** TerAustralis Incognita™ — ABN 70 741 068 059
