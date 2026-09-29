---
type: Handoff
name: W-239
description: "The ingest extract phase slowed down (Arpit, 2026-09-29). Three per-document costs found: identifier-family matching (W-233) makes tokenize ~7.7x slower; decode.registry() re-executes every consumer decoder per front-matter document (W-205); meta_bindings() re-reads formats.toml per document. Fix all three with byte-identical output."
item: W-239
filed: 2026-09-29
ball: agent
---

# W-239 — make the ingest `extract` phase fast again

**Status: filed 2026-09-29, not built.** Arpit, 2026-09-29: *"fux ingest
extraction step has slowed down how to improve it performance."*

**Model:** Claude Code, **Opus** — fix 1 touches the analyzer, which both
readers must agree on (L4, and the Node twin).

**The bar for every fix: the index is byte-identical before and after.** These
are speed changes only. Nothing about what is extracted may move — no
`analyzer` bump, no new root hash.

## What was found (Cowork, 2026-09-29, from the bridge)

⚠ **Indicative, not filed evidence.** Micro-timings of single functions on the
fux repo itself, Python 3.12 in a throwaway venv, one run each. They locate the
cost; they are not a conformance run. Step 1 below measures properly.

The extract loop is `ingest/run.py:566`; per document it calls
`extract.extract_fields()`.

| # | cost per document | where | since | measured |
|---|---|---|---|---|
| 1 | **identifier-family matching** — one regex of 103 alternatives, each behind two lookbehinds, tried at every character | `query/identifiers.py` `IdentifierRules.matches()`, called by `analyzer._with_families` for every field of every doc | W-233 (`dcb9fb47`) | `tokenize` on a 76 KB doc: **27 ms without families, 203 ms with the repo's 103**; `matches()` alone 157 ms. ≈ 2 ms/KB — roughly **95 s** over this repo's 47 MB of tracked Markdown, vs ≈ 16 s for all other tokenizing |
| 2 | **`decode.registry(root)` rebuilt per document** — `_consumer_decoders()` globs `.fux/decoders/` and `exec_module`s every file, uncached | `extract._decoder_for()` → `registry()`; only when `doc.meta` is non-empty | W-205 part 1 (`51be0ff1`) | **11.6 ms/call** with this repo's 17 consumer decoders; 649 of 745 tracked `.md` files have front-matter |
| 3 | **`meta_bindings(root)` re-reads and re-parses `.fux/formats.toml`** — uncached, unlike `_declared_bindings` beside it | `parse.meta_fields()` → `decode.meta_bindings()`, every document | W-205 part 1 | **1.1 ms/call** |

`mine()` (W-168 step 4) was checked and is cheap: 0.9 ms on 76 KB.

## Definition of done

1. **Measure first**, in `fux-lab` (L9), at `rung-01000` and `rung-10000`:
   the extract phase before any change, with the repo's real
   `.fux/identifiers.toml`. File it under `work/regression/` (SR-RS 10a).
2. **Fix 2 and 3 — cache per run.** `registry(root)` and `meta_bindings(root)`
   are pure functions of committed files; cache them on the same key
   `_declared_bindings` already uses (path, `st_mtime_ns`, `st_size`), plus the
   `.fux/decoders/` listing and mtimes for the registry. Or resolve once before
   the loop and pass them into `extract_fields`. Either is fine; do not
   `exec_module` a decoder more than once per process.
3. **Fix 1 — gate the family matcher.** A match can only start where one of
   the templates' leading letter runs starts after a non-alphanumeric. Find
   those positions with one cheap gate regex (the 71 distinct leading letter
   runs, case-insensitive, as a lookahead), then `rx.match(text, pos)` at each,
   skipping past each match's end.
   - **Prototyped in Cowork scratch, not in the repo:** byte-identical match
     spans on 108 files (`records/`, `docs/`, `work/*.md`), **2.1× faster**.
   - A literal `-` in the gate is wrong — templates accept flexible separators
     (`RF-118`, `RF 118`, `RF118`); the prototype mismatched on
     `records/0001_LAWS.md` until the gate used letters only.
   - Worth trying beyond 2×: dropping the per-position lookbehinds into the
     gate, or dispatching by prefix to per-family compiled patterns. Keep
     leftmost-first order identical.
   - **Node:** the query side matches short strings, so the Node reader needs
     no change. If the gate lands in shared logic, the Node twin gets the same
     change and the parity tests stay green.
4. Re-run step 1's measurement and file the after number beside the before.
5. Record the change in SR-INGEST / the identifiers record, whichever owns
   `identifiers.py` (records/README.md §Ownership).

## Tests

- A property test: for every tracked Markdown file in `tests/` fixtures, the
  gated `matches()` returns exactly what the ungated one does.
- Ingest the same corpus before and after: identical root hash.
- `registry()` called twice loads each consumer decoder once, and picks up an
  edited decoder file (mtime change) in the same process.

## Out of scope

- Fewer or different identifier families — that changes the index.
- Parallel extraction — a bigger change with its own determinism questions.
