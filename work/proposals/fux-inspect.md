---
type: Proposal
title: "`fux inspect` — an X-ray of the index: boilerplate words, unfindable documents, duplicates, orphans"
description: "Arpit asked for a tool that says what the index looks like across all documents — which words are on every card (\"TLDR\"), whether documents produce similar or different index shapes, and whether the consumed index is good or bad. Proposed: a read-only verb with six lenses (boilerplate, findability, length and fields, duplication and templates, analyzer coverage, graph), descriptive by default with three declared checks whose floors are provisional. The committed index holds term hashes, so the words come from a local, gitignored dictionary built by re-tokenising the sources; nothing new is committed."
status: graduated
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

**Graduated 2026-09-14 → [W-169](../open/W-169-fux-inspect.md)** (Arpit). This file stays the spec the item points at.

# `fux inspect` — an X-ray of the index

**Model: Opus for the lens definitions and the three checks (what "findable"
means is a judgement); Sonnet for the report plumbing.**

**Found:** Arpit, 2026-09-13 — *"I need some kind of tool to analyse the index
that is consumed: is it a good index or a bad index?"* Kept as a proposal at
his instruction. **Owning records when built:** a new **SR-INSPECT**;
[SR-CLI](../../records/0101_cli-surface.md); [SR-POSTINGS](../../records/0112_postings.md)
(the local dictionary); [SR-DOCTOR](../../records/0152_doctor.md) (the
boundary between the two verbs).

---

## 1 · The constraint that shapes the design

- The committed index holds **term hashes, not words** — 8-byte blake2b keys,
  a deliberate privacy property ([SR-POSTINGS](../../records/0112_postings.md)
  decision 2). *"TLDR is everywhere"* cannot be read off the index alone.
- So `inspect` **re-tokenises the sources locally with the same analyzer**,
  builds a hash → word dictionary under **`.fux/runtime/inspect/`
  (gitignored)**, and joins it to the index statistics.
- **The report names words; the commit never does.** Offline (L4),
  deterministic (L3), nothing new committed (L2, L8). Term lists are
  statistics, not content — the report never quotes a line of a document.

---

## 2 · Six lenses

| lens | numbers | names | why it matters |
|---|---|---|---|
| **Boilerplate** | terms by `df/N` with their IDF; hapax share; Zipf / Heaps fit | the top-k high-`df` **non-stopwords** — *tldr*, *status*, *owner*, template headings | IDF ≈ 0 terms score nothing and bloat postings; template words are exactly the TLDR case |
| **Findability** | per document: count of distinctive terms (IDF above a floor); **self-retrieval** — does the document's own top-IDF fingerprint retrieve it in the top 3? (the same check `enrich --check` runs) | **unreachable documents** | *the* quality metric: a document no query can reach is stored, not indexed |
| **Length & fields** | per-field token totals (from `stats.json`) and per-document distribution; empty title / headings; `ctx` dwarfing body | very short documents (the M1 lesson: 32–46-term vocabularies), very long ones | short documents cannot match; long ones are crushed by length normalisation |
| **Duplication & templates** | Jaccard / minhash over hashed term sets; heading-set signatures | near-duplicate pairs; **template families** | duplicates split `df` and confuse ranking; template families are the answer to *did they create a similar index* |
| **Analyzer coverage** | tokens kept vs dropped; identifier tokens; zero-token documents (joins `.fux/enrich/queue.tsv`) | documents the analyzer cannot see | an index that never saw the text is not bad — it is empty |
| **Graph** | orphans (no edges); hubs by in-degree; community sizes | isolated documents; mega-hubs | orphans gain nothing from the graph work; hubs will dominate the walk |

---

## 3 · Verdict discipline — descriptive by default

- `inspect` prints distributions and named lists. **Three checks**, and only
  three, carry a *pass / attention* flag: **findable share**, **boilerplate
  share of postings**, **near-duplicate share**.
- Their floors are **provisional and say so** — the same status
  `SEPARATION_FLOOR` carries — measured later on golden, **never tuned to this
  repo**. A wall of red on an unmeasured floor is how a tool gets ignored.
- Everything else is a number and a list, not a judgement. The one-number
  "index score" is refused for the same reason the confidence band refuses to
  be one number.

---

## 4 · Every finding maps to a lever that already exists

| finding | lever |
|---|---|
| boilerplate terms | `[index]` stopwords / an analyzer amendment — an index change, its own record |
| template files, duplicates | `.fuxignore`, `archived=`, `supersedes` |
| unreachable documents | `fux enrich`, [`fux correct`](../compare/fux-correct.compare.md), or fix the source |
| orphans, hubs | link-IDF in [ask-graph-expansion](../compare/ask-graph-expansion.compare.md) |
| zero-token documents | a decoder (`fux-decoder`), or the backlog queue |

The report prints the lever beside the finding. It never applies one.

---

## 5 · Placement

- **A verb, not `doctor`.** `doctor` checks the *environment*; `inspect`
  checks the *index* (L6 vocabulary). Both read-only.
- `--json` for agents; a Markdown report under `.fux/runtime/inspect/`.
- **Tune-free:** it reads; it never changes ranking.
- Both readers eventually; Python first — the dictionary build needs the
  analyzer, which Node has.

## 5b · What is tested, what is measured, and the keep/remove call

`inspect` changes no ranking, so it is judged on **truthfulness and
determinism**, not on a quality number — except its three checks, whose floors
are measured.

| | how | keep if | remove if |
|---|---|---|---|
| determinism | the report over the same index is byte-identical twice, and across the two readers once Node has it | holds | — (L3 makes this a defect, not a call) |
| the lenses tell the truth | a **planted corpus** in `tests_e2e/`: a known boilerplate term on every document, two near-duplicates, one template family, one unfindable document, one orphan, one zero-token file — each lens must name its plant and nothing else | every plant named, no false name | a lens that cannot find its plant is removed from the report |
| nothing committed | a test that `fux inspect` on a clean clone leaves `git status` clean and writes only under `.fux/runtime/inspect/` | holds | — |
| the three checks' floors | measured on the golden ladder: findable share, boilerplate share, near-duplicate share per rung; the floors are set from the ladder **and marked provisional** | a floor separates the planted-bad corpus from every golden rung | a floor that flags a healthy rung is dropped to *descriptive* — the number prints, the flag does not |
| the levers are right | each finding's suggested lever is one the records name; a test holds the finding→lever table equal to the record | holds | — |

Order: implement → test (planted corpus) → measure the floors → call the
flags. The verb ships even if all three flags are dropped; the report is the
product, the flags are a convenience.

## 6 · Graduation trigger

Graduates when Arpit names it: a `W-nn` item with a handoff, SR-INSPECT
drafted from the template, and a guide skill `fux-inspect` alongside (the
report is for agents as much as humans).

## References

- Zipf — *Human Behavior and the Principle of Least Effort*, 1949; Heaps —
  *Information Retrieval: Computational and Theoretical Aspects*, 1978.
- Broder — *On the resemblance and containment of documents*, 1997 (minhash).
- Azzopardi, de Rijke, Balog — *Building simulated queries for known-item
  topics* / findability, SIGIR 2007 (the retrievability measure).
- Live: [`src/fux/query/analyzer.py`](../../src/fux/query/analyzer.py),
  [`src/fux/derive/_build.py`](../../src/fux/derive/_build.py) (`df`),
  [SR-RUNTIME-STATS](../../records/0125_runtime-stats.md).
