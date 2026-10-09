---
type: Analysis
description: "What the W-236 build and capture leave to decide: the verdict (Arpit's score, then a non-capturing session's decide.py), and the one cost outside the bar — section records on .jsonl and long Markdown, 8.0x the document plane on this repository."
run: 2026-10-10-section-records
item: W-236
filed: 2026-10-10
---

# Analysis — section records, before the score

## 1 · The verdict path, unchanged from the bar

1. **Arpit scores** the five hand-offs: `just golden-score work/regression/2026-10-10-section-records`.
2. **A session that did not capture** runs
   `python3 work/regression/2026-10-10-section-records/evidence/decide.py`. It
   checks G2 first, then applies the frozen table, and writes `decision.json`
   and `per-query.jsonl`.
3. On **PASS**, the first clearing λ becomes the `[ranking] section_weight`
   default and branch `w236-sections` merges with the bar's §If it passes list,
   and §2 below must be settled in the same change. On **FAIL**, the
   branch is Arpit's to keep or drop. Nothing reached `main`, so no `_format`
   number is spent.

Repro of the capture: [`report.md`](report.md) §1. Each arm is one
`golden_run.py` call against its copy, with the pinned build engine.

## 2 · The cost outside the bar — `.jsonl` and long Markdown

**Finding.** On this repository the build's section plane is **8.0×** the
document plane (337.5 MB against 42.1 MB). By source format:

| extension | section bytes | share | sections |
|---|---:|---:|---:|
| `.jsonl` | 255.2 MB | 75.6 % | 79 611 |
| `.md` | 77.7 MB | 23.0 % | 14 004 |
| `.json` | 3.9 MB | 1.2 % | 4 522 |
| everything else | 0.6 MB | 0.2 % | 608 |

**Cause.** The `.jsonl` decoder emits one sibling heading per record, so
decision 2 makes each record a section, as the record intends. Each one then
carries its own copy of the field names and repeated values every record
shares. Postings that one document line holds once are held 300 times. The
ladder is all prose, which is why G1 reads 0.98× there and this reads 8.0×.

**Why it is not a stop.** No frozen commit limit fails: the largest file is
6.2 MB against 50 MiB, and the total is 0.38 GB against 1 GB. G1 is about the
ladder, and G1 passed. SR-SECTIONS' veto reads only the ladder.

**Why it is Arpit's before any merge.** A PASS merges a format bump that every
consumer re-ingests, and this repository is the first consumer. Three
options, none taken:

| | what | cost |
|---|---|---|
| (a) | accept it: this repo's index grows 42 → 380 MB | git history carries it permanently |
| (b) | no section records for decoded record formats (`.jsonl`, `.csv`, `.json`), only for prose | a record amendment and a format-class list. A ranking change for those formats is then never measured |
| (c) | a size cap per document, past which a document is sectionless | a tunable cannot reach a committed byte (SR-TUNE d6), so it would be a fixed constant, and its value would be a guess |

Repro: build the branch, `fux ingest --full` in a scratch copy of this
repository, then sum `.fux/index/sections/*.jsonl` by parent extension. The
numbers above are [`evidence/own-repo-sizes.json`](evidence/own-repo-sizes.json).

## 3 · What the build settled that the design left open

Each was written into [SR-SECTIONS](../../../records/0161_sections.md) on the
branch **before any arm ran**, as the bar requires:

- **Decision 9, the merge driver, amended.** *"The parent's verdict"* cannot be
  built, because git merges one file at a time. A section shard now merges by
  parent group, and both-sides-changed is refused.
- **Decision 3:** a totality miss makes the document sectionless. The ladder
  measured none (G1: 0).
- **Decision 5:** a best of zero names no section.

None of them moves a ranking number. G0 shows the first two cannot reach a
query at `0.0`, and the third only changes what `section` says.

## 4 · Unresolved

- Whether `.jsonl` sections help or hurt **ranking** is unmeasured. The golden
  ladder has no such documents.
- The capture's latency gap (§3 of the report) is attributed to load from one
  standalone re-run. That is not a benchmark.
