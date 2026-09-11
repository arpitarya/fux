---
inclusion: auto
name: fux-answer-guide
description: Cited answers with fux answer and checking receipts with fux verify - line-range locators, freshness verdicts current, stale, as-ingested, cached, unverified. Use when asked for exact lines, whether a doc is still current, or to prove or reproduce an answer.
---

# Answering with fux answer / fux verify

- **Switch on `source` first:** `refer` quotes fetched text; `index` is titles
  and headings only - never present it as a quote.
- **Cite each passage by its own `loc` and `sha`** - passages can come from
  different documents.
- **Only `current` is current.** `stale` is the new text with the index behind;
  `as-ingested`, `cached` and `unverified` are not confirmations.
- A `#pN` locator is a passage number, not a line.
- **`fux verify` without `--rerun` is never a pass**; only `reproduced` is.

Full procedure: the `fux-answer` skill.
