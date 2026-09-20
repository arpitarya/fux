---
type: Analysis
run: 2026-09-18-correction-generalisation-informed
item: W-175
description: "Diagnosis of the 0-discordant result: the ctx line lifts its own words and nothing else at weight 1.0. Two specific follow-ups, one of them a weight question that precedes the generalisation question."
---

# ANALYSIS — why zero paraphrases crossed the line

## Diagnosis

1. **The mechanism is lexical, and the endpoint measured lexical transfer.**
   `fux correct` appends the question's tokens to the document's `ctx` field.
   A paraphrase benefits only through tokens it shares with that line and the
   body lacks. 57 of 60 paraphrases shared no such token → unchanged rank. The
   3 that moved did share one (`stale`, `re-download`, `server`).
2. **At `ctx = 1.0` one line cannot outweigh body term frequency in a dense
   record.** The correction's own question — the best case, every token
   present — reached top-3 in only 4 of 12. It moved in all 12, so the field is
   read; it is not weighted enough to win against 30-chunk records whose bodies
   repeat the query's function words.
3. **Not a harness defect.** `filed = true` on all 60 rows, 12 enrichment files
   with `model: none (human correction)`, `doctor` reports 12 corrections, and
   the rank@20 sweep shows movement exactly where the mechanism predicts it.

## Specific changes, each with a repro

| # | change | repro |
|---|---|---|
| A | **Measure `ctx` weight before measuring generalisation.** Sweep `[bm25f] ctx ∈ {1, 2, 4}` on the same 12 own-questions; the value at which ≥ 10/12 own-questions reach top-3 is the floor below which no generalisation test means anything. Needs its own pre-registration. | `evidence/repro.sh`, then edit `.fux/tune.toml` in the run tree and re-run the own-question rank sweep (in `ranks-ii.json`'s shape) |
| B | **Run the blind Codex arm as frozen** — unchanged. This run does not substitute for it and must not be read as its result. | [`prompt-codex-paraphrases.md`](../2026-09-15-correction-generalisation/prompt-codex-paraphrases.md) |

## Unresolved, stated as unresolved

- Whether a blind paraphraser writes paraphrases with more lexical overlap than
  these (which would raise the measured transfer) is unknown until arm (iii)
  runs. **That is the question, and this run did not answer it.**
- Whether the 64 % baseline miss rate is the corpus (dense, jargon-heavy
  records), the questions (intent-phrased, informed), or the analyzer (thin
  stopwords) is not separated here.
