---
type: Run Report
run: 2026-09-06-csv-chunk-granularity
classification: informed
date: 2026-09-06
---

# 2026-09-06 — CSV chunk granularity: row vs band

**Run class: `informed`.** One author wrote the corpus generator and the
queries, so under RUN-CLASSIFICATION this **supplies no delta** for a shipping
decision. TEST-PLAN §0a: the lab produces numbers, the playground produces
grades, and a number is not a grade.

**Surface:** Linux x86_64 · python 3.11.15 · Cowork cloud container. Latency is
not comparable to the `Darwin arm64` figures elsewhere in the lab (§2).
**Corpus:** seeded, `sha256[:16] = 29cb743d8dfe252b`, 12 files, 6 998 rows.
**Reproduce:** `fux-lab/2026-09-06-csv-chunk-granularity/`.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| `corpus.py` — the seeded corpus generator | Claude Code, this session | the shape of the questions it was about to be asked |
| `pairs.jsonl` (set A) and `pairs_b.jsonl` (set B) — the evaluation queries | Claude Code, this session | the corpus it had just generated |
| `run.py` — the harness | Claude Code, this session | **both of the above** |
| this report and `ANALYSIS.md` | Claude Code | everything |

**`informed`, and every row is the same author.** One author wrote the corpus,
the queries and the instrument that scores them, so under RUN-CLASSIFICATION
this **supplies no delta** and is not a generalisation estimate. The numbers
below are a measurement of a mechanism, not an estimate of how fux will behave
on a corpus nobody wrote for it.

🔴 **Set A is the evidence for that caution, not an aside.** Its queries planted
a token unique in the whole corpus, and every arm scored `hit@1 = 1.000` — a
result that would have been reported as *chunk size does not matter*. Set B
exists because the author, knowing how set A was built, could see what it could
not measure. A blind author would not have known to write it.

## Question

Does one passage per row answer better than the band of rows the chunker
produced before? Chunking is a **refer-plane** concern — `extract.py` indexes
the whole decoded document either way — so the index is identical across arms
and only the retrieval unit within a document changes.

## Result

Two query sets. Set A plants a unique token in the target row; set B asks with
terms that are individually common so only the **combination** identifies a
row, which is the realistic shape.

| rows/passage | A hit@1 | **B hit@1** | B hit@3 | B MRR | B bytes | B p95 ms |
|---|---|---|---|---|---|---|
| 58 | 1.000 | 0.229 | 0.229 | 0.229 | 6 094 | 42 |
| 11 | 1.000 | 0.292 | 0.458 | 0.382 | 5 412 | 49 |
| **1** | 1.000 | **0.875** | **1.000** | **0.934** | **946** | 109 |

🔴 **Set A separates nothing.** All three arms are perfect on it. A run that
stopped at the obvious experiment would have reported "no difference" and been
wrong. That is the transferable lesson from this run.

### hit@1 by ambiguity

Cohort = how many rows share all three common terms.

| cohort | n | 58 rows | 11 rows | 1 row |
|---|---|---|---|---|
| 1 | 3 | 0.333 | 1.000 | 1.000 |
| 2 | 17 | 0.235 | 0.294 | 0.941 |
| 3 | 13 | 0.231 | 0.077 | 0.923 |
| 4+ | 15 | 0.200 | 0.333 | 0.733 |

### The win is not short-passage bias

Control: score the correct row against decoys sharing 3 of 4 query terms, every
candidate the same size so length cannot do the work. **42/48 = 0.875.**

### Cost

`rescore` is O(passages), one document:

| rows | passages | chunk | rescore + assemble |
|---|---|---|---|
| 500 | 500 | 0.9 ms | 63 ms |
| 5 000 | 5 000 | 9.7 ms | 654 ms |
| 20 000 | 20 000 | 39.2 ms | ~2.6 s (2 498 / 2 596 / 2 780) |

A token pre-filter removes only ~40 % on a realistic table and does not rescue
this: rows share vocabulary, and the repeated header means any query naming a
column matches every row.

## Outcome

[ADR-TABULAR](../../adr/0152_tabular.md) — one passage per row, and
`[decode] max_table_rows` raised 500 → 20 000. The latency was ruled acceptable
by Arpit with the numbers above in hand, over the alternative of degrading to
bands past a row threshold.
