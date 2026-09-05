---
type: Run Report
run: 2026-09-05-vector-gate
classification: informed
date: 2026-09-05
---

# W-106 — a contextual embedder, int8, fused by RRF. Measured; **no verdict filed**

🔴 **This run files NO `VERDICT.md`, and that is a ruling, not an omission.**
**Arpit, 2026-09-05:** measure and file without a verdict.
[DENSE-CHUNK](../2026-08-24-dense-lane-gate/VERDICT.md)'s frozen bar —
`>= 3 fixed / 0 broken` against *today's ask* — **was not tested**, because the
corpus behind *today's ask* no longer exists. §"The corpus problem" is the whole
of it, and nothing below may be read as clearing or failing that bar.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the 50 goldens and their `known_failure` notes | pre-existing (playground) | — |
| the corpus documents | pre-existing | — |
| 🔴 `tools/vector-gate/`, and the choice of model, pooling, quantisation and fusion | Claude Code, this session | **the queries, the goldens, and DENSE-CHUNK's failure analysis** |
| this report and `ANALYSIS.md` | Claude Code | everything |

**`informed`.** The instrument's author had read the graded queries. **Not a
generalisation estimate**, and no delta is claimed against any other run.

## 🔴 The corpus problem — why no verdict may be filed

`fux-playground` is empty in two independent ways, and **neither is
recoverable**:

1. **Its committed index is `_format: fux.index.v1`.** This engine writes `v2`
   and refuses to read v1 outright — *"there is no in-place migration"*. So the
   committed bytes cannot be graded at all; a re-ingest is mandatory.
2. **Its ten enrichment files were never committed.**
   `git log -- .fux/enrich` in that repo returns nothing. The corpus
   [`2026-08-28-first-recall`](../2026-08-28-first-recall/report.md) measured is
   gone from the working tree and absent from the history.

A re-derived, un-enriched corpus grades **28 / 50** where DENSE-CHUNK's control
was **32 / 50** — **four more failing queries**, so a `>= 3 fixed` bar is
strictly *easier* to clear here. **A PASS on this corpus would be a moved
threshold arriving through the corpus instead of through the number**, which is
the failure the pre-registration discipline exists to prevent.

⚠ This is [W-87 Part B](../../OPEN-WORK.md)'s blocker, filed 2026-08-27 and
**9 days old**. It now blocks a second item.

## Arms

| arm | implementation | pooling | weights | note |
|---|---|---|---|---|
| **`node-cls`** | `@huggingface/transformers` 3.7.6, ONNX, Node 24 | **`cls`** | **q8** | the model's declared configuration |
| **`py`** | `sentence-transformers`, torch, Python 3.14 | `cls` (declared) | fp32 | the reference implementation |
| **`node-mean`** | `@huggingface/transformers` 3.7.6 | **`mean`** | q8 | 🔴 **W-106's DoD specified this, and it is WRONG for BGE** — kept because it is evidence |

Model **`BAAI/bge-small-en-v1.5`** (the Node arms load `Xenova/bge-small-en-v1.5`,
its ONNX conversion — transformers.js needs ONNX weights). 384 dimensions,
10 documents → **75 chunks** by `fux.refer._chunk.chunk`, 50 queries.
int8 per vector at `127/max|x|`, max-sim per document, RRF `k = 60` against
`fux ask --json`'s ranks, graded on **rank**.

## Result 1 — retrieval: neither correctly-configured arm nets anything, and neither reaches 0 broken

All 50 goldens. `known_failure` rows are **included** — those nine *are* the
vocabulary-gap population W-106 is judged on, and DENSE-CHUNK's control counts
the same way (32 pass + 9 fail + 9 xfail = 50).

| arm | lexical pass | fused pass | dense-only pass | **fixed** | **broken** | of the 9 vocabulary-gap failures |
|---|---|---|---|---|---|---|
| **`node-cls`** | 28 | **28** | 29 | 6 | **6** | **1** now passes |
| **`py`** | 28 | **28** | 29 | 5 | **5** | **1** now passes |
| `node-mean` (misconfigured) | 28 | 34 | 32 | 10 | **4** | 2 now pass |

**Every arm breaks queries.** The correctly configured pair nets exactly zero
and moves **one** of the nine vocabulary-gap failures.

⚠ **The misconfigured arm scored best.** Mean-pooling a CLS model fixed 10 and
broke 4 where the correct configuration fixed 6 and broke 6 — **that is how a
misconfiguration gets adopted as a result**, and it is why both are filed.

## Result 2 — two implementations of one model do NOT produce the same vector

The question W-112 rests on, and retrieval cannot answer it.
`evidence/cross-arm-*.txt`:

| comparison | mean cosine | int8 vectors identical | int8 codes differing | top-5 dense orderings discordant |
|---|---|---|---|---|
| **`node-cls` vs `py`** (same config, two implementations) | **0.9964** | **0 / 125** | 71–77 % | **41 / 50** |
| `node-mean` vs `py` (the DoD's config) | 0.9090 | 0 / 125 | 96 % | 49 / 50 |
| `node-fp32` vs `node-q8` (quantisation alone) | **0.9962** | 0 / 125 | 83 % | 37 / 50 |

Three things fall out, and the second is the finding:

1. **The pooling mismatch was the dominant error**, not quantisation: fixing
   `mean` → `cls` moves cross-arm cosine 0.909 → 0.996. **`BAAI/bge-small-en-v1.5`
   declares `pooling_mode: cls`**, read from its own sentence-transformers
   config.
2. 🔴 **At cosine 0.996, ZERO of 125 int8 vectors are identical and 41 of 50
   top-5 orderings still differ.** A pinned, committed vector is an artefact of
   **one implementation on one machine**, not of "the model".
3. **int8 quantisation is cheap** — 0.9962 against the same implementation's
   fp32 — and is not what breaks reproducibility.

## What was NOT run

- 🔴 **The two-architecture arm.** W-106 asks for x86-64 **and** arm64 query
  vectors; **only arm64 exists on this machine.** Result 2 measures across
  *implementations* on one architecture, which is a different and weaker cut.
  The cross-architecture number is still owed.
- Any comparison against DENSE-CHUNK's control. See §"The corpus problem".

## Reproduce

See [`tools/vector-gate/README.md`](../../../tools/vector-gate/README.md). The
corpus is a copy of `fux-playground` with `docs` restored to
`.fux/sources/dirs` and re-ingested; **the playground itself was not modified.**

## Evidence

- `evidence/per-query-{node,node-cls,py}.{csv,jsonl}` — **150 rows**, one per
  query per arm: lexical/dense/fused rank, pass per arm, and both top-5 lists.
- `evidence/grade-*.txt` — each arm's summary as printed.
- `evidence/cross-arm-*.txt` — the three implementation comparisons.
- `evidence/prepared.json` — the 75 chunks and 50 queries exactly as embedded.

## Nothing is claimed at 10 000 documents

Ten documents. A result here licenses nothing about a larger corpus, and the
report states no threshold at any size.
