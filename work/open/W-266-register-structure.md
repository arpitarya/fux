---
type: Handoff
name: W-266
description: "Arpit's ask (2026-10-04): a better structure for `.fux/index/REGISTER`, the committed register of what the index holds. Research found five defects in today's five-column TSV (positional columns that make any new field a silent total read failure, a `-` sentinel, a near-constant `kind` column, two grammars in the `decoder` column, no format marker, no grouping by source). This item: a compare doc of the candidate shapes, one 🔴 row for Arpit to pick, then the build. Ratified, not built."
item: W-266
filed: 2026-10-04
ball: agent
---

# W-266 — a better structure for the register

**Status: filed 2026-10-04, not started. Ratified, not built.** The research
below is this session's; the compare doc, the ruling and the build are the
item.

**Arpit, 2026-10-04 (Cowork):** *"Can we have a better structure for the
register? Register being the file inside the `.fux` directory. Create that as a
work item."*

**What the register is.** `.fux/index/REGISTER` — one tab-separated line per
document in the index, sorted by `loc`, committed beside the shards it
describes. Arpit asked for it on 2026-09-20 (W-199 D4: *"a log file should be
generated of every document that is indexed … today there is nowhere we document
what files and URLs were ingested"*). It is decided in
[SR-INGEST](../../records/0106_ingest.md) decision 22 (+22a, 22b), written by
[`src/fux/ingest/register.py`](../../src/fux/ingest/register.py) from
[`run.py::_record_register`](../../src/fux/ingest/run.py), read only by
[`doctor.py::_register`](../../src/fux/doctor.py) (drift against the index).
The Node reader does not read it. Its three load-bearing laws: **L4** (sorted,
no clock, no run id — byte-identical across runs from the same sources),
**L3** (paths and hashes, never content), **not L9** (it names what the corpus
is, never who asked — and must never grow a question/query/reader field).

**Model:** **Cowork** (the `research` section, SR-WORK-OPEN-QUEUE rule 37a) — the
compare doc and the 🔴 row are this item; the build is a *separate* item, filed
for Claude Code (**Opus**) once Arpit has picked a shape.

## What is wrong with the shape today (the evidence)

The file on this repo, 2026-10-04: 2 177 lines, header
`# loc	kind	sha	decoder	fetcher`.

1. **Positional columns, and a new column is a silent total failure.**
   `register.read()` does `loc, kind, sha, decoder, fetcher = line.split("\t")`
   and `continue`s on a `ValueError` — so a register with a sixth column reads
   as `{}` for **every** row, and `fux doctor` then says *"no REGISTER beside an
   index of N documents"*. The shape cannot grow by one field without breaking
   its one reader, and it breaks by saying the wrong thing.
2. **`kind` carries almost no information.** 2 176 of 2 176 rows say `file`;
   the one `url` value this column exists for is `src == "url"`, already on the
   record, and visible from the `loc` itself (`https://…`). It is the column that
   replaced the ruling's `outcome` (which could not survive L4 — d22's own
   note), and it replaced it with a near-constant.
3. **Two grammars in one column.** `decoder` is a bare name for the built-in
   (`prose`) and `name@sha:<16 hex>` for everything else
   (`html@sha:773b7cb1d9a7be6e`). A reader that wants *"which decoder"* must
   special-case the built-in; a reader that wants *"did the decoder change"*
   gets no digest for the one decoder most rows use.
4. **A `-` sentinel for "no fetcher"**, documented in code as *"absent and
   unknown are different, and this says which"* — but every file row carries it
   (files have no fetcher by definition), so the sentinel marks a structural
   non-field 99.95 % of the time and an unknown 0 % of the time on this repo.
5. **No format marker.** The index's first line says `fux.index.v7`; the
   register's header is a column list with no version, so a reader cannot tell
   a v1 register from a v2 one except by column count — which is defect 1 again.
6. **No grouping by what produced the rows.** The human question the file was
   asked for — *"what files and URLs were ingested"* — is per source-list entry
   (which `dirs` line, which URL line), and the file is 2 177 alphabetical rows
   with no section per source. Alphabetical-by-`loc` happens to cluster
   directories, which is why it is readable at all today.

**Also absent, and already on the record, deterministic and L3-clean:**
`archived` (a declared fact about the source list), `mode` (`extracted`),
`src` (`git` / `url` / `file`), the field lengths (`flen`) as a size column.
**Deliberately NOT a candidate:** titles — display text on a committed path is
L3's edge and the register's whole licence to be committed is paths-and-hashes
(d22); **and anything run-shaped** — `outcome`, timestamps, run ids (L4; d22's
own `outcome` story).

## The candidate shapes (for the compare doc — not decided here)

