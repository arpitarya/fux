---
type: Standing Record
kind: component
name: SR-DOCS-TABLE
title: SR-DOCS-TABLE (0122) — docs.jsonl, the docidx-ordered doc table
description: One JSON line per document, sorted by id, so its position (docidx) is a stable, small join key every other derived structure references instead of repeating the string id.
status: accepted
amended: 2026-10-05
date: 2026-08-19
feature: "`.fux/runtime/docs.jsonl` — the derived doc table and the join key it defines"
owns: [node/src/derive/docstable.mjs@74dd7c2a91a2, src/fux/derive/docstable.py@8e287539fe3c]
laws: [L4]
timestamp: 2026-08-19T00:00:00Z
content_sha: 203f5d5b2b35353005c1f4dbdf2a116d6673336c4acae2291d347704cd4280a3
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`node/src/derive/docstable.mjs`](../node/src/derive/docstable.mjs) · file
- [`src/fux/derive/docstable.py`](../src/fux/derive/docstable.py) · file

**Describes** — reaches into, does not own:

- [`src/fux/derive/_build.py::_read_committed`](../src/fux/derive/_build.py) · owned by [SR-T1-ACCELERATOR](0110_accelerator.md)
- [`src/fux/derive/format.py`](../src/fux/derive/format.py) · owned by [SR-T1-ACCELERATOR](0110_accelerator.md)

<!-- COMPONENTS-END -->

# SR-DOCS-TABLE — docs.jsonl, the docidx-ordered doc table

## §1 — For humans

