---
type: Pre-registration
description: "The frozen bar for W-287 stage B: table_column_weight = 1.0 with the column selector, key column and record tables on (B2-B5 as ONE mechanism), on a seeded 102-question tabular set under law L13 with its defaults mapped onto passages — gates G0 (off = the engine without row metadata) and G1 (no committed byte moves), slice = the 83 table questions (>= 15 winnable per endpoint), C1 on passage hit@1 AND cell@1 by SR-RS d19, C2 by L13's default margin on the 19 prose questions, C3 net > 0, six guardrails. Decided arm tc-1.0; four ablations reported only. Frozen before any arm exists; decider run by a hand that did not capture."
run: 2026-10-19-w287-table-columns
item: W-287
filed: 2026-10-19
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — tables by row and by column (W-287 stage B)

## What is being asked

**When a question's answer is one row of a table, does scoring the row on three
fields — its section and key value, its column names, its cells — with a query
word that names a column selecting that column's cell, cite the right row first
and print the asked cell first, without costing the prose questions beside it?**
One value is decided, named here: `[ranking] table_column_weight = 1.0`, with
B3 (the selector), B4 (the key column) and B5 (record tables) on, as ONE
mechanism ([W-287](../../open/W-287-tables-by-row-and-column.md) §Measurement).

## The bar: **L13, defaults** — mapped onto a passage endpoint, tightened once

