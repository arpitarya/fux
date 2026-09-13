---
type: Compare Doc
title: The types file as TOML
description: Whether `.fux/sources/types` becomes `.fux/formats.toml`, and in what shape — a reversal of SR-TYPES' recorded rejection of a TOML types list.
status: accepted
timestamp: 2026-09-11T00:00:00Z
---

# `.fux/sources/types` → `.fux/formats.toml` — Comparison

> **Verdict: ACCEPTED (Arpit, 2026-09-11) — D, and F1–F6 exactly as proposed.**
> ⚠ **F1's file was renamed the same day: `.fux/types.toml` → `.fux/formats.toml`**
> (Arpit, after `map.toml` and `decoders.toml` were weighed — reasons in
> SR-TYPES decision 12). Every mention in this doc now reads `formats.toml`;
> the doc's file name keeps `types-toml` so its links do not break.
> Shipped the same day as [SR-TYPES](../../records/0128_types-list.md)
> decision 12. Two refinements the build found, both recorded there: F3's
> *stated twice* check is **exact-case** (`"*.CSV"` beside `csv` admits other
> files), and F5's conversion **refuses** an upper-case bound pattern rather
> than change the allowlist. Converting this repo re-ingested byte-identical.
>
> **Proposed verdict, as filed: D — `.fux/formats.toml`, an `include` glob array
> plus a `[decoders]` table keyed by extension.**
>
> **Arpit's ask (2026-09-11, Cowork):** *"convert it to .toml or .yaml file and
> put it in .fux dir rather than .fux/sources"* — then, when asked: **TOML**, and
> **do it properly** (this doc, then the record and the code in one change).
>
> **Status:** ✅ accepted and built (W-130).
>
> **Confidence:** medium. A consistency and ergonomics call; nothing here is
> measurable, and **A (change nothing) stays a legitimate answer.**
>
> **Reopen-trigger:** §8.

## 0 — Two corrections first

- 🔴 **This reverses a recorded rejection.** SR-TYPES §Alternatives: *"A
  `[sources] types` TOML array. Rejected: the shape SR-DIR-LIST had just moved
  away from."* Also [file-type-filter](file-type-filter.compare.md) option D.
  §3 re-reads each reason against this proposal.

- 🔴 **The chat question that picked a shape carried a false premise, and it
  was the agent's.** It said the `!` lines are order-sensitive. **They are
  not**: `sourcelist.parse` sorts every entry
  (`sorted(seen.values(), key=lambda e: (e.exclude, e.value))`), and
  SR-DIR-LIST decision 2b has no un-exclude. The "ordered rule list" pick
  (option C) rested on that claim, so it is re-opened here rather than assumed.

## 1 — Context

- **The file does two jobs:** *what is a document* (SR-TYPES decisions 2, 3, 6)
  and *which decoder reads each extension* (decision 11 — Arpit, 2026-09-01:
  *"use the file as map"*).

- **It shares one grammar and one writer with `dirs` and `urls`.** Parsed by
  `sourcelist.parse` with `ListSpec TYPES`; written by `src/fux/sources.py`
  (914 lines — `add`/`remove`/`update`/`list`/`check`, all line-text edits).

- **Every other hand-edited policy file in `.fux/` is already TOML** —
  `tune.toml`, `output.toml`, `refusals.toml`, `pii.toml`. `sources/dirs` and
  `sources/urls` are not.

- **`.fux/formats.toml` would never be indexed itself.** The walker skips
  dot-prefixed path parts (`gitdir.py`, `part.startswith(".")`), so the `toml`
  decoder never sees it.

- 🔴 **Found while reading, independent of the verdict:**
  `src/fux/config.schema.json` advertises `[sources] types_file` (default
  `.fux/sources/types`), but **`config.py` reads no such key** — every caller
  uses the `DEFAULT_TYPES_FILE` constant. The schema documents configurability
  that does not exist. Filed in OPEN-WORK.

