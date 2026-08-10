# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This is the v0.30 rebuild's changelog — a fresh start. The v0.26 engine's
history is archived at [`archive/v0.26/CHANGELOG.md`](archive/v0.26/CHANGELOG.md).

## [0.30.0] - 2026-08-11

M0 scaffold + M1 T0 slice — the first real code of the v0.30 rebuild.
[ADR-0004](docs/adr/0004-index-format.md); R1 PASS, R2 2/3 PASS.

### Added

- `src/fux/` package scaffold: `store/`, `derive/` (M2 stub), `query/`,
  `ingest/`, `refer/` (M4 stub), `cli.py`, `errors.py`, `config.py`,
  `doctor.py`.
- `fux --version`, `fux doctor` (python version, repo root, `.fux/` writable).
- Canonical committed store (`store/`): sharded doc-major JSONL under
  `.fux/index/`, exactly per [`docs/compare/index-format.compare.md`](docs/compare/index-format.compare.md) §5/§7.
- Git-dir ingest adapter and `extracted`-mode extractors (tokenizer, heading
  phrases, `ref`/`tag`/`code` edges, FuxVec `code`); `fux ingest` is
  incremental by sha.
- `fux ask`: bytes-level prefilter scan over shards + ported BM25F, with
  citations.
- [`docs/adr/0004-index-format.md`](docs/adr/0004-index-format.md) — the
  schema, canonical rules, unicode policy, and analyzer version frozen.