[Law L13](../../../records/0015_LAW-13-the-standing-bar.md). This run fills in
the parameters, **tightens C1 to two endpoints** (the work item's own wording,
ratified by Arpit 2026-10-19: *"passage hit@1 … and cell@1 … — paired net
clears SR-RS decision 19's floor"*), and loosens nothing.

| L13 row | this run |
|---|---|
| **G · gates** | **G0** — at `tc-0.0`, every question's cited passages equal the engine **without row metadata** (`chunk._row_meta` returning `None`, so no `TableRow` exists and nothing of B is reachable) on document, ordinal, heading, text and score, compared per run of equal scores (`evidence/g0.py`, which states the two exclusions and why). **G1** — the size bar: every arm's committed index is byte-identical (`capture.py` records each arm's digest). **Slice floor** — at `tc-0.0`, at least **15** slice questions miss each endpoint; below it the run STOPS before any arm is read |
| **C1 · helps** | on the slice, the paired net at `tc-1.0` against `tc-0.0` clears [SR-RS](../../../records/0133_predictions.md) decision 19 at the observed flips, by [`verdict.py`](../../../tools/quality-controls/verdict.py)'s `rule`, **on BOTH endpoints**: `hit1` and `cell1` (below) |
| **C2 · collateral** | on the 19 questions outside the slice, `hit1` losses − wins ≤ `max(2, ⌊0.03 × 19⌋)` = **2** |
| **C3 · net** | the whole-set paired `hit1` net is above 0 |
| **GR · guardrails** | below — every one must hold |
| **arms** | **decided: `tc-1.0`**. Reported only: `tc-1.0-noB3`, `tc-1.0-noB4`, `tc-1.0-noB5`, `tc-1.0-B2` |
| **data** | a fresh set: no mechanism has been decided on it, or on any tabular set |

### The endpoints, defined now

- **`hit1`** — the TOP cited passage is the answer. A table question: the
  passage is in the answer document, is a table row (`cells` present), its
  `row` is the answer's data-row ordinal, its cells hold the answer's key value,
  and — in `services.xlsx`, the one document with several tables — its `table`
  is the answer's sheet. A prose question: the passage is in the answer document
  and its text holds the answer phrase.
- **`cell1`** (slice only) — `hit1`, **and** the first cell `fux answer` prints
  for that row is the asked column: `Citation.record`'s order, the cells the
  query's columns named first, then the rest, empty cells left out. The asked
  column is the question's `column_index` into the row's own header, so a
  combined HTML header (`Detail Owner`) is matched by position, not by spelling.
- Why two: `hit1` is the ranking claim; `cell1` is what the work item exists
  for (*"it should give me just that row … what is the column name"*), and it
  cannot be met by ranking alone.

### Guardrails — L13 decision 3's four, mapped; the work item's two, added

| guardrail | limit | from |
|---|---|---|
| passage `hit5` (the answer among the first five citations) | falls by at most **1** | L13 `hit@5` |
| `quoted` — the answer among ALL citations `answer` seats | falls by at most **2** | L13 `section@1`: whether the answer is quoted at all |
| `grounded` band count (`fux answer --band`) | falls by at most **2** | L13 `grounded` |
| `fux ask` median at `rung-10000`, decided − baseline | at most **100 ms**, three interleaved runs, standalone | L13 latency |
| `fux ask` output | **byte-identical** on every question, both arms | work item: B touches passages only |
| `fux answer` p95 on a 20 000-row sheet, decided ÷ baseline | at most **1.2** | work item: SR-TABULAR's ~2.6 s case |

⚠ **How each L13 guardrail is mapped is a reading, stated so it can be
challenged.** L13 decision 3 names golden-set measures; this run has no golden
set, because a table question needs `.csv`/`.xlsx` documents and the golden seed
has none (W-287 §Measurement). Each mapping keeps the measure's question and
its limit. `ask` latency is measured on the golden ladder's `rung-10000`, as the
law says, with **this run's** question text — never a golden question, so no
golden file is opened.

## The outcome table — L13 decision 4, verbatim in `decide.py`

| outcome | condition |
|---|---|
| **STOP** | G0, G1 or the slice floor fails |
| **PASS** | C1 (both endpoints), C2, C3 and every guardrail hold at `tc-1.0` |
| **INCONCLUSIVE** → Arpit | C1, C3 and the guardrails hold and C2 misses by 1 or 2; or C2, C3 and the guardrails hold and both slice nets are positive but C1 is not met |
| **FAIL: drift** | C2 misses by more than 2, or C3 fails |
| **FAIL: no gain** | a slice net is 0 or below |
| **FAIL: guardrail** | a guardrail fails and no row above applies |

**PASS ships `table_column_weight = 1.0` as the template value** and nothing
else; FAIL keeps it at `0.0` with a FAILED banner on SR-REFER's decision;
INCONCLUSIVE is Arpit's (W-287 step 7). A reported ablation that would also have
passed is a lead for a new run, never a default.

## The data — [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md)

`evidence/corpus.py`, seed 287 — **regenerated twice, byte-identical**. 25
documents; 102 questions: **F1** 40 key lookups naming a column, **F3** 16
column filters, **F2** 12 combinations (SR-TABULAR's set B shape), **F4** 15
record-field lookups, **P** 19 prose. Slice = F1–F4, 83.

| T row | carried? |
|---|---|
| **T1** the input | **yes** — sparse/dated/bannered `.xlsx`, `<thead>`/`colspan`/`rowspan`/`<caption>` HTML, a pipe-less GFM table, a `vMerge` `.docx`, `Field \| Value` sheets in `.md` and `.xlsx`, key columns, column words in the questions |
| **T2** a coverage tag | **yes** — `family` and `slice` per question |
| **T3** headroom by construction | **yes** — every F1/F3/F4 question has a decoy row built to out-count the answer row on the query's terms; `construction` records the counts, and `corpus.py` re-checks every one on the final rows and fails if any no longer holds. **Never by ranking**: no arm has run |
| T4–T11, T15 | **not carried** — anchor text, abbreviations, identifiers of the failing shape, links, supersession, unanswerables, heading distractors, git history and enrichment are other features' inputs; this run measures none of them |
| **T12** additions only | n/a — a new generated corpus, not the golden seed |
| **T13** custody | **not a golden set**: the answers come from the generator, as in SR-TABULAR's run, so [L11](../../../records/0013_LAW-11-sealed-answer-key.md) does not reach them. `informed` (below) |
| **T14** ≤ 10 000 documents | **yes** — 25 (and `rung-10000` for latency only) |

## Classification — `informed`

| artifact | author | could reach |
|---|---|---|
| the engine (stages A–C) | Claude Code, this session | everything below |
| `corpus.py`, `questions.jsonl` | Claude Code, this session | the mechanism it was about to be asked to show |
| `capture.py`, `g0.py`, `latency.py`, `decide.py`, this file | Claude Code, this session | both of the above |

**One session wrote the engine, the data, the instrument and the bar.** Under
[SR-RS](../../../records/0133_predictions.md) the result is `informed`,
permanently: a measurement of a mechanism on data built so it can move, not an
estimate of fux on tables nobody wrote for it.

⚠ **The build exists before this bar, and that departs from L13 decision 4's
order** (*the decider is frozen before any build code exists*). Stages A–C were
built first in this session, tested only on unit fixtures, a two-question smoke
run of the harness on throwaway questions that are not in this set, and the
construction checks in `corpus.py`. **No arm has been captured on this set and
no endpoint has been computed on any data.** One design change was made after
the corpus's construction arithmetic was worked and before any arm: a record
table's field-name column became its key (B4 over B5), because by the counts a
record row named once could not beat a value saying the field twice — stated
here so a reader can weigh it.

## Procedure

1. `corpus.py ~/my_programs/fux-lab/w287-tables/base/repo` (done; hashes
   below), `fux.setup.fill_missing`, sources `docs`.
2. `capture.py --env ~/my_programs/fux-lab/w287-tables --questions
   evidence/questions.jsonl --out evidence/captures` — six arm copies, each
   ingested `--full` with this engine; no score computed.
3. `g0.py --repo …/arms/tc-0.0/repo --questions evidence/questions.jsonl >
   evidence/g0.json`.
4. `latency.py --prepare`, then `latency.py > evidence/latency.json`,
   standalone, nothing else of this run in flight.
5. **A hand that did not run 1–4** runs `decide.py --questions
   evidence/questions.jsonl --captures evidence/captures --g0 evidence/g0.json
   --latency evidence/latency.json > evidence/decision.json`, and the verdict
   is filed from it as `VERDICT.md`.

## What this run may NOT do

1. Move any number above ([SR-RS](../../../records/0133_predictions.md) d10b).
2. Decide an ablation, or name any value but 1.0 a default.
3. Change the corpus, the questions or any frozen script after this file.
4. Be adjudicated by the session that captured the arms.
5. Proceed past a STOP.
6. Open a golden file of any kind: no question set, no key, no `score.py`.
7. Re-ingest the golden ladder in place; every rung is a copy.

## Freeze

| | sha256 |
|---|---|
| `evidence/corpus.py` | `b6a0dccbb69ad7ce537fcca41a2568eeccf5271f3bc939d435c0b350097718e6` |
| `evidence/questions.jsonl` (102 lines) | `1adcc79c109b1f7c29879aefe1801effd445e68a0aaf90361cf0674b539cf0dd` |
| `evidence/capture.py` | `16c385a6c47d04953cf5acff0c0585658541e53332a0f1d5600833405a989c17` |
| `evidence/g0.py` | `ec21c401238f1967838438f88d567440e2f801408bfc688bfccd36c2d46fe495` |
| `evidence/latency.py` | `068bdead39647e8fce0014189697afd315024cf391f65c8d138c0383d2d4b406` |
| `evidence/decide.py` | `bd38f62096c3eb668af2d023adbebb2e551abd6f4fce19973922a97471a335ea` |
| `tools/quality-controls/verdict.py` | `8839fb19809bcf75344c7033c844a64a5a90bf446b80937b08cb01138a458e9a` |
| `tools/quality-controls/resolution.py` | `07e283e4404c16a14f9c3e1f4911908efdd095ff2ff549c7aed95b8c158ee76c` |
| the corpus — `corpus-sha256.txt` (every file's sha256) | `3dbf85d6cd788b279805269e062edec0e7916eeec01b54fc1a01ef7a04941aaf` |
| the engine — every file under `src/fux/`, path + bytes | `aa13bc6239db36b3ea76c261c7675a634ce27ffcec5918e62a48512987c4bdcb` (the working tree on `896382fb`, **uncommitted**) |
| scores on this set | **none exist** |

⚠ **Frozen by hash, not by commit.** This session was not asked to commit, so
the freeze is these hashes in the working tree; a reader checks them with
`shasum -a 256`. The commit that lands W-287 carries this file unchanged.

## STOP 1 — G0, and the engine re-frozen (2026-10-19, same session, before any endpoint)

**G0 failed on 2 of 102 questions**, so the first capture STOPPED, as the table
above says it must. It was a **build defect**, not a verdict: `rescore` and
`assemble` broke equal scores on the *displayed* locator, and C3 had changed
that string for a spreadsheet row (`#p12` → `#Incidents!R13`), so rows scoring
identically were reordered — and where the budget cut a tie, a different row was
cited — with the key **off**. Both questions (`w287-075`, `w287-079`) differ only
inside a tie group the budget truncated; every score and every score-order is
identical (`evidence/stop-1/g0.json`).

- **The fix:** ties break on the positional `order_key` (`path:L…` / `path#pN`)
  in both runtimes; the displayed locator is untouched.
  `tests/refer/test_table_columns.py::test_c3_a_sheet_locator_moves_no_order_among_tied_rows`
  pins it.
- **What did not change:** this bar, the corpus, the questions, and every
  frozen script — their hashes above still hold. **Only the engine moved:**
  `src/fux/` digest **`daabfe4c2c48f44123f4349d68b9c56e32939bd45cb4c7ff3f9e98bcf73543e4`**.
- **What was seen:** the G1 digests and the two G0 rows, both gates. **No
  endpoint was computed on the stopped capture, and `decide.py` was not run.**
  The stopped capture is kept unscored in `evidence/stop-1/` and is read by
  nothing.
- The capture is re-run from step 2 on the re-frozen engine.

## Engine re-frozen 2 — stage A to one table module (2026-10-19, before any endpoint)

At 19:45 Arpit's Cowork session corrected W-287: stage A is **one shared table
module**, `decode/_table.py`, that xlsx, HTML, docx and csv feed as grid
parsers ([SR-DECODE](../../../records/0139_decode.md) decision 23). The capture
above ran on per-decoder stage A. The engine was refactored to the ratified
shape, **behaviour-neutral by construction and by measurement**:

- every tracked Markdown, HTML, `.docx` and `.xlsx` file in the repo decodes and
  chunks byte-identically to the per-decoder stage A;
- all six arms re-captured on the refactored engine are **identical, field for
  field, to the capture they replace** (timing excepted); the index digests
  differ only because `REGISTER` records `csv@2`, and every arm of the new
  capture shares one digest (G1);
- **G0** on the new capture: 0 of 102 differ, 0 tie reorders.

The replaced capture and its gates are kept in `evidence/superseded-engine-2/`,
unscored. **The engine:** `src/fux/` digest
**`d942320c21944af501da3701b2920efe1c2117bdcb8a77035a8f175dbbffa009`**; latency
is re-measured on it. The bar, the data and every frozen script are unchanged.
**Still no endpoint computed, and `decide.py` not run.**

## Filing note — paths only (2026-10-19)

The per-run contract (`tests/test_regression_runs.py`) holds every `.jsonl`
under `evidence/` to be per-query result rows, and a question set is not one
(SR-RS decision 21b). So, with **no byte of content changed**:

- `evidence/questions.jsonl` → **`questions.jsonl`** at the run root — sha256
  still `1adcc79c109b1f7c29879aefe1801effd445e68a0aaf90361cf0674b539cf0dd`; the
  decider is run with `--questions ../questions.jsonl`.
- every capture row gains `"arm": "<its file's arm>"`, the label its file name
  already carried. `decide.py` reads neither. The raw files' sha256, before the
  label, are in `evidence/captures-raw-sha256.txt`.
