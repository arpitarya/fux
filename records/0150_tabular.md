---
type: Standing Record
kind: component
name: SR-TABULAR
title: "SR-TABULAR (0150) — a table is a list of rows, and a row is the unit of an answer"
description: "How .csv, .tsv, .xlsx and .xlsm are read and cited: one passage per row, how much of a table is admitted, every value under its true column name (cells by address, number formats, merges, the header found by fill), a row passage that knows its table, and the sheet-and-row citation."
status: accepted
date: 2026-09-06
amended: 2026-10-20
feature: tabular documents — row granularity, the admitted-row limit, the one table emitter, and what a table citation is
owns: [packages/fux-decoder-sheet@446fd8804270, src/fux/decode/ext/limits.py@4fe441b1aa86, packages/fux-extension-table@f43a4ccab57e]
laws: [L2, L3, L4]
timestamp: 2026-09-06T00:00:00Z
content_sha: 1cb18a818deef3e83db95bad8358d964b3cee33819f2e85370f656d9b9ba906f
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`packages/fux-decoder-sheet/`](../packages/fux-decoder-sheet) · dir
- [`packages/fux-extension-table/`](../packages/fux-extension-table) · dir
- [`src/fux/decode/ext/limits.py`](../src/fux/decode/ext/limits.py) · file

<!-- COMPONENTS-END -->

# SR-TABULAR — a table is a list of rows, and a row is the unit of an answer

## §1 — For humans

A spreadsheet is not prose. A paragraph depends on the one above it; **row 41
does not depend on row 40**. So every instinct the engine had about splitting
documents was wrong here, twice over, and both errors were invisible until
someone went looking with a harness.

**The first error was how much of a table fux read at all.** `MAX_ROWS = 500`
was hard-coded in `csv.py` and again in `xlsx.py`. A 754-row file decoded to
500 rows: a fact in row 600 was **not decoded, not indexed, and not citable in
any configuration**, and the only trace was a `*(table truncated)*` line that
nobody diffs. It is now `max_table_rows`, default **20 000** — in
`.fux/tune.toml [index]` since 2026-09-11 (it began in `fux.toml [decode]`).

**The second was how a table was cited.** The chunker split on headings and
blank lines; a table has neither, so a whole sheet arrived as one passage. A
reader asking about one row was handed fifty-eight. Tables are now split **one
passage per row**, header repeated so the columns have names.

The second change was measured before it was made, and the measurement is the
substance of this record — including the fact that the obvious cheap experiment
showed nothing, and would have been reported as "no difference" by anyone who
stopped there.

## §2 — For agents

### Context

`.csv`/`.tsv` decode through `csv.py` into one Markdown table; `.xlsx`/`.xlsm`
through `xlsx.py` into one table per sheet under a `## <sheet name>` heading.
Both then reach `text/chunk.py`, which is what decides a citation.

⚠ **`.xls` is out of scope for this record.** It is the OLE2 compound binary
format, not a zip of XML, and nothing here reads it.

### Decision

**1. One passage per row.** `[refer] table_rows_per_passage = 1` as shipped. Tables are
split at **every size**, not only when a section exceeds the passage ceiling —
`_pieces` used to return early for any section that fitted, so a ten-row table
never reached the split at all.

**2. The header row and its separator are repeated into every passage**, and
this is the one documented exception to the chunker's totality property. Every
*content* byte still lands in exactly one passage. A row whose columns have no
names is a citation nobody can read.

- ⚠ **The repeated header is scored.** Every row of a table carries the
  header's terms, so a table's passages gain a small **uniform** uplift against
  non-table passages in `_rescore`. Uniform within the table, so no row
  outranks another for it.
- **Putting the header in `Passage.heading` instead was measured and scored
  identically** (`hit@1` 0.875 either way). Not taken: `heading` already
  carries the section — the sheet name, for `.xlsx` — and losing that costs
  more than the duplication does.

