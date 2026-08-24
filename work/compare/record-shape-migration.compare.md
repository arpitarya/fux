---
type: Compare Doc
title: "The record shape under five fields — encoding, `wlen`, and the block bound"
status: proposed
filed: 2026-08-23
gates: W-76 Phase 1 (second half), and therefore Phases 2, 5, 7 and 8
---

# The record shape under five fields

**Why this document exists.** W-76 Phase 1's analyzer half is built and green
(identifier splitting, Porter stemming, `analyzer` v1 -> v2). Its *record* half
is not, and it turns out not to be routable-around: **every remaining phase
needs a new fact in the record.**

| phase | the fact it needs |
|---|---|
| 2 · priors | a commit timestamp per document, and `supersedes` edges |
| 5 · citations | `line_start` / `line_end` per passage |
| 7 · vectors | committed per-chunk `int8` |
| 8 · enrich | a `ctx` field, and its own length |

So the record shape is the backbone, not a detail, and it is worth settling
once rather than four times.

**What makes it delicate** is that three things assume a scalar today, in three
different layers:

```
committed   "terms": {"<16hex>": [tf_heading, tf_body]},  "wlen": 5233
                                  ^ fixed pair            ^ a weighted sum, COMMITTED

scan        _WLEN_RE = rb'"wlen":(\d+)'          the byte-level oracle, per line
            -> total_wlen -> avg_wlen            corpus stats, derived per query

accelerator ENTRY_STRUCT = "<8sHQIIIIIH"  (40 B)  mx = max weighted tf   } scalars,
                                                  mnw = min wlen         } precomputed
```

A change to the field set moves all three at once, and the third one is a
packed binary format.

---

## Fork 1 — how a sparse tf vector is encoded

**Measured on this repo, 2026-08-23** (411 documents, 186 799 postings):

| shape | share |
|---|---|
| body only | **92.5 %** |
| both heading and body | 5.1 % |
| heading only | 2.4 % |

92.5 % is the number that decides this fork. Encodings, all sized against the
same 941 130 bytes of tf vectors in the live index:

| | form | body-only term | measured total | delta |
|---|---|---|---|---|
| **A** | dense 5-slot, heading-first | `[0,1,0,0,0]` | ~1.16 MB | **+24 %** |
| **B** | **dense, trailing zeros omitted, BODY FIRST** | `[1]` | **595 492 B** | **-36.7 %** |
| C | object keyed by field | `{"b":1}` | ~1.4 MB | +49 % |
| D | scalar when body-only, list otherwise | `1` | ~560 KB | -40 % |

**Proposed verdict: B.**

Field order is the whole trick — `[body, heading, title, path, ctx]`, so the
92.5 % case is `[1]` and shorter than today's `[0,1]`. **Analyzer v2 therefore
makes the terms block smaller while adding three fields**, which is not the
result anyone expected going in.

D is 3 % better than B and introduces a union type into the hottest parse in
the system, for a saving that is inside the noise of a single commit's churn.
Not worth it.

## Fork 2 — `wlen`: committed, or derived from committed field lengths?

`wlen` is BM25F's length normaliser, and it is **a function of the field
weights**:

```
wlen = 3.0 * len(heading_tokens) + 1.0 * len(body_tokens)
```

