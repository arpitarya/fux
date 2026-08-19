# W-53 — move source directories out of `fux.toml` into `.fux/sources/dirs`

**Status:** OPEN (Lane A — agent-executable) · **Filed:** 2026-08-19
**Blocked by:** — · **Model:** **Opus.** The code is small; it retires a required
config key, adds a second reader under one grammar, and lands the archived
declaration three other items depend on.
**Spec:** [ADR-DIR-LIST](../../docs/adr/0023_dir-list.md) — accepted, unbuilt
**Lands with:** [W-44](W-44-archived-content-signalling.md), which is the
annotation half and is gated on its instrument

## What lands

- `.fux/sources/dirs` — one entry per line, `#` comments, loader dedupes and
  sorts, `<entry> archived=true` attributes, unknown key a loud `file:lineno`
  error. **The grammar is [ADR-URL-LIST](../../docs/adr/0018_url-list.md)'s and
  is shared, not copied** — one parser, two files, or the two rules drift.
- `[sources] dirs` in `fux.toml` becomes a **retired key that errors with
  instructions**, the pattern [ADR-CONFIG](../../docs/adr/0014_config.md)
  decision 7 sets and [ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 7
  has already used.
- This repo's own list migrated, with `archive/v0.26-docs   archived=true`.
- `.fux/README.md`'s layout table gains the file.

## Definition of done

- [ ] The reader, sharing the URL list's parser rather than duplicating it.
- [ ] The retired key errors and names both the new file and the migration.
- [ ] **Tests:** a dirs file with and without attributes loads; an unknown key
      errors at `file:lineno`; a duplicate entry with conflicting attributes
      errors; the old `[sources] dirs` key errors; file order does not change
      committed bytes.
- [ ] `fux.toml` and `.fux/sources/dirs` migrated in this repo; ingest is
      byte-identical across the move **except** for the new `archived` property
      — assert that explicitly, because it is the whole risk of the change.
- [ ] [ADR-CONFIG](../../docs/adr/0014_config.md) decision 2 and
      [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) decision 2 amended in
      the same change — Law zero.
- [ ] `CHANGELOG.md` under `[Unreleased] → Changed`, flagged **breaking**.
- [ ] This file archived to `archive/open/`, its OPEN-WORK row deleted, outcome
      in [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazards

- **Do not copy the URL list's parser.** Two parsers for one grammar is how
  `#`-handling, sorting and the unknown-key error end up disagreeing — the exact
  class of drift [W-49](W-49-url-fragment-truncation.md) already documents.
  **Land after or with [W-50](W-50-url-fetch-mechanism.md)**, which is rewriting
  that parser anyway.
- **Do not write the `archived` property without W-44's gate.** The file may
  carry the declaration before anything reads it; the *annotation in results* is
  gated on a pre-registered instrument
  ([ADR-DIR-LIST](../../docs/adr/0023_dir-list.md) decision 10).
- **Do not derive `archived` from the path** as a shortcut while the file is
  being built. Decision 4 is the reason this record replaced its predecessor.

## Note

**[W-45](W-45-source-exclusion.md) now has an obvious home** — an exclusion
attribute on a directory line — and is **not** decided here. The attribute set
is closed at one; adding to it is a change to ADR-DIR-LIST, and W-45 is a fork
that still owes a compare doc.