**3. `max_table_rows`, default 20 000, counting DATA rows** — `.fux/tune.toml
[index] max_table_rows` since 2026-09-11. The
header is always kept and never counted: a consumer who writes 20 000 means
twenty thousand records. Per **sheet** for `.xlsx`, because a sheet is the
document's own division and truncating the fifth because the first four were
long would be arbitrary.

**4. ⚠ REVERSED 2026-09-11 (Arpit): it lives in `.fux/tune.toml [index]`, not
`fux.toml [decode]`.** As shipped, this decision said a row limit changes what is
**indexed**, so it could not be a tunable ([SR-TUNE](0135_tuning.md) decision 7)
and belonged in `fux.toml`. It also added a **fourth** top-level table to
`fux.toml`, which is [SR-CONFIG](0113_config.md)'s veto, unnoticed for five
days. Arpit moved it beside `max_phrases` into tune.toml's `[index]` — the
declared exception to SR-TUNE's boundary rule, SR-TUNE decision 13. What
survives unchanged: it still changes what is indexed, the file is still
committed, and L4 still reads `same sources + same committed [index] -> same
index`. `fux.toml [decode]` is now refused by name.

**4a. A changed limit now reaches an unchanged table.** 🔴 **From 2026-09-06 to
2026-09-11 it did not:** delta ingest reuses extraction keyed on a document's
sha, which the limit does not move, so raising `max_table_rows` left every
unchanged CSV indexed at the old limit until `--full` — and a delta run was no
longer byte-identical to a full one. Ingest now keeps a digest of `[index]` and
re-extracts when it changes ([SR-INGEST](0106_ingest.md)).
`tests/ingest/test_delta.py::test_changing_max_table_rows_is_not_carried_forward`
fails with the digest removed.

**5. A decoder reads it through `decode/ext/limits.py`, and the protocol does not
grow a parameter.** That module is a **decoder extension**
([SR-DECODE](0139_decode.md) decision 24, W-288): its own `VERSION` is in the
reuse key of every decoder whose `USES` names `limits`. A decoder is `EXTENSIONS` plus `decode(raw, rel_path)` and
[SR-DECODE](0139_decode.md) decision 1 is emphatic that this is the whole
interface. But `decode()` at the registry level *does* take a root, so the root
is bound in a `ContextVar` for the duration of one decoder call and read back by
whichever decoder wants it. A `ContextVar` rather than a module global because
nothing here promises to stay single-threaded, and a cross-document bleed that
only appears under concurrency is the worst kind of defect to leave behind.

**6. A malformed `[index]` does not fail the decode.** `max_table_rows()`
falls back to the default rather than raising: a decoder runs inside a walk over
thousands of documents, and `fux ingest` reads `tune.index_limits()` loudly
before any decoder runs, so a bad value has already stopped the run. Turning one
bad line into an unreadable corpus is a worse failure than an ignored setting —
and this is the ONE place that rule applies. (Written for `fux.toml`; the
reader moved on 2026-09-11 and the rule did not.)

**7. A BLANK ROW DOES NOT SPEND THE ROW BUDGET, and an `.xlsx` says when it
truncated** — decision 3's own promise, kept in both files rather than one.

⚠ **`xlsx.py` broke decision 3 for two weeks and nothing noticed.** `_rows`
appended and counted **every `<row>` element**, blank ones included — and a
worksheet carries a phantom blank row for any row that was ever styled, which
on a maintained tracker is most of them. So `max_table_rows` bounded XML
elements, not records: **a budget of 10 delivered 5 data rows** on a sheet with
interleaved phantoms (measured on a 20-row fixture, `20 real + 20 phantom`).
`_ooxml.table_markdown` then dropped the blanks, so the output looked like a
clean short table and **the loss left no trace anywhere**. `csv.py` never had
it — it filters empty rows *before* applying the limit. Two files, one record,
one of them right: the divergence was the defect.

