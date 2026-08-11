---
type: Conformance Report
title: "2026-08-12 — R2 closes: the third frozen question becomes reachable"
description: W-42's measurement. Adding archive/v0.26-docs to fux.toml's configured sources makes R2's third frozen citation reachable; all three frozen questions re-run from a cold tree. R2 moves 2/3 -> 3/3 PASS. R1 re-asserted. Committed index grows 45%.
status: final
timestamp: 2026-08-12T00:00:00Z
---

# R2 closes — the run

**Verdict: R2 is 3/3 PASS.** The third frozen question now returns its
frozen citation target, from a cold tree, with no change to the engine.

**What changed:** one line of `fux.toml`. `archive/v0.26-docs` was added to
`[sources].dirs`. Nothing in `src/fux/` was touched.

## Why the question was failing

R2's three questions were frozen in the M1 handoff §9 *before* the build, so
they could not drift toward what works. Question 3 requires a citation from
the archived-docs shard. That document existed on disk the whole time; it
simply sat outside the four configured source paths. The engine was never
pointed at it — a configuration gap, not a ranking failure.

## The measurement

Run from a **cold tree** (`git archive` of the staged tree, extracted to a
fresh directory), which is what R2's threshold requires — no warm state, no
accelerator, scan only.

### The three frozen questions

| # | frozen query | required citation | rank before | rank after | verdict |
|---|---|---|---|---|---|
| Q1 | *why did pruning fail* | `docs/adr/0003-…` | 2 | **2** | **PASS** |
| Q2 | *what format is the committed index* | `docs/compare/index-format.compare.md` | 2 | **2** | **PASS** |
| Q3 | *supersession penalty safe interval* | `archive/v0.26-docs/…` | absent | **1 and 2** | **PASS** |

Q3's top two are both from the archived-docs shard, and both genuinely
answer it:

```
1. archive/v0.26-docs/compare/supersession-handling.compare.md   14.904
2. archive/v0.26-docs/adr/0015-supersession-downrank-penalty.md  12.787
3. docs/conformance/README.md                                    11.917
```

ADR-0004 named `…/adr/0015-supersession-downrank-penalty.md` as the target.
It is at #2, and the compare doc that ranks above it carries the same
interval (`[11, ∞)`, both files, verified by grep). Neither was reachable
before.

**Raw output:** [`evidence/r2-questions-after.json.txt`](evidence/r2-questions-after.json.txt)
· before: [`evidence/r2-questions-before.json.txt`](evidence/r2-questions-before.json.txt)

### R1 — asserted, not assumed

Double-ingest after the config change writes **0 shards** on the second pass
and every shard's sha256 is unchanged. R1 does not regress.

```
ingested 119 docs (34 changed), 0 skipped, 42 shards written
ingested 119 docs  (0 changed), 0 skipped,  0 shards written
```

### Committed index size delta

The first time the index has grown from a **configuration** change rather
than from new work, which is why W-42 asked for the number.

| | docs | shards | raw bytes | zlib(9) bytes |
|---|---|---|---|---|
| before | 85 | 73 | 942,479 | 416,899 |
| after | 119 | 96 | 1,367,888 | 602,825 |
| **delta** | **+34 (+40%)** | +23 | **+425,409 (+45.1%)** | **+185,926 (+44.6%)** |

Statistics scale with document count, near-linearly here. Nothing anomalous.

## Two findings the DoD did not ask for

### Finding 1 — ADR-0004's recorded "#1" for Q2 has drifted to #2

ADR-0004 recorded Q2 as ranking `index-format.compare.md` **#1** after the
tokenizer fix (2026-08-10). Today it is **#2**, behind `README.md`.

- **This predates W-42.** The cold-clone check at `baa5b04` — before any
  change in this session — already showed #2. It is not caused by the
  config change or by W-43's file moves.
- **Cause:** `README.md` gained a `.fux/` layout table on 2026-08-12
  (ADR-0011), which is a strong match for *"what format is the committed
  index"*. The corpus moved under a recorded measurement.
- **Still a PASS** — the frozen bar is that the answer cites the document,
  and Q2's recorded failure mode was falling out of the top 5 (it was #9).
- **The lesson is the general one:** a recorded rank is a measurement of a
  corpus at a moment, not a property of the engine. Ranks recorded in ADRs
  should be read with their date attached.

### Finding 2 — archived docs now answer questions about the *current* engine

**Labelled post-hoc.** Five unregistered probe queries, chosen to stress the
risk, not sampled from any distribution. This is not part of the verdict.

| probe query | archived docs in top 5 | #1 result |
|---|---|---|
| *what is the ingest cache* | **5/5** | `archive/v0.26-docs/adr/0002-ingest-cache-chunker.md` |
| *what does fux doctor check* | **3/5** | `archive/v0.26-docs/adr/0012-debug-observability.md` |
| *how does BM25F weighting work* | 2/5 | `archive/v0.26-docs/adr/0008-…` |
| *how do I configure sources* | 1/5 | `docs/archive/v0.31.0-fux-dir-layout-handoff.md` |
| *what is the committed index layout* | 0/5 | `docs/adr/0011-fux-dir-layout.md` |

**Why this matters more than the ranks suggest.** The per-file cache these
top results describe is a thing CLAUDE.md explicitly forbids porting back.
An agent asking *"what is the ingest cache"* gets five confident,
well-written documents about a deleted subsystem, and the only signal that
they are retired is the `archive/v0.26-docs/` prefix on the `loc` — easy to
miss inside a context window.

**Raw output:** [`evidence/posthoc-intrusion-probe.json.txt`](evidence/posthoc-intrusion-probe.json.txt)

This is not a reason to revert. The archived set is genuinely the right
answer to historical questions, and Q3 exists precisely because it is. It is
a reason to decide, deliberately, how retired content is signalled. See
[`ANALYSIS.md`](ANALYSIS.md).

## Reproduce

```bash
# from a clean checkout of the commit that closed W-42
.venv/bin/fux ingest
.venv/bin/fux ingest                      # 0 shards written == R1 holds
.venv/bin/fux ask "supersession penalty safe interval" --json

# the post-hoc probe
.venv/bin/fux ask "what is the ingest cache" --json
```
