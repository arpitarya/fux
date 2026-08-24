# Fork 3 — what per-field extrema cost the block bound

**Filed:** 2026-08-23 (Cowork, W-76 Phase 1)
**Question:** W-76's record half made field weights tunable at query time,
forcing the accelerator's `mx`/`mnw` from pre-weighted scalars to per-field
arrays recombined at query time. Provably safe, provably looser. **How much
looser, and does it still clear R3's bar?**
**Harness:** [`tools/differential/bench_fork3.py`](../../../tools/differential/bench_fork3.py)

## 1 · The bar

| | |
|---|---|
| corpus | 10 000 synthetic documents (the design-point ceiling) |
| queries | 60 queries x 2 `top` values = 120 timed calls, caches warmed |
| **accelerator warm p95** | **64.54 ms** |
| bar (R3) | 150 ms |
| accelerator median | 44.69 ms |
| reference scan p95 | 207.28 ms |
| **verdict** | **PASS** |

⚠ **This is NOT comparable to R3's 27.2 ms.** Different corpus (synthetic vs
8 870 real RFCs), different machine (arm64 device VM), different analyzer.
Reading a regression into 27.2 -> 64.5 would be comparing three changes at
once. The bar is absolute and it is cleared; that is all this row says.

## 2 · The attribution — same corpus, same process, same second

Because (1) cannot attribute anything, the harness also computes the
**pre-fork-3 tight bound** (each block's true maximum weighted tf and true
minimum weighted length, read from its own postings) and counts blocks read
under each.

| | blocks read |
|---|---|
| per-field extrema (loose, shipped) | 18 252 |
| oracle scalar (tight, pre-change) | 18 252 |
| **extra attributable to fork 3** | **+0.0 %** |

## 3 · Why zero, and the check that the measurement is not vacuous

A zero result is exactly the shape a broken measurement takes, so the bounds
were compared numerically rather than trusted:

| | |
|---|---|
| blocks compared | 101 |
| bound identical | 35 |
| bound genuinely looser | **66** |
| loose/tight ratio, median | **1.005** |
| loose/tight ratio, max | **1.008** |

**The looseness is real and it is 0.5 %.** Two reasons it is that small:

1. **92.5 % of postings are single-field** (measured 2026-08-23). When every
   posting in a block touches one field, the sum of per-field maxima *equals*
   the true maximum weighted tf — the bound is not loose at all, it is exact.
2. Where blocks do mix fields, the per-field maxima usually come from the same
   document anyway.

A bound 0.5 % high essentially never flips `round(bound, 9) < round(theta, 9)`,
which is why the block count is unchanged.

---

## 5 · Amendment, same day — re-run on a REAL 10 000-document corpus

§5 declared *"synthetic corpus"* as the first threat to validity and said a
real-prose corpus was owed. `fux-lab`'s `2026-08-22-r9-t2` environment became
reachable later the same day; this is that run, on its 10 000 generated-prose
documents, with **queries drawn from the corpus's own vocabulary** rather than
from a synthetic word list.

| | synthetic (§1) | **real prose** |
|---|---|---|
| accelerator warm p95 | 64.54 ms | **33.53 ms** |
| accelerator median | 44.69 ms | **12.67 ms** |
| reference scan p95 | 207.28 ms | 225.18 ms |
| **extra blocks read (fork 3)** | +0.0 % | **+0.0 %** |
| R3 bar (150 ms) | PASS | **PASS** |

*(evidence: [`evidence/real-corpus-10k.log`](evidence/real-corpus-10k.log))*

**The verdict holds, and the threat resolved in the opposite direction to the
one declared.** §5 guessed real prose was *"more likely pessimistic than
optimistic"* for the timing. It was the reverse: the synthetic corpus was the
pessimistic one, at nearly **2x** the p95. A 30-term vocabulary makes every
query hit a large fraction of the corpus; real prose has a long tail, so the
rare term that seeds a query is genuinely rare and the candidate set is
smaller.

**33.53 ms is also the first figure in this file that is fairly comparable to
R3's 27.2 ms** — both real prose, both ~10 000 documents, both queried from
the corpus's own vocabulary. It is a different corpus on a different machine
with a different analyzer, so it is not a like-for-like regression test, but it
is the same order and the direction is right.

**Fork 3 costs +0.0 % on real prose too**, which was the open question. The
single-field share that explains it is a property of how documents are
written, not of the generator.

## 5b · The differential law, on the same corpus

| | |
|---|---|
| corpus | the same 10 000 real documents |
| queries | 10 from the corpus's own vocabulary |
| tops x weights x modes | 3 x 3 (incl. **500.0**) x 2 = **180 comparisons** |
| result | **byte-identical in every mode, top and weight** |

And on `fux-playground`'s 10 hand-written documents: **21 376 comparisons,
byte-identical**, weight sweep included.

Together these are the strongest available evidence that W-76's record-format
change, the per-field block bound, the weighted `theta` and the Phase 2 priors
did not move a single ranked byte between the two paths — on real corpora
rather than on fixtures written to exercise one condition.

## 4 · Verdict

**Fork 3 option B (per-field extrema, recombined at query time) is free.**
It buys tunable field weights with no measurable pruning loss, and
`ADR-TUNE`'s promise that *editing your ranking cannot break your index*
survives.

**Reopen if** a corpus with a materially lower single-field share is measured —
the 0.5 % looseness is a consequence of that 92.5 %, not a property of the
scheme. A corpus where most terms appear in three or more fields would widen
the gap, and the first place that could happen is **Phase 8**, when `ctx`
starts carrying real tokens.