✅ **The two-file story is closed** (W-287 stage A, 2026-10-19; W-288,
2026-10-20). Both rules — blank rows spend nothing, and the two notices — now
live ONCE, in the table decoder extension — `decode/ext/table.py` until
W-289 phase 2, `fux_extension_table.table` in the `fux-extension-table` package
since — which `csv`, `xlsx`, `html` and `docx` all feed (decision 8). `_ooxml.table_markdown` and
every other emitter are gone, so the two copies can no longer disagree. A fix
to that module bumps `constants.toml [extensions.table] version`, and that
version is in the reuse key of every decoder that uses it, so the fix reaches
an existing corpus on the next plain `fux ingest`
([SR-DECODE](0139_decode.md) decision 24).

⚠ **And `xlsx.py` emitted no truncation notice at all.** The `*(table
truncated)*` line this record is rude about — *"the only trace was a `*(table
truncated)*` line that nobody diffs"* — was rude about it because it was the
only trace of a **500-row cap that should not have existed**. The cap is fixed;
the notice is still the right thing, and `csv.py` has kept emitting it the
whole time. `xlsx.py` now emits the same line, plus
`*(columns past 40 dropped)*` for `MAX_COLS`, which had no disclosure in either
file because only `xlsx.py` has a column cap.

The column notice carries a number where the row notice does not. That is not
an inconsistency: a sheet's **width** is a property of the sheet, so the text is
stable, while a row count moves every time the file grows and would make the
indexed text a moving target for no benefit.

<!-- L12-VALUES-START -->

**Where this record's fixed values live — [L12](0014_LAW-12-values-live-in-config.md), W-225, 2026-09-27.**
Each name below keeps its spelling in code and holds no literal: it is read from
[`src/fux/constants.toml`](../src/fux/constants.toml), and a missing key stops the
process naming it ([SR-CONSTANTS](0159_constants.md)). **The values are unchanged** —
this moved where they are written, not what they are.

- `packages/fux-decoder-sheet/src/fux_decoder_sheet/csv.py` (`src/fux/decode/csv.py` until W-289 phase 2) — `VERSION` ← `[decoders.csv] version`, `EXTENSIONS` ← `[decoders.csv] extensions`
- `packages/fux-decoder-sheet/src/fux_decoder_sheet/xlsx.py` (`src/fux/decode/xlsx.py` until W-289 phase 2) — `VERSION` ← `[decoders.xlsx] version`, `EXTENSIONS` ← `[decoders.xlsx] extensions`, `_SHARED` / `_SHEETS` / `_WORKBOOK` ← `[decoders.xlsx.format] shared` / `sheets` / `workbook` ([L12](0014_LAW-12-values-live-in-config.md) decision 6b, R13, 2026-09-28); `_STYLES`, `_DATE_IDS` / `_TIME_IDS` / `_DATETIME_IDS`, the three epochs, `_PHANTOM_LEAP_DAY` and `_SECONDS_PER_DAY` ← `[decoders.xlsx.format] styles` / `date_formats` / `time_formats` / `datetime_formats` / `epoch_1900` / `epoch_1900_early` / `epoch_1904` / `phantom_leap_day` / `seconds_per_day` (W-287, 2026-10-19)

<!-- L12-VALUES-END -->

**8. Every value sits under its TRUE column name** (W-287 stage A, 2026-10-19).
Every rule below lives ONCE, in the table decoder extension (`fux_extension_table.table` since W-289 phase 2; `decode/ext/table.py` before), which all four table
formats feed ([SR-DECODE](0139_decode.md) decision 23); the bullets say what
each rule is.

- **An `.xlsx` cell is placed by its address.** Excel omits an empty cell, so a
  row whose second cell is blank stores two `<c>` elements; appending them in
  XML order put the third column's value under the second column's name. Each
  cell is placed by its `r="C7"` column; a gap is an empty cell; a column empty
  in every row is dropped (it names nothing and holds nothing).
- **A number is read through its format.** `styles.xml`'s `cellXfs` →
  `numFmtId`: a date reads `2026-07-11`, a time `14:30`, both `2026-07-11
  14:30`; a boolean `true`/`false`; any other number its shortest decimal. The
  built-in date ids and the epochs are ECMA-376's, in `constants.toml
  [decoders.xlsx.format]`; the 1900 system's phantom leap day (serial 60) stays a
  number, because it is a date that never existed.
- **A merged cell repeats its anchor's value** into every cell of the span that
  the sheet holds a row for.
- **The header is the first row whose source-filled cells reach
  `[limits.<decoder>] header_fill_percent` of the table's width**
  (`.fux/formats.toml`, shipped `60`, for `xlsx` and for an HTML table with no
  `<th>`; `decode/ext/table.py::_header_index`). Rows above it — a title banner — are prose under
  the sheet heading, so their words are no one's column name. *Filled in the
  source*: a merged banner fills one cell, not five. At `1` the first row is the
  header, as before.
  ⚠ **It is a decoder cap, not an `[index]` key, and the work item said
  `[index]`.** The index is a bag of terms: a banner's words are the same body
  terms whether they head the columns or sit above them, so the threshold moves
  **no committed byte** — measured: `test_an_index_key_does_change_the_index`
  stayed red with a banner table in its corpus. [SR-TUNE](0135_tuning.md)
  decision 1's rule therefore refuses it from `[index]`, whose exception exists
  for keys that DO change the index. What it changes is which words a ROW
  PASSAGE repeats as its column names, and it sits in the extract-config digest
  with every other cap.
- **The row budget counts data rows below the header** (decision 3); a banner
  spends none of it. Every row is read before the budget is applied, because
  the header cannot be known until the table's width is; the sheet's XML is
  already wholly parsed, so this costs no more than the parse.

**9. A row passage knows its table — on fetched bytes, never committed** (W-287
stage B, 2026-10-19). Each one-row passage carries a `TableRow`
([SR-CHUNKING](0151_chunking.md)): its columns, its cells, its data-row
ordinal, its KEY column — the leftmost whose values are filled and distinct in
every row — and whether the table is a **record**: two columns under a generic
header (`Field | Value`, a closed list in `constants.toml [tables]`), where each
row's first cell is its field name and, when the names are distinct, its key.
**How a row is scored on it is [SR-REFER](0127_refer-plane.md) decision 28's**,
behind `[ranking] table_column_weight`, shipped `0.0` — its L13 run FAILED on
the 20 000-row latency guardrail (1.74×) with 59 wins and 0 losses, so it stays
off. Nothing of it is written anywhere (L3):
`tests_e2e/test_table_answers.py::test_the_mechanism_writes_nothing_to_the_index`.

**10. A spreadsheet row is cited `book.xlsx#Sheet!R12`** — the sheet and the
data row, from 1, header not counted ([SR-ANSWER](0105_answer.md) decision 9).
The decoded Markdown's line numbers exist nowhere, and `#p12` names nothing a
person can open. `.csv`/`.tsv` keep `owners.csv:L438-L438`, which a person can.
⚠ **The address is presentation, and it may not move an order**: ties are broken
on the positional locator (`path#p12`), never this one. The first form broke
them on this string and reordered tied rows with the ranking key off — found by
the run's G0 gate, `work/regression/2026-10-19-w287-table-columns/`.

