---
type: OpenItem
id: W-80
title: "W-80 — fux tells users to run a tool that is not in the repo, and the bundled model's provenance is an archive citation"
description: "`tools/distill/` is archived at `archive/v0.26/tools/distill/`, but two live error messages and `model.json`'s `recipe` field still point at the live path. Archive-is-not-evidence makes 'point at the archive' illegal, so the fork is narrower than it looks. Blocks any model swap."
status: open
lane: agent
timestamp: 2026-08-24T00:00:00Z
---

# W-80 — the bundled model's recipe is not in the repo

## The defect, at the surface a user hits

`src/fux/embed/model.py` tells a user with a missing or corrupt model to run a
path that **does not exist**:

```
model.py:51   "it with tools/distill/distill.py (lexical search still works: --lexical-only)"
model.py:56   f"embedding model is corrupt ({exc}) — rebuild via tools/distill"
```

`ls tools/` → `archived-signal-eval differential graph-bench maintenance-bench
pruning-eval refer-bench refer-budget-sweep t2-eval`. **No `distill`.**

And `src/fux/embed/data/model.json` carries the same dead pointer as a
**provenance claim**:

```json
"recipe": "tools/distill/distill.py (see tools/distill/README.md)"
```

## It is recoverable, and it is demonstrably the right recipe

`archive/v0.26/tools/distill/distill.py`, archived by the v0.26 reset
(`7fb81a8`), matches the shipped bundle on **every** checkable field:

| | archived script | shipped `model.json` / runtime |
|---|---|---|
| teacher | `TEACHER = "minishlab/potion-base-8M"` | `"teacher": "minishlab/potion-base-8M"` |
| magic | `MAGIC = b"FUXEMB1\0"` | `model.py` `MAGIC` |
| quantization | `"int8 per-vector symmetric, scale = max|v|/127"` | **verbatim** |

⚠ **The bundle's own integrity claim passes** — `sha256` and `size_bytes` in
`model.json` both match `model.bin`. **Integrity is fine; provenance is what is
missing.**

## The fork is narrower than it looks

**A — restore `tools/distill/` live.** It is dev-only and has heavy deps
(`numpy`, `model2vec`), which is exactly what `tools/` already is: every other
directory there is a dev-only instrument with deps `src/` may not have. L1
constrains the **runtime**, not the workshop.

**B — retire the claim: repoint the messages and `model.json` at the archive.**
⚠ **This is not legal.** `model.json`'s `recipe` is a **live claim** and
CLAUDE.md's archive-is-not-evidence rule forbids grounding one in an archived
document. B would have to *delete* the provenance claim, not relocate it — and
then the shipped bundle has none at all.

**Recommend A.** B is only coherent as "we accept the model cannot be rebuilt",
which is a strange thing to accept about 7.9 MB of committed package data.

## Why it matters beyond tidiness

**It blocks any model change.** The dense lane
[failed its gate](../regression/2026-08-24-dense-lane-gate/VERDICT.md) on
2026-08-24 (0 fixed / 2 broken), and the bundled teacher is
**`potion-base-8M` — a general-purpose static embedding used for a retrieval
task** when a retrieval-tuned sibling exists
([proposal](../proposals/retrieval-tuned-static-embedding.md)). **Nothing can
be swapped, compared or re-measured while the recipe is archived.**

## Definition of done

- [ ] Ruled: A (restore) or A-with-a-rewrite.
- [ ] If A: `tools/distill/` live, its README with it, and **the reproduce
      command actually run once** to confirm it still regenerates a `model.bin`
      whose sha matches the committed one. A recipe nobody has executed since
      2026 is a claim, not a recipe.
- [ ] The two `model.py` error messages resolve to a real path.
- [ ] `no ADR affected`, or ADR-ENRICHED / the record owning `src/fux/embed/`
      amended — **check the ownership table; `embed/` is currently claimed by
      ADR-T1-ACCELERATOR, which W-77 already flagged as misleading.**
