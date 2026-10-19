---
type: Handoff
name: W-288
description: "Arpit's ruling (2026-10-19, Cowork): one shared TABLE module that xlsx, HTML, docx and csv all feed, and a name for that kind of module — a decoder EXTENSION. This item builds the mechanism (a versioned shared layer under the decoders, in every importing decoder's reuse key) and brings W-287's shared table module under it as the first extension; it follows W-287 so the two never edit the same files at once."
item: W-288
filed: 2026-10-19
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-19
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-288 — decoder extensions: one versioned shared layer, the table extension first

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Name the layer: a **decoder extension** is a shared module a decoder calls, with its own `VERSION`; `decode/ext/` is its home | the five shared helpers that already exist stop being nameless | ⏳ |
| 2 | Put every extension's `VERSION` into the reuse key of every decoder that uses it | a fix in shared code re-extracts the documents it changes — today only `--full` does | ⏳ |
| 3 | Move W-287's `decode/_table.py` to `ext/table.py` — the first extension built to the rule | the table module gets a version that reaches existing corpora | 🟡 after W-287 |
| 4 | Finish what W-287 leaves: csv on the same emitter, `_ooxml.table_markdown` and `html.py::_emit_table` gone if any copy remains | one emitter, zero copies | ⏳ |
| 5 | Keep W-287's round-trip gate (emit → `_table_bands` → cells) running against `ext/table.py` | the emitter and the chunker stay one contract | ⏳ |
| 6 | Move the existing helpers (`_ooxml`, `_xml`, `_zip`, `_markdown`, `_limits`) under the same rule | one kind of shared module, not two | ⏳ |

**Arpit, 2026-10-19 (Cowork):** *"how about we build 1 decoder just for table
and internally html, docs and xlsx use the same?"* … *"Okay, let's call it
extensions and file a work item for it."*

**Model:** Claude Code, **Opus**: a new layer in the decoder protocol with a
digest change, a record amendment and a five-format refactor. Ratified in
Cowork, **not built**.

## Goal

A **decoder extension** is a shared module under `src/fux/decode/ext/` that a
decoder calls to do part of its work — turning a grid into a Markdown table,
reading an OOXML zip, applying the row and column limits. It has no file
suffix of its own and is never chosen by the registry; a decoder names the
extensions it uses, and each one's `VERSION` rides in that decoder's reuse key.
The **table extension** is the first one built to this rule, and the five
helpers that already exist are brought under it.

## Why a mechanism and not a rename

- `_ooxml.py`, `_xml.py`, `_zip.py`, `_markdown.py`, `_limits.py` are shared
  by several decoders today. **None declares a `VERSION`, and none is in the
  reuse key** — [`acquire/decoderdigest.py`](../../src/fux/acquire/decoderdigest.py)
  digests `<decoder>@<version>` only, and
  `tests/decode/test_decoder_versions.py::test_a_changed_builtin_decoder_bumped_its_version`
  audits `BUILTIN_MODULES` alone. So an edit to `_ooxml.table_markdown` moves
  no document's bytes and no decoder's version: **an existing corpus keeps the
  old output until `fux ingest --full`**, while `fux doctor` stays green. That
  is [SR-DECODE](../../records/0139_decode.md) decision 11a's trap, open again
  one layer down.
- Tables are the worst case: four formats, three copies of the emitter, and
  SR-TABULAR decision 7's phantom-row defect was exactly *"two files, one
  record, one of them right."*

## The naming — a hazard, written down

**"Extension" already has two meanings in fux**, and this adds a third:

| phrase | means | where |
|---|---|---|
| a decoder's `EXTENSIONS` | the file suffixes it claims (`.xlsx`, `.xlsm`) | SR-DECODE decision 1 |
| the consumer's **extension points** | `.fux/decoders/`, `.fux/fetchers/` — readable source IS the contract | [L10](../../records/0012_LAW-10-bundled-output.md) |
| a **decoder extension** (this item) | a versioned shared module under `decode/ext/` that a decoder calls | here |

