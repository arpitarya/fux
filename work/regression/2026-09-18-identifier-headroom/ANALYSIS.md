---
type: Analysis
run: 2026-09-18-identifier-headroom
item: W-168
description: "Why the identifier field has no room to move on the golden ladder, why the survival report's premise did not translate to retrieval, and the two specific changes — one to a stopping argument, one to ingest."
---

# ANALYSIS

## Diagnosis

1. **Symmetric mangling is not a retrieval defect.** The analyzer is applied to
   documents and queries alike. A "mangled" token is a stable key on both
   sides; `kf` + `2014` is as good a posting pair as `kfs` + `2014` would be.
   The survival report's *"a string no document contains"* checked raw bytes.
2. **Splitting only hurts when every piece is common.** `QCL-F-22` → `qcl`,
   `f`, `22`: all three appear across the corpus, so the conjunction ranks 4th
   behind documents that mention forms more often. That shape is 2 of 33 here.
3. **The absolute misses are a different mechanism.** `parse.py` indexes `body`
   only. An identifier that exists solely as a frontmatter `doc_id:` is
   unreachable by any query, whole or split, at every rung — and `find ADR` /
   `find Deshmukh` show the same for any frontmatter-only value.

## Specific changes

| # | change | where | repro |
|---|---|---|---|
| A | **Correct W-168 step 2's stopping reason.** It is not *"the questions are missing"*; it is *"the headroom is 3–4 of 33 on this corpus."* Prompt 8 as written does not unblock it. | `work/open/W-168-search-improvements.md` | this run |
| B | **Index selected frontmatter scalars.** Decide which keys (`doc_id` at minimum; `owner`/`contributors` are a separate question — they are names, and PII rules apply) and which field (`title`-weighted or `ctx`). Needs its own pre-registration; the three frontmatter-only identifiers are its headroom, which is also below the floor **on this seed**. | `src/fux/ingest/parse.py`, `run.py`; SR-INGEST / SR-DECODE | `find ADR` on rung-00100 before/after |
| C | **A seed-authoring note for the next Codex corpus prompt:** include identifiers of the failing shape — a shared prefix across many documents plus a short numeric part — so a field built for that shape can be measured. | `work/golden/prompts/` (Codex's) | — |

## Unresolved

- Whether real corpora carry the failing shape at a rate that makes the field
  worth its format change is unknown from golden data. Ticket keys and
  requirement ids (`PROJ-123`, `REQ-0042`) are exactly that shape and are
  common in the corpora fux is for. **The golden seed under-represents it**,
  and that is a corpus fact, not a ranking one.
