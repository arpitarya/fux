---
type: Analysis
run: 2026-09-27-ladder-gen3-rebuild
description: "Why the generation-3 ladder was rebuilt from scratch, why the generation-2 rungs were kept, the seed-name leak search, and the one thing a phase-5 run at a later engine must do first."
---

# ANALYSIS — the 68-document ladder

## 1 · Why from scratch this time

The 2026-09-23 rebuild was done in place because it added documents and nothing
else. Generation 3 also adds **history**. `seed-history.tsv` gives 12 documents
their earlier revisions, and those revisions are dated before commits already in
every rung. A rung's history is chronological by construction, so the new
commits cannot go on top of the old ones. So the builder rebuilt each rung from
nothing. Its `rmtree` only ever reached empty directories, because the
generation-2 rungs had already been moved to `golden-gen2/`.

## 2 · What moved, and why

- **Seed 42 → 68, and every rung keeps its headline size.** Each rung above the
  seed carries 26 fewer generated documents, the rule since 2026-09-21.
  `rung-10000` stays at the [SR-WORK-SCALE](../../../records/0057_WORK-scale.md) ceiling.
- **Archived and superseded are each down 3 above the seed.** The seed's own
  counts are unchanged at 6 and 6. The 26 dropped ext documents held three
  whole supersession pairs, and truncation never splits a pair (§3 of the
  2026-09-21 analysis).
- **`ref` edges stay at 82.** Seeds 37–62 carry no inline links, so a link
  feature still measures one author's linking style.

## 3 · The generator's banned-name list is still behind the seed

The 2026-09-23 analysis said to extend the list *before the next seed change*.
**It was not extended**, and this rebuild did not extend it either: a change to
the generator is a change to every rung's bytes. Instead,
[`evidence/new_seed_name_leaks.py`](evidence/new_seed_name_leaks.py) intersected
every capitalised word and code that first appears in seeds 37–62 with the
words of `rung-10000/ext/` (287 tokens; 49 in both). **None is a seed entity**:
- 26 are dates;
- 22 are common words (`Audit`, `Saturday`, `Ammonia`, …);
- 1 is **`Sheikh`**. In seed 60 it belongs to a seed owner, Saira Sheikh. In ext
  it occurs 821 times, and every one is the generator's own `Imran Sheikh`, a
  different person.

The same search over the 20 hand-authored hard negatives found the same
surname and nothing else. ⚠ **A surname shared across the seed and ext is a
retrieval hazard, not a fact leak.** A query naming only "Sheikh" meets 821
decoys. **Extending the list is still owed**, and doing it will not change the
bytes unless a leak exists, because the list only refuses.

## 4 · The ladder is frozen at `80495b44`, and HEAD has moved past it

W-225 stage 2 (`0cbbc44b`, landed during this build) makes every
`.fux/tune.toml` key required. That engine refuses these rungs by name: seven
keys are missing from the `tune.toml` that `fux setup` wrote at `80495b44`.

A probe rung built at `0cbbc44b` had the **same index root and the same
manifest** as `rung-seed`, and a different `tune.toml` header. **The frozen
records therefore hold.** A phase-5 run at a later engine does what phase 5
already says for a mismatched engine: on the rung, or on a copy, it runs
`fux doctor --fix` (and re-ingests if the index format moved), then records it.
Stages 3a and 3b will add `output.toml` and `fux.toml` to that list.

## 5 · Commit hashes are not reproducible, and nothing depends on them

The machine's git config signs commits with GPG, and the signature carries its
own time. Two builds of `rung-seed` produced **identical trees at every commit**
but different commit hashes. So `rung_head_commit` is new on every build, as
every earlier rebuild's report found. The manifests and index roots are the
reproducible claim.

## 6 · A new baseline

A rebuilt ladder is a new baseline (A23). Every golden number filed before
today, including the step-4 arms and the 2026-09-24 capture, names a
generation-2 rung. Those rungs are still on disk under `golden-gen2/` and are
never differenced against this ladder.
