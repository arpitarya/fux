# Analysis — scaling run 1k→5k→10k (fux 0.23.0) — 2026-07-22

Purpose: turn the conformance numbers into **fixes**. What broke, why (measured,
not guessed), and the exact fux changes worth making.

Source data: `report.md` (curve), `5k.md` / `10k.md` (per-tier), `evidence/`
(raw `fux why` + trace). Diagnosis run on 0.24.0, whose retrieval is
byte-identical to the 0.23.0 under test (same state hash, same quality).

## Headline

- Two distinct failure mechanisms, both now **measured** at the query level.
- Neither is settled as engine-vs-corpus — same generator. See `report.md` Q1.
- The immediate, safe win is **observability**: fux already traces a lot; a small
  fusion-trace addition makes every future miss self-explaining.

## Mechanism 1 — zero-overlap miss: the document vector is diluted

Claim: doc-level dense codes cannot surface a one-sentence answer buried in an
off-topic document. Now measured on the 3 canonical zero-overlap pairs (10k).

| question | correct doc | dense cosine | hamming /256 | in 500-prefilter |
|---|---|---|---|---|
| what technology stores rows on disk? | indexing/note-000000 | 0.174 | 126 | no |
| how do we stop people getting in? | billing/note-000331 | 0.272 | 110 | no |
| what happens when the money is wrong? | search/note-000662 | 0.201 | 110 | no |

- Hamming ~110–126 of 256 is near-random (128 = pure noise). The planted answer
  sentence is swamped by the host document's off-topic prose.
- Lexical also misses (no shared terms — by construction).
- Result: 0/14 rescued at 10k, both modes. A well-powered negative result.

Consequence: **narrows ADR 0010's rescue claim** — rescue holds only when the
zero-overlap answer dominates its document vector. Points at **chunk-level dense
codes** as the real fix (a sentence-level vector would not be diluted).

evidence: `evidence/why-zero-overlap.json`
repro: `fux why "what technology stores rows on disk?" --doc docs/indexing/note-000000.md --json`

## Mechanism 2 — hybrid demotion: RRF has no dense-quality floor

Claim: fusing a full, near-random dense list demotes a correct lexical hit.
Measured on two overlap pairs where lexical finds the answer and hybrid drops it.

| question | correct doc | lexical rank (score) | dense cosine | hybrid result |
|---|---|---|---|---|
| why did we choose the composite index for indexing? | indexing/note-000800 | 3 (15.45) | 0.549 | **rank 6** — off top-5 |
| why did we choose the session token for auth? | auth/note-000450 | 5 (15.33) | 0.470 | **rank 10** — off top-5 |

From the trace (`evidence/trace-demotion-hybrid.txt`):

- `[query] hybrid fusion rrf_k=60 results=200 dense_global_rescues=200` — FuxVec
  contributes a **full 200-doc list**, no admission floor.
- Over near-identical indexing prose, that list is near-random, so RRF blends
  noise co-equally with the strong lexical signal.
- The fused band is razor-thin: the true answer (rrf 0.0335) trails wrong
  indexing notes (0.0492, 0.0484, …) that differ from each other by ~0.00002.

Consequence: this is exactly what the proposal's mitigations target — a dense
**admission threshold** and **confidence-weighted RRF**. But it is also the
corpus-artifact signature (nothing can separate the true answer). Do not ship a
ranking change off this corpus alone.

evidence: `evidence/why-demotion.json` · `evidence/trace-demotion-hybrid.txt`
repro: `fux --debug=trace find "why did we choose the composite index for indexing?" --top 5`

## Improvements to fux (ranked)

**A. Observability — safe, no behaviour change, do first.**

1. **Fusion trace.** For each fused candidate emit its *source* provenance:
   `bm25_rank/score · dense_rank/cosine · rrf_contrib_lex · rrf_contrib_dense ·
   final`. Today the trace prints only the final `rrf=` and mislabels the fused
   lines `[lexical]`. This one addition turns every demotion into a readable
   audit line — no N `fux why` calls needed.
2. **Fix the mislabel.** Fused-ranking trace lines are tagged `[lexical]`; should
   be `[fusion]`/`[query]`.
3. **Dense-list dispersion signal.** Log per query: top dense cosine, gap to the
   0.23–0.26 noise band, and effective list entropy — the exact quantity a
   quality floor would key on. Makes reading A observable directly.

**B. Behaviour candidates — gated on the acme-payments run, not this corpus.**

4. Dense **admission threshold** (min cosine before a doc may enter the fused list).
5. **Confidence-weighted RRF** (weight each list by its score dispersion).
6. **Size/diversity-aware default** (hybrid only above a threshold).
7. **Chunk-level dense codes** — the structural fix for Mechanism 1.

Nos. 4–7 stay candidates in `docs/proposals/hybrid-degrades-at-scale.md` until
the discriminating experiment resolves A vs B.

## What the lab should also capture next time

- `fux why --json` (both modes) for **every miss** — auto-archived to `evidence/`.
- Raw stdout/stderr + `--debug=trace` of each check.
- `fux doctor --json` snapshot per tier.

(Wiring this into `shared/regress/run.py` is a fux-lab change; see the run's WORKLOG note.)
