---
type: Handoff
name: W-168
description: "The ten ranking improvements of proposals/search-improvements-v3.md, promoted as one program with ten gated steps: anchor text, corpus-mined expansion, unstemmed identifier field, RM3, supersession-aware ranking, SDM proximity, MMR diversification, git authority prior, intent → doc-type prior, section-level units. Each step is its own golden question → pre-registration → build → measure → keep/remove; never two in one arm."
item: W-168
filed: 2026-09-14
ball: agent
---

# W-168 — the ten search improvements, one program

**Model: Opus for #4, #8, #9, #10 (drift, bias, a plane change); Sonnet for the rest once
a golden question and a pre-registration exist.**

**Promoted 2026-09-14 by Arpit** from
[`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md), which
stays the spec (the per-idea table in its §1 and §3b is the definition of done here, not
repeated). **W-156 ruled 2026-09-14:** every step is a ranking change and lands under
[SR-RS](../../records/0133_predictions.md) decision 19's paired floor on golden data —
the single-corpus sentence is gone ([SR-LAW-0](../../records/0002_LAW-0-authority.md)
decision 2a). Nothing agent-side waits.

## Definition of done — per step, in this order

| step | idea | golden prerequisite (Codex's hands where the sealed key is involved) |
|---|---|---|
| 1 | #1 anchor-text field | documents findable only via a linker's wording |
| 2 | #3 identifier field | id-queries |
| 3 | #5 supersession-aware ranking | a superseded/successor pair |
| 4 | #2 corpus-mined expansion | acronym / house-term questions |
| 5 | #4 RM3 (drift bound pre-registered) | under-specified questions |
| 6 | #6 SDM proximity in refer | phrase-sensitive questions |
| 7 | #7 community MMR (after W-161) | multi-facet questions |
| 8 | #8 git authority prior — **starts with a corpus that has history, or does not start** | none in golden |
| 9 | #9 intent → doc-type prior | intent-labelled questions |
| 10 | #10 section units — its own compare doc first | long-document questions |

For every step: golden question(s) → frozen pre-registration (both directions, SR-RS
d19 floor) → build behind a tunable, default off → measure → verdict under
`work/regression/` → default on **only on PASS**; on FAIL the tunable stays at 0 and the
record names the failed direction. **One step per measurement.** Ambiguous → Arpit with
per-query rows.

## Out of scope

The graph-composed `ask` (W-161) and `fux correct` (W-162) — separate items.

## Records this will touch

Per step, as the proposal's §3 table lists: SR-RANKING · SR-POSTINGS · SR-EXTRACTED ·
SR-EXPAND · SR-GRAPH · SR-ARCHIVED-CONTENT · SR-REFER-PLANE · SR-CHUNKING · SR-ASK ·
SR-INDEX-RECORD · SR-TYPES-LIST · SR-RS (one prediction id per step).
