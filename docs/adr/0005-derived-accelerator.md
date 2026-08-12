---
type: ADR
title: "ADR-0005: the derived T1 accelerator and the differential law"
description: M2's decision record. A derived term-major blocked accelerator under .fux/runtime/ with a binary offset table and bounded skipping, constrained by a byte-for-byte differential law against the reference scan. The dense lane and RRF fusion land alongside it and ship default-off on measured evidence.
status: proposed
timestamp: 2026-08-12T00:00:00Z
---

# ADR-0005: the derived T1 accelerator and the differential law

- **Status:** proposed (Arpit ratifies)
- **Date:** 2026-08-12
- **Feature:** M2 — the T1 accelerator, the dense lane, and RRF fusion.

## Context

M1 shipped `fux ask` as a **B2 byte-prefilter scan**: every shard line is read
as raw bytes, `json.loads`'d only if it contains a query term's hash. Correct,
clone-ready, and linear in corpus size. The index-format compare doc measured
where that runs out — 653 ms per query at 5k docs unfiltered, 191 ms with the
prefilter, and a common-term line at `df=400k` costing **397 ms to parse on
its own** (B4).

The compare doc's answer is a **derived, blocked, term-major** accelerator
with integer `mx` skipping, measured at 44 ms on B4's trap (B5). It is
gitignored, rebuilt from the committed shards, and — the part that makes the
whole tiering story hold — **must return exactly what the scan returns**.

Two other things landed with it because M2 is where they were scheduled: the
dense lane over the FuxVec `code` property M1 has been writing and nothing has
been reading, and RRF fusion ported from the archived engine.

## Decision

### 1 · One scorer, two candidate generators

**The accelerator generates candidates and corpus statistics. It never scores
and never sorts.** `query/rank.py` does both, for both paths, summing each
document's BM25F contributions in query-hash order.

This is structural, not stylistic. Floating-point addition is not associative,
so a term-major accelerator that accumulated scores term-by-term would produce
different low-order bits and a different `--json` payload while being
logically correct. Keeping one scorer reduces the differential law to a claim
that can actually be tested: *the candidate set and the statistics are
identical.*

### 2 · The differential law

**Accelerator results equal scan results, byte for byte**, asserted over
generated sweeps and the graded playground corpus, in both skipping modes, at
four `top` values. Not spot-checked, not top-5, not tolerance-based.

### 3 · The offset table is binary, and `mx` lives in it

A 40-byte fixed-width entry per block: `term, block_no, offset, length, mx,
mnw, first_doc, last_doc, count`, sorted by `(term, block_no)`.

This **improves on B5**. B5 reads a block's max-impact by string-slicing the
block line; reading it from a fixed-width side table is strictly cheaper (one
`struct.unpack` at a computed index, the block line never touched) and keeps
the block line honestly valid JSON — fixed-width integers inside the line
would need zero padding, which JSON forbids. `first_doc`/`last_doc` let a
deferred term test *"does this block cover any of my candidates?"* without
parsing it.

The table is derived and never committed, so no committed-bytes law applies.
`mx` and `mnw` are integers regardless, per compare doc §7.

### 4 · Bounded deferred-term admission (the skipping rule)

Query terms open **rarest first**. After each term, every candidate has an
exact score, so the k-th best `theta` is exact. An unseen document matches
only deferred terms, so its ceiling is the sum of those terms' best block
bounds. If the ceiling cannot reach `theta`, every unopened block is skipped;
otherwise the next term opens and the test retries. **Worst case is the scan's
work — never a wrong answer.**

`bound(block)` uses `mx` **with** `mnw` because a term's BM25F contribution

```
idf(h) · wtf · (K1+1) / (wtf + K1·(1 − B + B·wlen/avg_wlen))
```

is strictly increasing in `wtf` (derivative `C(K1+1)/(wtf+C)² > 0`) and
strictly decreasing in `wlen`. `mx` alone is a valid but loose bound.

**The comparison is rounding-aware**, and that is load-bearing: `rank()` sorts
on `round(score, 9)`, so a document scoring `theta − 1e-12` still ties after
rounding and can win on `id`. The test is
`round(bound, 9) < round(theta, 9)` — since `round` is monotone and
`bound ≥ score`, that proves the document loses outright rather than ties. A
naive `bound < theta` is wrong, and wrong *only on ties*.

### 5 · Two build-time invariants, enforced by refusing to build

`scan.py` derives `df` from a **raw-bytes substring check** and `total_wlen`
from a **regex**, then scores from the parse. The accelerator derives both
from the parse. They agree only if no quoted 16-hex token ever appears outside
`terms`, and if the regex `wlen` is always the record's `wlen`. Neither is
guaranteed by the schema — a document titled `deadbeefdeadbeef` breaks the
first, silently, on the scan side only.

Both are asserted per record at build time, and the build **fails loudly**.
Same discipline as `store/collisions.py`: a loud build failure beats a
one-in-a-million ranking divergence no test would catch.

