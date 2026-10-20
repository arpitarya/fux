---
type: Handoff
name: W-287
description: "Arpit's ask (2026-10-19, Cowork): fux should work better with tables — Excel, Markdown tables, HTML tables. A hit inside a table returns that row, as a record with its column names, and a query that names a column returns that cell. Ruled the full design, not the cheapest: ONE shared table model every format decoder feeds, column-aware row passages behind an L13 pre-registration, and a record-shaped answer surface."
item: W-287
filed: 2026-10-19
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-19
updated_by: "Claude Code (Opus 5.5)"
ball: agent
---

# W-287 — tables answer by row and by column

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | One shared table module (`decode/_table.py`): grid → spans → header → values → limits → Markdown; xlsx, HTML, Word, CSV parse into it | every value sits under its TRUE column name | ✅ built, uncommitted |
| 2 | Give each row passage its columns — `{column: value}` worked out at answer time, never committed | the engine knows which word is a column name and which is a value | ✅ built, uncommitted |
| 3 | Score a row by three fields — sheet/section, column names, cell values — and let a query word that names a column point at that column's cell | *"owner of INC6014999"* finds the row AND the owner cell | ✅ built behind the key (`0.0`), uncommitted |
| 4 | Treat `Field \| Value` and transposed sheets as records | property sheets answer by field name | ✅ `Field \| Value` built; transposed sheets NOT (State §) |
| 5 | Show a hit as a record: `Sheet1 · row 438`, one `column: value` line per cell, the asked cell first; locator `file.xlsx#Sheet1!R438` | an agent reads one answer, not a three-line Markdown fragment | ✅ built, uncommitted |
| 6 | Seed a tabular test corpus and pre-register steps 3–4 under L13, decided arm named before any number exists | the ranking part ships only if it clears the standing bar | ✅ decided: **FAIL (guardrail)** |
| 7 | Arpit reads the verdict | ship, or hold | ✅ Arpit ran the decider: **FAIL (guardrail)** — `table_column_weight` stays `0.0` ([VERDICT](../regression/2026-10-19-w287-table-columns/VERDICT.md)) |

## State — 2026-10-19, Claude Code (Opus 5.5)

**Built and green, uncommitted in `main`'s working tree** (not asked to commit).
Both suites and the Node suite pass; three governance gates wait on the commit
itself (records' `content_sha`, the twin note `query/__init__.py` ↔
`verbs/answer.mjs`, the working-tree freshness check).

- **Stage A — one table module, `decode/_table.py`**, as ruled at 19:45: xlsx
  (cells by `r=`, kind from `numFmt`, merges), HTML (`<thead>`/`<th>`, spans,
  caption, nested tables), docx (`gridSpan`, `vMerge`, nested tables once) and
  csv are grid parsers; `_ooxml.table_markdown` and `html.py`'s emitter are
  gone. 20 per-defect fixtures plus a four-format round-trip test in
  `tests/decode/test_tables.py`. HEAD → this: only five tracked HTML files
  differ, in escaped `|`. ([SR-DECODE](../../records/0139_decode.md) d23,
  [SR-TABULAR](../../records/0150_tabular.md) d8.) **W-288 moves it to
  `ext/table.py`.**
- ⚠ **The header threshold is a decoder cap, not an `[index]` key**, and
  W-288's text still says `[index] table_header_min_fill`. Measured: the index is
  a bag of terms, so a banner's words are the same body terms whether they head
  the columns or sit above them — `test_an_index_key_does_change_the_index`
  stayed red with a banner table in its corpus, and SR-TUNE decision 1's rule
  then refuses it from `[index]`. It is `.fux/formats.toml [limits.html|xlsx]
  header_fill_percent = 60`, in the extract-config digest. **W-288's text needs
  the same correction.**
- **A5, B1–B5, C1–C3** as designed, Node twins held equal by
  `tests/refer/test_table_twins.py` to the last float bit. Two changes, both
  before any number: a **record's field-name column is its key** (B4 over B5 —
  by the corpus's construction counts a record row named once could not beat a
  value saying the field twice); and **ties break on the positional locator**
  (found by the run's G0 gate: C3 reordered tied rows with the key off —
  [SR-REFER](../../records/0127_refer-plane.md) d28a).
- **Not built:** *transposed* sheets (header in the first COLUMN): no closed
  rule tells one from an ordinary key-first table, and L4 wants a list or a
  threshold, not a guess. A follow-up if wanted.
