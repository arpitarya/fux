---
type: Analysis
description: "What the generation-5 rebuild leaves: a ladder whose smallest named rung is now as large as the seed, and nothing to fix before W-270's capture."
run: 2026-10-11-ladder-gen5-rebuild
item: W-270
---

# ANALYSIS — the generation-5 ladder

## 1 · `rung-00100` stopped meaning *100 documents*

**Finding.** The seed is 118 documents; the builder refuses any rung smaller
than the seed. **Cause:** each generation adds seeds and no rung moves.
**Change (ruled, made):** Arpit chose to keep `rung-00100` at 118 documents,
so it now equals `rung-seed`. A seed that grows past 200 reaches `rung-00200`
next. Repro:

```bash
python3 work/regression/2026-10-11-ladder-gen5-rebuild/evidence/build_from_worktree.py <clean worktree> rung-00100 118
```

**Unresolved:** whether the ladder's small end needs a different shape when the
seed outgrows the next rung. Not asked here.

## 2 · Nothing else to fix

Every count matches, nesting holds, the generated stream is deterministic and
the ref census is unchanged. The name-leak hazards (report) are hard negatives,
not fact leaks. Repro of the whole build: `evidence/build.log`'s eight
`build_from_worktree.py` calls, in rung order, from a clean worktree at
`9ab19fc6` with its own venv.
