---
type: OpenItem
id: W-108
title: "W-108 — answer refers the top-3, and the passage rescore sees proximity"
description: "cmd_answer runs run_query(…, 1) and hands one document to refer(), so answer inherits recall@1 (0.60 vs 0.95 at k=5 on the graded set) by construction. refer() already takes a list and _rescore already computes passage df across everything fetched. Fetch min(3, results) inside the existing byte budget, and multiply passage scores by rerank.passage_boost so the passage that says the question back wins."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-108 — `answer` refers the top-3

**Model: Opus** (Arpit's instruction). The code is small; the gate and the
budget reasoning are the work.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §2.1 and §8 (W-108).

## Goal

`fux answer` can return a passage from the second- or third-ranked document
when that passage scores higher than anything in the first — without
exceeding today's byte budget, without a fetch it does not make today, and
with the receipt naming every sha it fetched.

## Definition of done

- [ ] `query/__init__.py::cmd_answer`: `run_query(…, 3)`; `_answer_via_refer`
      and `query/refer_answer.py::answer_via_refer` take the list; `refer()`
      is called once with up to three citations; fallback to the index path
      only when **no** document produced a usable citation.
- [ ] `refer/_rescore.py::rescore`: score `*= (1 + weight * passage_boost(query_terms, analyze(passage.text)))`
      with the same `rerank_weight`/`WEIGHT` semantics ADR-RERANK defines —
      **one constant, not a second knob**; when the reranker is off, the
      rescore is unchanged (byte-identical `answer` at `rerank_weight = 0`).
- [ ] `--json` shape unchanged (`citation` = the winning passage's document;
      `answer.passages` may now span documents — ADR-ANSWER records this);
      receipt `subject` lists all fetched `(id, loc, sha)`.
- [ ] `_declare_change_since_last_ask` compares the full cited set.
- [ ] Tests: unit for the list path, the fallback, the budget invariant, and
      the `rerank_weight = 0` byte-identity; `tests_e2e` golden updated
      deliberately with the diff explained in the commit.
- [ ] Filed run: `answer` over the 43 graded queries, before/after, per-query
      rows, `informed`; `recall@1` recomputed and reported, nothing claimed
      at 10 000.
- [ ] ADR-ANSWER, ADR-REFER, ADR-RERANK amended in the same commit;
      CHANGELOG; `IMPLEMENTATION.md` row; this file to `archive/open/`.

## Blockers

- `arpit`: ratification. Nothing technical.

## Hazards

- 🔴 **Budget.** Three documents share `budget`; `per_doc_fraction` bounds
  each. Assert assembled bytes never exceed today's for the same query.
- 🔴 A `url:` document with no fetcher degrades **per document** (its
  citation is dropped), never the whole answer.
- The proximity multiplier must use the reranker's constants, not new ones —
  two knobs for one signal is how they drift.
- `--no-refer` is unchanged.

## Out of scope

Abstention (Arpit's open call). Sentence-level extraction. Changing which
document `ask` ranks first.
