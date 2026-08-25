---
type: ADR
name: ADR-EXTRACTED
title: "ADR-EXTRACTED (0016) — the extracted ingest mode"
description: "The deterministic ingest mode, ratified by name. Everything is taken from the document; nothing is invented; every guarantee in the paper is stated for this mode and no other."
status: accepted
timestamp: 2026-08-19T00:00:00Z
---

# ADR-EXTRACTED — the deterministic ingest mode

- **Name:** `ADR-EXTRACTED` — cite this everywhere; never cite the number
- **Status:** accepted
- **Date:** 2026-08-19
- **Feature:** the `extracted` ingest mode — the value in every committed record's `mode` property, and the contract it asserts
- **Owns:** `src/fux/ingest/extract.py`
- **Laws:** L1, L2, L3, L4 — see [ADR-LAWS](0001_laws.md); never restated here
- **Ratifies:** [W-30](../../work/OPEN-WORK.md), Arpit 2026-08-19 — the naming call open since 2026-08-09

---

> ## Amended 2026-08-25 — the dense lane and the embedding model were DELETED
>
> **Extraction no longer emits `code` or `vectors`, and no longer loads a
> model at all** (Arpit, 2026-08-25). `Extracted` is now four fields —
> `title`, `phrases`, `terms`, `flen` — every one of them a pure function of
> the document's own bytes and the analyzer.
>
> **This makes the extracted-mode law easier to state, not harder.** *Every
> field is taken from the document; nothing is invented* was always slightly
> awkward about an embedding: a vector is not *in* the bytes, it is a model's
> reading of them, and the model was a 7.9 MB binary whose recipe was not in
> the repo (the defect filed as W-80). That awkwardness is gone with it.
>
> | field | went | why |
> |---|---|---|
> | `code` | W-76 Phase 1, 2026-08-23 | 0.4 % of the index, **91 % of every full ingest** |
> | `vectors` | **2026-08-25** | its lane measured 0 fixed / 2 broken |
>
> ⚠ **The second removal is not a reversal of the first's reasoning.** Phase 1
> removed a per-*document* vector and Phase 7 replaced it with per-*chunk*
> vectors on the argument that the unit was the defect. **That argument was
> measured and it was wrong** — the model mean-pools static token vectors, so
> the unit was never the binding constraint.
>
> **`tests/ingest/test_extract.py` keeps a test asserting the absence of both**,
> for the reason it kept one in 2026-08-23: a removal is a decision, and a
> decision with no test is one a later session re-implements by accident.

## §1 — For humans

Every record Fux commits today carries `"mode":"extracted"`. This record says
what that word promises: **everything in the record was taken from the
document's own bytes, and nothing was invented.** Title, phrases, terms,
length, edges, dense code — each is a function of the file, computed by
stdlib code, offline, with no model anywhere in the path.

> **Amended 2026-08-24 (W-76 Phases 1 and 7).** *"Dense code"* names a field
> that no longer exists — `code`, one 256-bit sign vector per document, was
> removed in Phase 1 and Phase 7 committed **per-chunk `int8` `vectors`** in its
> place. *"Length"* is `flen`, five raw per-field token counts, not the single
> weighted `wlen` this sentence was written for.
>
> **The law is untouched, and the new field is held to it as strictly as the
> old one.** A vector is still a function of the document's bytes and a bundled
> static model — a lookup table, not an inference — computed offline with no
> network. The one thing that changed is what happens when the bundle is
> absent: `vectors` is simply empty, a degraded lane and never an error,
> because the lexical index answers on its own. **An absent field is still not
> an invented one**, which is the whole of what `extracted` promises.

That is why the mode is worth naming at all. `mode` is not documentation — it
is a property in the committed wire format, sitting beside `meta` in every
line of `.fux/index/*.jsonl`. A reader who sees `extracted` may rely on the
whole chain: same bytes in, same index out, no network, no model, no drift.
**Every guarantee stated in the paper is stated for this mode and no other.**

