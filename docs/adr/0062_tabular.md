---
type: ADR
name: ADR-TABULAR
title: "ADR-TABULAR (0062) — a table is a list of rows, and a row is the unit of an answer"
description: "How .csv, .tsv, .xlsx and .xlsm are read and cited: one passage per row, how much of a table is admitted, and the two silent data losses this record was written to close."
status: accepted
date: 2026-09-06
amended: 2026-09-11
feature: tabular documents — row granularity, the admitted-row limit, and what a table citation is
owns: [src/fux/decode/csv.py, src/fux/decode/xlsx.py, src/fux/decode/_limits.py]
laws: [L1, L2, L3]
timestamp: 2026-09-06T00:00:00Z
---

# ADR-TABULAR — a table is a list of rows, and a row is the unit of an answer

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
Both then reach `refer/_chunk.py`, which is what decides a citation.

⚠ **`.xls` is out of scope for this record.** It is the OLE2 compound binary
format, not a zip of XML, and nothing here reads it.

### Decision

**1. One passage per row.** `_chunk.TABLE_ROWS_PER_PASSAGE = 1`. Tables are
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
**indexed**, so it could not be a tunable ([ADR-TUNE](0045_tuning.md) decision 7)
and belonged in `fux.toml`. It also added a **fourth** top-level table to
`fux.toml`, which is [ADR-CONFIG](0023_config.md)'s veto, unnoticed for five
days. Arpit moved it beside `max_phrases` into tune.toml's `[index]` — the
declared exception to ADR-TUNE's boundary rule, ADR-TUNE decision 13. What
survives unchanged: it still changes what is indexed, the file is still
committed, and L3 still reads `same sources + same committed [index] -> same
index`. `fux.toml [decode]` is now refused by name.

**4a. A changed limit now reaches an unchanged table.** 🔴 **From 2026-09-06 to
2026-09-11 it did not:** delta ingest reuses extraction keyed on a document's
sha, which the limit does not move, so raising `max_table_rows` left every
unchanged CSV indexed at the old limit until `--full` — and a delta run was no
longer byte-identical to a full one. Ingest now keeps a digest of `[index]` and
re-extracts when it changes ([ADR-INGEST](0016_ingest.md)).
`tests/ingest/test_delta.py::test_changing_max_table_rows_is_not_carried_forward`
fails with the digest removed.

**5. A decoder reads it through `decode/_limits.py`, and the protocol does not
grow a parameter.** A decoder is `EXTENSIONS` plus `decode(raw, rel_path)` and
[ADR-DECODE](0049_decode.md) decision 1 is emphatic that this is the whole
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

### Consequences

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
  [ADR-TYPES](0038_types-list.md) verdict G is exactly about datasets inflating
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
from fux.refer._chunk import chunk
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

- [ADR-DECODE](0049_decode.md) — the decoder protocol decision 5 keeps intact
- [ADR-REFER](0037_refer-plane.md) decisions 25–26 — the chunker this rests on
- [ADR-TUNE](0045_tuning.md) decision 7 — why this is config and not a knob
- [ADR-TYPES](0038_types-list.md) — verdict G, and why `.csv` is opt-in
- [`work/regression/2026-09-06-csv-chunk-granularity/report.md`](../../work/regression/2026-09-06-csv-chunk-granularity/report.md) — the run

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