### The measurement

`work/regression/2026-09-06-csv-chunk-granularity/`. Seeded corpus
`sha256[:16] = 29cb743d8dfe252b`, 12 files, 6 998 rows.

⚠ **Classification: `informed`** — the same author wrote the corpus generator
and the queries — so under RUN-CLASSIFICATION it **supplies no delta** and this
decision does not claim one. TEST-PLAN §0a: a number is not a grade.

**Query set B — 48 queries where every term is common and only the combination
identifies a row.** This is the realistic shape.

| rows per passage | hit@1 | hit@3 | MRR | bytes returned | p95 ms |
|---|---|---|---|---|---|
| 58 | 0.229 | 0.229 | 0.229 | 6 094 | 42 |
| 11 | 0.292 | 0.458 | 0.382 | 5 412 | 49 |
| **1** | **0.875** | **1.000** | **0.934** | **946** | **109** |

**hit@1 by ambiguity** (cohort = rows sharing all three common terms):

| cohort | n | 58 rows | 11 rows | 1 row |
|---|---|---|---|---|
| 1 | 3 | 0.333 | 1.000 | **1.000** |
| 2 | 17 | 0.235 | 0.294 | **0.941** |
| 3 | 13 | 0.231 | 0.077 | **0.923** |
| 4+ | 15 | 0.200 | 0.333 | **0.733** |