## 2 — Options

| | location | shape |
|---|---|---|
| **A** | `.fux/sources/types` | unchanged — the shared line grammar |
| **B** | `.fux/types` | unchanged grammar, moved only |
| **C** | `.fux/formats.toml` | `[[type]]` array of tables, one per pattern (`pattern`, `decoder`, `exclude`) — the chat pick |
| **D** | `.fux/formats.toml` | `include = [...]` plus `[decoders] ext = "module"` — **proposed** |
| E | `.fux/types.yaml` | ⛔ eliminated — Arpit chose TOML; YAML also needs a third-party parser named by its own record under L1 |

**D — the default as `fux setup` would write it (abridged):**

```toml
# Which files are documents, and which decoder reads each one. See SR-TYPES.
# Absent file -> the built-in default. Present -> it REPLACES the default.

# Already text: no decoder in the path. One glob per line.
include = [
  "*.adoc",
  "*.markdown",
  "*.md",
  "*.org",
  "*.rst",
  "*.txt",
]

# Extension = the decoder module that reads it. A bound extension IS a
# document -- do not repeat it in `include`.
[decoders]
cfg = "ini"
csv = "csv"
docx = "docx"
tsv = "csv"
```

**C — the same two kinds of entry:**

```toml
[[type]]
pattern = "*.csv"
decoder = "csv"

[[type]]
pattern = "*.md"
```

## 3 — The recorded rejection, reason by reason

| why TOML was rejected | where | does it hold against D? |
|---|---|---|
| a large inline array is **one diff hunk, one merge conflict** | SR-URL-LIST decisions 1-2 | **No.** TOML arrays span lines with trailing commas and comments; one entry per line merges line by line. The writer keeps that layout (§6). |
| it **buries a corpus decision in config** (`fux.toml`) | SR-URL-LIST and SR-DIR-LIST §Alternatives | **No.** Its own file, beside `tune.toml` — not a key in `fux.toml`. |
| **one grammar, one parser** for the three lists | SR-DIR-LIST decision 2; file-type-filter matrix | 🔴 **Yes — the cost is real and D pays it.** `types` leaves the shared grammar and `sources.py` grows a second writer. |

## 4 — Matrix

| criterion (weight) | A | B | C | **D** |
|---|---|---|---|---|
| one entry = one line, merges line by line (H) | yes | yes | no — 2-3 lines per entry | **yes** |
| *"a binding is per extension"* is **structural** (H) — decision 11 | no — `_bound_extension` refuses `docs/api/*.json decoder=json` at runtime | no | no — same runtime refusal | **yes — the key is an extension; a path-scoped binding cannot be written** |
| two bindings for one extension (M) | runtime check | runtime check | runtime check | **TOML refuses** — *"defining a key multiple times is invalid"* |
| one grammar, parser and writer for three lists (M) | **yes** | **yes** | no | no |
| same shape as the other `.fux/*.toml` policy files (M) | no | no | yes | **yes** |
| the 36-glob default, in entry lines (L) | 36 | 36 | ~110 | **~42** |
| blast radius (M) | none | path + prose | large | large |
| reverses a recorded rejection (M) | no | no | yes | yes (§3) |

- **Why D over C:** C spends TOML's verbosity expressing an order the loader
  discards, and keeps every runtime check A has. **D's shape is decision 11's
  rule** — a map from extension to module.

- **Why D over A:** one shape across `.fux/` policy files, and two runtime
  checks become impossible to write. **That is the whole gain.** If it is not
  worth the grammar split, A is the answer.

- **Precedent:** Ruff ships exactly this pair — `include` (a glob list) and
  `extension` (a bare-extension map, `{rpy="python"}`), where *"any file
  extensions listed here will be automatically added to the default `include`
  list as a `*.{ext}` glob"*.

## 5 — Sub-forks for Arpit