### 6 · The dense lane and RRF fusion ship **default-off**

Fusing a second lane changes rankings by construction, so the differential law
cannot cover it. `ask` with no flags stays the lexical answer; `--hybrid` opts
in. The default is set by the measurement in Consequences, not by preference.

## Alternatives considered

| alternative | why it lost |
|---|---|
| **Score inside the accelerator** (term-at-a-time accumulation) | The natural term-major shape, and it silently breaks byte-identity through float non-associativity. The bug would look like a rounding artifact and be a design error. |
| **`mx` string-sliced from the block line** (literal B5) | Works, and is what the compare doc measured — but it parses/slices the line to make a decision that a side table answers for free, and forces the line out of valid JSON if the field is fixed-width. |
| **Full Block-Max WAND** | The textbook answer, and tighter. It also interleaves partial scoring with skipping, which reintroduces the summation-order problem and makes the tie-break interaction much harder to prove. The bounded-admission rule above is weaker but has a one-paragraph correctness argument and the same effect on the case that matters. |
| **`mx` alone, without `mnw`** | Valid but loose, and *looks* correct on any corpus whose documents are similar in length — the worst kind of wrong. |
| **Re-hash every shard to check freshness** | Correct, and costs hundreds of ms on a large index — inside R3's own budget. Split into a volatile `stamp.json` (sizes + mtimes, the fast check) and a deterministic `manifest.json` (shas, for `doctor`). |
| **Ship hybrid enabled**, as v0.26 did | Measured net **−6** on the graded corpus (see Consequences). The archived engine shipped it enabled only *after* an eval gate passed. |
| **Drop `offsets` from the ported RRF** | Nothing passes it in this build. Kept because it encodes archived ADR-0015's *calibrated* arithmetic, and re-deriving that from prose later is re-doing paid-for measurement. |

## Consequences

### The differential law holds

- **5,536 comparisons** on this repo (692 generated queries × 4 `top` values ×
  2 skipping modes): byte-identical.
- **552 comparisons on the RFC corpus** (92 queries × 3 `top` × 2 modes):
  byte-identical. **This is the run that matters** — it is the only one where
  block skipping is genuinely load-bearing, so it exercises the bound and
  checks correctness simultaneously. Aggregate: scan 768.3 s, accelerator
  14.6 s — **52× with zero byte changed**.
- **50/50 playground goldens**: the accelerator's pass/fail set is identical
  to the scan's.
- **The shipped CLI**: `ask` and `ask --scan` emit identical `--json` bytes
  across four queries and three `top` values (`tests_e2e/test_verbs.py`).
- The unit suite carries a hermetic differential over synthetic corpora built
  for ties, missing `wlen`, `title_h`, and terms spanning many blocks.

### Mutation testing changed the harness, and that is the most useful thing here

The harness was written before the accelerator, as required. It was then
**mutation-tested, and found blind**: replacing `block_bound` with a constant
**zero** still produced byte-identical output at `top=5`, because on a
repo-scale corpus the rarest query term already determines the answer. The
bound was never load-bearing at the default.

The harness now sweeps `top ∈ {1, 5, 20, 50}`, where the same mutation is
caught immediately. Measured sensitivity afterwards:

| bound understated by | caught? |
|---|---|
| 0.1 % / 1 % / 5 % | no |
| **10 %** | **yes** (2 mismatches) |
| 50 % / 100 % | yes (51 / 165 mismatches) |

So the end-to-end differential catches *structural* bound errors, and
`tests/derive/test_bounds.py` catches *any* understatement — exhaustively, per
posting, per block — plus asserts the bound is not vacuous. Both layers are
needed; neither is sufficient.

**A differential harness that only checks the default `top` will certify an
unsound bound as proven.** That is the generalizable finding.

### R3 — **PASS**, with the worst-case population reported separately

**8,870 RFC documents** (2 of 8,872 skipped as non-UTF8), 419,627 distinct
terms, highest `df` 8,866, median `df` 1. Committed index 230 MB; derived
accelerator 130 MB. Warm, median of 3 runs after a warm-up, per query.

| population | path | median | p95 | max |
|---|---|---|---|---|
| **worst (highest df)** | scan | 2869.2 ms | 4248.8 ms | 4492.0 ms |
| | accel, skipping **off** | 32.1 ms | 53.6 ms | 59.7 ms |
| | **accel, skipping on** | **25.2 ms** | **27.2 ms** | **29.1 ms** |
| typical (median df) | scan | 274.3 ms | 324.0 ms | 346.1 ms |
| | accel, skipping off | 10.8 ms | 11.2 ms | 11.4 ms |
| | accel, skipping on | 11.1 ms | 11.6 ms | 11.9 ms |
| multi-term | scan | 2981.6 ms | 4604.5 ms | 5833.6 ms |
| | accel, skipping off | 23.3 ms | 24.8 ms | 44.2 ms |
| | accel, skipping on | 24.1 ms | 27.7 ms | 28.0 ms |