Per-row leads at every cohort and degrades gracefully at 4+, where four or
more rows genuinely match all three terms and no ranker can always put the
right one first. The 58-row arm is at or below 0.333 throughout.

🔴 **The obvious experiment shows nothing, and this is the part worth
remembering.** Query set A planted a unique token in the target row. All three
arms score `hit@1 = 1.000`. A run that stopped at set A would have reported "no
difference" and been wrong.

**The win is not short-passage bias.** Control: score the correct row against
decoy rows sharing 3 of 4 query terms, every candidate the same size so length
cannot do the work. The correct row outranks the next-best in **42/48
(0.875)**.

**`MAX_CELL_CHARS` and `MAX_COLS` are `[limits.csv] max_cell_chars` and `[limits.xlsx] max_cols`** ([L12](0014_LAW-12-values-live-in-config.md) decision 9b, W-225 stage 4a, 2026-09-27), read through `_limits.limit()` like `max_table_rows`; the values and the notices are unchanged ([SR-DECODE](0139_decode.md)).

### Consequences

- **Both decoders declare a `VERSION`, and it is in the reuse key** (2026-09-14,
  W-166, [SR-DECODE](0139_decode.md) decision 11a). A change to how a table
  becomes text — the cell cap, the truncation notice, the separator sniff — moves
  no document's bytes, so before this it reached an existing corpus only on
  `fux ingest --full`. **Bump `VERSION` in the same change**, and the next ingest
  re-extracts the `.csv`/`.tsv` or `.xlsx`/`.xlsm` documents and nothing else.

  ⚠ **A decoder's blast radius is every extension it claims**, not the one in
  front of you: `csv.py` binds `.csv` *and* `.tsv`, `xlsx.py` binds `.xlsx` *and*
  `.xlsm`. Pinned by `tests/decode/test_decoder_versions.py`, which checks a
  multi-extension decoder for exactly that reason.

- 🔴 **Query latency is the price, and it was accepted with the number in
  hand.** `rescore` is O(passages), and a table now yields one passage per row:

  | rows | passages | chunk | rescore + assemble |
  |---|---|---|---|
  | 500 | 500 | 0.9 ms | 63 ms |
  | 5 000 | 5 000 | 9.7 ms | 654 ms |
  | 20 000 | 20 000 | 39.2 ms | **~2.6 s** (2 498 / 2 596 / 2 780 over three repeats) |

  At the 20 000 default a single large sheet costs roughly two and a half
  seconds per document per query; a multi-document `ask --refer` multiplies
  it. **Ruled by Arpit
  2026-09-06** over the alternative of degrading to bands past a threshold.
  `.fux/tune.toml [index] max_table_rows` is the lever a consumer with big
  sheets turns — and, unlike every other tune.toml key, turning it re-extracts.
  Latency is Linux x86_64 and not comparable across machines (TEST-PLAN §2).

- **A token pre-filter does not rescue it.** Dropping passages that share no
  token with the query removes only ~40 % on a realistic table, because rows
  share vocabulary — and the repeated header (decision 2) means every row
  matches any query mentioning a column name.

- **A table citation is now `owners.csv:L438-L438`** — one row, openable.

- ⚠ **Raising the row limit is also an index-size change**, not only a latency
  one. Twenty thousand rows of a spreadsheet is a great many tokens, and
  [SR-TYPES](0128_types-list.md) verdict G is exactly about datasets inflating
  a corpus. `.csv` is still not in `DEFAULT_TYPES`; a consumer opts in.

