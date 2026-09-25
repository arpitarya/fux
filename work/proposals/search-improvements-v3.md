---
type: Proposal
title: "Ten ways to rank better, all $0 and deterministic — the 3.0 search backlog"
description: "Ten ranking improvements Arpit kept on 2026-09-13, each independent of the graph-composed `ask`: anchor text as a field, corpus-mined expansion, an unstemmed identifier field, RM3 pseudo-relevance feedback, supersession-aware ranking, passage proximity (SDM), community diversification (MMR), a git-derived authority prior, a query-intent → doc-type prior, and section-level index units. Each is its own ranking change: its own golden questions, its own pre-registration, behind W-156."
status: graduated
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

**Graduated 2026-09-14 → [W-168](../open/W-168-search-improvements.md)** (Arpit). This file stays the spec the item points at.

# Ten ways to rank better — the 3.0 search backlog

**Parked by Arpit, 2026-09-13: *"Keep all ten of them."*** Nothing here is
decided and nothing is built. Each idea graduates alone — to a compare doc when
it is a fork, or straight to an item when it is not.

**Model when picked up: Opus for 4, 8, 9, 10 (a judgement about drift, bias or
a plane change); Sonnet for the rest once a golden question and a
pre-registration exist.**

---

## 0 · The rules every one of these lands under

- **Every one is a ranking change.** It lands behind **W-156** (what evidence a
  ranking change may have) and needs golden questions that exercise it
  ([SR-RS](../../records/0133_predictions.md) decision 23) plus a
  pre-registered prediction at 10 000 documents, both directions.
- **Build the golden question before the feature**, or the verdict is theatre.
  Anchor text needs documents findable *only* through a linker's wording; the
  identifier field needs id-queries; supersession needs a superseded/successor
  pair with a question that the old one answers wrongly.
- **All ten are `$0`, offline, deterministic, and put no model on the
  maintenance path.** Where one could drift toward a law, the row says so.
- **Independent of [ask-graph-expansion](../../archive/compare/ask-graph-expansion.compare.md).**
  None requires it; #1, #5, #7 interact with it, favourably.

---

## 1 · The ten

| # | idea | what it fixes | cost | law check | golden prerequisite |
|---|---|---|---|---|---|
| 1 | **Anchor-text field** — index the words other documents use when *linking* to a document as a BM25F field | vocabulary mismatch: `0126_graph.md` never says "graph lane"; five linkers do. Shrinks Tier B lexically | small — edges are already extracted; one field in `P/` | clean — statistics, not content (L2) | a doc reachable only by link wording |
| 2 | **Corpus-mined expansion** — acronyms from `Term (ABBR)` patterns, glossary `term — definition` lines, `[[alias]]` frontmatter → a deterministic synonym table in `D/`, fed through the existing `--expand` path at `expand_weight`, with SR-EXPAND's refusal intact; the agent's own `--expand` stacks on top | "PPR" vs "personalized pagerank"; house vocabulary | small–medium | clean | an acronym question whose document spells it out |
| 3 | **Identifier field, unstemmed** — `W-146`, `SR-GRAPH`, `ERR_2031`, versions: exact tokens, high boost | the stemmer mangles ids; agents search by id constantly | small | clean | id-queries |
| 4 | **RM3 pseudo-relevance feedback** — distinctive terms from the top-k re-queried once at low weight (an auto-filled `--expand`) | recall on under-specified queries | small | clean — **but drift is real; pre-register or don't build** | under-specified questions with a known answer |
| 5 | **Supersession-aware ranking** — a `supersedes` edge demotes its target in lexical rank *and* inside the walk; the successor inherits the target's anchor text | the biggest wrong-answer class in org knowledge: the old runbook | small — the edge kind exists | clean; pairs with archived markers | a superseded/successor pair |
| 6 | **Passage proximity (SDM)** — in refer, score ordered and unordered query-term windows on the fetched bytes | "index lock" ≠ "lock the index" — phrase sense without a positional index | small — refer holds the bytes | clean; zero index cost | phrase-sensitive questions |
| 7 | **Community diversification (MMR)** — if the top-5 share one community, swap #5 for the best document of the next | five near-duplicates, zero coverage | tiny once the graph plane is in `ask` | clean; **measure — it can hurt precision** | multi-facet questions |
| 8 | **Git-derived authority prior** — distinct authors × commit count, from commit metadata | a document ten people maintain over one person's draft | medium — a new `M/` stat | L3 only if derived from commit metadata, never wall-clock; **recency bias is the trap** | needs a corpus with history — golden is synthetic |
| 9 | **Query-intent → doc-type prior** — "how do I…" prefers runbooks, "why did we…" prefers records; declared per source | shape mismatch, not vocabulary mismatch | medium | clean; declarative | intent-labelled questions |
| 10 | **Section-level index units** — rank sections, back off to the document | long documents where the answer is one heading | large — a plane change, a major of its own | clean | long-document questions |

---

## 2 · Suggested order

1. **#1 + #3 + #5** — each is a new *field or edge use*, not a new algorithm;
   they compound with the graph work and are cheap to reason about.
2. **#2 + #4** — both recall; **#4 needs a pre-registered threshold**: drift on
   a 10 000-document corpus is exactly the result that looks like a win and
   isn't.
3. **#6 + #7** — ride on refer and the graph plane W-161 already touches.
4. **#8, #9, #10** — majors of their own; each starts as a compare doc.

---

## 3 · What each idea would touch

