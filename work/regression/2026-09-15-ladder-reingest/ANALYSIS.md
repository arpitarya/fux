---
type: Analysis
run: 2026-09-15-ladder-reingest
description: "Why nine days of silence was structural, the check that would have caught it and why it is not built here, and what a re-ingest does and does not preserve."
filed: 2026-09-15
---

# ANALYSIS — nine days of a silent ladder

## 1 · The diagnosis

**The ladder has no reader but a person.** Every other committed artifact in
this repository is held by something that runs: the index by `fux doctor` and
the merge driver, the records by four ownership tests, the docs by a link gate,
the harness — since today — by
`tests/derive/test_differential_harness.py`. **A golden rung is read only when a
session goes looking**, and between 2026-09-06 and 2026-09-15 nobody did.

Three changes landed in that window, each correct, each with its own refusal
message, each fatal to every rung:

1. **W-151/W-152** retired three `[ranking]` priors with a *hard* refusal — by
   design, so a typo fails loudly. A frozen corpus has no typo to fix; it has a
   file nobody will edit.
2. **W-164** moved `urls_file` one level up, same shape.
3. **W-168 step 1** bumped `_format` to `v3`, which
   [SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) decision 3
   makes a refusal rather than a misread — also correct, also fatal here.

🔴 **Each one is a good decision whose blast radius nobody swept.** The pattern
is not "a bad refusal"; it is **a refusal whose affected population lives
outside the repository that made it**.

## 2 · The check that would have caught it, and why it is not in this change

**A ninth row in `tools/differential/ladder_check.py`:** for each rung, if the
corpus is present, run one `fux ask` and report the exit code.

It is not built here, and the reason is not effort:

- `ladder_check.py`'s stated virtue is that **it reads no corpus**, so it runs
  on a fresh clone and a GitHub runner. A row that needs `fux-lab` would be
  skipped everywhere it currently runs and green everywhere it is skipped —
  which is the shape of a check that says nothing.
- The honest version is a **separate** lab-side script, and where it should live
  and who should run it is a decision about `fux-lab`, not a line to add while
  clearing a backlog.

**So it is named as unresolved rather than half-built.** ⚠ Filing this as *fixed*
would leave the next `_format` bump exactly where this one was.

## 3 · What a re-ingest preserves, and what it does not

| | |
|---|---|
| **preserved** | every document, byte for byte — the manifests are untouched and the per-document check is clean on all eight |
| **preserved** | the ladder's nesting property, re-verified after the fact |
| **changed** | `.fux/index/` (derived from those documents, committed by design), `.fux/tune.toml`, `fux.toml` |
| 🔴 **not comparable** | **any absolute number measured on the old indexes.** Term hashes and `df` are unchanged, so a *ranking* comparison survives; a *latency* comparison does not, because the shards were rewritten by a different engine |

⚠ **The second row of that table is the trap.** A session reading a filed ladder
timing from before today and one from after will find both quoted in the same
units. `engine_commit:` in the stamp is what lets them tell the two apart.

## 4 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | eight rungs re-ingested at `fux.index.v3`, configs fixed, rungs committed | `evidence/reingest.py` |
| 2 | eight stamps rewritten, and **`engine_commit:` added** — the version alone was a false match | `cat work/golden/ladder/rung-seed.index` |
| 3 | `work/golden/README.md` describes the new field where it describes the stamp | — |
| 4 | **W-180, W-154 Part B and W-175 unblocked** | `work/OPEN-WORK.md` |

## 5 · Unresolved

- 🔴 **Nothing detects the next one.** §2. The lab-side check is a decision, not
  a line.
- **Whether a rung should be re-ingested automatically on a version bump.**
  That would write to a frozen corpus without a person asking — a bigger
  decision than this run, and not one to take while clearing a backlog.
- **Whether `2.0.1` should have been bumped when `v3` landed.** The changelog's
  `[Unreleased]` shape says no; the stamp's false match says the ambiguity is
  real. `engine_commit:` routes around it rather than settling it.
