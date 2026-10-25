# ANALYSIS — W-298 step 1

## The one miss — `i08`, rank 6

*"put all the module exports at the bottom of the file"* → expected `js/exports-at-end`
("Exports are gathered at the end of the file"). Top 5 returned:
`node/no-unpublished-import` · `node/no-unpublished-require` · `graph/no-unused-exports` ·
`node/no-missing-import` · `node/no-missing-require`.

**Cause (read from the rows, not guessed):** the intent's content words are *exports*,
*module*, *bottom*, *file*. `bottom` appears in no rule; the rule says *end*. `exports`
and `file` are frequent across the whole `node/` pack (every published-files rule says
both, many times), so df-weighted overlap on those two words outranks the one document
that is about the position of exports. A **synonym gap** (`bottom` ≠ `end`), not a
ranking defect — and exactly the shape `fux correct` exists for (one human question
line on the document). **No engine change is proposed from one miss.**

Repro: `fux ask --json --top 10 "put all the module exports at the bottom of the file"`
in the scratch repo (`evidence/REPRODUCE.sh`).

## The near-misses — ranks 2–4

`i06` (3), `i12` (2), `i13` (2), `i15` (4), `i17` (2), `i19` (2). In each, the rank-1
document shares a *more* frequent content word with the intent (e.g. `i19`: `import` +
`package` → `no-unpublished-import` ahead of `no-extraneous-import`). Within-pack
siblings that differ by one qualifier are the hard case for a 140-document corpus and
20 words of query; the expected rule is still on the first screen in every case.

## What it says about W-299–W-302

- **Build:** the pack's own vocabulary is reachable from plain words with the shipped
  tune — the premise of shipping a pre-built segment holds on this pack.
- **Open after this run, not before:** how a *merged* query behaves when the consumer's
  own docs also use words like `import` and `export` (W-300's L13 run is where that is
  measured; this run has one segment and cannot say).
- **Corpus note for W-299's digest:** 140 documents produced **106 shard files**
  (`00…ff.jsonl` by id hash) — the segment an author ships is ~100 small files, not one.
  Recorded for W-302's manifest, not a change request (a shard-count change is a
  `_format` change).

## Unresolved

- The item's **438** rules vs the published pack's **140**: whichever tree the 438 came
  from is not on npm as 0.1.0. Unresolved here; the next pack version re-runs the same
  sealed intents.
