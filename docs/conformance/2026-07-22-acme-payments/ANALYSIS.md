# Analysis — acme-payments realistic run (fux 0.23.0) — 2026-07-22

Purpose: turn the numbers into **fixes**. What the realistic corpus settled, what
it newly exposed, and the exact fux changes worth making — each with a repro.

Source data: `report.md`, `evidence/` (`find --json --explain` on 0.23.0 for every
miss; `why`/`--debug=trace`/`doctor` captured on 0.24.0, whose retrieval is
byte-identical to 0.23.0 — top-1 parity verified on the settlement query; 0.23.0
has no `why`/`doctor`/`trace`).

## Headline

- The hybrid degradation was a **corpus artifact** (reading B). It vanishes on
  realistic prose: hybrid hit@5 .182 → .855, parity with lexical.
- So mitigations #4–#7 in the proposal (admission threshold, confidence-weighted
  RRF, size-aware default, chunk dense codes) lose their original justification —
  they targeted a synthetic collapse that isn't real. **Do not ship them off the
  scaling story.** One (chunk dense codes) survives for a *different* reason below.
- Three residual findings are real and corpus-independent. They, not the hybrid
  gap, are where the engine work is.

## Settled — hybrid does not degrade on realistic text

Claim retired: "the default hybrid path is worse than `--lexical-only` at scale."
Measured false on genuine prose (hybrid .855 vs lexical .873 hit@5). The synthetic
collapse came from ~450 near-identical template notes making the dense ordering
arbitrary; that condition does not occur in a real repo.

repro: `cd fux-lab/acme && ./run.sh` → `eval_hybrid` vs `eval_lexical-only` in the
metrics block.

## Finding 1 — no currency signal in ranking (staleness: 9/12 inversions)

Claim: retrieval ranks by lexical/semantic match, never by truth or recency, so a
superseded doc with denser query terms beats the still-true one.

| question | current (rank) | superseded (rank) | Δrrf |
|---|---|---|---|
| settlement window today | 0018 T+2 (2) | 0006 T+3 (**1**) | 0.00079 |
| idempotency-key TTL | idempotency-keys (2) | legacy-idempotency-notes (**1**) | — |
| PAN storage | 0002 tokenize (6) | legacy-card-storage (**1**) | — |
| auth method | authentication (5) | legacy-api-keys (**1**) | — |

- BM25F length normalization favors the terse legacy doc; the dense plane can't
  break a tie between topically near-identical docs (`why-staleness-*.json`).
- **All three supersession markers are invisible** to retrieval — `superseded_by`
  frontmatter, dated inline note, and no marker fail identically.

**Improvement (ranked):**

1. **Ingest-time supersession awareness (structural fix).** Parse
   `status: superseded` / `superseded_by:` frontmatter at ingest and record a
   `superseded` flag on the chunk. Then either (a) down-rank superseded chunks by
   a fixed penalty in fusion, or (b) annotate them in output so an agent/`answer`
   can prefer the current doc. This is deterministic, needs no model, and fits the
   substrate. Gate behind a proposal + ADR.
   repro: `fux find "What is the card settlement window today?" --json --top 5`
2. **`answer` should prefer the un-superseded source** when two candidates
   conflict and one is marked superseded — a decline-to-current rule, not a
   ranking change to `find`.
3. **Observability:** `fux why` should surface a `superseded: true` line so the
   inversion is self-explaining. (Cheap; no behaviour change.)

Note: this is a **capability gap, not a bug** — the engine has no supersession
input to use. It is also the single most product-relevant result of the run.

## Finding 2 — dense rescue is ineffective even undiluted (0/6 clean)

Claim: doc-level FuxVec does not surface a zero-overlap answer even when the answer
is the entire short document — so ANALYSIS's 10k "document-vector dilution"
explanation is **incomplete**; the dense plane under-delivers on its headline
class regardless of dilution.

- 0/6 clean dense rescues; the one top-5 appearance was a **lexical** rank-4 hit.
- From the trace: `fuxvec prefilter codes=876 width=500 scanned=500 rescued=200`
  then `dense_global_rescues=200` — the dense list is injected wholesale, yet the
  correct short doc is not among the top of it.

**Improvement:**

4. **Chunk-level dense codes** (proposal #7) survives — but re-motivated: not to
   fix the (synthetic) hybrid collapse, but because *doc-level* dense cannot
   reliably surface a single-sentence answer, diluted **or not**. A sentence/chunk
   vector is the structural fix for the zero-overlap class.
   repro: `fux find "How is the same instruction kept from running twice?" --json`
5. **Dense-list dispersion in `why`** (observability): log top cosine + gap to the
   0.23–0.26 noise band so "the dense list carried no signal here" is visible.

## Finding 3 — honest-decline is too permissive for well-formed queries (0/4)

Claim: the decline path keys on (near-)zero lexical overlap, so it catches
gibberish but not a fluent out-of-scope question that incidentally overlaps some
passage.

- Gibberish declines (`answer=null`); all 4 typed unanswerables fabricate with
  1–5 sources from unrelated docs (`unanswerable-fabrication.json`).

**Improvement:**

6. **Absolute-confidence floor on `answer`.** Decline when the best extractive
   score (or top dense cosine) is below an absolute threshold, not merely when the
   candidate pool is empty. The run shows non-empty pools with weak top scores are
   exactly the fabrication case.
   repro: `fux answer "What is the uptime SLA percentage for Acme's GraphQL API?" --json`
7. **A "no-confident-match" margin check** — decline when the top candidate does
   not clear the runner-up by a margin, since off-topic pools are flat.

## Also observed (safe, no behaviour change)

- **A1 fusion-trace mislabel reproduces.** In `trace-staleness-settlement.txt`
  the fused ranking lines are tagged `[lexical]` though they carry `rrf=`. Confirms
  the scaling run's A1: relabel fused lines `[fusion]`/`[query]` and emit per-
  candidate `bm25_rank/dense_rank/rrf_contrib` provenance. (Not done here — engine
  change, own handoff.)
- **README/CHANGELOG accuracy.** Fresh-clone reproduced "top-1 stable, tail
  re-ranked" again; the "same rankings *and scores*" wording is corrected in this
  change (README.md + CHANGELOG.md) to "same top-ranked result; tail order/scores
  approximate (state plane is quantized)."

## What the lab captured this run (and should keep)

- `find --json --explain` per miss (version-under-test provenance) — auto-worth
  archiving; wire into `run.py` next.
- `why`/`--debug=trace`/`doctor` on the parity-matched 0.24.0 for diagnosis.
- New suite checks added (additive, data-guarded): **staleness precision** (per-
  pair inversion) and **typed unanswerable decline**. Both no-op on the synthetic
  tiers (they plant neither), so they cannot change those baselines.

## Do-not-do

- No ranking/fusion/decline behaviour change ships off this single corpus. Each
  improvement above graduates through `docs/proposals/` and an ADR. One corpus is
  evidence, not proof.