- **The run:** [`work/regression/2026-10-19-w287-table-columns/`](../regression/2026-10-19-w287-table-columns/report.md)
  — frozen bar (L13 defaults mapped onto passages, C1 tightened to hit@1 AND
  cell@1), 102 seeded questions, six arms captured, G0 and G1 PASS. STOP 1 (G0,
  a build defect) and the engine re-freeze for the one-module refactor are filed
  beside it, unscored. **No endpoint computed by anyone.**

**Arpit, 2026-10-19 (Cowork):** *"I want Fox to work better with tables, Excel,
tables when inside Markdown files, tables inside HTML. If … something that I'm
looking for … is present inside a table … it should give me just that row entry
or details of that row … Maybe we can look for the column as well … what is the
column name."* And, on the staged proposal: *"i dont want the cheapest i want it
the best way which gives best results. file a work item for it."*

**Model:** Claude Code, **Opus**: a decoder, chunker, rescore and answer-surface
change in Python with Node twins, carrying an L13 pre-registration. Ratified in
Cowork, **not built**.

## Goal

A question whose answer is one cell or one row of a table — in `.csv`/`.tsv`,
`.xlsx`/`.xlsm`, a Markdown table, an HTML `<table>` or a Word table — comes
back as **that row, as a record with its column names**, and when the question
names a column, **that cell first**. Every value is attributed to the column it
actually sits under.

## What already exists — do not rebuild it

- Every table source decodes to ONE Markdown table (`decode/csv.py`, `xlsx.py`,
  `html.py`, `docx.py`; `_ooxml.table_markdown`), and `text/chunk.py::_table_bands`
  splits it **one row per passage, header repeated**
  ([SR-TABULAR](../../records/0150_tabular.md) decisions 1–2: hit@1 0.875 vs
  0.229 for whole-table passages, `informed`). `fux answer` already cites one
  row (`owners.csv:L438-L438`).
- Committed per-section records **failed the bar twice** (W-236, W-269; the
  plane was 8× the doc plane). **Nothing in this item commits a row record.**
  The column work lives in the refer plane, on fetched bytes.

## The defects this item closes (read from the code, 2026-10-19)

| # | where | defect | effect |
|---|---|---|---|
| 1 | `xlsx.py::_rows` | cells appended in XML order; the `r="C7"` address is never read, and Excel **omits empty cells** | sparse rows shift left — values land under the wrong column |
| 2 | `xlsx.py::_cell` | no `styles.xml`/`numFmt` read | dates index as serials (`46214`), booleans as `0`/`1` |
| 3 | `xlsx.py`, `html.py` | header = first non-blank row, always | Excel title banners become the header; HTML `<thead>`/`<th>` ignored |
| 4 | `html.py` | no `colspan`/`rowspan`, no `<caption>`; a nested `<table>` resets state | misaligned columns, lost table title |
| 5 | `docx.py` | no `gridSpan`/`vMerge` | same misalignment |
| 6 | `chunk.py` `_TABLE_ROW_RE = ^\s*\|` | GFM tables without edge pipes are not tables | the whole table stays one passage — the 0.229 case |
| 7 | `chunk.py`, `_rescore.py` | transposed / `Field \| Value` tables are ordinary rows | the row is the wrong unit; the repeated header is noise |
| 8 | `_rescore.py` | header text sits in the row BODY | a column name in the query is just another word |
| 9 | `answer` locator | `.xlsx` cites a line of the DECODED text | not openable in Excel |

## Design — three stages, built in this order

### Stage A — one shared table module

**Arpit, 2026-10-19 (Cowork):** *"how about we build 1 decoder just for table and
internally html, docs and xlsx use the same?"* — ratified as a shared internal
module `decode/_table.py` (not a decoder: no suffix, never chosen by the
registry). Pipeline, in one place: `Grid` of placed cells → spans expanded
(merged/colspan/rowspan/gridSpan/vMerge) → header (declared `<th>` wins, else
fill-ratio threshold) → values (ISO dates, `true/false`, number repr) → limits
and the two notices → Markdown with edge pipes. xlsx (cells by `r=`, `kind` from
`numFmt`), HTML, docx and csv become grid parsers. **Round-trip gate:**
`emit(grid)` → `_table_bands` → cells equals the grid, per format. **Naming it
a *decoder extension*, moving it under `decode/ext/` and putting its `VERSION`
into every importing decoder's reuse key is [W-288](W-288-decoder-extensions.md)**,
which follows this item so the two never edit the same files at once. Also:

