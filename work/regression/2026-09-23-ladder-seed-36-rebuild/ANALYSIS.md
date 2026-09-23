---
type: Analysis
run: 2026-09-23-ladder-seed-36-rebuild
description: "Why the ladder went stale, why it was rebuilt in place, and the three things a later reader of these rungs should know."
---

# ANALYSIS — the 42-document ladder

## 1 · Why it went stale

Prompt 10 added 14 seed documents on 2026-09-23. A rung is frozen against the
exact bytes of `work/golden/seed/`, so every rung went stale the moment those
documents landed. The gate caught it, as designed. ⚠ **The gate caught it only
after `3.0.0-alpha.3` had shipped over it.** The eight red rows were named in the
release commit as "known red", and that turned `main`'s CI red for every matrix
cell. **Adding seed documents and rebuilding the ladder belong in the same push.**

## 2 · Why in place

The builder opens by deleting the rung directory, and the lab corpora are kept,
never wiped (Arpit, 2026-09-12). The driver instead edits each rung's git repo:
it adds the seeds and drops the ext tail. The from-scratch cross-build, done in a
scratch directory, agrees on every manifest and every index root. So in place
cost nothing in fidelity, and the rungs' git history survives.

Before the run, `rung-01000` held an uncommitted Node reader bundle
(`.fux/node/`) left over from alpha.2. The alpha.3 re-ingest rewrote it, and it
is committed in that rung's index commit. Every rung also carries an untracked
`fux.toml`, byte-identical across all eight. The run left those files as they
were.

## 3 · What moved, and why

- **Superseded is up 2 on the seed.** TMS-44 supersedes TMS-41, and LQ-53
  supersedes LQ-51. Both are seed-to-seed.
- **Ext's archived and superseded counts are each down 1 above the seed.** The
  14 dropped ext documents held one whole supersession pair, and no pair was
  split. That is the same rule §3 of the 2026-09-21 analysis proves: truncation
  only ever drops the later member.
- **82 ref edges, up from 61.** The new seeds link to the older ones. As on
  2026-09-21, every edge is a seed-to-seed link written by one author, so a link
  feature measured here is measured on one author's linking style.

## 4 · The generator's banned-name list is behind the seed

The generator's list of seed entities it must never mention predates seeds
16–36. It was not edited. Instead, `rung-10000/ext/` was searched for every
capitalised word and code in seeds 23–36. No `TMS-`, `LQ-` or `QCL-` identifier
and no new person appears. The matches were common words, "Nashik" (already in
the older seed, and in ext since 2026-09-12), and room codes such as `VTX-D3`
that name other companies' rooms. **Extending the list is owed before the next
seed change**, because it is the mechanical form of prompt 4's "no fact about a
seed entity" rule.

## 5 · Every golden number filed before today names a ladder that no longer exists

That includes the 2026-09-23 RM3 arms, which were captured on the 28-document
`rung-01000`. They stay the pre-seed-36 baseline and are never differenced
against this ladder. No pre-registration pins a rung index root, so no threshold
moved.