[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 6 already names this as its
own violation — *no committed field may be a function of a tunable* — and
proposes the remedy *"commit the two token counts and derive `wlen` at query
time when the format next moves"*. **This is that move**, and Arpit's fork B
ruling (2026-08-23: keep the tuning parameters) makes it mandatory rather than
opportunistic: `w_ctx` cannot be a dial while the denominator it divides is
baked in.

| | A · keep `wlen` committed | B · commit `flen`, derive `wlen` at query time |
|---|---|---|
| field weights tunable | **no** — changing one silently reweights the numerator against a stale denominator | **yes** |
| bytes per record | 1 int | 5 ints (trailing zeros omitted: usually 2) |
| scan byte oracle | `rb'"wlen":(\d+)'`, unchanged | new regex over `"flen":[...]`, and the sum is computed per query |
| ADR-TUNE decision 6 | violation goes from 1 field to **5** | **discharged** |
| re-ingest to retune | every time | never |

**Proposed verdict: B.** A is only defensible if tuning is abandoned, and it
has been explicitly ruled in.

⚠ **The one-line equality gate ADR-TUNE asks for is owed here**: assert that
`derive_wlen(flen, weights) == wlen` for every record in the pre-migration
index, at the shipped default weights. That is what proves the migration moved
no ranking.

## Fork 3 — the block bound when `wlen` is weight-dependent

**This is the fork that is actually hard**, and it is not mentioned in the
ideal set at all.

The accelerator precomputes, per block of 128 postings:

- `mx` — the maximum **weighted** tf in the block
- `mnw` — the minimum `wlen` in the block

Both are weighted sums. If weights become tunable at query time, both become
stale the moment a weight changes — so either the accelerator rebuilds whenever
someone edits `tune.toml` (which breaks ADR-TUNE's central promise that
*editing your ranking cannot break your index*), or the block metadata stops
being a scalar.

| | A · rebuild the accelerator on a weight change | B · store PER-FIELD extrema, combine at query time | C · pin field weights, give up fork 2 |
|---|---|---|---|
| `tune.toml` edit costs | a full accelerator rebuild | **nothing** | n/a |
| entry size | 40 B (unchanged) | 40 B -> ~64 B (5 × `mx`, 5 × `mnw`, narrowed) | 40 B |
| bound tightness | exact | **looser** — see below | exact |
| ADR-TUNE promise | **broken** | kept | kept by abandoning fork 2 |

**B is correct, and the looseness is provably safe:**

- `mx' = sum_i (w_i * max_i tf_i) >= max_d (sum_i w_i * tf_i(d))` — a sum of
  per-field maxima dominates the maximum of the sums. An **over**-estimate of
  `mx` gives an over-estimate of the bound, which is the safe direction.
- `mnw' = sum_i (w_i * min_i len_i) <= min_d wlen(d)` — likewise an
  **under**-estimate of the minimum length. Contribution *decreases* in `wlen`,
  so a smaller `mnw` also gives a larger bound. Safe again.

Both errors push the bound up, never down, so **no document that should be
retrieved is ever skipped**. What is lost is pruning efficiency: a looser bound
skips fewer blocks.

**Proposed verdict: B, with the cost measured before it is accepted.** The
budget is R3's headroom — warm p95 **27.2 ms** against a **150 ms** bar, so
there is 5× of room, but *"there is room"* is not a measurement. Owed: p95 at
10 000 documents with per-field extrema, against the same bar.

## Fork 4 — how the migration lands

| | A · big bang | B · staged behind the analyzer bump | C · dual-read |
|---|---|---|---|
| what ships | fields + encoding + `flen` + block format, one change | analyzer v2 first (**done, green**), then the record shape | v2 reads both shapes |
| re-ingests | one | two | none, then one |
| reviewable | no — three layers in one diff | **yes** | no — the shim is permanent surface |

**Proposed verdict: B, which is already what happened.** Analyzer v2 landed
alone and the suite is green at 1149; the record shape is the second step. C is
rejected outright: a dual-read shim in `store/reader.py` is exactly the
"two analyzers in one index" hazard ADR-INDEX-LIFECYCLE decision 10 refuses,
wearing different clothes.

---

## What this costs, assembled

| | delta | running |
|---|---|---|
| today | — | 5.12 MB |
| fork 1B — body-first sparse tf | **-345 KB** | 4.78 MB |
| identifier splitting (+2 % rows, measured) | +94 KB | 4.87 MB |
| `code` field deleted (Phase 1) | -22 KB | 4.85 MB |
| fork 2B — `flen` replaces `wlen` | +~15 KB | 4.87 MB |
| **subtotal: analyzer v2 + record shape** | **-5 %** | **the index gets smaller** |

The growth in W-76 comes from Phase 7's committed vectors, not from here.

## Owed before this is accepted

1. **The `wlen` equality gate** (fork 2) — one line, and it is the proof the
   migration moved no ranking.
2. **A p95 measurement with per-field extrema** (fork 3) at 10 000 documents,
   pre-registered under ADR-RS, against R3's 150 ms bar.
3. **`ENTRY_STRUCT` is a packed binary format and `RUNTIME_SCHEMA` must bump
   with it** — it is already at `fux.runtime.v2` from W-73; this takes it to
   v3.
4. Fork 3 has **no proposed verdict from Arpit yet** and it is the one with a
   real trade in it. The other three are close to forced.