**Rule for the build:** in prose always the two-word form *decoder extension*;
in code the package is `decode/ext/`, the declaration on a decoder is
`USES = ("table", "ooxml")`, and the constant `EXTENSIONS` keeps its meaning
untouched. Where a sentence must name a `.xlsx`-style extension beside a
decoder extension, call the former a **suffix** (Python's own word,
`Path.suffix`). Both enter `docs/GLOSSARY.md` in the same change. ⚠ This is
a vocabulary ruling in the sense of [L6](../../records/0008_LAW-6-say-index.md)
— Arpit's word stands; a rename is one word from him and this table is where
it lands.

## Design

### The mechanism

- **E1 home and shape.** `src/fux/decode/ext/<name>.py`; each declares
  `VERSION` read from `constants.toml` `[extensions.<name>] version`
  ([L12](../../records/0014_LAW-12-values-live-in-config.md)) and nothing
  else protocol-wise. No registry, no suffix, no `decode()`.
- **E2 declaration, not introspection.** A decoder lists what it uses:
  `USES: tuple[str, ...]`. Explicit and deterministic ([L4](../../records/0006_LAW-4-deterministic.md));
  import-graph discovery would make the digest depend on how a module is
  written rather than what it declares.
- **E3 the digest.** `decoderdigest` composes
  `<decoder>@<v>+<ext>@<v>+…` per suffix, extensions in declared order.
  Blast radius stays per suffix (SR-DECODE's design call): a `table` bump
  re-extracts the table-bearing formats and nothing else; an `xml` bump
  re-extracts what declares `xml`.
- **E4 the gates.** `test_decoder_versions.py` grows three checks: every
  `ext/*.py` declares `VERSION`; a decoder that imports `ext.<name>` declares
  it in `USES` (the one place introspection is used — to catch a missing
  declaration, never to build the key); a changed `ext/*.py` in the diff
  bumped its `VERSION`.
- **E5 the existing five.** `_ooxml` → `ext/ooxml.py`, `_xml` → `ext/xml.py`,
  `_zip` → `ext/zip.py`, `_markdown` → `ext/markdown.py`, `_limits` →
  `ext/limits.py`, each with `VERSION = 1`; decoders declare `USES`.
  ⚠ **This changes every digest once**, so the first release re-extracts every
  document of every consumer on their next `fux ingest`. Named in the CHANGELOG
  as a one-time cost; nothing hides it.

### The table extension — `ext/table.py` (W-287 builds it as `decode/_table.py`; this is the contract the move keeps)

The pipeline, in order, one place for each rule:

1. `Grid` — cells placed by `(row, col)`, sparse allowed;
   `Cell(text, kind)`, `kind ∈ {text, number, date, time, bool, empty}`: the
   parser says WHAT a value is, the extension decides how it is written.
2. **spans** — merged / `colspan` / `rowspan` / `gridSpan` / `vMerge` expand
   by repeating the anchor value into the span.
3. **header** — a declared header wins (`<th>`/`<thead>`, a parser flag);
   otherwise the first row whose filled-cell count ≥ width ×
   `[index] table_header_min_fill` (a committed `[index]` key beside
   `max_table_rows` — it changes what is indexed, and the `[index]` digest
   re-extracts on change); rows above it are emitted as prose.
4. **values** — dates ISO-8601, times `HH:MM`, booleans `true`/`false`,
   numbers shortest repr, `|` escaped, `[limits.csv] max_cell_chars`.
5. **limits** — `max_table_rows` counts data rows, blank rows spend nothing,
   `[limits.xlsx] max_cols`; the two notices written once.
6. **emit** — a Markdown table with edge pipes and a separator row, the caption
   or sheet name as its heading line: exactly what `text/chunk.py::_table_bands`
   parses.

**The parsers, each returning `Grid`s and nothing else:**

- **xlsx** — one `Grid` per sheet; cell placed by its `r=` address (today
  cells are appended in XML order and Excel omits empty cells, so sparse rows
  shift left); `kind` from `t=` and `styles.xml` `cellXfs → numFmtId`/`numFmt`
  (today dates are serials, booleans `0`/`1`); `mergeCells` as spans.
- **html** — one `Grid` per `<table>`; `<th>`/`<thead>` flagged as header,
  `colspan`/`rowspan` as spans, `<caption>` as caption; a nested table is
  flattened into its cell.
- **docx** — one `Grid` per `w:tbl`; `gridSpan`/`vMerge` as spans.
- **csv/tsv** — one `Grid`; the separator sniff stays, everything else moves.
- **pptx** keeps using `ext/ooxml.py` for its tables through the same emitter.

**Round-trip gate:** `emit(grid)` → `_table_bands` → cells == the grid's rows,
for every fixture, per format. **Byte-identity gate:** every existing decoder
fixture unchanged where no defect above applies. **Fixture per defect per
format** — a bug in the extension reaches five formats at once, so each proves
it separately.

## Definition of done

1. `decode/ext/` exists; the five helpers moved with `VERSION = 1` and
   `USES` on every decoder; `decoderdigest` composes; the three new checks in
   `test_decoder_versions.py` pass and fail when they should.
2. `ext/table.py` is the only place a table becomes Markdown;
   `_ooxml.table_markdown` and `html.py::_emit_table` deleted; xlsx/html/docx/
   csv reduced to grid parsers; the round-trip and byte-identity gates pass.
3. Records amended in the same change: [SR-DECODE](../../records/0139_decode.md)
   — a new decision for decoder extensions (E1–E5) and the naming table;
   [SR-TABULAR](../../records/0150_tabular.md) — owns `ext/table.py`, decision
   7's two-file story closed, the header rule; `records/README.md` ownership rows
   for every `ext/*.py` (SR-DECODE owns `ooxml`, `xml`, `zip`, `markdown`;
   SR-TABULAR owns `table`, `limits`).
4. `docs/GLOSSARY.md` carries *decoder extension* and *suffix*; CHANGELOG names
   the one-time re-extraction.
5. `IMPLEMENTATION.md`, WORKLOG, the registry rows; both suites green.
6. W-287 closed first; this item's move leaves every W-287 fixture byte-identical.

## Out of scope

- The table module's first build, column-aware passages and the record-shaped answer — W-287.
- Consumer-written extensions under `.fux/` — the extension points of L10 stay
  decoders and fetchers; a consumer decoder may import `fux.decode.ext` as it
  may import anything else, and that is all.
- Tables in PDFs (`pdf.py` is text-only); `.xls`.

## Blockers

🟡 Waits on **W-287** — its stage A writes `decode/_table.py`, html/docx/xlsx and the
decoder `VERSION`s; this item moves and versions them afterwards so two sessions never edit
the same files at once.

## Record affected

- [SR-DECODE](../../records/0139_decode.md) — new decision: decoder extensions
  (home, `USES`, digest composition, the three gates, the naming table).
- [SR-TABULAR](../../records/0150_tabular.md) — owns `ext/table.py` and
  `ext/limits.py`; decision 7 and the header rule.
- `records/README.md` §Ownership — one row per `ext/*.py`.

## Hazards

- **The word.** Three meanings of *extension* in one codebase; the naming table
  above is the only defence, and GLOSSARY must land in the same change.
- **One-time full re-extraction** when the digest shape changes (E5). Say it
  in the CHANGELOG; do not stage it across releases, which would leave two
  digest shapes alive at once.
- **Shared-code blast radius.** One defect in `ext/table.py` misreads five
  formats; per-format fixtures and the round-trip gate are not optional.
- **`USES` drift.** A decoder that imports an extension it does not declare
  gets the old trap back; E4's introspection check exists for that one reason.
- **SR-DECODE decision 5** — the decoder protocol does not grow a parameter;
  `USES` is a declaration beside `EXTENSIONS` and `VERSION`, read by the
  digest, never passed to `decode()`.

## Reference

- SR-TABULAR decision 7 — the phantom-row defect: two copies, one right.
- SR-DECODE decision 11a — why `VERSION` is in the reuse key, keyed per suffix.
- W-287 — what the table extension is built for.
