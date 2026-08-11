# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This is the v0.30 rebuild's changelog — a fresh start. The v0.26 engine's
history is archived at [`archive/v0.26/CHANGELOG.md`](archive/v0.26/CHANGELOG.md).

## [Unreleased]

### Removed

- **`examples/` is gone** ([ADR-0012](docs/adr/0012-playground-sibling-repo.md)).
  The 20-document AcmePay fixture that shipped inside this repository was
  deleted. It contaminated the engine's own dogfood corpus, it entered the
  sdist by accident of layout rather than by decision, and — having no
  expected answers — it could not notice a ranking regression.

### Added

- **A graded corpus, in a sibling repository** (`fux-playground`,
  [ADR-0012](docs/adr/0012-playground-sibling-repo.md)). Ten
  internal-developer-platform documents, **fifty golden queries asserting
  ranks** across seven hazard classes (supersession, near-duplicate,
  attractor, collision, precision, edges, no-answer), and ten URLs that
  exercise the CDP middleware. Its committed index holds **file documents
  only**, and a staleness guard re-ingests and asserts `git diff --exit-code`
  on every run — the byte-determinism law, checked continuously. Goldens are
  hand-written from the corpus and never derived from engine output; there is
  no `--update-goldens` flag. Standing status: 41 pass, 9 named engine gaps.
  README reading-order item 5 now points there.
- **The `.fux/` directory is a declared layout**
  ([ADR-0011](docs/adr/0011-fux-dir-layout.md), ⏳ proposed): every child is
  committed (`index/`, `sources/`, `middleware/`) or derived (`runtime/`,
  `cache/`). Ingest writes a self-describing `.fux/README.md` and a narrow
  `.fux/.gitignore` — derived names only, **never `*`** — both
  write-if-missing so consumer edits survive. `derived_dir()` drops a
  spec-exact `CACHEDIR.TAG` for M2/M4 to use. `fux doctor` gains two checks:
  the committed index must not be git-ignored (error), and undeclared
  top-level `.fux/` entries are reported (warning).
- **URL source via consumer-owned middleware**
  ([ADR-0010](docs/adr/0010-url-source-consumer-middleware.md), ⏳ proposed):
  `fux.toml [sources.url]` names a consumer-editable Python file
  (`middleware`, `urls_file`, `meta`); `fux ingest --refresh-urls` — the only
  networked ingest path — calls its `fetch(url) -> str` and indexes the
  result as `src:"url"`. Hashed meta by default (`title_h`, the non-git
  law's first exercise); plain ingest stays offline and carries `url:`
  records forward byte-identically; a failed fetch keeps the prior record.
  Absolute http(s) links now resolve to in-corpus `url:` docs as `ref`
  edges. Core gains no network code and no dependencies.
- `.fux/middleware/cdp.py` — the shipped, consumer-owned template: Chrome
  DevTools Protocol capture over a hand-rolled RFC 6455 WebSocket +
  deterministic HTML→markdown, pure stdlib, ported from the archived
  v0.26 `render = "cdp"` path (never bundles a browser). Its constants are
  defaults, overridable from `fux.toml` via the new optional
  `configure(config)` hook.

### Changed

- The URL list moved out of `fux.toml` into **`.fux/sources/urls`** — one URL
  per line, `#` comments allowed, deduped and sorted before fetching, with
  line-numbered errors on a bad scheme. An inline `urls = [...]` key is now a
  hard error pointing at the file. The middleware moved from the repo root to
  `.fux/middleware/cdp.py`. Both are breaking changes against an unreleased,
  hours-old surface, so no shims exist ([ADR-0011](docs/adr/0011-fux-dir-layout.md)).
- Middleware tunables now live in an optional **`[sources.url.config]`** table
  passed verbatim to `configure(config)`. Fux validates only that it is a
  table and never reads a key inside it — the PEP 518 `[tool.*]` discipline,
  which keeps one middleware's vocabulary out of fux's config schema.
- The repo's own `.gitignore` no longer blanket-ignores `.fux/*`; the narrow
  `.fux/.gitignore` carries the derived names instead.

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