| # | records | code |
|---|---|---|
| 1 | SR-RANKING (a field), SR-POSTINGS, SR-EXTRACTED (anchor extraction) | `ingest/edges.py`, `ingest/extract.py`, `query/bm25f.py` |
| 2 | SR-EXPAND, a new dictionary section in SR-POSTINGS | `ingest/`, `query/expand.py` |
| 3 | SR-RANKING, the analyzer note in SR-POSTINGS | `query/analyzer.py`, `query/bm25f.py` |
| 4 | SR-EXPAND, SR-RS (prediction) | `query/expand.py`, `query/__init__.py` |
| 5 | SR-RANKING, SR-GRAPH, SR-ARCHIVED-CONTENT | `query/rank.py`, `graph/walk.py` |
| 6 | SR-REFER-PLANE, SR-CHUNKING | `refer/` |
| 7 | SR-ASK, SR-GRAPH | `query/__init__.py`, `graph/community.py` |
| 8 | SR-RANKING, SR-INDEX-RECORD, SR-LAWS L3 note | `ingest/`, `M/` |
| 9 | SR-TYPES-LIST, SR-RANKING | `sources.py`, `query/rank.py` |
| 10 | a new record; SR-POSTINGS, SR-CHUNKING | a plane |

---

## 3b · Per idea: what is tested, what is measured, and the keep/remove call

**Order for every idea: golden question(s) → pre-registration → implement →
measure → call.** Never two ideas in one arm. Every floor is SR-RS decision
19's paired floor for the observed discordant count; "both directions" means
the gain on the target questions **and** zero new misses elsewhere.

| # | unit tests prove | measured on | keep if | remove if (and what is removed) |
|---|---|---|---|---|
| 1 anchor text | the field is populated only from `ref` edges; determinism (same edges → same field bytes) | golden questions answerable only via linker wording | recall@k gain clears the floor, no new misses | fails → the field stays indexed at weight 0 (no index change on removal), the record says so |
| 2 corpus-mined expansion | the mined table is deterministic and contains only patterns the record names; the refusal still holds | acronym / house-term questions | same | fails → the table is not consulted; the miner stays as a `fux inspect` lens (it is useful as a report) |
| 3 identifier field | ids survive the analyzer byte-exact; a stemmed collision test | id-queries | recall@1 on id-queries clears the floor | fails → removed outright (a field nobody hits costs postings) |
| 4 RM3 | the expansion is a pure function of the top-k; weight 0 is byte-identical to today | under-specified questions | gain clears the floor **and drift bound holds**: no answerable question loses its top-1 | any drift → removed; RM3 stays reachable only as an agent's manual `--expand` |
| 5 supersession | the `supersedes` edge demotes exactly its target; no effect without the edge | superseded/successor pairs | the successor wins on ≥ the registered fraction; no demotion of a live doc | fails → the demotion weight is 0 (edge still indexed for `graph`) |
| 6 SDM proximity | window scoring on fetched bytes is deterministic; zero weight is byte-identical | phrase-sensitive questions | passage-level gain clears the floor | fails → weight 0 in refer, code stays behind the tunable |
| 7 MMR | the swap fires only when the top-k share one community; deterministic | multi-facet questions | coverage gain **and** precision@1 unchanged | precision moves → removed |
| 8 git authority prior | derived from commit metadata only; `SOURCE_DATE_EPOCH`-safe | needs a corpus with history — **golden is synthetic, so this idea starts with an instrument, not a measurement** | a corpus exists and the prior clears the floor | no corpus → stays a proposal; never ships unmeasured |
| 9 intent prior | declared, not inferred; an undeclared repo is byte-identical | intent-labelled questions | gain clears the floor | fails → the declaration key stays, weight 0 |
| 10 section units | a plane change — its own compare doc before any test | long-document questions | its own pre-registration | its own doc decides |

⚠ **Endpoints, ruled 2026-09-23 (Arpit, [W-168](../open/W-168-search-improvements.md)):** RM3 and the intent prior are judged at **rank 1** (`hit@1`, with `primary@1` beside it); SDM, MMR and section units keep the measures in this table. ⚠ **This table numbers the ideas differently from W-168's steps** — RM3 is `#4` here and step 5 there; W-168's numbering is the one the queue uses.

- **"Remove" means the default is off and the record says why**, not that
  the code is deleted in the same change — a measured negative is evidence
  worth keeping reachable for one release; the following release deletes what
  nobody re-armed.
- **Ambiguous → Arpit**, per-query rows filed under `evidence/`.

## 4 · Graduation trigger

**Per idea, not as a block.** An idea graduates when Arpit names it, in which
order: golden question(s) written (Codex's hands where the sealed key is
involved) → pre-registration filed → compare doc if there is a fork, else a
`W-nn` item with a handoff. Never two ideas in one measurement: a paired
comparison that changed two things cannot attribute the delta.

---

## References

- Craswell, Hawking, Robertson — anchor text, SIGIR 2001 (#1).
- Lavrenko & Croft — relevance models, SIGIR 2001; Abdul-Jaleel et al. — RM3,
  TREC 2004 (#4).
- Metzler & Croft — *A Markov random field model for term dependencies*,
  SIGIR 2005 — the sequential dependence model (#6).
- Carbonell & Goldstein — MMR, SIGIR 1998 (#7).
- Jardine & van Rijsbergen — the cluster hypothesis, 1971 (#7).
- Kamps et al. — element/section retrieval at INEX (#10).
- Live code: [`src/fux/query/expand.py`](../../src/fux/query/expand.py),
  [`src/fux/query/analyzer.py`](../../src/fux/query/analyzer.py),
  [`src/fux/graph/`](../../src/fux/graph/).