**R3 is judged on the worst-case population, at p95: 27.2 ms against a
150 ms bar. PASS**, with 5.5× headroom. The slowest single query in that
population — `community`, `df` in the thousands — is 29.1 ms.

Three things the table says that a headline number would not:

- **Skipping is load-bearing at this scale**, unlike on the repo corpus.
  Worst-case p95 halves (53.6 → 27.2 ms) and the tail flattens (max 59.7 →
  29.1 ms). The earlier finding — that a 100-document corpus cannot validate
  the bound — was a property of that corpus, not of the design.
- **Skipping slightly *costs* on typical queries** (11.2 → 11.6 ms p95): the
  threshold computation is real work on queries where nothing can be skipped.
  Reported rather than hidden; it is well inside budget either way.
- **The scan is not merely slower, it is over budget by 28×** on worst-case
  p95. B4's trap reproduces at RFC scale exactly as the compare doc predicted.

### Hybrid: measured, and off

Graded on the playground's 50 goldens with a **verbatim port** of the
playground's own `grade()` (copied, not approximated — a lab bench that scores
itself more generously than the consumer's harness is worse than no bench):

| mode | pass | fail | xfail | XPASS | regressions |
|---|---|---|---|---|---|
| scan | 41 | 0 | 9 | 0 | 0 |
| accelerator | 41 | 0 | 9 | 0 | 0 |
| **hybrid** | **35** | **9** | 6 | **3** | **9** |

Hybrid closes three named gaps (`q009`, `q030`, `q036`) and breaks nine
passing queries. Net **−6**.

**All five no-answer queries regress**, and the archived engine had already
written down why: *a binary prefilter always has a nearest neighbour*, so
fusing a dense lane destroys the reachability of "No confident matches"
(archived ADR-0010, preserved in INTERVIEW's "what a confident successor must
not clean up"). The archived measurement — noise at 0.23–0.26 cosine against a
true rescue's 0.34, no separating floor — is exactly what reproduced here.
This implementation walked into a documented trap and the graded corpus caught
it in one run.

The other four (`q018`, `q019`, `q023`, `q025`) are attractor/collision
queries: a document that mentions everything sits close to every query in a
256-bit sign-quantized space.

**A second instrument agrees.** Under fusion, R2's frozen Q1 loses ADR-0003
from the top 5 and Q2 loses the index-format compare doc.

### What we now owe

- **A `known_failure` list in the plan that matches the corpus.** `PLAN.md`
  §M2 and W-22 name class 3 as `q008, q017, q030, q031, q036`. On disk `q008`
  and `q017` are **not** known failures and pass today. The real set is
  `q005, q009, q011, q015, q030, q031, q036, q040, q041`.
- **A source-exclusion mechanism** ([W-45](../open/W-45-source-exclusion.md)) —
  filing this milestone's own evidence into `docs/` contaminated the corpus it
  measured.
- **A decision on hybrid's default** if anyone wants it flipped: that needs a
  no-answer floor first, and the archived calibration says none exists on
  pool-relative scores.
- `.fux/runtime/` is a new derived directory in every consumer's tree. `fux
  doctor` reports it; `.fux/.gitignore` already listed `runtime/` from
  ADR-0011, which is the ignore rule that ADR predicted would matter.

## References (required)

- **Ding, S., Suel, T.** *Faster Top-k Document Retrieval Using Block-Max
  Indexes.* SIGIR 2011 —
  <https://engineering.nyu.edu/~suel/papers/bmw.pdf>. The block-max idea this
  ADR's `mx` implements, and the design the bounded-admission rule
  deliberately simplifies.
- **Cormack, G., Clarke, C., Buettcher, S.** *Reciprocal Rank Fusion
  Outperforms Condorcet and Individual Rank Learning Methods.* SIGIR 2009 —
  <https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf>. The `k=60`
  default, unchanged from the archived engine.
- **Robertson, S., Zaragoza, H.** *The Probabilistic Relevance Framework:
  BM25 and Beyond*, FnTIR 2009 — the weight-then-saturate formulation whose
  monotonicity in `wtf` and `wlen` the block bound rests on.
- [`docs/compare/index-format.compare.md`](../compare/index-format.compare.md)
  §2 (B1–B6) — the measurements this milestone implements, and the format of
  record it does not change.
- [`docs/adr/0004-index-format.md`](0004-index-format.md) — the committed
  format, frozen; and [ADR-0011](0011-fux-dir-layout.md) — the derived-plane
  contract `.fux/runtime/` lands under.
- `archive/v0.26/src/fux/index/fuse.py` + `tests/test_hybrid.py`,
  `tests/test_supersession_penalty.py` — ported with their tests.
- [`docs/INTERVIEW.md`](../INTERVIEW.md) §"what a confident successor must not
  clean up", item 5 — the nearest-neighbour finding this milestone
  reproduced.
