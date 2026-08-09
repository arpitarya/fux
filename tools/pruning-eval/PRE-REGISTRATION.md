# Pre-registration — M1, the pruning-quality gate (P1)

**Written before any number was produced.** Everything in this file — metric
definitions, slice definitions, gold-label rules, arm definitions, and the
pass/fail threshold — is fixed here so that it cannot be adjusted in the
direction the numbers happen to point. `git log` on this file is the evidence:
it is committed **before** the first run.

If something below turns out to be under-specified once the data exists, the
honest move is to **record the ambiguity in ADR-0017** and hand the call to
Arpit — not to redefine the term.

---

## 1. The question

Does document-centric KL top-*k* static pruning preserve ranking quality on
Fux's corpora, with Fux's scorer?

If it does not, the committed index cannot be small and the index-and-refer
architecture is falsified at its foundation.

## 2. The threshold (from handoff §5.4 and paper §8 — NOT restated loosely)

| outcome | condition | action |
|---|---|---|
| **PASS** | mean hit@5 delta ≤ **2 pts** at k=128 on **each** of the three corpora, and no single corpus worse than **3 pts** | proceed to M0b, then M2 |
| **PASS-with-k=64** | k=64 also meets the above | record; top-64 becomes the default candidate |
| **FAIL** | any corpus worse than **3 pts** at k=128 | stop the plan; `storage-architecture.compare.md` reopens |

"pts" = percentage points of absolute hit@5, i.e. `100 × (hit@5_baseline −
hit@5_pruned)`. **Delta is signed**: a pruned arm that scores *higher* than
baseline is a delta ≤ 0 and passes.

Landing between 2 and 3 points on some corpus is **ambiguous by construction**
and is Arpit's call, not the executing agent's.

## 3. Arms — exactly three per corpus per k

Every arm runs through **one scorer**: the archived v0.26 `Searcher.search`
(BM25F, heading 3.0 / path 2.0 / body 1.0, k1 1.2, b 0.75). Nothing about the
scorer, the queries, or the aggregation differs between arms. **Only the index
differs.**

| arm | postings | `df` / `n` / `avg_wlen` | purpose |
|---|---|---|---|
| `baseline` | full | from the full index | the reference |
| `pruned` | top-*k* per document | **recomputed from the pruned postings** | **the system we would actually ship** |
| `diag` | top-*k* per document | borrowed from the **full** index | diagnostic only — attributes losses to *missing postings* vs *shifted statistics* |

`pruned` is the arm the verdict is read from. `diag` never enters the verdict;
it exists so the failure catalogue can say *why*.

**Why `pruned` recomputes statistics:** in production, `D/` holds exact `df`
over the pruned index — a term's `df` is the number of documents in which it
*survived*, and `avg_wlen` reflects pruned field lengths. Borrowing the
baseline's statistics would make the scores line up better and would measure a
system nobody is going to ship.

## 4. Pruning — what exactly is pruned

- **Granularity: per document.** The shipped index prunes a document's entry.
  A document's term-frequency vector is the sum of its chunk heading tokens and
  chunk body tokens, plus its path tokens counted **once**.
- **Selection:** `score(t,d) = P(t|d) · log( P(t|d) / P(t|C) )`, keep top *k*,
  ties broken **lexicographically on the term**.
- `P(t|d)` from the document's own raw (unweighted) term counts. Field weights
  are a scoring concern, not a selection concern; the weighted variant is *not*
  explored here and that is a stated limitation.
- `P(t|C)` = collection term frequency / total collection tokens, computed in a
  first pass over the **unpruned** corpus.
- **Application:** every posting `(chunk, term)` where the chunk's document did
  not keep `term` is dropped. Field structure survives for kept terms — pruning
  chooses *which terms survive*, never which fields.
- **Length recomputation:** each chunk's weighted length `wlen` is recomputed
  over surviving terms only; `avg_wlen` follows.

## 5. Corpora and gold labels

| corpus | docs | queries | gold label |
|---|---|---|---|
| **acme** | 929 | 59 committed pairs | the pair's `doc` (human-authored) |
| **orbit** | 944 | 57 committed pairs | the pair's `doc` (human-authored) |
| **synth** | synthetic, generated | 200 generated | **see §5.1 — no human judgments exist** |
| *fixture* | 9 | 21 committed pairs | development only, **not a gating corpus** |

`unanswerable` pairs (4 in acme, 4 in orbit) have **no gold document** and are
excluded from all retrieval metrics. That exclusion is declared here, not
discovered later.

### 5.1 The synthetic corpus has no relevance judgments — the honest handling

`tools/synth_corpus.py` generates documents from a ~50-word closed vocabulary
plus a per-document zero-padded index token. Two consequences, both known
before running:

