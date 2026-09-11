---
type: OpenItem
id: W-130
title: "W-130 — the types file becomes `.fux/types.toml`"
description: "Arpit, 2026-09-11: convert `.fux/sources/types` to TOML and move it up to `.fux/`. It reverses ADR-TYPES' recorded rejection of a TOML types list and splits the one grammar the three source lists share, so it goes through a compare doc first. Proposed shape: an `include` glob array plus a `[decoders]` table keyed by extension."
status: open
lane: arpit
timestamp: 2026-09-11T00:00:00Z
---

# W-130 — the types file becomes `.fux/types.toml`

**Model: Opus** for the build — a close call. Once the sub-forks are ruled the
reader is Sonnet work; the writer's refuse-don't-reformat rule and the
old-file conversion are judgment no test catches.

## State

- ⏳ **Blocked on Arpit:** the verdict and six sub-forks in
  [`compare/types-toml.compare.md`](../compare/types-toml.compare.md) §5.
- ⛔ **Then blocked on the W-126 session committing** — it holds uncommitted
  edits in `sourcelist.py`, `setup.py`, `doctor.py` and
  `tests/test_source_verbs.py`, all of which this build rewrites.
- **Nothing is built and no record is amended.** Law zero puts the ADR-TYPES
  change in the same change as the code.

## Definition of done (once ruled)

1. `.fux/types.toml` is read and written in the ruled shape; `.fux/sources/types`
   is handled per F5; `.fux/sources/` holds `dirs` and `urls` only.
2. Every component in the compare doc's §7 table changed, **each owning record
   amended in the same commit** (the freshness gate checks the owner).
3. **A byte-identical re-ingest** of this repo before and after conversion —
   the proof that the allowlist and bindings did not move.
4. `uv run pytest -q tests tests_e2e` green; the new reader, writer, F3 and F5
   paths each carry a test.

## Records

ADR-TYPES (owner of the decision) · ADR-URL-LIST · ADR-DIR-LIST ·
ADR-FUXIGNORE · ADR-DECODE · ADR-CLI · ADR-DOTFUX · ADR-CONFIG ·
ADR-AGENT-POLICY · ADR-INGEST.