- **A5 Markdown.** `_table_bands` accepts a paragraph as a table when its second
  line is a separator row and every line contains `|`; edge pipes optional
  (author-written Markdown never passes through the extension).

### Stage B — column-aware row passages (a ranking change → L13)

- **B1** `Passage` gains `cells: tuple[tuple[str, str], ...] | None`
  (column, value) and `table: tuple[str, int] | None` (sheet/caption, data-row
  ordinal), filled by `_table_bands`. **Derived in the refer plane, never
  committed** ([L3](../../records/0005_LAW-3-content-never-durable.md)).
- **B2** A row passage is scored on three fields — heading (section/sheet),
  **columns** (header cells), **values** (its own cells) — instead of header
  stuffed into body. Field weight `[ranking] table_column_weight`, shipped so
  that the row's score is byte-identical to today's when the mechanism is off.
- **B3 column selector.** A query term that matches a header cell selects that
  column; the remaining query terms score against the selected cell(s) with the
  passage's own BM25F, and the passage records `columns_matched`. Lexical,
  deterministic, runs only when a header term matched.
- **B4 key column.** The leftmost column whose values are unique within the
  table is the row key; its value folds into the row's heading field.
- **B5 records.** A two-column table, or one whose header is a generic pair
  (`Field|Value`, `Key|Value`, `Property|Value` — a closed list in
  `constants.toml`), is a record: its first column is the selector, B3 applies
  to row labels, and the "header" is not repeated.
- **Node twins:** `node/src/refer/chunk.mjs` and `rescore.mjs` mirror B1–B5;
  the differential harness must agree byte-for-byte.