1. A **known-item** query built from a document's title necessarily contains
   its index token, which has df ≈ 1 and therefore an extremely high KL score.
   Pruning at any sane *k* keeps it. Such an eval would score ≈ 1.0 in both
   arms and **would measure nothing** — precisely the "a PASS could be
   measuring nothing" failure the handoff §8 warns about.
2. Sampling query terms uniformly from the body yields non-discriminative
   queries (the vocabulary is closed), so baseline hit@5 would be near zero and
   the comparison would be noise.

**Therefore, for `synth` the primary metric is ranking fidelity against the
baseline:** the gold label for a query is the **baseline arm's top-1
document**. The baseline scores 1.0 by construction (stated openly), and the
pruned arm's hit@5 is the fraction of queries whose baseline-preferred document
still appears in its top 5.

This is **stricter** than true hit@5 — it counts a re-ordering as a loss even
when the new result is equally good — so it can only under-state pruning's
quality, never flatter it. That direction is deliberate.

The known-item eval is still run and reported, labelled **secondary and
easy-by-construction**, purely as a sanity check that the corpus and harness
behave.

**Synthetic query set** (deterministic, seeded, no wall clock): 200 queries
over evenly-spaced source documents, in three kinds — `known-item` (title
terms, includes the index token), `topical` (3 body terms sampled with a fixed
seed, index token excluded), `phrase` (a verbatim 5-token body span).

## 6. Metrics — exact definitions

Retrieval is at **document** level, matching `fux find`: the top 200 chunks are
scored, then aggregated per file by **max chunk score**, sorted by
`(-round(score, 9), path)` — the archived `_run_find` rule, unchanged.

- **hit@5** — fraction of queries whose gold document is in the top 5.
- **P@10** — precision at 10: `|relevant ∩ top-10| / 10`. With exactly one gold
  document per query this is `hit@10 / 10` by construction. Reported because
  the handoff requires it; the equivalence is stated so nobody reads it as an
  independent signal.
- **MRR** — mean of `1/rank` of the gold document within the top **50**
  aggregated documents; `0` if absent. Truncation depth declared here.

All three are reported per corpus × per k × per arm.

## 7. The rare-term slice

Pruning is theoretically expected to hurt rare terms. Definition, fixed now:

1. For every eval query, tokenize it with the archived tokenizer and take the
   **minimum baseline `df`** across its terms that exist in the index (a query
   whose terms are all absent is excluded from the slice computation).
2. Rank queries by that minimum-df statistic ascending, ties broken by query
   text.
3. The **rare-term slice is the bottom tercile** of that ranking (`ceil(n/3)`
   queries).

This yields a non-empty, ~⅓-sized slice by construction, and is
corpus-relative — which is the point, since "rare" only means anything against
a given collection.

If a corpus's slice turns out to be degenerate (e.g. every query has the same
minimum df), that is reported as **"slice degenerate"** and is a finding about
the eval set, **not a pass**.

## 8. The failure catalogue

Every query where the gold document was in the **baseline** top-5 and is **not**
in the **pruned** top-5 is catalogued with a cause, assigned by these tests in
this order:

1. **`tie-reordering`** — the gold document's pruned score is within `1e-9` of
   the 5th-placed document's score.
2. **`term-pruned`** — at least one query term that contributed to the gold
   document's baseline score was pruned out of that document.
3. **`score-compressed`** — every contributing query term survived in the gold
   document, but its rank fell anyway (statistics shifted, or competitors rose).
4. **`unclassified`** — none of the above; reported as-is rather than forced.

The `diag` arm is used to attribute: if a loss disappears under `diag`, it was
caused by **shifted statistics**; if it persists, by **missing postings**.

## 9. Prune coverage — so a PASS cannot be vacuous

Reported per corpus × per k:

- **documents actually pruned** — fraction whose distinct vocabulary exceeds
  *k* (for the rest, top-*k* is a no-op).
- **postings kept** — total surviving `(chunk, term)` postings, and the ratio
  to baseline. This is also the free empirical anchor for P2's size model.

A corpus where few documents are pruned is reported as such, and its PASS is
explicitly labelled weak evidence.

## 10. Sanity checks that must pass before any number is believed

1. **Identical-arm reproducibility** — running `baseline` twice produces a
   byte-identical report.
2. **No-op pruning** — `k = ∞` reproduces the baseline metrics **exactly**
   (this is what proves the only difference between arms is pruning).
3. **Selector unit tests** — known distributions, tie determinism, `k >`
   vocabulary, empty document, a universal term scoring ≈ 0, collection model
   built from the unpruned corpus.

## 11. Declared limitations (stated before the result, not after)

- The synthetic arm's gold labels are baseline-derived (§5.1), so its "hit@5"
  is a fidelity measure, not an independent quality measure.
- Field-weighted KL selection is not explored.
- Only `k ∈ {∞, 128, 64}` is measured; no sweep.
- Dense and graph retrievers are out of scope — this is a lexical-only
  experiment by design, because P1 is a claim about **postings**.
