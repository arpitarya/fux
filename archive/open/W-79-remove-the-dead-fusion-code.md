---
type: OpenItem
id: W-79
title: "W-79 — remove the dead fusion code and the inert flag"
description: "`query/hybrid.py` is off the live path, its two `[fuse]` tune keys have no CLI reader, and `explain --no-tune` parses and does nothing. Three things that look shipped and are not. Agent-executable."
status: open
lane: agent
timestamp: 2026-08-24T00:00:00Z
---

# W-79 — three things that look shipped and are not

Arpit, 2026-08-24: *"we need to remove the dead code."*

## What is actually dead — and one thing that ISN'T

**1. `src/fux/query/hybrid.py` is off the live path.**
`run_query` routes `--hybrid` through [`query/dense.py`](../../src/fux/query/dense.py)'s
gated fusion. `hybrid_ask` is reached only from
`tools/differential/playground_grade.py`. The module's own docstring says so;
nothing acts on it.

**2. `[fuse] rrf_k` and `[fuse] dense_width` have no CLI reader.**
They are validated by [`tune.py`](../../src/fux/tune.py), documented in the
specimen `fux setup` writes, and consumed **only** by `hybrid_ask` — so they
are settable, checkable, and unreachable. Same root cause as 1.
Disclosed in [ADR-TUNE](../../docs/adr/0038_tuning.md)'s 2026-08-24 amendment
rather than discovered later.

**3. `explain --no-tune` is inert.** `cmd_explain` reads no tunable. The flag
was added for a consistent surface across the three graph verbs and is a
promise with nothing behind it.

> ⚠ **`[dense] mode = "gated"` is NOT dead, and an earlier reading said it was.**
> It did not fire at `threshold = 0.5` or `2.0` because the top lexical score on
> the playground is ~8.08 and the gate is `score < threshold`. At `8.0` it fires
> on some queries; at `100` on all. **The code works.** It failed
> [its own gate](../regression/2026-08-24-dense-lane-gate/VERDICT.md) on what it
> lets through, which is a different disposition entirely: **keep the code, keep
> it `off`, keep the verdict.** Deleting it would destroy the thing that made the
> FAIL measurable.

## The decision this actually needs

**Delete, or wire up?** They are the same three items either way:

| | delete | wire up |
|---|---|---|
| `hybrid.py` | -1 module, -2 tune keys, `playground_grade.py` moves to `run_query` | give `--hybrid` an RRF path again, and grade it |
| `[fuse]` keys | leave the closed key set smaller and honest | keys become reachable; needs a gate before they mean anything |
| `explain --no-tune` | remove the flag | make `cmd_explain` read the tune (it reads none today) |

**Recommend delete.** `ask --hybrid` already has a live lane; a second fusion
implementation that only a tool calls is exactly the drift ADR-TUNE decision 1
exists to prevent, and the `[dense]` FAIL means the RRF path has nothing to
prove right now.

⚠ Deleting the two `[fuse]` keys is a **closed-key-set change**, so it is a
change to ADR-TUNE, not a tidy-up — decision 5 says so explicitly. It also
breaks any consumer who set them; they have been reachable-but-inert for one
release, so the blast radius is small and should still be stated in CHANGELOG.

## Definition of done

- [ ] Ruled: delete or wire up.
- [ ] If delete: `hybrid.py` gone, `[fuse]` out of `_SCHEMA` and the specimen,
      `explain --no-tune` removed, `playground_grade.py` repointed at
      `run_query`, ADR-TUNE and ADR-CLI amended in the same change.
- [ ] `tests/test_tune.py`'s specimen/schema round-trip still passes both ways.
- [ ] CHANGELOG entry naming the removed keys.
