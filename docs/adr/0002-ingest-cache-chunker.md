---
type: ADR
title: ADR-0002 — inferred-tier ingest, OKF cache, deterministic provenance, heading chunker
description: Sources → markdown cache with provenance frontmatter, canonical manifest, per-dir index.md, structure-aware chunks; byte-determinism resolved over wall-clock provenance.
timestamp: 2026-07-21T00:00:00Z
---

# ADR-0002: ingest (inferred tier) → OKF cache + manifest + chunker

- **Status:** accepted
- **Date:** 2026-07-21
- **Feature:** M3 of handoff 0001 — ingest pipeline

## Context

The ingest cache is a **long-term, git-versioned corpus** (fux-plan §6b), so
deterministic, diff-friendly output is a hard requirement, and every cached file
must carry provenance (the frontmatter parser's first dogfood). The two-tier
strategy (inferred now, advanced in v1.1) is decided in the ingest-strategy
compare doc.

## Decision

- **Walk:** sorted `os.walk`, dotfiles and `[ingest] exclude` names skipped;
  the config maps *types to dirs*, so a dir is scanned only for its type's
  extensions. POSIX relative paths everywhere; sources outside the project root
  land under `_external/<sha8>/`.
- **Converters (stdlib):** md native (source frontmatter merged, our keys win,
  unknown keys preserved per OKF); txt verbatim; code language-fenced; JSON
  flattened to dotted paths + fenced raw; YAML fenced as text (stdlib has no
  parser); images → metadata stub with dimensions `struct`-parsed from
  PNG/JPEG/GIF headers; office/PDF only via the `markitdown` extra, otherwise
  skipped with a reason (`--list-skipped`). Binary sniff (`\0` in the first
  8 KB) catches binaries masquerading as text. Oversize text truncates at
  `max_kb` with a warning + `truncated: true`.
- **Cache = OKF bundle:** `type: Ingested Document` + title/description/
  timestamp + provenance keys (source, source_sha256, origin, fidelity,
  converter, converted_at, fux_version); per-directory `index.md` for
  progressive disclosure; write-if-changed so mtimes stay stable.
- **`converted_at` is deterministic, not wall clock** — `SOURCE_DATE_EPOCH`
  (the reproducible-builds convention) when set, else the source file's mtime.
  *This is the one deliberate deviation from the handoff's letter:* it lists
  `converted_at` as provenance **and** requires byte-identical double-ingest;
  a wall clock cannot satisfy both. Recorded in implementation.md Deviations.
- **Manifest** `.fux/manifest.jsonl`: one canonical JSON line per file
  (sorted keys, sorted by source); machine provenance incl. `line_offset` (body
  line → source line mapping) lives here, not in user-facing frontmatter.
  `--check` = full-sha drift (exit 1 on drift, CI-friendly); `ask` uses a
  stat-only quick probe to warn on staleness.
- **Chunker:** heading-based with heading-path context; 256–512 token target
  where **token ≈ whitespace word** (v1 approximation — validated on the
  fixture corpus: chunk sizes land in range; a subword heuristic bought nothing
  at this scale); small sibling sections merge, oversize paragraphs split with
  ~12 % word overlap; code fences and tables are atomic; every chunk keeps a
  1-based line span mapped to *source* coordinates via `line_offset`.
- **Incremental:** unchanged sha + existing cache file → entry reused, nothing
  rewritten; deleted sources drop their cache file (git history keeps the
  knowledge); emptied dirs pruned.

## Alternatives considered

- Parse-at-query (no cache) and lazy-hybrid — rejected in the ingest-strategy
  compare (latency, no fidelity tiers, no versionable corpus).
- Wall-clock `converted_at` — rejected: breaks the determinism requirement
  that outranks it (see above).
- tiktoken-style subword counting for chunk targets — rejected for v1: adds a
  dependency or a big vendored table; whitespace words are within ~±25 % on
  prose, which the 256–512 band absorbs.

## Consequences

Easier: `git diff` of `.fux/` reads as knowledge changes; re-ingest is safe and
cheap; agents can trust provenance. Harder: `converted_at` reflects source
mtime, not conversion wall time — a conscious trade; synthetic bodies (JSON
flatten, image stubs, office) cite file-only (no line span), honest rather than
fabricated line numbers.

## References (required)

- Ingest-strategy compare doc (verdict, tiers, traceability):
  [../compare/ingest-strategy.compare.md](../compare/ingest-strategy.compare.md)
- SOURCE_DATE_EPOCH — the reproducible-builds timestamp convention:
  https://reproducible-builds.org/docs/source-date-epoch/
- Open Knowledge Format v0.1 (bundle shape, index.md, permissive consumption):
  https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
