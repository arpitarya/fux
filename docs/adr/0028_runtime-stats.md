---
type: ADR
name: ADR-RUNTIME-STATS
title: ADR-RUNTIME-STATS (0028) — stats.json, the corpus-wide numbers BM25F needs
description: n, the RAW per-field token-count totals, and the corpus's newest commit timestamp — computed once at build time so length normalisation is an O(1) lookup, and stored unweighted so a field weight cannot bake into the plane.
status: accepted
date: 2026-08-19
feature: "`.fux/runtime/stats.json` — the corpus-wide aggregates, and the rule that they are stored raw"
owns: []
laws: [L3]
timestamp: 2026-08-19T00:00:00Z
---

# ADR-RUNTIME-STATS — stats.json, the corpus-wide numbers BM25F needs

## §1 — For humans

`stats.json` holds three things: `n`, the document count; `total_flen`, the
**raw** per-field token-count totals; and `newest_mtime`, the newest commit
timestamp in the corpus.

No single term's postings can supply any of them — they are properties of the
whole corpus — and BM25F's length-normalisation term needs the average document
length on every scored document, every query. Computing that once at build time
turns a per-query, O(corpus) scan into an O(1) lookup.

**The totals are stored raw and weighted at query time**, which is the whole
point of the file's shape. `avg_wlen` is still `total_wlen / n`; it is just that
`total_wlen` is derived on the way past, under the query's own `Scoring`, rather
than baked in.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    A[".fux/index/*.jsonl,<br/>every record's flen"] -->|"fux build, one pass:<br/>SUM the raw counts, per field"| B["stats.json:<br/>{n, total_flen, newest_mtime}"]
    B -->|"derive_wlen(total_flen, scoring)<br/>AT QUERY TIME"| W["total_wlen<br/>avg_wlen = total_wlen / n"]
    W --> C["BM25F length<br/>normalisation"]
    B -->|"newest_mtime"| D["recency prior —<br/>normalised so the freshest<br/>document scores 1.0"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   .fux/index/*.jsonl -- every record's flen and mtime, one pass
              |
              |  fux build: total_flen[i] += flen[i]   RAW, never weighted
              |             newest_mtime = max(mtime)
              v
   stats.json: {n: document count,
                total_flen: five RAW per-field token-count totals,
                newest_mtime: newest commit timestamp in the corpus}
              |
              +-- AT QUERY TIME, under the query's own Scoring:
              |     total_wlen = derive_wlen(total_flen, scoring)
              |     avg_wlen   = total_wlen / n
              |        v
              |   BM25F length normalisation, every scored document
              |   (both paths do this, which is why a field weight
              |    cannot make --fast and --scan disagree)
              |
              +-- newest_mtime
                       v
                  recency prior: the freshest document scores 1.0,
                  so the multiplier can only ever DEMOTE

   A weight applied on the LEFT of stats.json is baked,
   and a baked weight cannot be a tune key.
```

</details>

### Examples

The file's current shape is three sorted keys, `total_flen` a list of raw
integers. **No capture is pasted here**: this repo's runtime plane is derived
and gitignored, and inventing a line of JSON for a build nobody ran is exactly
the fabricated evidence a dated capture exists to avoid.

```console
$ fux build && cat .fux/runtime/stats.json
```

---

## §2 — For agents

### Context

BM25F's length-normalisation term needs `avg_wlen` for every scored document,
on every query. Neither the committed record nor any single posting carries a
corpus-wide average — it has to be aggregated across every document, and doing
that per query would scale with corpus size on the hot path.

### Decision

**1. Fields: `n`, `total_flen`, `newest_mtime`.** The membership bar is
**corpus-wide, unsupplied by any single posting, needed on the hot path**, and
each of the three passes it. The set is not closed by the word *exactly* — it
grows when ranking needs it to, and the veto below is what makes that growth
visible.

**2. `total_flen` is RAW, and this is the decision the file exists for.** It was
once a stored *weighted* total, and that made it a **stored function of a
tunable**. The moment field weights became `.fux/tune.toml` keys, `avg_wlen`
would move on the scan path — which derives it per query — and **not** on the
accelerator path, which read the baked number. Same corpus, two `avg_wlen`s: the
two paths returning different bytes, which is [ADR-ASK](0004_ask.md)'s
differential law breaking.

⚠ **And it would have needed a `fux build` to repair**, which is the part that
made it unshippable rather than merely wrong. **A knob whose effect requires a
rebuild is not a knob**, and the whole claim under [ADR-TUNE](0038_tuning.md) is
that editing ordering cannot touch the maintenance path.

**The rule this generalises to: store the observation, not the value derived
from it.** `flen` is a fact about a document; the weighting is a policy applied
to that fact. `total_flen` is the corpus-wide sum of the facts, and **both query
paths weight it at query time** through `derive_wlen`, which remains the one
place that arithmetic exists.

**3. `newest_mtime` is the recency prior's origin, and it buys a bound.**
Scoring a document against wall-clock *now* would make a query's results depend
on when it was run and break the byte-identity the derived plane rests on.
Normalising against the newest commit timestamp in the corpus fixes that and
gives something the accelerator cannot do without: **the freshest document
scores exactly `1.0`, so the recency multiplier is bounded to `(0, 1]` and the
prior is a pure demotion.**

⚠ **That bound is load-bearing.** `Weighting.maximum` is the supremum the block
bound is computed from, and an unbounded recency prior would make that supremum
unbounded and the pruning bound useless
([ADR-T1-ACCELERATOR](0011_accelerator.md) §The weighted bound).

**4. Computed once, at build time, in the same pass `build()` already makes**
over every committed shard — not recomputed per query.

**5. Lives in the derived plane, not the committed plane.** It is a pure
aggregate of information the committed index already carries — each record's own
`flen` and `mtime` — so committing it would be redundant, derivable bytes.
**The change to raw totals strengthens this rather than weakening it**: a
committed weighted total would go stale the moment anyone edited a field weight,
silently and corpus-wide.

**6. One of `DETERMINISTIC_FILES`.** `sort_keys` JSON, byte-identical for the
same committed input.

### Consequences

- **`rank()` gets `avg_wlen` as an O(1) lookup** instead of an O(corpus) scan on
  every query.
- **A corpus change moves length normalisation for every document.** That is the
  intended BM25F behaviour, not a side effect to guard against.
- **Editing a field weight moves it too, with no `fux build` at all.** That is
  the property the raw-totals shape bought: ordering is editable without
  touching the maintenance path.
- **`avg_wlen` costs a five-element weighted sum per query rather than a dict
  lookup**, and that is the price paid, said plainly. Five multiply-adds against
  an O(corpus) scan the file exists to avoid — the lookup was never the
  expensive part.
- ⚠ **This record owns no module, so no mechanical check can point at it.**
  Decisions about `stats.json` live here; the code lives in
  `derive/_build.py` under [ADR-T1-ACCELERATOR](0011_accelerator.md). A change to
  this file satisfies
  [`tests/test_adr_freshness.py`](../../tests/test_adr_freshness.py) by touching
  the accelerator's record, and **this record's own veto has fired unnoticed
  before, exactly that way.** Open it deliberately.

### Alternatives considered

- **Compute the aggregates at query time by scanning `docs.jsonl`.** Rejected:
  it turns a build-time, once-paid O(corpus) cost into a per-query cost.
- **Fold them into `manifest.json` instead of a separate file.** Rejected: it
  keeps the manifest focused on build fingerprinting and staleness, and this
  file focused on the one thing ranking actually reads — two small
  single-purpose files beat one file serving two unrelated readers.
- **Store the weighted total.** Rejected under decision 2, and it is the
  rejection this record exists for.
- **Track richer per-field statistics.** Once rejected as anticipation, with the
  trigger named: *not without a real requirement*. **The trigger arrived** —
  field weights became query-time keys, so the only number safe to store was the
  unweighted one, and the unweighted one is per-field by construction. Worth
  keeping as a worked example: the rejection did not say *no*, it said *not
  without a requirement*, and it named what would count.

### Reference (required)

- Generator — [`src/fux/derive/_build.py`](../../src/fux/derive/_build.py)
  (`_read_committed()`, the `stats` dict, the write to `fmt.STATS_NAME`).
- The consumers — [`src/fux/derive/accel.py`](../../src/fux/derive/accel.py)
  reads this file into `rank.Corpus`;
  [`src/fux/query/scan.py`](../../src/fux/query/scan.py) computes the same three
  numbers from the shards instead, which is what makes the two paths comparable.
  ⚠ **`rank.py` does not read this file** — it receives a `Corpus`. Pointing a
  veto check at it is what once made the check vacuous.
- The weighting function both paths share — `derive_wlen` in
  [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py).
- The parent record — [ADR-T1-ACCELERATOR](0011_accelerator.md); the scorer that
  consumes the result — [ADR-RANKING](0012_ranking.md).

### Veto condition

**Reopen this decision if** scoring needs a statistic beyond `n`, `total_flen`
and `newest_mtime`, or if a *derived* value is ever stored here.

⚠ **This veto has fired once without anyone noticing.** A field was added to
`stats.json` on the same day the record still read *"and nothing else"* — the
change landed in `build.py`, `scan.py` and `rank.py`, and **nothing in any of
the three points back here.** A veto condition is a tripwire whose only value is
that someone notices it; a contract that only moves when someone remembers to
move it does not hold. The checks below are written so the next such addition
fails a grep instead of depending on memory.

**How to check it:**

```bash
# 1. the reader's key set. A fourth key is this veto firing again.
grep -n 'stats\[\|stats\.get(' src/fux/derive/accel.py
# expect: exactly three keys — "n", "total_flen", "newest_mtime".
# NOTHING AT ALL means the reader moved and this check has gone blind —
# treat that as a failure, not a pass.

# 2. the stored number must stay RAW: a weight applied on the build side is a
#    stored function of a tunable, and only the accelerator path would see it
grep -n 'derive_wlen' src/fux/derive/_build.py
# expect: no output. build.py sums flen; accel.py weights it per query.

# 3. both paths compute the recency origin, so --fast and --scan cannot disagree
grep -n 'newest_mtime' src/fux/query/scan.py src/fux/derive/_build.py
# expect: matches in both
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-DOTFUX](0003_fux-directory.md) ·
[ADR-ASK](0004_ask.md) · [ADR-RECORD](0010_index-record.md) ·
[ADR-T1-ACCELERATOR](0011_accelerator.md) · [ADR-RANKING](0012_ranking.md) ·
[ADR-RUNTIME-MANIFEST](0026_runtime-manifest.md) · [ADR-TUNE](0038_tuning.md)

**Code**

- [`src/fux/derive/accel.py`](../../src/fux/derive/accel.py)
- [`src/fux/derive/_build.py`](../../src/fux/derive/_build.py)
- [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py)
- [`src/fux/query/rank.py`](../../src/fux/query/rank.py)
- [`src/fux/query/scan.py`](../../src/fux/query/scan.py)