### Alternatives considered

- **Keep byte-sized bands (900 bytes, ~11 rows).** Rejected on the numbers:
  `hit@1` 0.292 against 0.875.
- **Degrade to bands past a row threshold.** The recommended option, and
  **declined by Arpit** in favour of per-row at every size with the latency
  stated. Recorded because it is the first thing to reach for if the ~2.6 s
  ever becomes a complaint.
- **Header in `Passage.heading`.** Scored identically; costs the sheet name.
- **Leave `MAX_ROWS` at 500.** It was never a decision, only a constant, and it
  silently dropped data.

### Reference (required)

```bash
# the limit is data rows, header always kept
python -c "
from fux.decode import decode
rows = b'col\n' + b''.join(b'value %d\n' % i for i in range(50))
print(decode(rows, 'a.csv', __import__('pathlib').Path('.')).count(chr(10) + '| value '))"
# expect: 50 with the default; the configured number when .fux/tune.toml [index] sets one

# one passage per row
python -c "
from fux.decode import decode
from fux.text.chunk import chunk
md = decode(b'a,b\n1,2\n3,4\n5,6\n', 'x.csv')
print(len(chunk(md)))"
# expect: 3
```

### Veto condition

**If a corpus of ordinary spreadsheets shows per-row citation scoring no better
than an 11-row band on a `blind` run, decision 1 loses its evidence** — the
measurement behind it is `informed` and supplies no delta.

⚠ **Arpit ruled 2026-09-11 to keep the current evidence.** Decision 1 stands on
his ruling and the `informed` run; **no `blind` run is owed** and none is queued.
The condition above is unchanged: it is checked if a `blind` spreadsheet run is
ever filed, and it is not a reason to file one.

**If the ~2.6 s at 20 000 rows is reported as a blocker by anyone actually
using it**, the declined alternative above is the answer, and it is one
constant.

⚠ **Both of these said `3.7 s` until 2026-09-11, while the table in §1 above
said `~2.6 s`.** 3.7 s was a single unrepeated observation; the table's figure
is the median of three repeats (2 498 / 2 596 / 2 780 ms) and was corrected on
2026-09-06 in `fux.toml`, `setup.py` and `_chunk.py` — **and missed here, in
the veto condition, which is the one place a wrong number changes what somebody
does.** Found by re-reading the record rather than by any check.

## References

- [SR-DECODE](0139_decode.md) — the decoder protocol decision 5 keeps intact
- [SR-REFER](0127_refer-plane.md) decisions 25–26 — the chunker this rests on
- [SR-TUNE](0135_tuning.md) decision 7 — why this is config and not a knob
- [SR-TYPES](0128_types-list.md) — verdict G, and why `.csv` is opt-in
- [`work/regression/2026-09-06-csv-chunk-granularity/report.md`](../work/regression/2026-09-06-csv-chunk-granularity/report.md) — the run

**Papers and specifications** *(consulted 2026-09-06, filed 2026-09-11)*

- **Chroma, *Evaluating Chunking Strategies for Retrieval*** — independent
  corroboration of decision 1's direction. On token-level metrics, 200-token
  chunks scored **8.0 precision and IoU against 1.5 at 800 tokens, with recall
  roughly flat**: smaller passages bought precision and cost almost no recall,
  which is the shape of this record's 0.229 → 0.875.
  <https://www.trychroma.com/research/evaluating-chunking>

  🔴 **This does NOT discharge the veto condition above.** It is a different
  corpus, and its retrieval is embedding-based where fux's is lexical BM25F, so
  it agrees about the *direction* and predicts nothing about the magnitudes
  here. The bar stays what it was: per-row beating an 11-row band on a `blind`
  run. **An outside paper agreeing with an `informed` run does not make it a
  blind one**, and treating it that way is how a pre-registered threshold moves
  without anybody deciding to move it.
