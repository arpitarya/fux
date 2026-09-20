---
type: Report
run: 2026-09-18-identifier-headroom
item: W-168
classification: informed
description: "33 id-queries, one per seed identifier, Claude-authored on Arpit's instruction after Codex declined prompt 8. Baseline on rung-00100 / 01000 / 10000: primary document in the top 3 for 30 / 29 / 30 of 33. The analyzer's mangling is SYMMETRIC — documents are mangled identically — so split identifiers still retrieve. Improvement headroom for an unstemmed identifier field is 3–4 of 33 at every rung, below the floor. The persistent misses have a different cause: frontmatter `doc_id:` values are not indexed at all."
filed: 2026-09-18
engine_commit: 7259bab7
---

# REPORT — how much an identifier field could fix

🔴 **The premise W-168 step 2 was stopped on is wrong in the direction that
matters.** *"0 of 33 identifiers survive the analyzer"* is true and *"so a query
spelled the way a person spells it cannot reach that piece"* is false — because
**the document is mangled the same way.** `DAIRY-2 → ['dairi', '2']` on the
query side, and `G-DAIRY-2` in `02-sensor-thresholds.yaml` becomes
`['g', 'dairi', '2']` on the index side. They meet. The survival report compared
query tokens against **raw** text; the index holds **analyzed** text.

## The questions

**33 id-queries, one per distinct identifier in the seed**, written by this
session on Arpit's instruction (*"Codex is not going to run it. You go ahead."*).
Targets were derived by `grep` over `work/golden/seed/` — the document that
literally contains the identifier — so **no key was needed and none was used.**
Two forms per identifier: a question (*"when did probe KV-NGP-C2-07 start
reading high"*) and the bare identifier alone.
[`evidence/id-queries.jsonl`](evidence/id-queries.jsonl).

## The number, three rungs

| rung | primary hit@1 | **primary hit@3** | any-relevant hit@3 | bare-id hit@3 | **improvement headroom** |
|---|---:|---:|---:|---:|---:|
| rung-00100 | 25/33 | **30/33** | 30/33 | 31/33 | **3** |
| rung-01000 | 21/33 | **29/33** | 29/33 | 29/33 | **4** |
| rung-10000 | 19/33 | **30/33** | 30/33 | 29/33 | **3** |

- **Identifiers already retrieve at 88–91 % top-3, on every rung including the
  design point.** The split pieces (`bv` + `4437`, `ngp` + `mnt` + `552`) are
  jointly rare enough that their conjunction finds the document.
- **Headroom is 3–4 of 33.** [SR-RS](../../../records/0133_predictions.md)
  decision 19's floor of all floors is a net of 6. **A field that fixed every
  miss could not clear α on this corpus.** This is 22d's *inconclusive by
  headroom*, measured before a line of the field was built.
- 🔴 **Regression headroom is 29–30 of 33, and it is ten times the
  improvement headroom.** [SR-RS](../../../records/0133_predictions.md) decision
  22b asks for **both** directions, because they answer different questions and
  one number answers neither. **Improvement headroom** — the queries no arm gets
  right — is 3–4. **Regression headroom** — the queries a change could *break* —
  is every query currently in the top 3: **30, 29 and 30**. ⚠ **This is a
  single-arm baseline**, so neither figure is a paired count across two arms; the
  regression figure is the exposure a second arm would be measured against, and
  it is stated rather than omitted because omitting it is what makes a 3-of-33
  upside look like a free change. **An identifier field risks ten documents for
  every one it could win**, and that asymmetry is the run's second finding.
- hit@1 falls 25 → 19 with corpus size — siblings (`-02` vs `-03`, the 2025 and
  2026 matrices) compete for rank 1. Top-3 does not move.

## The three misses are the finding, and they are not an analyzer problem

| identifier | rank@20, 100 / 1 000 / 10 000 | where it lives |
|---|---|---|
| `QCL-IT-ADR-08` | **absent / absent / absent** (not in top 50) | **only** in `doc_id:` frontmatter of `11-decision-telematics-vendor-2026.md` |
| `QCL-CS-MTX-02` | 6 / 8 / 3 | only in `doc_id:` frontmatter of `14-…-matrix-2025.md`; the 2026 sibling wins |
| `QCL-F-22` | 4 / 4 / 4 | body, `01-sop-temperature-excursion.md` — `f` and `22` are both common |
| `SANDHU-EXC` | 2 / 4 / 4 | body — `sandhu` is in many documents |

🔴 **Frontmatter is not indexed.** [`src/fux/ingest/parse.py`](../../../src/fux/ingest/parse.py)
splits a document into `meta` and `body`, and the postings are built from
`body`. So a `doc_id:` value — **the exact string a person types to ask for that
document** — is in no posting list. Confirmed two ways on rung-00100:
`find ADR` returns every document with *ADR* in its body and never document
11, whose only *ADR* is its `doc_id`; `find Deshmukh` returns the three
documents naming her in body text and never document 11, whose only mention is
`contributors:`. **Three of the seed's 33 identifiers live only in frontmatter,
and those are the ones that fail.**

## What this says about step 2

- **The unstemmed identifier field is built for a defect this corpus barely
  has.** The defect it would fix — an identifier whose every piece is common —
  needs identifiers like a ticket key `PROJ-123`, where `proj` is in every
  document. The seed has one prefix family (`QCL-`) and two such cases.
- **Prompt 8 would not change that.** Thirty more questions of the same shape
  over the same 33 identifiers give the same ~10 % headroom. What is missing is
  not questions — it is **identifiers of the failing shape in the corpus**, which
  is a seed-authoring note for Codex, not a question-authoring one.
- **The cheaper fix is upstream of the field.** Indexing selected frontmatter
  scalars (`doc_id` at least) reaches the three misses without a new field, a
  format change, or committed postings for a second analyzer. It is its own
  decision — which keys, into which field — and it is filed as
  [W-201](../../open/W-201-frontmatter-scalars-not-indexed.md).

## Authorship

| artifact | author | could reach |
|---|---|---|
| the 33 questions | Claude, this session | `work/golden/seed/` (permitted), the survival report |
| the targets | `grep` over the seed | — |
| the probe | this session, [`evidence/probe_idq.py`](evidence/probe_idq.py) | — |
| the analysis | Claude, this session | everything above |

**`informed`** — the question author is the measurer. No key was read, needed,
or requested. **No `VERDICT.md`**: nothing was pre-registered for this and
nothing is ruled; it is a headroom measurement under SR-RS 22d.

## Reproduce

[`evidence/repro.sh`](evidence/repro.sh) — copies the three rungs out of
`fux-lab`, re-ingests each copy on this engine, runs the probe. Engine
`7259bab7`, `fux 3.0.0-alpha.1`, from the Cowork bridge VM; rung-10000's
`build` takes ~4 minutes there.
