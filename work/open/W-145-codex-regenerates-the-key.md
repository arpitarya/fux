---
type: OpenItem
id: W-145
title: "W-145 — Codex regenerates the golden answer key"
description: "Arpit, 2026-09-12: Codex's quota was exhausted mid-phase-1, so Claude authored the ~124-question key as a stopgap. Every number measured against it is contaminated by construction. Codex re-runs prompt 1 part B and the Claude-authored key is discarded."
status: open
lane: arpit
timestamp: 2026-09-12T00:00:00Z
filed: 2026-09-12
---

# W-145 — Codex regenerates the golden answer key

## 🟣 Gated on 2026-09-30 — Arpit, 2026-09-13

**His Codex limit is exhausted; he runs part B on 2026-09-30.** The decision is
made, so this is no longer a *Blocked on Arpit* row — it is a 🟣 date gate in
[OPEN-WORK](../OPEN-WORK.md), and nothing is owed from him before that day.

- **Do not ask again before 2026-09-30**, and do not work around it: the
  stopgap key stays in place and every number scored against it stays
  `informed` (below).
- **What this gate holds up**, moved here from the inbox sub-row it used to
  live in: **[W-87](W-87-what-good-means.md)'s Part B**, which needs a key
  nobody has contaminated. Nothing else — this item governs what a phase-5
  number may *claim*, not whether phase 5 runs.

## Why this exists

**Arpit, 2026-09-12.** His Codex quota was exhausted with phase 1 half done: the
ten seed documents had landed, the questions and answers had not. He ruled that
Claude should write the corpus's feature-coverage documents and the key so phase 2
is not blocked, **and that this item be filed in the same breath** so the stopgap
is never mistaken for the real thing.

## What is contaminated, and why it is not a leak

**This is not the failure the seal was built to stop.** Nothing leaked: no Claude
session read a key it was not meant to. The defect is upstream of that — the same
model family now authored the questions *and* will grow the corpus and run the
engine.

- `work/golden/README.md` says of phase 1: *"Claude wrote the brief — the company,
  the cast and the document roster — but no facts."* **That property is now
  false for the key and for documents 11–15 and the archive.** The base ten
  documents are still Codex's and still carry Codex's facts.
- A leak is detectable after the fact; correlated priors between the
  question-writer and the corpus-writer are not. There is no test that finds this.
- **Consequence, binding:** every run scored against this key is `informed` under
  the conformance rule, whoever authored the analysis, and **no delta measured
  against it may be stated**. It exercises the plumbing; it does not produce a
  number anyone may cite.

## What Codex has to do

1. Run [`prompts/1-codex-seed.md`](../golden/prompts/1-codex-seed.md) — **part B
   only**; the corpus in `seed/` already exists and part A says to skip it.
2. Answer the key-location question first, as the prompt requires.
3. Discard the Claude-authored key entirely. **Do not diff against it, do not use
   it as a starting point, do not ask for it** — reading it is how Codex's
   independence goes the same way.
4. Once Codex's key exists, the Claude-authored key is destroyed wherever Arpit
   stored it, and this item is deleted.

## What the stopgap key is

- **124 questions**, ids `g001`–`g124`, `key_version: 1`, all `sealed: false`.
- Held **in the chat only**, at Arpit's instruction (option 2). **No key file was
  written**, on this machine or anywhere else.
- Type mix: lookup 37 · paraphrase 25 · multi-doc 25 · temporal 19 ·
  unanswerable 12 · negation 6 — every share inside ±5 points.
- Feature coverage: `superseded_weight` 12 · `archived_weight` 9 · `recency` 7,
  each above its minimum, each with the intent split the prompt requires.
- Mechanically checked before it was handed over: every `relevant`, `primary` and
  `evidence` path exists; all 136 quotes match their file under whitespace-collapsed
  comparison; ids sequential; `primary` inside `relevant`; unanswerable rows empty;
  `supersedes:` targets exist; `seed-dates.tsv` complete and correctly ordered.

## What is NOT contaminated and does not need redoing

- The **ten base seed documents** — Codex's, untouched.
- **Documents 11–15 and `seed/archive/`** are Claude-authored, but they carry no
  question and no answer. Codex may keep them; if it prefers its own, that is
  part A of the prompt and a bigger job than the key.
- **`seed-dates.tsv`** — mechanical, and checked against the pair ordering.

## Blocks

**[W-87](W-87-what-good-means.md)'s Part B, and nothing else.** Phase 2 runs on
this corpus today. This item governs what any number coming out of phase 5 is
allowed to claim, never whether phase 5 runs.