- **Latency:** per-row work is bounded by today's O(passages) rescore; B3 adds
  work only for rows of tables whose header matched. Re-measure the
  20 000-row sheet (SR-TABULAR's ~2.6 s) and report it as a guardrail.

### Stage C — the answer surface (output only)

- **C1** A row hit renders as a record on the text surface:

  ```
  owners.xlsx#Owners!R438 · current
  Owner: Alice Rao          ← asked
  Ticket: INC6014999
  Status: open
  Opened: 2026-10-02
  ```

  `--json` and MCP `fux_passage` carry `cells`, `table`, `row`,
  `columns_matched`; the Markdown band stays available as `text`.
- **C2** When B3 resolved a column, that cell prints first, marked.
- **C3** Locator for `.xlsx`/`.xlsm`: `path#<sheet>!R<n>` (data row, 1-based,
  header excluded); `.csv`/`.tsv` keep `:L<n>-L<n>`; Markdown/HTML/docx keep the
  line range. [SR-ANSWER](../../records/0105_answer.md) decision 9 amended.

## Measurement — the pre-registration for stage B

- **Test data first** ([SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md),
  T1–T14; [SR-RS](../../records/0133_predictions.md) decision 23): a seeded
  tabular corpus ≤ 10 000 documents with every shape above — sparse xlsx,
  dated columns, title banners, spanned HTML, pipe-less Markdown, `Field|Value`
  sheets, and prose decoys sharing the vocabulary. The golden seed has 46
  Markdown-table documents and HTML tables; it has **no `.csv`/`.xlsx`**.
  Classification: `informed` — same author for corpus and questions. Reuse the
  SR-TABULAR harness (`work/regression/2026-09-06-csv-chunk-granularity/`) and
  its query-set-B shape (common terms, only the combination identifies a row).
- **Shape — [L13](../../records/0015_LAW-13-the-standing-bar.md), parameters only:**
  - **gates** — G0 byte-identical `ask`/`answer` output with the mechanism off;
    size bar: committed index bytes unchanged (nothing is committed).
  - **helps** — target slice: questions whose answer is one cell or row.
    Endpoint: **passage hit@1** (the cited row is the answer row) and
    **cell@1** (the first printed cell is the answer) — paired net clears
    SR-RS decision 19's floor.
  - **limited collateral** — on every non-table question, losses − wins within
    the default margin (3 %, floor 2); expected 0 by construction, measured
    anyway.
  - **net positive** — whole-set net > 0.
  - **guardrails** — p95 `answer` latency on the 20 000-row sheet ≤ 1.2× today;
    `fux ask` document ranking byte-identical (B touches passages only).
  - **Decided arm:** `table_column_weight` at the template value with B3–B5 on,
    as ONE mechanism. Sub-ablations (B2 alone, B3 alone, B4/B5 off) are
    **reported, never decided**. Named here, before any number exists.
- Outcome PASS / INCONCLUSIVE / FAIL by L13's table; INCONCLUSIVE goes to Arpit
  (step 7).

## Definition of done

1. Stage A landed: `decode/_table.py` is the only place a table becomes
   Markdown, the round-trip gate passes, a fixture per defect per format,
   decoder `VERSION`s bumped; A5 in `_table_bands` with a pipe-less fixture.
2. Stage B landed behind the key, G0 proved by a test named for it, Node twins
   agree in the differential harness.
3. Stage C landed: text surface, `--json`, MCP, locator; `fux serve` Answer
   tab shows the record.
4. The tabular corpus seeded and checked against T1–T14; the pre-registration
   frozen and filed under `work/regression/` with the decided arm; the run
   filed with the seven captures ([SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md)).
5. Records amended in the same change (below); `IMPLEMENTATION.md`, WORKLOG,
   the registry rows, GLOSSARY (*column selector*, *record table*, *key column*).
6. The verdict reaches Arpit; PASS ships the template value, FAIL keeps it off
   with a FAILED banner on the decision, INCONCLUSIVE is his.

## Out of scope — named so nobody assumes

- Committed row or cell records (W-236/W-269 precedent); pandas/openpyxl
  (rejected design, [L2](../../records/0004_LAW-2-zero-cost.md) packaging).
- Tables inside PDFs (`pdf.py` is text-only) — its own item if wanted.
- A `fux find --where column=value` filter — a follow-up once B lands.
- `.xls` (OLE2), as SR-TABULAR already states.

## Blockers

None. **The verdict is in** (2026-10-19, decider run by Arpit): FAIL on the
20 000-row latency guardrail (1.74× vs 1.2×) with 59 wins and 0 losses on both
endpoints; the key stays off and SR-REFER decision 28 carries the banner. What
remains is landing stages A–C as built. A faster stage B, decided on a fresh
set, would be its own item if Arpit wants one. W-288 follows this item.

## Record affected

- [SR-TABULAR](../../records/0150_tabular.md) — decisions 1–2 (fields, cells,
  record tables), the `.xlsx` locator. (The extension and header rule are
  W-288's amendments.)
- SR-CHUNKING — `Passage` shape, the universal table rule (A5, B1, B5).
- [SR-DECODE](../../records/0139_decode.md) — A2/A3 fidelity, `VERSION` bumps.
- [SR-REFER](../../records/0127_refer-plane.md) — three-field row scoring, B3.
- [SR-ANSWER](../../records/0105_answer.md) — decisions 9 and 12 (locator,
  record surface).
- [SR-MCP](../../records/0136_mcp.md) — `fux_passage` fields.
- [SR-RS](../../records/0133_predictions.md) — the filed pre-registration.

## Hazards

- **L3:** `cells` exist only on fetched bytes; a test asserts no committed
  shard changes when a table document is ingested with B on.
- **L4:** header detection and record detection are thresholds and closed
  lists in config — no heuristics with hidden constants ([L12](../../records/0014_LAW-12-values-live-in-config.md)).
- **L13:** no number before the pre-registration is frozen; the decided arm is
  the one named above.
- **Scale:** nothing measured or promised above 10 000 documents
  ([SR-WORK-SCALE](../../records/0057_WORK-scale.md)).
- **Twins:** `chunk.mjs`/`rescore.mjs` drift ships `--fast`/scan disagreement;
  the harness is the gate.
- **`_table.py` has no `VERSION` of its own until W-288**: until then every
  edit to it must bump the `VERSION` of html, docx, xlsx AND csv by hand, or an
  existing corpus keeps the old table text until `--full`.
- The row fragment stays available (`text`): an agent that parsed the Markdown
  band must not break.

## Reference

- SR-TABULAR §The measurement — per-row 0.875 vs 0.229; the control that rules
  out short-passage bias.
- *Structure-Aware Chunking for Tabular Data in RAG* (arXiv 2605.00318): row-
  boundary chunks beat recursive splitting on BM25 (R@1 0.754 vs 0.366); naive
  key-value linearisation HURT retrieval — so B keeps rows as the scored unit
  and uses `column: value` for display and field scoring, not as the text.
- *SQuARE: Structured Query & Adaptive Retrieval Engine for Tabular Formats*
  (arXiv 2512.04292) — header-aware retrieval over spreadsheets.