The name was chosen to *agree* with the ported edge-grade vocabulary rather
than merely avoid it: `EXTRACTED` already means "deterministic, no model" as
an edge grade, so the mode and the grade now say the same thing with the same
word. Its counterpart is [ADR-ENRICHED](0017_enriched-mode.md), which is
proposed and unbuilt.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    D["document bytes"] --> X["extract<br/>stdlib + bundled static model, offline"]
    X --> T["title · phrases<br/>terms · flen · vectors · edges"]
    T --> R["record<br/>mode: extracted"]
    R --> G["guarantee<br/>byte-reproducible"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  +----------+     +------------------+     +----------------------+
  | document | --> | extract          | --> | title · phrases      |
  |  bytes   |     | stdlib + static  |     | terms · flen         |
  |          |     | model, offline   |     | vectors · edges      |
  +----------+     +------------------+     +---------+------------+
                                                      |
                                                      v
                                        +-----------------------------+
                                        | record: mode = "extracted"  |
                                        | guarantee: byte-reproducible|
                                        +-----------------------------+
```

</details>

> **Amended 2026-08-24 (W-76 Phases 1 and 7) — both halves of the pair,
> together.** Both drew the extracted set as *"title · phrases · terms · `wlen`
> · edges"*. `wlen` is not extracted and is not committed — `flen` is, and
> `wlen` is derived at query time from the weights in force — and `vectors` was
> missing from a picture whose whole job is to show what the mode covers.
>
> The extract box gained *"+ bundled static model"* for the same reason. It
> read *"stdlib only"*, which was already an overstatement when `code` existed
> and would now be read as saying `vectors` comes from somewhere outside this
> diagram. **The model is a lookup table shipped in the wheel, not an
> inference and not a network call** — which is precisely why the mode's
> guarantee survives it, and why the diagram should say so rather than omit it.

### Examples

**What the mode looks like on disk.** One record, captured from this repo's own
committed index (`.fux/index/c0.jsonl`), pretty-printed; `terms` is truncated
from 299 entries, `edges` from 42, and each of the 4 `vectors` from 342
base64url characters, marked where. Keys are reordered for reading — the shard
sorts them — and every value shown is verbatim. The shard itself is one record
per line, unindented.

```json
{
  "_format": "fux.index.v2",   // the shard's first line, once per file
  "analyzer": "v2",
  "tf_fields": ["body", "heading", "title", "path", "ctx"]
}
{
  "id":      "file:docs/index.md",
  "src":     "git",
  "loc":     "docs/index.md",
  "sha":     "e8005dd97a8caeb59205e0e4a945b1ed92acdc13",
  "ver":     1,
  "mode":    "extracted",
  "meta":    "plain",
  "mtime":   1787122917,
  "title":   "Fux docs — knowledge bundle root (v0.30 rebuild)",
  "phrases": ["Fux docs — knowledge bundle root (v0.30 rebuild)",
              "Core (read in this order)", "Decisions", "Build"],
  "terms":   {"0097ee914e37dedf": [1],
              "031b0e9051c7d6b4": [1],
              "0387c9370a386785": [1]},      // … 299 total
  "flen":    [691, 13, 8, 3],
  "vectors": ["E0GB1kceAvGoBMJHARIl8-km4PbqBxb2DA4aAP0L8gk2Lw0X…",
              "En-E0Ew6EMDDBNonxgQUBPsSA_7g--bnHvUUBPYu8QgsECUJ…",
              "_0an3n8TJQbPAvIr2fE9-PcI9e3-GwX39-8FAA0W5AsQHSYP…",
              "DGSB431JOuOdDsYVyBYT9f8I4t7s8Q_87hEk4-hFBggkHA8W…"],
  "edges":   [{"dst": "file:CLAUDE.md",           "grade": 10, "kind": "code"},
              {"dst": "file:README.md",           "grade": 10, "kind": "code"},
              {"dst": "file:docs/GLOSSARY.md",    "grade":  8, "kind": "code"}]  // … 42 total
}
```

> **Amended 2026-08-24 (W-76 Phases 1, 2 and 7) — re-captured, because the
> label promised something the block had stopped delivering.** It read
> *"captured from this repo's own committed index (`.fux/index/c0.jsonl`) …
> **Every other byte is verbatim**"*, and what followed was a `v1` header, `[0,
> 1]` tf pairs under `["heading", "body"]`, `"wlen": 444` and
> `"code": "c-oipo_E6Ew44yT0wlJqDbvYgp01Ju-n4hqhqWTXlUw"`. **Not one of those
> is in that file.** §1 of this record went stale while the amendment at the
> foot of §2 correctly described every one of the changes — which is how a
> reader ends up trusting the wrong half of the same document.
>
> The block above is the same document's record, read out of `c0.jsonl` today:
> `v2` header, five tf fields in `store.TF_FIELDS` order, single-element tf
> lists (trailing zeros are trimmed, and 92.5 % of postings are body-only),
> `flen` instead of `wlen`, four committed per-chunk `vectors` instead of one
> document `code`, and the Phase-2 `mtime` prior. **`ver` went *down*, from `2`
> to `1`, and that is not a typo** — the schema migration ran `--full`, which
> reads no prior index, so every revision counter in the corpus restarted at
> `1`. `sha` moved because the document has been edited since.
>
> **One promise in the label is now weaker and is stated instead of quietly
> dropped:** the keys are shown in a reading order, and the shard sorts them
> alphabetically. Every *value* is verbatim; the *byte sequence* is not, and
> was not before either.

**Read it as the contract.** Every value above is a function of
`docs/index.md`'s bytes and the corpus's link structure, and of nothing else:
`title` and `phrases` are the document's own headings; `terms` are hashes of
tokens that literally appear in it, with per-field frequencies; `wlen` is its
token count; `code` is the bundled static model's sign-quantized vector — a
lookup table, not an inference; `edges` are links the document actually
contains, graded `10` when the target resolved unambiguously and `8` when a
backtick path resolved only by basename.

> **Amended 2026-08-24 (W-76 Phases 1, 2 and 7) — two clauses name fields that
> are gone, and one field is missing a clause.** Read it as: **`flen`** is its
> per-field token counts, five of them, raw and unweighted — the weighting is a
> query-time policy and deliberately not committed; **`vectors`** are the
> bundled static model's quantized chunk vectors, one per chunk, still a lookup
> table and still not an inference; and **`mtime`** is the document's git
> **commit** timestamp, which is a fact about the corpus's history rather than
> about the file on disk, and is committable for exactly that reason — a
> filesystem mtime differs per machine and would break the reproducibility this
> mode's name asserts.
>
> **Every one of them still passes the test this paragraph applies**, which is
> the only reason the amendment is short: each is a function of the document's
> bytes, its path, or the corpus's own recorded structure, and of nothing else. **Grade `6` — `INFERRED` — does not
appear here and cannot**: [`ingest/edges.py`](../../src/fux/ingest/edges.py)
reserves it and states it is "unused until the enriched tier". That absence is
the mode, visible in the bytes.

**And the guarantee it asserts** — same sources, same bytes:

```console
$ sha1sum .fux/index/*.jsonl > /tmp/a && fux ingest >/dev/null \
  && sha1sum .fux/index/*.jsonl > /tmp/b && diff /tmp/a /tmp/b && echo IDENTICAL
IDENTICAL
```

---

## §2 — For agents

### Context

The naming was opened by Arpit's 2026-08-09 directive — *"ingest needs to
happen without ai model … ingest with AI model can be extracted mode"* — which
collided head-on with the ported edge-grade vocabulary, where `EXTRACTED`
already means deterministic and `INFERRED` already means model-derived. The
fork was worked in [`work/compare/ingest-mode-naming.compare.md`](../../work/compare/ingest-mode-naming.compare.md)
and the recommendation has carried `⏳ proposed` since.

It stopped being a taste call the moment `mode` entered the committed wire
format. A rename now costs a format bump and a re-ingest of every corpus that
ever committed an index — a cost that is zero today and rises with every
adopter, which is exactly the shape of damage CLAUDE.md's priority rule
ranks first.

### Decision

**1. The deterministic ingest mode is named `extracted`**, and that string is
the committed value of the `mode` property. Ratified by Arpit, 2026-08-19.

**2. `extracted` asserts a contract, not a label.** A record in this mode
guarantees: every property is a pure function of the document's bytes and the
corpus's link structure; no model was consulted at any point; no network was
touched (L4's fenced exceptions — `fux add <URL>` and `fux update` — fetch *bytes* and
still extracts from them deterministically); the run is byte-reproducible.

**3. It is the default, and today it is the only mode that exists.** A record
carrying any other `mode` value is a defect until
[ADR-ENRICHED](0017_enriched-mode.md) is accepted.

**4. Every guarantee in the paper and in every regression run is stated for
this mode.** A measurement taken under any other mode is a different
experiment and may not be compared against a pre-registered threshold.

**5. `inferred` is retired as a mode value** and is not valid in v0.30+. It
survives only in the frozen archived fidelity vocabulary.

### Consequences

- **The word is load-bearing in two vocabularies at once**, deliberately: the
  mode and the edge grade agree. A change to either is a change to both.
- **Renaming later is a format change**, not a rename — `_format`/`analyzer`
  bump plus re-ingest everywhere. That is the cost this ratification buys out.
- **The paper's §3.2 is stale in the other direction** — it still calls this
  tier "Inferred mode". That text is superseded by this record; the paper is
  rewritten to measured values at M6 ([W-26](../../archive/open/W-26-m6-scale-t2.md)).
- **`extract.py` moves to this record** in the ownership table, out of
  ADR-INGEST's claim on `src/fux/ingest/`. Most specific wins, exactly as
  `store/fuxdir.py` already resolves against `store/`. ADR-INGEST keeps how
  ingest *runs*; this record owns what extraction *promises*.

### Alternatives considered

- **`derived` / `enriched`** *(runner-up)* — collision-free and visually
  distinct from its counterpart; loses only because it merely avoids the edge
  grades rather than agreeing with them.
- **`inferred` / `enriched`** — rejected: leaves `mode = inferred` (no model)
  beside `grade: INFERRED` (model-derived), reproducing the collision one word
  to the left.
- **`inferred` / `extracted`** (Arpit's original assignment) — matches his
  phrasing but requires renaming the ported edge grades and *still* leaves
  `inferred` colliding.
- **Leave it unnamed until the second mode exists** — rejected: the string is
  already in the committed format, so "unnamed" is not one of the options.

Full matrix: [`work/compare/ingest-mode-naming.compare.md`](../../work/compare/ingest-mode-naming.compare.md).

### Reference (required)

- The extractor — [`src/fux/ingest/extract.py`](../../src/fux/ingest/extract.py);
  the property is written at [`run.py`](../../src/fux/ingest/run.py) lines 102
  and 123.
- Determinism, captured — [`work/regression/2026-08-18-ingest-and-index/`](../../work/regression/2026-08-18-ingest-and-index/report.md) §4.
- The fork and its matrix — [`work/compare/ingest-mode-naming.compare.md`](../../work/compare/ingest-mode-naming.compare.md).
- How ingest runs, as distinct from what extraction promises —
  [ADR-INGEST](0007_ingest.md).

**Amended 2026-08-23 (W-76 Phase 1).** Extraction now produces **five tf
fields** — `body`, `heading`, `title`, `path`, `ctx`, in `store.TF_FIELDS`
order — and **`flen` in place of `wlen`**.

- **`title` and `path` are new fields, not new content.** Both were already
  *in* the record (as `title`, and as `loc`); extracted-mode law is unchanged
  because nothing is invented — the title's own tokens and the path's own
  segments are taken from the document and its location. `title` previously
  had to be folded into the heading tokens because there was nowhere else to
  put it; it now has its own field and is **no longer double-counted**.
- **`ctx` is declared and always empty** until Phase 8's `fux enrich` exists.
  An empty field is a trailing zero and is not written at all, so it costs
  nothing to reserve.
- **`flen` replaces `wlen` because `wlen` was a function of a tunable** —
  ADR-TUNE decision 6. `flen` carries raw per-field token counts, which are
  facts; the weighting happens at query time in `query/bm25f.py::derive_wlen`.
- **`code` is no longer emitted.** It was 0.4 % of the index and **91 % of a
  full ingest**; Phase 7 returns the same Hamming scan as a *derived*
  prefilter over per-chunk vectors. `Extracted.code` is retained as a field
  and is always `None`, so the shape of the dataclass does not churn twice.

### Veto condition

**Reopen this decision if** a committed record carries a `mode` value other
than `extracted` before `src/fux/enrich/` exists (the enriched mode is
ratified but unbuilt — [ADR-ENRICHED](0017_enriched-mode.md)), or if
re-ingesting an unchanged corpus stops producing byte-identical shards, or if
an `edges` entry ever carries grade `6` on an `extracted` record — each means
the contract this name asserts is no longer true of the bytes.

> **Amended 2026-08-24 (W-76 Phase 8) — the first trip-wire stopped matching,
> and it stopped matching in the direction that hides a fire.**
> **`src/fux/enrich.py` exists**, so *"before `src/fux/enrich/` exists"* now
> reads as a window that has already closed — a reader checking this condition
> would conclude it can no longer fire, which is the opposite of the truth.
>
> **The path was a proxy for the wrong thing.** `fux enrich`
> ([ADR-ENRICH](0040_enrich.md)) does **not** build the enriched mode: it plans
> and validates enrichment that a coding agent generates, the result is pinned
> text that ingest tokenizes into the `ctx` field, and the record it lands on
> stays `"mode": "extracted"` — correctly, because a pinned file is bytes fux
> read, not something fux inferred. `run.py` writes the literal string
> `"extracted"` at both of its two record sites and there is no third.
> [ADR-ENRICHED](0017_enriched-mode.md) is still `proposed` and still unbuilt.
>
> *Restated, without the proxy:* **reopen if any committed record carries a
> `mode` value this record has not ratified** — which is check 1 below,
> unchanged, and the only form of the condition that cannot go stale by a
> module being renamed. A second mode arriving is a change to
> [ADR-ENRICHED](0017_enriched-mode.md) and to this record, together, before
> a byte of it is written.

**How to check it:**

```bash
# 1. no mode value exists that this record has not ratified
grep -oh '"mode":"[a-z]*"' .fux/index/*.jsonl | sort -u
# expect exactly: "mode":"extracted"

# 1b. no inferred-grade edge on a deterministic record
grep -c '"grade": *6' .fux/index/*.jsonl | grep -v ':0$'
# expect: no output

# 2. the byte-reproducibility the name promises
sha1sum .fux/index/*.jsonl > /tmp/a && fux ingest >/dev/null \
  && sha1sum .fux/index/*.jsonl > /tmp/b && diff /tmp/a /tmp/b && echo OK
```
---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-INGEST](0007_ingest.md) ·
[ADR-ENRICHED](0017_enriched-mode.md)

**Code**

- [`src/fux/ingest/edges.py`](../../src/fux/ingest/edges.py)
- [`src/fux/ingest/extract.py`](../../src/fux/ingest/extract.py)
- [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py)

**Measured evidence**

- [`work/regression/2026-08-18-ingest-and-index/report.md`](../../work/regression/2026-08-18-ingest-and-index/report.md)

**Project docs**

- [`work/OPEN-WORK.md`](../../work/OPEN-WORK.md)
- [`work/compare/ingest-mode-naming.compare.md`](../../work/compare/ingest-mode-naming.compare.md)
