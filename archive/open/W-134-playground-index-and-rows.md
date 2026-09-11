---
type: OpenItem
id: W-134
title: "W-134 — the playground gets a current index and per-query rows"
description: "fux-playground was repaired on Arpit's 2026-09-11 ruling (its source list indexes docs again; goldens saved). Left: ingest the ten documents with the current engine, and a check.py --rows writer so the hand-graded corpus satisfies ADR-RS decision 15."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-134 — the playground gets a current index and per-query rows

**Model: Sonnet** — an ingest, a small writer and a commit against a written
definition of done. The one judgment call (what the corpus is) is fixed below.

## Why

- The four-priors remeasure, W-97's veto leg and W-87 Part B all need the
  **hand-graded** playground, graded **per query** ([ADR-RS](../../docs/adr/0043_predictions.md) decision 15).
- **Arpit, 2026-09-11 (R-11): repair, then go ahead.** Done in `fux-playground` `3b4d275`:
  `.fux/sources/dirs` lists `docs` again, the 50 goldens and 20 unanswerable
  questions are saved, the unreadable `fux.index.v1` shards are gone.

## Definition of done — in `~/my_programs/fux-playground`

1. **Templates current, corpus untouched.** Bring fux's files up to date through its
   install path (write-if-missing) — this must add `.fux/pii.toml`, which ingest
   requires ([ADR-PII](../../docs/adr/0060_pii.md) decision 17). 🔴 **`.fux/sources/dirs`
   must still list exactly `docs` afterwards** — a template overwrite is what emptied it.
2. **The corpus is `docs/` — the ten documents — and nothing else.**
   ⚠ `.fux/sources/urls` holds a OneDrive share link with `fetch=cdp`. **It must not
   reach this index.** If `fux ingest` would read it, **stop and ask Arpit** — do not
   edit or delete his file.
3. `fux ingest --full`; `fux doctor` clean; `fux ask` returns results from `docs/`.
4. **`check.py --rows <path>`:** one JSON line per golden, `{id, state, detail}` from
   `grade()`, sorted by `id`, byte-stable across runs. Match the field names of
   `fux-lab/shared/regress/run.py`'s `results/per-query.jsonl`.
5. **Resolve the 7 `partial` goldens** (q020, q021, q027, q032, q039, q042, q050): set
   `relevance` to `complete`, leave `relevant` unchanged — per
   [`regression/2026-09-11-third-annotator`](../regression/2026-09-11-third-annotator/report.md)
   (Arpit delegated the call, 2026-09-11). No other golden changes.
6. **Smoke-run `check.py --rows` once and delete the output.** No number from it is a
   result, and nothing is filed under `work/regression/`.
7. Commit the index, `check.py`, `goldens/queries.jsonl` and the template files in the playground, in the
   same style and identity as its recent history.

## Close-out — in fux

- Delete the W-134 row from `OPEN-WORK.md`; the W-97 row and the four-priors item
  stop naming W-134 as their blocker.
- `IMPLEMENTATION.md` + `WORKLOG` entries; DOC-REGISTRY bump; move this file to `archive/open/`.

## Hazards

- 🔴 **Never add, edit or delete** `capture.html`, `fixtures/` or `.fux/sources/urls` —
  Arpit's fetcher experiments.
- Do not re-author or re-rule any golden beyond step 5.

## Prompt

```
Execute work/open/W-134-playground-index-and-rows.md exactly.
Read CLAUDE.md, then that file. Explore → plan → implement → verify.
The corpus is docs/ only; stop and ask if ingest would read .fux/sources/urls.
Never touch capture.html, fixtures/ or .fux/sources/urls. No number from the
smoke run is a result. Finish with the close-out list.
```