| | shape | growth-safe (1) | human (6) | L4 | one reader, no module | cost |
|---|---|---|---|---|---|---|
| **S1** | **TSV v2 with a format line and a key=value tail**: `# fux.register.v2` + `loc  sha  decoder@digest  k=v k=v…` — the grammar [`.fux/sources/urls`](../../.fux/sources/urls) already uses (`fetch=`, `decoder=`, `archived=`), so the two committed line formats read the same way. Optional fields appear only when they hold a value (no sentinel); the built-in decoder gets a digest like every other | ✓ tail is additive | ✓ | ✓ sorted by `loc` | ✓ `split` + `partition("=")` | small — `register.py` render/read, `doctor.py` untouched |
| **S2** | **S1, grouped by source entry**: a `## <dirs line or URL>` section per source-list entry, rows sorted within. Reads as a table of contents | ✓ | ✓✓ | ✓ if sections sort by entry | ✓ | medium — the writer needs each record's source entry; `sourcelist` has it |
| **S3** | **JSONL**, one object per document, same shape as the index record's provenance fields | ✓✓ keys are named | ✗ worst of the four by eye | ✓ canonical dumps exist | ✓ `json` | small — reuses `canonical.py`; but it stops being the one file a person opens |
| **S4** | **Markdown table** | ✗ cells positional | ✓ renders in GitHub | ✓ | ✗ needs a table parser | small; diffs are noisy (column padding) |

**Recommendation to test in the compare doc:** S1, with S2 as the one fork
Arpit should see rendered (a 40-line mock of this repo's register in each
shape, in chat, before any code — the OPEN-WORK-symbols precedent). S3 and
S4 are there to be refused on the page rather than reopened later.

## Questions the compare doc must settle

1. **Migration.** A v2 register is new bytes beside a v7 index on every
   consumer repo — one commit per repo, written by the next `fux ingest`. Does
   `fux doctor` treat a v1 register as *drift* (today's read says *no register*,
   defect 1) or as *stale format, run ingest*? Recommend the second, named.
2. **The built-in decoder's digest.** Giving `prose` a `@sha:` tail means the
   register changes when the engine's own analyzer/decoder code changes — which
   is **correct** (it is exactly what the column is for) but means a fux upgrade
   touches every row once. State it; it is a feature with a cost.
3. **Grouping (S2) and L4.** Section order must derive from the sorted source
   list, never from walk order; a document reachable from two entries needs one
   rule (first entry wins by sort) stated in the record.
4. **Does anything else read it?** Confirm Node (`node/src/store/`) and
   `tools/` do not — then the one reader is `doctor.py`, and the test owed since
   d22 (*"two consecutive ingests write it once"*) is the L4 gate for v2 too.
5. **Which record owns the shape.** d22 lives in SR-INGEST; the file sits in
   the index plane that SR-INDEX-LIFECYCLE and SR-DOTFUX describe. Amend d22
   in place (L1: superseded records are rewritten, never duplicated) and add the
   format line to the `[register]` table in `constants.toml` (L12).

## Definition of done

1. `work/compare/register-shape.compare.md`: the six defects above with the
   line that proves each, S1–S4 rendered on this repo's own first 40 rows, a
   recommendation, and the five questions answered.
2. One 🔴 inbox row: Arpit picks a shape.
3. After the ruling, **file the build item** (Claude Code) covering: `register.py` render + read, `constants.toml
   [register]` (format line, header), SR-INGEST d22 amended in place,
   `.fux/README.md`'s `index/` row names the register, `fux doctor`'s row
   distinguishes *missing* / *old format* / *drift*.
4. Tests: two consecutive ingests write identical bytes (the d22 gate, now
   existing); a v1 file is reported as old format, not as absent; a row with
   an unknown `k=v` key is kept, not dropped (defect 1 closed); `doctor`
   reports a `loc` in the index with no row and a row with no record (22b,
   unchanged).

## In scope / out of scope

- **In:** the file's grammar, its header, what optional attributes it may carry
  from fields the record already holds, its grouping, the doctor row's three
  states, the migration note.
- **Out:** anything run-shaped (W-200's ledger has it), titles or any display
  text (L3), any reader or query field (L9), a Node reader for the register
  (nothing in Node needs it), changing what is *in* the index.

## Key files

`src/fux/ingest/register.py` · `src/fux/ingest/run.py::_record_register` ·
`src/fux/doctor.py::_register` · `src/fux/constants.toml [register]` ·
`src/fux/ingest/sourcelist.py` (for S2) · `records/0106_ingest.md` d22 ·
`.fux/README.md` · [`tests/ingest/test_register.py`](../../tests/ingest/test_register.py) (the d22 two-ingests gate) · `tests/test_doctor_fetcher_routes.py`.
