---
type: Compare Doc
title: "The query-side lens — `--intent`, `--as-of`, `--no-archived`, and whether `supersedes:` is a concept anyone will use"
description: "The fork three records call 'unopened, no compare doc, not authorised' (SR-TUNE d15, SR-ARCHIVED-CONTENT d6, SR-API d7), plus the two questions beside it: whether supersession stays a declared fact (B-144) and which of SR-ENRICH's four candidate enrichments are still live (B-145). Recommended: no `--intent` flag (the cue-derived prior shipped), refuse `--as-of`, build `find --no-archived` only, keep `supersedes:` as a declared fact, and two of four candidates remain."
status: proposed (W-251 §3 #3 — Arpit's ruling)
timestamp: 2026-10-03T00:00:00Z
filed: 2026-10-03
---

# The query-side lens

> **Verdict: PROPOSED.** (1) **`--intent` is answered** — W-168 step 9 shipped
> an intent prior derived from the question's own cues ([SR-RANKING](../../records/0111_ranking.md)
> d13); a flag would be a second way to say the same thing (SR-CLI veto 1).
> (2) **`--as-of` is refused** — a recency order is exactly what SR-TUNE d15
> removed from ranking, and a per-query date lens over an index that holds no
> dates for most documents orders by `mtime` noise. (3) **`find --no-archived`
> is the one lever worth building** — a REMOVE-only filter (SR-FIND d7's
> shape), deterministic, cheap, and the only one of the three a reader has asked
> for in words (*"what do we do now?"*). (4) **`supersedes:` stays a declared
> fact** — tie-break, edge, `superseded_by:` enrichment — with no weight and no
> further mechanism; the concept question closes. (5) Of SR-ENRICH's four
> candidates, **two are resolved by other means** (expansion → mined expansion
> and doc2query; retirement flags → `superseded_by:`), and **two remain**
> (inferred edges, richer embeddings), both behind B-245's trigger.
> **Confidence: high on 1, 2, 4; medium on 3** (a filter is a build and he
> stopped W-168's last query-side steps). **Reopen-trigger:** a scored gen-4
> run shows the cue-derived prior wrong on ≥ 6 questions a stated intent would
> have fixed; or a corpus arrives whose documents carry dates on most records.

**Model: Sonnet** for (3) if ruled — a filter in the shape SR-FIND already has.

## Context

Three records refused to take this fork by implementing it, and said so:

- [SR-TUNE](../../records/0135_tuning.md) d15 — after removing the three ranking
  priors: *"the query-side mechanism — an `--intent` flag, an `--as-of` date
  lens, or surfacing the supersession chain instead of ranking for it. It is an
  unopened fork with no compare doc."*
- [SR-ARCHIVED-CONTENT](../../records/0134_archived-content.md) d6 — *"'what do
  we do now?' and 'what did we do before?' want opposite orderings out of one
  corpus, and a per-document multiplier cannot carry a per-query distinction."*
- [SR-API](../../records/0154_api.md) d7 — `mtime` is exposed and orders nothing;
  *"sorting or filtering by it — `--as-of`, a recency order — is the unopened
  query-side fork."*

Since then: **W-168 step 9 shipped the intent prior** (2026-09-28) — `run_query`
reads the question's cues and prefers a `[doctype]`; that is the `--intent`
question answered from the query text rather than from a flag. **W-168 step 7
(supersession-aware ranking) was stopped by Arpit**, and `archived_weight` was
retired as *"a fact, not a weight"* (SR-TUNE 15a). The fork is narrower than
when it was named.

Beside it, two rows the same records carry:

- **B-144** — *whether anyone will ever write `supersedes:`* (SR-TUNE d15,
  *"a question about the concept, not the knob, and is Arpit's"*). Evidence
  since: [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) A21/R5 — his
  own 2026-09-22 ask — **requires** `supersedes:` in seed documents; fux's own
  records never carry it (L1: *"no need for superseded part"*); only SR-ENRICH's
  `superseded_by:` writes it in this repo.
- **B-145** — SR-ENRICH's four candidate enrichments, *"None is approved"*. The
  table is duplicated verbatim in the record (W-245 fixes that).

## Options

For the lens itself:

- **L0 — none.** The index-side priors are gone, the cue-derived prior is in,
  and no query-side flag ships. Closes three records' ⚠ lines with one sentence.
- **L1 — `find --no-archived` only** (recommended). A REMOVE filter on the
  `archived` fact, in SR-FIND d7's shape: it can never widen the pool; `band` is
  computed on the unfiltered ranking (d9). `ask` untouched.
- **L2 — `--no-archived` + `--as-of <date>`.** The date lens orders or filters
  by `mtime`/`date:`; most records carry no date and `mtime` is a checkout
  artefact, so the lens is noise outside a dated corpus.
- **L3 — all three, `--intent` included.** Duplicates the shipped prior.

## Matrix

| | L0 none | L1 `--no-archived` | L2 + `--as-of` | L3 + `--intent` |
|---|---|---|---|---|
| answers *"what do we do now?"* | no | **yes** | yes | yes |
| deterministic from the committed index | — | yes (`archived` is a record fact) | **no** (`mtime` is per checkout) | yes |
| duplicates a shipped mechanism | — | no | no | **yes** (SR-RANKING d13) |
| SR-CLI veto 1 (no second way) | — | clean | clean | **fails** |
| widens a pool / changes `band` | — | never (REMOVE only) | can reorder | prior already does |
| build size | 0 | S | M | S |
| records amended | 3 (one sentence each) | SR-FIND, SR-ARCHIVED-CONTENT, SR-TUNE, SR-API | + SR-RANKING tie-break | + SR-RANKING |

For `supersedes:` (B-144): **keep as a declared fact** — he authored test data
that exercises it, kept the fact when he removed the weight, and the graph edge
and tie-break cost nothing when the property is `False` everywhere. The
alternative, retiring the concept, deletes a key his own test-data record
requires.

For the candidates (B-145): the row should read *inferred edges and richer
embeddings, both behind B-245's reopen trigger*; the other two are shipped
under other names and are not candidates any more.

## Consequences of the verdict

- Three ⚠ lines close (SR-TUNE d15, SR-ARCHIVED-CONTENT d6, SR-API d7) with a
  pointer here; SR-FIND gains a fourth precision control if L1 is ruled.
- `--as-of` is **refused, not deferred** — the row leaves the backlog rather
  than waiting; a dated corpus is the reopen-trigger.
- B-143, B-144, B-145 leave the backlog on his *yes*.

## References

- SR-TUNE d15, 15a · SR-ARCHIVED-CONTENT d6 · SR-API d7 · SR-FIND d7, d9 ·
  SR-RANKING d13 · SR-ENRICH §The candidate enrichments, d15, d17 ·
  SR-EXPAND d17 · SR-WORK-TESTDATA A21, R5 · W-168 (archived) steps 7 and 9.
- W-251 §3 #3.

## Reopen-trigger

A scored generation-4 run shows the cue-derived prior wrong on ≥ 6 questions
that a stated intent would have fixed (then `--intent` is a correction, not a
duplicate); or a consumer corpus carries `date:` on most records (then `--as-of`
has something to read).