`docs.jsonl` is the derived plane's doc table: one JSON object per line, sorted
by `id`, so a document's **position in the file** — its `docidx` — is fixed for
a given committed corpus. That integer is what every other derived structure
references instead of repeating the string `id`: a postings block's entries
carry `[docidx, [tf, …]]`, the tf vector in `TF_FIELDS` order with trailing
zeros trimmed. **Small keys, one source of truth for the mapping, no separate
lookup table required.**

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    A[".fux/index/*.jsonl records,<br/>doc-major, COMMITTED"] -->|"fux build,<br/>sorted by id"| B["docs.jsonl —<br/>one line per doc"]
    B --> C["docidx = line position, 0-based"]
    C --> D["postings entries reference docidx"]
    C --> E["the field set is pinned in manifest.json"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   .fux/index/*.jsonl records, doc-major, COMMITTED
              |
              |  fux build, sorted by id
              v
   docs.jsonl — one line per doc:
     {archived, flen, id, loc, mtime, superseded, title}
              |
              |  docidx = the line's 0-based position
              v
   postings blocks store [docidx, [tf per field, trailing zeros trimmed]]

   the seven-key set is a CHECKED contract: fmt.DOCS_FIELDS is written
   into manifest.json as docs_fields and compared by is_fresh().
```

</details>

### Examples

The first two lines of this repo's `.fux/runtime/docs.jsonl` — `docidx 0` and
`docidx 1`:

```console
$ head -2 .fux/runtime/docs.jsonl
{"archived":false,"flen":[4913,135,10,2],"id":"file:CLAUDE.md","loc":"CLAUDE.md","mtime":1787383116,"superseded":false,"title":"CLAUDE.md — coding-agent guide for the Fux engine"}
{"archived":false,"flen":[945,6,1,2],"id":"file:README.md","loc":"README.md","mtime":1787414909,"superseded":false,"title":"Fux"}
```

Note what the table does that the committed record does not: `archived` and
`superseded` are written **explicitly, even when false**. On the committed line
they are omitted when false, because that line is paid for in every diff; here
the file is derived, disposable, and read by an accelerator that must not have
to distinguish *absent* from *false* on the hot path.

---

## §2 — For agents

### Context

Every derived structure that references a document needs to do so cheaply. The
document's own `id` string is the durable, corpus-independent identifier, but
repeating it inside every postings entry would bloat both the block line and the
**fixed-width** offset-table entry that indexes it
([SR-T1-ACCELERATOR](0110_accelerator.md)).

### Decision

**0. This record owns [`src/fux/derive/docstable.py`](../src/fux/derive/docstable.py) and its Node twin [`node/src/derive/docstable.mjs`](../node/src/derive/docstable.mjs)** since 2026-10-05 ([SR-WORK-OWNERSHIP](0054_WORK-ownership.md) decision 11, W-261 — Arpit's ruling that every `kind: component` record owns a file). The docs table's writer is a pure move out of `derive/_build.py` (and `build.mjs`): `write` — one sorted-key JSON row per document, in docidx order, byte-identical. `_build.py` still decides **when** it is written, in `build()`'s order, and computes its inputs in `_read_committed`; `format.py` keeps the constants and `write_json`, the serializer every runtime JSON file shares — both [SR-T1-ACCELERATOR](0110_accelerator.md)'s, both reached by this record's `describes` rows. ⚠ **This decision read *owns nothing, case (a)* until W-261, arguing that carving the file out would give one plane two owners for one pass.** The ruling answered it: the build orchestrates, this record owns the bytes of its one file.

**1. One JSON object per line: `archived`, `flen`, `id`, `loc`, `mtime`,
`superseded`, `title`** — the set `derive/format.py::DOCS_FIELDS` names. It is
**part of the runtime contract**, written into `manifest.json` as `docs_fields`
and compared by `is_fresh()`
([SR-RUNTIME-MANIFEST](0123_runtime-manifest.md)).

⚠ **A principle was abandoned here, and it deserves saying so rather than a
longer field list.** The table once held *exactly the fields a hit needs to be
rendered — nothing that participates in scoring*, and that was load-bearing: a
corrupt or stale doc table could produce an ugly result but never a wrong
ranking. **Four of the seven now feed scoring.** `flen` is what
`bm25f.derive_wlen()` turns into the length normaliser, and `archived`,
`superseded` and `mtime` are the facts `rank.Weighting.of()` multiplies by.

**What broke the old principle was a real defect**: a multiplier that reached
the scorer without reaching the accelerator's pruning bound made `--fast` and
`--scan` return **different documents** at any non-default weight. The fix has
to give the accelerator the same facts the scan reads off the record — and the
accelerator's only per-document input is this table. **There is no version of
that fix in which scoring data stays out of `docs.jsonl`.**

**2. What replaced it is narrower and stronger: nothing here is *derived*, only
*carried*.** Every one of the seven is copied verbatim from the committed record
— `bool(r.get("archived", False))`, `r.get("mtime")` — and **never recomputed**
from `loc`, from a configured directory list, or from anything else.

⚠ **Recomputation is precisely how the two paths drift.** A record stamped
`archived: true` whose `loc` no longer matches a configured archived directory
is flagged by the path that reads the stamp and missed by the path that
re-derives it. The separation that survives is **fact versus derivation**, not
display versus scoring, and it is enforced by `docs_fields` in the manifest
rather than by anyone remembering it.

**3. Sorted by `id` before writing.** A given committed corpus always produces
the same `docidx` assignment across two builds — the specific piece of *the
derived plane rebuilds byte-identically* that this file is responsible for.

**4. `docidx` is the line's 0-based position, and the join key everywhere
else.** An integer keeps a postings entry small and makes a fixed-width
offset-table entry possible; a string `id` would do neither.

**5. `docs.jsonl` is one of `DETERMINISTIC_FILES`.** Byte-identical output for
the same committed input, verified the same way as `manifest.json` and
`stats.json`.

**6. Unchanged by W-168 step 4 (2026-09-27).** `mined.json` joined
`DETERMINISTIC_FILES` beside this table; the table's own fields did not move.

<!-- L12-VALUES-START -->

**Where this record's fixed values live — [L12](0014_LAW-12-values-live-in-config.md), W-225, 2026-09-27.**
Each name below keeps its spelling in code and holds no literal: it is read from
[`src/fux/constants.toml`](../src/fux/constants.toml), and a missing key stops the
process naming it ([SR-CONSTANTS](0159_constants.md)). **The values are unchanged** —
this moved where they are written, not what they are.

- `src/fux/derive/format.py` — `RUNTIME_DIR` ← `[runtime] dir`, `BLOCK_SIZE` ← `[runtime] block_size`, `RUNTIME_SCHEMA` ← `[runtime] schema`, `DOCS_FIELDS` ← `[runtime] docs_fields`, `DOCS_NAME` ← `[runtime] docs`, `ANCHORS_DIR` ← `[runtime] anchors_dir`, `STATS_NAME` ← `[runtime] stats`, `MINED_NAME` ← `[runtime] mined`, `MANIFEST_NAME` ← `[runtime] manifest`, `STAMP_NAME` ← `[runtime] stamp`, `POSTINGS_DIR` ← `[runtime] postings_dir`, `DETERMINISTIC_FILES` ← `[graph] file`

<!-- L12-VALUES-END -->

**No decision here moved** ([L12](0014_LAW-12-values-live-in-config.md) decision 6a, W-225 stage 5c, 2026-09-28). A component this record owns or describes lost a numeral — to `constants.toml` ([SR-CONSTANTS](0159_constants.md)) or to a refactor that removed it — and behaves byte-identically; JSON it prints is indented by `[json] indent`.

**No decision here moved** ([L12](0014_LAW-12-values-live-in-config.md) decision 6a R8, W-225 stage 6, 2026-09-28). A function this record owns or describes lost a boolean or value parameter default; every caller now passes the value the default had, so behaviour is unchanged.

**No decision here moved** ([L12](0014_LAW-12-values-live-in-config.md), W-225 stage 7, 2026-09-28). A component this record owns or describes now reads an artefact name or a format value from `constants.toml` that it spelled in code; every value is unchanged. The veto test `tests/test_l12_values_live_in_config.py` now holds the rest of its literals to `tests/l12_allow.toml`.


**W-236 — section records (2026-10-10; built on branch `w236-sections`, unmerged until [its run](../work/regression/2026-10-10-section-records/PRE-REGISTRATION.md) passes).** `docs.jsonl` gains **`nsec`** (0 when sectionless), carried off the record and checked against the section plane at build ([SR-SECTIONS](0161_sections.md) decision 9). `DOCS_FIELDS` and `RUNTIME_SCHEMA` (v10) move together, so a v9 table is refused, not read.

### Consequences

- **`docidx` is meaningful only within one build of one corpus.** It is never
  persisted outside `.fux/runtime/`, and nothing may treat it as a stable
  identifier across builds or across corpora — `id` remains the only durable
  identifier.
- **Adding or removing one document can shift every later document's `docidx`.**
  This is safe only because the entire runtime plane is rebuilt together, never
  patched in place ([SR-T1-ACCELERATOR](0110_accelerator.md)).
- **A change to the field set is a runtime-schema change.** `docs_fields` in the
  manifest is what makes an out-of-date plane refuse rather than answer from a
  shape it does not have — which is the guard that was missing when
  `superseded` and `mtime` first joined the table.

### Alternatives considered

- **Repeat the string `id` in every postings entry.** Rejected: it would
  materially inflate every block line, and make the **fixed-width**
  offset-table entry impossible, since ids are variable-length. The width is the
  argument, not any particular number of bytes.
- **A separate `id -> docidx` side index.** Rejected: redundant.
  `docs.jsonl`'s own line order already is that map, at zero extra storage.
- **Leave `docs.jsonl` unsorted, in shard-read order.** Rejected: it makes
  `docidx` depend on filesystem iteration order, breaking the byte-identical
  rebuild guarantee (L4).
- **Keep scoring data out and let the accelerator re-derive it.** Rejected under
  decision 2 — re-derivation is exactly what made the two query paths disagree.

### Reference (required)

- Generator — [`src/fux/derive/_build.py`](../src/fux/derive/_build.py)
  (`_write_docs()`, `_read_committed()`); the field set and the postings entry
  layout — [`src/fux/derive/format.py`](../src/fux/derive/format.py).
- The consumers of what the table carries —
  [`src/fux/query/bm25f.py`](../src/fux/query/bm25f.py) (`derive_wlen`) and
  [`src/fux/query/rank.py`](../src/fux/query/rank.py) (`Weighting.of`).
- The parent record — [SR-T1-ACCELERATOR](0110_accelerator.md); the freshness
  check that pins the field set —
  [SR-RUNTIME-MANIFEST](0123_runtime-manifest.md).

### Veto condition

**Reopen this decision if** a use case needs `docidx` to be stable across two
different builds or two different corpora, or if any field in the table is ever
**computed** rather than copied from the committed record.

**How to check it:**

```bash
# 1. nothing caches docidx across builds
grep -rn docidx src/fux/derive/
# expect: every consumer reads docidx fresh from the current build; none caches
# it across builds or writes it anywhere outside .fux/runtime/

# 2. every field is carried, not derived
grep -n '_write_docs' -A 20 src/fux/derive/_build.py
# expect: each value read off the record with .get(); no path matching, no
# directory list, no recomputation
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [SR-LAWS](0001_LAWS.md) ·
[SR-T1-ACCELERATOR](0110_accelerator.md) · [SR-RANKING](0111_ranking.md) ·
[SR-POSTINGS](0112_postings.md) ·
[SR-RUNTIME-MANIFEST](0123_runtime-manifest.md)

**Code**

- [`src/fux/derive/_build.py`](../src/fux/derive/_build.py)
- [`src/fux/derive/format.py`](../src/fux/derive/format.py)
- [`src/fux/query/bm25f.py`](../src/fux/query/bm25f.py)
- [`src/fux/query/rank.py`](../src/fux/query/rank.py)
