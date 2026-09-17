---
type: Report
run: 2026-09-15-observer-latency
item: W-181
classification: surface capture
description: "The observer hook's seam costs +0.7 ms p50 on fux's own repo and -0.3 ms on golden rung-10000 — indistinguishable from zero on both. A 2 000 ms observer adds +63 ms, not 2 000: the cap's promise holds, and 0 of 350 abandoned threads ever finished."
filed: 2026-09-15
---

# REPORT — what `.fux/observers/` costs

**Not a paired run** in SR-RS decision 22's sense: no queries are judged and no
ranking moves — every arm returns byte-identical results by construction
(SR-OBSERVE decision 5, held by a hostile test). It times three configurations
of one engine, so it is a **surface capture** and files no verdict.

## The fork W-181 was filed with, resolved

| | | chosen |
|---|---|---|
| **a reference observer in fux** | `tools/observer-bench/reference_observer.py` — append a line, return | ✅ |
| cage's real observer | `cage setup` drops it; it writes cage's ledger | ⏳ the **reopen trigger**, not an alternative |

🔴 **The number below prices the SEAM, not a subscriber.** Finding the
directory, importing a module, building the record, calling it, restoring
stdout. Cage's observer writes cage's ledger and that cost is cage's; **this
number may never be reported as a subscriber's**, which is why the reference
observer's own docstring opens with the same sentence.

**Why this arm first anyway:** the seam's cost exists today and is fux's to
know. W-170 sat 🟡 on *"a real subscriber's observer"* — a wait nothing in fux
could ever clear.

## Method

- **One process per query**, cold start included — what a consumer pays, and the
  shape the hook actually runs in (SR-OBSERVE decision 10d: one process, one
  verb, one dispatch).
- **Interleaved `off on` inside every repeat**, never blocked.
- **Median of each query's repeats**, then p50 and p95 **of those medians**.
- Queries drawn from each corpus's own vocabulary by the differential harness's
  fixed generator — corpus-derived, so they cannot be curated toward a friendly
  latency profile.
- **`[observe] max_ms` = 50** (the shipped default; this repo sets no override).

## Result 1 — the seam is free, on both corpora

| corpus | arm | p50 | p95 |
|---|---|---|---|
| **fux's own repository** (1 239 docs, 40 queries × 5) | off | 181.7 ms | 304.0 ms |
| | on | 182.3 ms | 306.5 ms |
| | **delta** | **+0.7 ms** | **+2.5 ms** |
| **golden `rung-10000`** (10 000 docs, 30 queries × 5, scratch copy) | off | 194.2 ms | 256.6 ms |
| | on | 193.9 ms | 256.0 ms |
| | **delta** | **−0.3 ms** | **−0.6 ms** |

**The 10 000-document delta is negative**, which is the honest way to read both:
the seam's cost is **below this instrument's resolution**. It does not scale with
the corpus, which is the property that matters — the dispatch runs once per
process regardless of how much work the verb did.

⚠ **Both arms fired.** 200 of 200 and 150 of 150 observer records written. A
delta measured against an observer that silently never ran would be a measurement
of nothing, so the run counts them and says so.

## Result 2 — the cap's promise, tested against the claim it actually makes

[SR-OBSERVE](../../../records/0157_observe.md) decision 10b corrected decision
6: the cap **abandons** a thread, it does not kill one. So the testable claim is
not *"the observer was stopped"* — it is **a consumer's analytics cannot make
`fux ask` slow, only itself**.

A third arm installs an observer that sleeps **2 000 ms**:

| corpus | slow p50 | delta vs off | what it would be if the cap did nothing |
|---|---|---|---|
| fux's repo | 245.1 ms | **+63.5 ms** | +2 000 ms |
| `rung-10000` | 256.7 ms | **+62.5 ms** | +2 000 ms |

**+63 ms against a 50 ms cap, on both.** The cap holds, and the ~13 ms above it
is thread start plus the dispatch the fast arm already showed is free.

🔴 **And `0 of 350` abandoned observers ever finished.** The slow observer writes
its line *after* the sleep; across both corpora, with a half-second grace after
the sweep, **not one record appeared**. So in practice the abandoned thread dies
with the process — which is what decision 10b said could not be *promised*, and
is what happens. **The record is right to promise the weaker thing**: a consumer
whose process outlives the sleep would see the write land.

## What this does NOT establish

- **Nothing about a subscriber's cost.** See the fork above.
- **Nothing about Node.** Out of scope by declaration (SR-NODE-SEARCH decision
  18) — a repo with observers records its Python runs and not its Node runs.
- **No threshold is ruled.** There was none to rule.

## Headroom

**Not a paired run.** No arms over judged queries and nothing to compare in
quality terms, so decision 22's disclosure does not apply.

## ⚠ The rung was re-ingested, and that is a finding of its own

`rung-10000` could not be read at all: a `fux.index.v2` index, three
`[ranking]` keys W-152 removed, and a `fux.toml` key W-164 moved. **All eight
rungs carry all three** — filed as **W-186**, which blocks W-180, W-154 Part B
and W-175.

**This run used a SCRATCH COPY**, re-ingested at `fux.index.v3` with the retired
keys deleted; no frozen rung was touched. ⚠ **The absolute latencies here are
therefore not comparable with any earlier ladder timing**, and nothing in this
run needs them to be: what it reports is a within-run delta between three
configurations measured minutes apart.

## Reproduce

```console
$ python tools/observer-bench/run.py --root . --queries 40 --repeats 5 \
      --warmups 3 --cap-arm 2000
```