| # | fork | proposed | alternative |
|---|---|---|---|
| F1 | location | **`.fux/formats.toml`** — Arpit's ask, recorded as his ruling | `.fux/sources/formats.toml`, keeping the three lists together |
| F2 | shape | **D** | C — the chat pick, on the false premise in §0 |
| F3 | does a binding admit its extension? | **yes** (Ruff's rule). `[decoders] csv` makes `*.csv` a document; `*.csv` also in `include` is a loud *stated twice* error | no — admission only through `include`; a bound-but-not-included extension is an error |
| F4 | subtraction (`!`) | **dropped.** `.fux/.fuxignore` is already the home and `!` here the deprecated spelling (SR-TYPES 2a, SR-FUXIGNORE decision 5); a new format should not ship a deprecated spelling | carry `exclude = [...]` |
| F5 | an existing `.fux/sources/types` | **loud error** from `ingest` and `doctor` while it exists; `fux setup` writes `.fux/formats.toml` converted from it (only if the new file is missing) and says to delete the old one; its `!` lines become `.fuxignore` lines | no migration — SR-DECODE decision 17 is the precedent, Arpit's call for the decoder rename |
| F6 | error positions | **key path always** (`decoders.geojson`), plus the line number when a scan finds exactly one line for it | key path only |

⛔ **Disqualified for F5: silently ignoring the old file.** The default would
apply, the index would change, and nothing would say so — *a plausible index
with different postings*, the worst case SR-TYPES decision 11 names.

## 6 — Consequences of D

- **Reader lenient, writer strict** (SR-URL-LIST decision 13, kept). Any valid
  TOML loads; `fux source add --types` edits only the canonical
  one-entry-per-line layout and **refuses** a hand-reformatted array rather than
  rewriting it — a rewrite would eat the comments inside it.

- **`tomllib` reads; nothing in the stdlib writes.** *"This module does not
  support writing TOML."* The writer is hand-rolled like every codec in fux
  (L1), and its output is sorted (L3).

- **Closed key set:** `include` and `decoders`, nothing else — `tomllib`
  accepts any key, so fux must refuse.

- **Unchanged:** absent → default (decision 3); present replaces (2); no
  positive entry → error (3); the extending/redirecting check (11a); default
  derived from built-ins only (1a).

- 🔴 **Semantic errors lose a guaranteed `file:lineno`** (F6), which every
  source list promises today.

- 🔴 **`.fux/sources/` stops holding "the trio".** SR-TYPES' consequence line
  and SR-DIR-LIST decision 1 (*"beside `urls` and `types`"*) are rewritten.

- ⚠ **Index bytes should not move** — a converted file states the identical
  allowlist and bindings. **The build proves that with a byte-identical
  re-ingest, not with this sentence.**

## 7 — Build scope once ruled (not started)

⛔ **Gated on two things:** this verdict, and **the concurrent W-126 session
committing.** At 07:33 UTC on 2026-09-11 it held uncommitted edits in
`sourcelist.py`, `setup.py`, `doctor.py`, `tests/test_source_verbs.py`,
`OPEN-WORK.md` and `WORKLOG.md`.

| component | owning record (Law zero) | change |
|---|---|---|
| `config.py`, `config.schema.json` | SR-CONFIG | `DEFAULT_TYPES_FILE`; the phantom `types_file` |
| `ingest/sourcelist.py` | SR-URL-LIST | `TYPES` leaves the shared grammar; TOML reader |
| `ingest/gitdir.py` (`read_types`) | SR-INGEST | reads the new file; old-file error (F5) |
| `decode/__init__.py` (`_declared_bindings`) | SR-DECODE | bindings from `[decoders]`; `_bound_extension`'s refusal becomes unreachable |
| `sources.py` | SR-CLI | the types branch of every verb; canonical-layout writer; `_seed_types` |
| `setup.py` | SR-DOTFUX | the default file; the `.fuxignore` header prose; conversion (F5) |
| `doctor.py` | SR-DOTFUX, SR-DECODE | `types list usable`; `_decoder_bindings`; an old-file row |
| `ingest/fuxignore.py`, `ingest/__init__.py`, `ingest/run.py` | SR-FUXIGNORE, SR-INGEST | `duplicate_warnings` loses its types half (F4) |
| `cli.py` | SR-CLI | `--types` help |
| `templates/agents/DECODER-SKILL.md` and its three vendor copies | SR-AGENT-POLICY | the binding example |
| tests | — | `test_binding`, `test_source_filters`, `test_fuxignore`, `test_setup`, `test_source_verbs`, `test_skipnotice`, `test_doctor`, e2e |
| records | — | SR-TYPES (2, 2a, 10, 11, 11a, consequences, alternatives, veto check commands), SR-URL-LIST, SR-DIR-LIST, SR-FUXIGNORE 5, SR-DECODE 13, SR-DOTFUX, SR-CONFIG, SR-CLI; path mentions in SR-TUNE, SR-OUTPUT, SR-INGEST, `docs/handbook.html`, `work/architecture-detailed.svg` |

**Model: Opus** — a close call. With §5 ruled the reader is Sonnet work; the
writer's refuse-don't-reformat rule and F5's conversion are judgment no test
catches.

**Why SR-TYPES is not amended yet:** Law zero puts the record change in the
same change as the behaviour. A record describing `.fux/formats.toml` today would
describe code fux does not have — which CLAUDE.md calls worse than no record.

## 8 — Reopen-trigger

Redo this comparison if any of these is true:

1. **`dirs` or `urls` is proposed as TOML.** The grammar-split cost in §3
   disappears, and the three lists are judged together. Check:
   `ls work/compare/ work/proposals/ | grep -i toml`.
2. **`types` gains a second attribute that belongs to a pattern, not an
   extension.** D's extension-keyed table cannot hold it; C can. Check:
   SR-TYPES decisions after 11a.
3. **A defect is filed where a `fux source` verb behaves differently for
   `types` than for `dirs`** because of the split writer. Check:
   `grep -n "types" work/OPEN-WORK.md`.

## References

- SR-TYPES — [`records/0128_types-list.md`](../../records/0128_types-list.md): decisions 1a, 2, 2a, 3, 11, 11a; §Alternatives.
- SR-URL-LIST — [`records/0116_url-list.md`](../../records/0116_url-list.md): decisions 1-2 and 13; §Alternatives.
- SR-DIR-LIST — [`records/0120_dir-list.md`](../../records/0120_dir-list.md): decisions 1, 2, 2b; §Alternatives.
- SR-FUXIGNORE — [`records/0144_fuxignore.md`](../../records/0144_fuxignore.md): decision 5.
- SR-DECODE — [`records/0139_decode.md`](../../records/0139_decode.md): decisions 13 and 17.
- [file-type-filter](file-type-filter.compare.md) — option D and its matrix.
- Code: [`sourcelist.py`](../../src/fux/ingest/sourcelist.py) (`parse`, `TYPES`), [`sources.py`](../../src/fux/sources.py), [`decode/__init__.py`](../../src/fux/decode/__init__.py) (`_declared_bindings`, `_bound_extension`, `_bind`), [`gitdir.py`](../../src/fux/ingest/gitdir.py) (`read_types`, the dot-skip), `config.schema.json` (deleted 2026-09-12 by W-122's consolidation; the declared key block in [SR-CONFIG](../../records/0113_config.md) decision 13 replaced it).
- TOML v1.0.0 — duplicate keys invalid; multi-line arrays with trailing commas and comments — <https://toml.io/en/v1.0.0>
- Python `tomllib` — read-only, added in 3.11 — <https://docs.python.org/3/library/tomllib.html>
- Ruff settings, `include` and `extension` — <https://docs.astral.sh/ruff/settings/#extension>
