---
type: Report
run: 2026-09-15-ladder-reingest
item: W-186
classification: surface capture
description: "All eight golden rungs re-ingested at fux.index.v3 and re-stamped. Every rung had been unreadable by HEAD; every rung now answers. No document moved — the manifests are untouched and the per-document check is clean on all eight."
filed: 2026-09-15
---

# REPORT — the golden ladder, made readable again

**Not a paired run.** No arms, no judged queries, no threshold — it is
maintenance, performed and recorded. A **surface capture**, and it files no
verdict.

## What was wrong, on all eight rungs

Three refusals, in the order a plain `fux ask` hits them:

| # | refusal | landed |
|---|---|---|
| 1 | `.fux/tune.toml`: `[ranking] archived_weight` (with `superseded_weight` and `recency_half_life_days`) | W-151/W-152, **2026-09-13** |
| 2 | `fux.toml`: `[sources.url] urls_file` moved to `[sources]` | W-164, **2026-09-14** |
| 3 | `.fux/index/*.jsonl` declares `fux.index.v2`; the engine writes `v3` | W-168 step 1, **2026-09-15** |

**All three on all eight** — `rung-seed` · `00100` · `00200` · `00500` · `01000`
· `02000` · `05000` · `10000`. Checked, not inferred.

🔴 **Nothing detected it.** No test, hook or CI arm reads a rung, so a format
bump and two key retirements landed over nine days and the ladder went quiet.
Four queued items measure on it, and the queue had been calling three of them
ready.

## What was done — the documented step, performed

[`work/golden/README.md`](../../golden/README.md) already decides this: *"use
the rung's own index — do not re-ingest; check the engine version matches
`ladder/rung-NNNNN.index`; if it does not, re-ingest that rung once, update the
record, and say so in the report."* This is that, on eight rungs.

Per rung: the three retired `[ranking]` keys deleted, `urls_file` moved up one
level, `fux ingest --full`, the rung committed, the stamp rewritten, then
`rungs.verify(documents_too=True)` and one real `fux ask`.

| rung | documents | ingest | verify | `ask` |
|---|---|---|---|---|
| `rung-seed` | 20 | ok | clean | 3 results |
| `rung-00100` | 100 | ok | clean | 3 results |
| `rung-00200` | 200 | ok | clean | 3 results |
| `rung-00500` | 500 | ok | clean | 3 results |
| `rung-01000` | 1 000 | ok | clean | 3 results |
| `rung-02000` | 2 000 | ok | clean | 3 results |
| `rung-05000` | 5 000 | ok | clean | 3 results |
| `rung-10000` | 10 000 | ok | clean | 3 results |

**Manifests untouched, and that is the claim that matters.**
`ladder/rung-NNNNN.sha256` hashes the **documents**; not one was written.
`tools/differential/ladder_check.py` re-run afterwards:

```
8 rungs, manifests consistent and nesting verified
```

⚠ **The `verify()` index-root check is circular and the document check is not.**
`verify` compares the corpus's index root against the stamp this run just wrote,
so that half can only agree. **The load-bearing half is the per-document pass** —
100 to 10 000 file hashes per rung, against manifests written weeks ago by a
different session — and it is clean on all eight.

## 🔴 The stamp gained a field, because the version alone was a false match

The engine that wrote these indexes reports **`fux 2.0.1`**. `fux-engine 2.0.1`
is published on PyPI and npm, and it writes **`fux.index.v2`**. `fux.index.v3`
sits under `[Unreleased]` in the changelog, which is the normal shape — the
version bumps at release.

**So *"check the engine version matches the stamp"* compared two engines that
cannot read each other's index, and saw a match.** Every stamp now also carries:

```
engine_commit: 1c84acb6a1e82be8d8d0114fe04052986a91c185
```

Between releases the version string is the *last release's*; the commit is what
identifies the engine that actually built the rung.
[`work/golden/README.md`](../../golden/README.md) says so where it describes the
stamp.

## What this run does NOT do

- **It measures nothing.** No latency, no ranking, no quality. A rung that
  answers is not a rung that answers *well*.
- **It touches no document and no manifest.** The corpus is frozen and stays
  frozen; what moved is a derived, committed index and two config files.
- **It does not re-freeze anything.** `ladder/*.sha256` is byte-identical.
- ⚠ **It does not make this detectable next time.** See the analysis.

## Headroom

**Not a paired run.** Nothing is compared, so SR-RS decision 22 does not apply.

## Reproduce

```console
$ python work/regression/2026-09-15-ladder-reingest/evidence/reingest.py
$ python tools/differential/ladder_check.py
```
