---
type: Pre-Registration
description: "W-205 part 1: which front-matter keys reach the index, and into which field. The endpoint is DATA-SHAPED — six identifiers that are absent from the index become reachable — because six is at the floor and a paired flip test cannot carry it. Plus two no-harm arms."
run: 2026-09-21-frontmatter-reachable
item: W-205
status: frozen
filed: 2026-09-21
---

# PRE-REGISTRATION — W-205 part 1, front-matter identity keys

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b). The build had not
run when this was written; `parse.meta_fields()` did not exist.

---

## 1 · The defect, and it is recall rather than ranking

`parse()` returns `ParsedDoc(meta, body)` and **only `body` reaches the
postings**. `title` is read out of `meta`; **everything else is dropped.**
Nothing recorded that until [SR-INGEST](../../../records/0106_ingest.md)
decision 23, so *"a `doc_id:` you can read is not one you can search"* was true
and undocumented.

**Measured on the seed corpus, before any change** — 14 declared identity keys
(`doc_id`), of which **7 are front-matter-only**, across **6 distinct
identifiers**:

| identifier | declared by | in the body? |
|---|---|---|
| `QCL-QA-SOP-17` | `01-sop-temperature-excursion.md` **and** `archive/a01-…-rev2.md` | 🔴 no |
| `QCL-IT-ADR-08` | `11-decision-telematics-vendor-2026.md` | 🔴 no |
| `QCL-OPS-DOCK-03` | `13-dock-scheduling-rules-2026.md` | 🔴 no |
| `QCL-CS-MTX-02` | `14-customer-notification-matrix-2025.md` | 🔴 no |
| `QCL-CS-MTX-03` | `15-customer-notification-matrix-2026.md` | 🔴 no |
| `QCL-QA-MAP-01` | `22-cold-chain-document-map.md` | 🔴 no |

⚠ **`QCL-QA-SOP-17` is declared by TWO documents** — the live SOP and its
archived revision 2. That is a supersession pair sharing one `doc_id`, and it is
the one row in this table whose *ranking* is a question rather than a fact.

## 2 · 🔴 The endpoint is DATA-SHAPED, and that is a decision, not a convenience

**Six identifiers is AT [SR-RS](../../../records/0133_predictions.md) decision
19's floor of 6, and the floor tracks flips, not population.** A paired test
would need all six to flip and none to break, which is a total sweep — the
weakest possible form of a pass.

**So the primary endpoint is an absolute reachability claim, stated as data:**

> **Before: each of the six identifiers, as a bare query, returns the document
> that declares it at NO rank in the top 50 — it is absent from the index.
> After: each returns that document.**

**PASS** — all **6 of 6** reachable, at `rank ≤ 50`, on both rungs.
**FAIL** — any of the six still absent, or any no-harm arm breaches §4.
**There is no INCONCLUSIVE on this endpoint.** *Absent* and *present* are not a
matter of degree; either the value entered the postings or it did not.

⚠ **Reachability is NOT ranking, and this document will not claim it is.**
Reaching rank 50 from nowhere is the whole result. **Where in the top 50 the
document lands is reported and is not an endpoint** — a bar on rank would be a
threshold invented to be cleared.

🔴 **`QCL-IT-ADR-08` will NOT become whole, and predicting otherwise would
mis-state this endpoint.** SR-INGEST decision 23d says so in advance: the value
goes in **through the analyzer**, so it loses its `IT` to the stopword list and
its hyphens to `_WORD_RE`, exactly as it would in the body. **Part 2 measured
that separately and came back INCONCLUSIVE**, so the analyzer is `v2` here.
**Part 1 buys reachability; wholeness is a different change.**

## 3 · What is built, and the resolution order

Per SR-INGEST 23a, [SR-DECODE](../../../records/0139_decode.md) 20 and
[SR-TYPES](../../../records/0128_types-list.md) 13 — **all three already
ratified**, so this build implements a spec rather than proposing one:

| | layer | where | wins |
|---|---|---|---|
| 1 | **binding** | `.fux/formats.toml [meta]` | **over everything** |
| 2 | **claim** | the decoder's `META_FIELDS` | over the default |
| 3 | **engine default** | `doc_id` · `id` · `aliases` → `title`; `tags` → `ctx` | — |

**A key absent from the resolved dict is not indexed.** `none` silences a claim.
**No person key in the default** (`owner`, `author`, `contributors`).

⚠ **A prose document has NO decoder, and that is why layer 3 does the work
here.** `parse_document` returns `meta={}` for anything a decoder handled, so
front-matter reaches the index only on the prose path, where there is no module
to make a claim. **The claim layer is for consumer decoders** (`.eml` →
`Message-ID`) and is built because the spec ratifies it, not because a built-in
uses it today. Stated now so a later reader does not read an unused layer as
dead code.

🔴 **No Node twin is owed.** Node does not ingest — `node/src/ingest/` carries
only the query-time halves, and its own docstrings say so. Field assembly is
Python's alone.

## 4 · The two no-harm arms — conjunctions, not trades

Both must hold for a PASS, and neither may be traded against the endpoint.

1. **The 43 id-queries** (part 2's frozen set, unchanged) on `rung-01000`:
   **a net of ≥ 6 against on `rank_primary_bare` is a FAIL.** New title terms
   change `avg_wlen` for every document with front-matter, so this arm is not a
   formality — it is the blast radius.
2. **60 set-1 questions**, the same sample part 2 used (`every other id, capped
   at 60`), on `rung-01000`: **a net of ≥ 6 top-1 changes is a FAIL.**

⚠ **Neither control has a key and neither claims quality.** They ask whether
this change disturbed queries it has no business touching.

## 5 · Rungs, and what is measured

**`rung-00100` and `rung-01000`**, each arm on its own `arm_corpus.py` copy,
ingested end to end. ⚠ **`rung-10000` is deliberately NOT in the endpoint** —
the six identifiers are in `seed/`, which is byte-identical at every rung, so a
third rung costs 20 minutes and adds no case. **It is run for the no-harm arm
only if the two rungs disagree.**

**Also reported, and not endpoints:** committed index bytes, distinct terms, and
the rank each of the six lands at.

## 6 · What this run may never claim

- That an identifier is **whole**. It is not; part 2 is the change for that and
  it did not clear its bar.
- That ranking improved. **Reachability is not ranking.**
- That the `[meta]` binding or the `META_FIELDS` claim are exercised by a
  built-in decoder. **They are not** — §3.
- Anything about a person key. The default excludes them and this run does not
  bind one.

## 7 · Classification

**`informed`.** The endpoint's six identifiers were found by the measurer, by
grep over `work/golden/seed/`, and this session rebuilt the corpus. 🔴 **No
golden answer is used, needed or reachable** — the endpoint is *does this
document come back at all*, which is answerable from a ranked list alone.
