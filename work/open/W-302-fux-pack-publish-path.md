---
type: Handoff
name: W-302
description: "W-298 step 5, ruled 2026-10-25: a read-only `fux pack <outdir>` verb for package authors — copies the committed shards and the `identifiers.toml` in force, writes `fux-index.json` (fux version, `content` package + version, docs count, segment digest), refuses on a dirty or foreign index; plus the author's recipe in docs/. The segment it emits is what W-299 pins and W-300/W-301 read."
item: W-302
filed: 2026-10-25
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-302 — `fux pack`: the publish path for a package author

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `fux pack <outdir> --content <npm-or-pypi name>@<version>` copies `.fux/index/*.jsonl` and `.fux/config/identifiers.toml` into `<outdir>/`, writes `fux-index.json` | the shippable segment, one command | ✅ |
| 2 | Manifest fields: `fux_version`, `index_header` (copied), `content {npm, pypi, version}`, `docs`, `digest` — the same segment-files digest W-299 verifies | anyone reproduces the digest from the same docs (L4) | ✅ |
| 3 | Refuses: a dirty index (`.fux/runtime/dirty` set / uncommitted shards), a foreign header, `url:` records present (a package segment may hold `file:` records only), `--content` missing | a half-ingested or network-born segment never ships | ✅ |
| 4 | Author's recipe in `docs/` — `.fux/sources.yaml` → `fux ingest` → `fux pack` → put `<outdir>` in the index package's wheel **and** npm tarball — with a CI example | any package author can do it | ✅ |
| 5 | `tests_e2e`: build a fixture docs package, pack it, pin it (W-299), search it (W-300), read a passage (W-301) | the round trip, as a user | ⏳ |

**Arpit, 2026-10-25 (Cowork), Fork B:** *"New read-only `fux pack <outdir>` verb"*
over a documented recipe only.

**Model:** Claude Code, **Sonnet** — a copy, a digest and a manifest; the hard
parts live in W-299–W-301. **Ratified, not built.**

## Why

- Without one command every author re-derives the digest by hand and a mistyped
  pin is a loud error on every consumer machine.
- `pack` reads the index and writes outside the repo; it never ingests, fetches
  or edits — it is read-only on `.fux/` by construction.

## What to build

- `src/fux/cli.py` — `pack` (in `PLUGINS_EXEMPT`? **No** — a packed segment must
  reflect the declared decoders; `require` runs as for any index-reading verb).
- `src/fux/store/` — `write_segment(root, outdir, content)`; the digest function
  **shared** with `plugins.py` (one implementation, W-299's).
- `src/fux/constants.toml` — manifest file name, segment file set (L12).
- Node: **none** — ingest and pack are Python-only; the Node reader consumes.

## Records amended in the same change

- **SR-PKG-INDEX** — the publish path and the manifest (its schema owned by W-299).
- **SR-CLI** — the verb, its exit codes under d5.
- **SR-DOTFUX** — `pack` reads `index/` and `config/identifiers.toml`, writes nothing under `.fux/`.

## Tests

- pack → digest equals W-299's `verify` digest of the same outdir.
- dirty index · foreign header · a `url:` record · missing `--content` → `FuxError`, nothing written.
- manifest validates against `fux-index.schema.json`.
- the e2e round trip (step 5) passes on Python; the Node half of the round trip is
  W-300/W-301's differential.

## Definition of done

1. `fux pack` emits a segment W-299 pins and verifies unchanged.
2. The recipe page exists in `docs/` (OKF field, tracker row), with a CI snippet.
3. Both suites green; `IMPLEMENTATION.md`, `CHANGELOG.md` updated.

## Out of scope

- Publishing to a registry from fux (L5), signing, a `fux unpack`.
- Shipping `url:` records — a package's docs are its files.

## Hazards

- ✅ **W-298 step 1 passed 2026-10-25** — no blocker; independent of W-299, so the
  two may run in parallel, provided the digest function is written once and
  imported by both.
- 256 shard files for a few hundred documents is wasteful but **not** this item's
  to change: a different shard count is a `_format` change (SR-INDEX-LIFECYCLE).
