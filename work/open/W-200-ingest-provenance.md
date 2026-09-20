---
type: OpenItem
id: W-200
title: "W-200 — ingest provenance: one runtime line per document naming its fetcher, decoder and version"
description: "Arpit's ask 2026-09-18 — record, per consumed file and URL, which decoder (and version) and which fetcher produced its record, from which bytes, with what outcome. Filed as `.fux/runtime/provenance.jsonl`: gitignored, clock-free, content-free, best-effort, read by `fux doctor` and by nobody at query time. RATIFIED, NOT BUILT."
status: open
lane: agent
timestamp: 2026-09-18T00:00:00Z
filed: 2026-09-18
ball: agent
---

# W-200 — ingest provenance

**Model: Sonnet** — one new runtime file, one writer at the end of ingest, one
doctor row. No committed byte changes, no grammar, no record shape.

⚠ **RATIFIED, NOT BUILT.** No `src/`, `node/` or `tests/` line has changed.

## The ask

> **Arpit, 2026-09-18:** *"Create a log file of the files that are being
> consumed as well as the URLs that are being consumed, with what decoders were
> used, what version they were used, and just some kind of information."*

## What exists, and the gap

| have | where | granularity |
|---|---|---|
| decoder digest (`csv@sha:3dcd…`) | `.fux/runtime/decoder-digests.json` (W-166) | per **extension** — the reuse key |
| decoder `VERSION` | each built-in module, test-enforced | per **module** |
| document rows (id, loc, title, lengths, mtime) | `.fux/runtime/docs.jsonl` | per document — **no decoder, no fetcher, no bytes sha** |
| URL health, `run_seq` | `.fux/runtime/url-state.json` | per URL — no decoder |

**The gap:** nothing answers *"which decoder, at which version, produced THIS
record, from which bytes, fetched by what?"* W-166 closed it at the extension
level; this closes it at the document level.

## The shape

`.fux/runtime/provenance.jsonl` — one JSON object per document the run
consumed, keys sorted, one line each, sorted by `id`:

    {"id":"url:https://…/policy.xlsx","kind":"url","loc":"…","fetcher":"cdp@sha:9f1e…","decoder":"xlsx@v1","content_type":"application/octet-stream","raw_sha":"…","raw_bytes":48211,"wlen":1930,"outcome":"indexed","run_seq":41}
    {"id":"file:docs/GLOSSARY.md","kind":"file","loc":"docs/GLOSSARY.md","decoder":"prose","raw_sha":"…","raw_bytes":9120,"wlen":1402,"outcome":"reused","run_seq":41}

- `decoder` — the string W-166 already mints: `xlsx@v1` for a built-in,
  `xlsxdoc@sha:…` for a consumer file, `prose` for Markdown/text.
- `fetcher` — URLs only; `<stem>@sha:<file sha>`. Fetchers have no `VERSION`;
  the consumer-owned file's sha *is* its version, the same rule consumer
  decoders already follow. **Not added to file rows.**
- `outcome` — `indexed` · `reused` (record unchanged, decoder unchanged) ·
  `skipped:<reason>` · `refused:<rule>` · `queued` (decoder returned `None`,
  enrichment queue).
- `run_seq` — the counter `url-state.json` already owns. **No wall clock**, by
  the same argument the acquired manifest makes.
- `raw_sha` / `raw_bytes` / `wlen` — numbers and hashes only. **No content, no
  title, no excerpt** (L2). `loc` is already in `docs.jsonl`, so it leaks
  nothing new.

## Why this shape

- **Runtime, never committed.** A consumer decoder's sha differs between two
  machines; a committed field would state a fact true on one of them — the
  argument that kept the blob sha off the record (SR-ACQUIRED). Gitignored, it
  is advisory and reversible: delete the file and nothing is lost.
- **Clock-free**, so nothing that reads it can pick up non-determinism (L3).
- **Not a use record.** It records what *ingest* did, not what anyone asked;
  L8 does not reach it, and it must never grow a query field.
- **Best-effort, written once, atomically, at the end of ingest** — the
  `_record_refusals` precedent: a ledger that can fail a run is worse than none.
- **A separate file**, not columns on `docs.jsonl`: that file is the query hot
  path; this one is read by `doctor` and by humans.

## Definition of done

