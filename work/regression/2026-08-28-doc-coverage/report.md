---
type: Report
title: doc_coverage — the signal separates the case, the threshold does not
description: "Per-document coverage is computed and published. Gating the band on it is held: the one decoy that reaches the clause sits at 0.710, inside the real goldens' 0.401-1.000 range, so no floor separates them."
classification: informed
timestamp: 2026-08-28T00:00:00Z
---

# `doc_coverage` — what it can and cannot decide

**Why it exists:** [the decoy control](../2026-08-27-decoy-control/report.md)
found one of fifteen unanswerable questions reported `grounded`, because
`coverage` and `missing` are **corpus-wide** and the query's four terms sat in
four *different* documents.

**Ruled by Arpit 2026-08-28:** add per-document coverage alongside, and let
`grounded` require both. **The first half shipped. The second is held on this
measurement**, which he did not have when he ruled.

> ⚠ **A SURFACE CAPTURE of two distributions.** It gates no prediction and
> pre-registers no threshold — and the finding is precisely that **it must not
> be used to pick one**.

## What shipped

- **`doc_coverage`** — the same idf mass as `coverage`, over the **top-ranked
  document's own terms**. Always present in `--json` and the MCP result.
- **`coverage` is unchanged.** A consumer reading `coverage: 1.0` today gets the
  same number tomorrow; the field was **added, not redefined**.
- **Derived in `rank()` and handed out through `stats_out`** — the seam
  ADR-CONFIDENCE already owns. Both the accelerator and the scan reach `rank()`
  with the same record dicts, so **the two paths cannot disagree** and the
  differential law is untouched. Deriving it anywhere else would mean re-reading
  the index on one path and not the other.

## The measurement

Playground corpus, 10 documents, enriched, reranker on. **50 real goldens** and
**15 decoys**. Only rows that *reach* the clause are counted — anything with a
term missing corpus-wide is already `partial` and never gets that far.

| population | n | min | median | max |
|---|---:|---:|---:|---:|
| **real goldens** | 37 | **0.401** | 0.882 | 1.000 |
| **decoys** | **1** | **0.710** | — | 0.710 |

## The finding

**The distributions overlap, and the decoy is inside the goldens' range.**

- Any floor that catches the decoy at `0.710` also demotes every real answer
  below it — and there are real answers down at `0.401`.
- A floor of **`1.0`**, which reads structural (*"every term the corpus has, the
  cited document has too"*), turns **19 of 50 correct answers `partial`**.
- **There is no gap to pick a number in.** Picking one anyway would be fitting a
  threshold to 65 queries — the failure
  [R10](../2026-08-27-r10-separation-floor/VERDICT.md) is currently
  `INCONCLUSIVE` over, in a different costume.

⚠ **And the original finding was smaller than it read.** **Fourteen of fifteen
decoys never reach this clause at all** — they are `partial` via `missing`,
which is the corpus-wide signal working correctly. The scattered-terms case is
**one query in fifteen**.

## What was done instead

**`DOC_COVERAGE_FLOOR = 0.0` — the clause is off, and says so in the source.**
The module now **reports** the case rather than claiming to catch it: an agent
gets `doc_coverage: 0.42` beside `band: grounded` and can act on it.

**What would change this:** a decoy set large enough for the two distributions
to be *estimated* rather than sampled, and a pre-registration fixing the floor
before any score exists under it. **Not a number read off the table above.**

## Authorship

| artifact | author | could reach |
|---|---|---|
| `doc_coverage`, the floor, this analysis | Claude Code (Opus 5), 2026-08-28 | the goldens, the decoys, and their prior scores |
| the 50 goldens | agent-drafted 2026-08-24, human-author rule waived by Arpit | the corpus |
| the 15 decoys | Claude Code, 2026-08-27 | the corpus; **no correct answers exist to fit to** |

`informed`. **No delta between arms is stated** — the table is two
distributions, not a before/after.

## Reproduce

```bash
cd ~/my_programs/fux-playground
.venv/bin/python <fux>/work/regression/2026-08-28-doc-coverage/evidence/separate.py \
    <fux>/tools/quality-controls/decoys.jsonl
```
