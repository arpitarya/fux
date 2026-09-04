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

## Plan

*Written 2026-09-05, before any edit. Reconciled against the code: every claim
in the DoD above held except one — see **the confidence hazard the DoD does not
name** below, which is the reason this plan is longer than the change.*

### The seam, as it actually is

| fact | where |
|---|---|
| `cmd_answer` retrieves **one** result | `query/__init__.py:682` — `run_query(…, 1)` |
| `answer_via_refer` takes **one** `(doc_id, loc, sha)` and wraps it in a list | `query/refer_answer.py:40` |
| `refer()` already loops candidates and degrades **per document** | `refer/__init__.py:178-198`, `_obtain` |
| `rescore` already computes passage `df` across everything fetched | `refer/_rescore.py:59` |
| `assemble` already caps per document — **and disables the cap for a single one** | `refer/_assemble.py:163` |
| `_declare_change_since_last_ask` already reads `bundle.documents`, plural | `query/__init__.py:891` |

So the list path exists end to end. Three things do **not**, and they are the work.

### 1 · One fetcher is loaded, and three documents may need three

`refer()` takes **one** `fetcher` callable for the whole call, and
`_load_fetcher` resolves exactly one document's fetcher module. Three `url:`
citations from different `[sources.url]` lines can name different fetchers, and
verifying with the wrong one *reports a false staleness on every query* —
`refer/source.py` says so in its own docstring.

**Fix: `_load_fetchers(root, citations)` returns a `loc`-dispatching callable.**
`_fetch_url` calls `fetcher(loc)` with the URL as its only argument, so the
dispatcher is keyed on exactly what it is handed. Modules are memoised by
`fetcher_path`, so two URLs behind one fetcher `connect()` once, and one `close`
closes all. **An all-`file:` candidate set loads nothing at all** — the common
path is byte-identical to today.

### 2 · The proximity multiplier is the reranker's constant, not a new one

`rescore(query, candidates, *, weight=0.0)`, and
`score *= 1 + weight * rerank.passage_boost(analyze(query), analyze(passage.text))`
— the same expression `rerank.rerank` applies to documents, on the same
analyzer, with the same `COVERAGE_POWER`. `refer()` gains `rerank_weight: float
= 0.0` and passes it down; `refer_answer` passes `tune.rerank_weight`.

🔴 **This ships switched OFF, and that is deliberate.** `Tune.rerank_weight`
defaults to `0.0`, so on an unconfigured repo the multiplier is `1 + 0 * x` and
every bundle is byte-identical to today. Turning it on would be moving
`rerank_weight`, which is **already on Arpit's Blocked list** and is explicitly
not this item's to move. The consequence is stated rather than hidden: **half of
W-108 is dark out of the box**, exactly like the reranker it borrows from.

### 3 · A multi-document answer that cites one locator is a mis-citation

Today every passage comes from one document, so `_print_refer_answer` printing
all passages above a single `-- {citations[0].locator}` is correct. With three
documents it attributes B's and C's prose to A's file — in the one product whose
promise is that a citation is checkable.

- **Text mode:** each passage prints under its own locator.
- **`--json`:** each entry of `answer.passages` gains `id`, `loc`, `sha`.
  `citation` stays the **winning passage's** document, unchanged.
  **This is additive, and the DoD's "shape unchanged" is read as W-48's rule —
  no key removed, none repurposed.** `output.schema.json` updated in the same
  change, because it is validated on this branch.

### 🔴 The confidence hazard the DoD does not name

`_fill_confidence` builds the block from the **final result list**, and
`separation = (scores[0] - scores[1]) / scores[0]` **when there are two scores**
— otherwise `1.0` ("one result separates perfectly").

`cmd_answer` retrieves one result, so **`fux answer --band` reports
`separation: 1.0` and `support: 1` on every query it has ever answered**, not
because the ranking is decisive but because nothing else was retrieved.
Retrieving three makes both numbers real, and a real `separation` **can fall
below `separation_floor` and demote the band**.

**Decision: let it become true, and report it.** The alternative is computing
the block off a one-document window that no longer exists, i.e. keeping a number
that was an artefact of `top=1`. What is *not* being done: no floor moves, no
abstention is implemented, nothing gates on the band. The demotion count over
the 43 graded queries is measured and reported to Arpit beside the recall
number, because a band is a claim fux makes out loud. ADR-CONFIDENCE gains the
consequence; ADR-ANSWER records that `answer`'s block is now computed over three.

### Files

| file | change |
|---|---|
| `query/__init__.py` | `ANSWER_TOP = 3`; `cmd_answer` retrieves it; `_answer_via_refer` takes the list; `_print_refer_answer` per-passage locators; `_declare_change_since_last_ask` narrowed to documents that actually produced a citation; `cmd_verify --rerun` follows the same path or it stops reproducing |
| `query/refer_answer.py` | `answer_via_refer(root, query, citations, *, tune)`; `_load_fetchers` dispatcher; `rerank_weight` passed through |
| `refer/__init__.py` | `refer(…, rerank_weight=0.0)` → `rescore(…, weight=…)` |
| `refer/_rescore.py` | the proximity multiplier |
| `query/output.schema.json` | `passages[]` gains `id`/`loc`/`sha` |

### Tests (first)

- `tests/refer/test_rescore.py` — `weight=0.0` is byte-identical to today's
  scores; `weight>0` promotes the passage that says the query back.
- `tests/query/test_refer_answer.py` — three citations in one `refer()` call;
  two `url:` documents on **different** fetchers each get their own; a `url:`
  document with no fetcher drops **its** citation and the answer survives; all
  three failing ⇒ `None` ⇒ the index fallback.
- `tests/refer/test_assemble.py` — the budget invariant: three documents'
  assembled bytes never exceed the same query's budget today.
- `tests_e2e/test_verbs.py` — the golden diff, explained in the commit body.

### Records

ADR-ANSWER (top-3, the passage-per-locator surface, the confidence
consequence) · ADR-REFER (`rerank_weight` reaches `rescore`; the dispatcher) ·
ADR-RERANK (`passage_boost` gains a second caller, one constant) ·
ADR-CONFIDENCE (the block is computed over three results on this verb).
No new component, so the ownership table does not move.

### The run

`answer` over the 43 `relevance: complete` playground goldens, before/after,
per-query rows, `classification: informed` (the goldens are known and the
installed enrichment is the contaminated arm — same standing as
[`2026-08-28-first-recall`](../regression/2026-08-28-first-recall/report.md)).
Reported: `recall@1` for the cited set, the band-demotion count, assembled
bytes per query both arms. **Nothing claimed at 10 000.**

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