1. `ingest/provenance.py` with `write(root, rows)` and `read(root)`; rows are
   dataclasses; the writer sorts by `id`, sorts keys, writes to a temp file and
   renames. Never raises past `fetch_all`/`run.py` — an `OSError` is one stderr
   note.
2. `run.py` collects one row per walked file (indexed / reused / skipped /
   queued) and `urlsrc.fetch_all` one per URL (indexed / skipped / refused /
   validated-unchanged → `reused`), with the fetcher stem and file sha.
3. The decoder string is obtained from `decoderdigest` (the existing minting),
   never re-derived here.
4. `fux doctor` gains `provenance`: *"N record(s) were produced by a decoder
   whose digest differs from the tree's — run `fux ingest --full`"*, and *"M
   URL(s) whose declared `decoder=` disagrees with the last observed
   `content_type`"* (the W-199 hook; the second finding lands only once W-199
   has). Read-only, offline.
5. `fux doctor --json` exposes both counts.
6. `.gitignore` for `.fux/runtime/` already covers it; a test asserts the path
   is under the derived directory and that no query-plane module imports
   `provenance`.
7. Skills: `INDEX-SKILL.md` §doctor rows and `MAINTAIN-SKILL.md` name the file
   and what it answers; regenerate the three vendor copies.
8. GLOSSARY: *provenance*.

## In scope / out of scope

**In:** the file, the two collection points, the doctor row, the guides.

**Out:** anything committed; a `fux provenance` verb (grep and `doctor` cover it
— add a verb only when a third reader appears); receipts citing the decoder
version at answer time (worth doing, but it is `fux verify`'s record, SR-REFER,
and a separate line); enrichment provenance (`enrich-digests.json` already
owns that).

## Key files

| area | files |
|---|---|
| new | `src/fux/ingest/provenance.py` |
| collect | `src/fux/ingest/run.py` (the walk; beside `DECODER_DIGEST_FILE` at ~958), `src/fux/ingest/urlsrc.py::fetch_all` (each `skipped.append` / `fetched.append` site) |
| digest source | `src/fux/ingest/decoderdigest.py` (read, not changed) |
| doctor | `src/fux/doctor.py` (beside `_fetcher_capabilities`) |
| dotfux | `src/fux/store/fuxdir.py` — see hazard 1 |
| guides | `src/fux/templates/agents/{INDEX,MAINTAIN}-SKILL.md` → `.agents/`, `.claude/`, `.kiro/` |
| docs | `docs/GLOSSARY.md` |

## Records amended in the same change

- `0106_ingest` — new decision: the provenance file, its fields, the
  best-effort rule.
- `0107_url-ingest` — the URL rows and the `fetcher@sha` string.
- `0152_doctor` — the row.
- `0102_fux-directory` — see hazard 1; one sentence either way.
- `records/README.md` ownership row for `ingest/provenance.py`.

## Tests

- **New:** `tests/ingest/test_provenance.py` — sorted, key-sorted, no clock
  field, atomic write, `OSError` is a note not a raise, one row per document
  across a mixed file+URL fixture, every `outcome` value reachable, the
  `reused` row on an unchanged document, consumer-decoder sha string.
- **New:** `tests/test_doctor_provenance.py` — the stale-decoder count; the
  file absent is *not* a finding.
- **New:** an import-fence assertion — no module under `query/` or `refer/`
  imports `provenance`.
- ⚠ Run on the Mac under `pytest.ini`.

## Hazards

1. **`fuxdir.py` says `runtime/` is "rebuildable from the committed index".**
   This file is not — it is *observed* during ingest. `url-state.json` and
   `enrich-progress.tsv` already live there on the same terms (advisory,
   deletable, not rebuildable), so the precedent is *stated*, not new; SR-DOTFUX
   needs the one sentence that names the category. If Arpit would rather it
   have its own `DECLARED` row like `acquired/`, that is a one-line change here.
2. **Which fetcher fetched a document becomes observable.** Refused for the
   *committed* index (SR-ACQUIRED); in runtime it is the whole point. Do not
   let the argument migrate.
3. **Never on the hot path.** No query, `answer` or `refer` code reads this
   file; the fence test is the gate.
4. **`reused` must carry the decoder that produced the reused record**, not the
   tree's current one — otherwise the stale-decoder finding can never fire.
   Read it from the prior row when the record is reused; write `unknown` when
   there is no prior row.
5. **Size.** ~200 B × 10 000 = 2 MB. No cap, no rotation; state that so nobody
   adds one.
