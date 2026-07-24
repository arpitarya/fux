---
type: Conformance Analysis
status: final
date: 2026-07-24
run: 2026-07-24-fusion-lexical-hit-loss
engine: fux 0.26.0 (published PyPI artifact)
corpora: fixture (21) · acme (55) · orbit (53) · synthetic 1k/5k/10k
---

# Analysis — how often does hybrid lose a document lexical alone would have found?

## What this run was for

Phase 9 M2. The orbit run filed one anecdote — *"hybrid demoted a lexical rank-5
hit out of top-5"* — under the heading **"fusion is not monotone."** Two
questions had to be answered before anyone could decide what to do about it:

1. **Is the monotonicity claim true?** (M0)
2. **How big is the population, really?** n=1 on one question kind is not a basis
   for changing fusion.

## Headline

- **The monotonicity claim is false, and the arithmetic is exact.**
- **The population is real, ~4% on realistic corpora, and spans four question
  kinds — not just `zero-overlap`.**
- **The supersession penalty is not implicated at all.**
- **Synthetic corpora lose 9–64%, and why they differ from realistic ones is
  NOT established here.**

## M0 — RRF is monotone; the arithmetic reconciles exactly

`RRF(d) = Σ_r 1/(k + rank_r(d))`, and `1/(k + rank)` is **strictly decreasing in
rank**. Monotone by construction. The filed claim conflates:

| property | true? |
|---|---|
| monotone in per-list rank | **yes** |
| rank-*preserving* w.r.t. one input list | **no — and that is what fusion IS** |

Verified empirically rather than argued: **160/160 fused results across 4 orbit
queries reconcile to the formula with zero delta**, including a penalised
superseded document (whose term is `1/(k + rank + 15)`).

> **A false mismatch, worth recording.** The first pass of the checker reported
> 1/160 failing — the superseded document. The checker, not the engine, was
> wrong: it omitted the supersession offset. Adding the term gave 160/160 at zero
> delta. **Reconciliation scripts must model every term the engine applies**, or
> they manufacture the bug they were written to rule out.

```bash
python3 evidence/verify_rrf.py     # 160/160, worst delta 0.00000000
```

## M2 — the population, measured across all four eval sets

Per question: is the expected document in top-5 under `--lexical-only`, and is it
in top-5 under default hybrid? `LOST` = lexical found it, hybrid did not.
**`gained` is reported alongside, because a one-sided count would misrepresent a
trade as a pure loss.**

| eval set | n | **LOST** | gained | net | loss rate |
|---|---|---|---|---|---|
| fixture | 21 | **0** | 1 | **+1** | 0.0% |
| acme | 55 | **2** | 1 | −1 | 3.6% |
| orbit | 53 | **2** | 2 | **±0** | 3.8% |
| synthetic 1k | 11 | **7** | 0 | −7 | 63.6% |
| synthetic 5k | 52 | **10** | 0 | −10 | 19.2% |
| synthetic 10k | 104 | **9** | 2 | −7 | 8.7% |

### It is not confined to `zero-overlap`

The filed anecdote was a `zero-overlap` question. It is **four kinds**, and the
worst case is far more serious than the one filed:

| corpus | kind | lexical rank | outcome |
|---|---|---|---|
| orbit | **`factual`** | **1** | **lost from rank 1** |
| orbit | `zero-overlap` | 5 | lost (the originally filed case) |
| acme | `cross-doc` | 2 | lost |
| acme | `stale-vs-current` | 2 | lost |

**A `factual` question whose answer lexical ranked #1 is dropped out of hybrid's
top-5 entirely.** That was not visible in the original filing.

### The supersession penalty is not implicated

Re-ran both realistic corpora at `supersession_penalty = 0` and at the shipped
default `15`:

- **Identical lost-sets, identical counts, both corpora.** The offset never
  *creates* a lexical-top-5 loss.
- acme's `stale-vs-current` loss is present at penalty 0 too — it is one of the
  **unmarked** inversions, which the penalty cannot reach by construction.
- Consistent with M0: the demoted orbit document is not superseded, and the
  finding predates v0.26.0.

**DoD 3 answered: no interaction.**

### Per-case mechanism — the other lists genuinely disagree

For the originally filed orbit case:

| document | bm25f | dense | dense_global | dense sim |
|---|---|---|---|---|
| **expected** (hybrid #23) | **5** | **56** | **117** | **0.3297** |
| beat it (hybrid #2) | 13 | 1 | 1 | 0.4895 |

The expected document's similarity (0.3297) sits barely above ADR 0010's
**0.23–0.26 noise band**. Two of three lists ranked it poorly. Fusion propagated
its inputs faithfully.

## A hypothesis this run tested and REJECTED

The obvious explanation for synthetic being so much worse is that its documents
are near-duplicates, so dense similarity is compressed and uninformative — while
RRF, being rank-only, cannot tell an uninformative list from a decisive one.

**The measurement does not support it.** Similarity spread over the top 16:

| corpus / query | spread |
|---|---|
| synthetic 1k — composite index | 0.1148 |
| orbit — inventory accuracy | 0.1058 |
| orbit — inbound ASN rejected | 0.1568 |

**Comparable.** Compressed dense spread does not distinguish the corpora, so it
cannot explain a 4% vs 64% difference. The hypothesis is recorded as tested and
rejected rather than quietly dropped.

## Unresolved — stated as unresolved

- **Why synthetic loses 9–64% while realistic corpora lose ~4% is NOT
  established.** The rate does fall as the synthetic corpus grows
  (63.6% → 19.2% → 8.7%), which is consistent with
  `proposals/hybrid-degrades-at-scale.md` concluding the 1k gap is a corpus
  artifact that closes with scale. Consistent with — not evidence for. The
  discriminating experiment (matched-length, matched-duplication corpora) was not
  run.
- **Synthetic 1k is n=11 with 7 lost.** Small enough that the rate is unstable;
  do not quote 63.6% as a property of anything.
- **Whether the ~4% realistic loss is *wrong*** is not a measurement question at
  all. In every realistic case the other two lists genuinely disagreed. Whether
  fusion *should* be allowed to overrule a strong lexical hit is a product
  decision — phase 9 M3's compare doc.

## Specific decisions this run supports

1. **Correct the filed finding.** "Non-monotone fusion" is a misdiagnosis and has
   been corrected in place (orbit ANALYSIS, release-verification ANALYSIS, the
   conformance index, and the harness's own check label).
2. **The guard question is legitimate but small on realistic corpora** — ~4%,
   roughly offset by gains (orbit net ±0, acme net −1, fixture net +1). A guard
   would buy little there.
3. **The `factual`-lost-from-rank-1 case is the strongest argument for a guard**,
   and it should be the case any proposed guard is judged against.
4. **Do not tune fusion against the synthetic corpora.** Their loss rate is large
   but unexplained, and the standing conclusion is that they are artifacts.

## Files

- `evidence/verify_rrf.py` — the 160/160 reconciliation.
- `evidence/lexlost.py`, `lexlost_fixture.py` — the measurement harnesses.
- `evidence/{fixture,acme,orbit,1k,5k,10k}-lexlost*.json` — per-set results with
  the full lost/gained detail.
- `evidence/{acme,orbit}-lexlost-p0.json` — the penalty-interaction control.
