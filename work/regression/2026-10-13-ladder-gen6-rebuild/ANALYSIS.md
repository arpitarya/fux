---
type: Analysis
description: "What the generation-6 rebuild leaves: a correct ladder, and a builder that waits on gpg when commit signing is on."
run: 2026-10-13-ladder-gen6-rebuild
item: W-278
---

# ANALYSIS — the generation-6 ladder

## 1 · Commit signing stalled the largest rung for 12 hours

**Finding.** `rung-10000` built in 43 690 s against 508 s for `rung-05000`.
**Cause:** the rung is a git repository and the builder commits per date; the
user's global `commit.gpgsign = true` signs each commit, and gpg blocked.
**Change:** none here (the builder is fux-lab's, unmodified). Owed:
[W-281](../../open/W-281-capture-harness-speed.md) DoD 1. Repro: any rung build
with `commit.gpgsign = true` and a locked gpg agent.

## 2 · Nothing else to fix

Every count matches, nesting holds; the name-leak hazards are hard negatives,
not fact leaks.
