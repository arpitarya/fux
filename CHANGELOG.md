# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This is the v0.30 rebuild's changelog — a fresh start. The v0.26 engine's
history is archived at [`archive/v0.26/CHANGELOG.md`](archive/v0.26/CHANGELOG.md).

## [Unreleased]

### Changed

- **`[sources.url] middleware` is now `fetcher`**, and `.fux/middleware/` is
  `.fux/fetchers/` ([ADR-FETCHER](docs/adr/0019_fetcher.md)). Middleware names a
  pattern whose defining property is composition, and nothing here composes: one
  file, one `fetch(url)`, exactly one running per URL. **The old key is a hard
  error with instructions**, not a silent fallback — rename the key and move the
  directory.
- **ADR-DOTFUX, ADR-URL-INGEST and ADR-CONFIG are ratified** (Arpit,
  2026-08-19), closing W-31. Their `⏳ proposed` qualifiers in the `0.32.0`
  entry below are stale as of that date; the register
  ([`docs/adr/README.md`](docs/adr/README.md)) is the live statement of every
  record's status, and released entries are left as written.

## [0.32.0] - 2026-08-12

**M2 — the query engine gets fast without changing a single answer.**

Warm `ask` is measured at a **worst-case p95 of 27.2 ms on 8 870 RFC
documents**, against a pre-registered 150 ms bar, where the reference scan
takes 4 248.8 ms (prediction **R3 PASS**). The speed comes from a *derived*
index that is never committed, and it is bound by a **differential law**: its
results are byte-identical to the scan's, asserted over 6 088 comparisons on
two corpora, every one of the playground's 50 graded goldens, and the shipped
CLI itself.

Also in this release: the `.fux/` directory becomes a declared layout, URL
ingestion arrives through consumer-owned fetcher, the demo corpus moves to
a graded sibling repo, and **R2 closes at 3/3**.

Versions 0.31.x were never published; their work ships here.

### Added

- **The derived T1 accelerator — M2** ([ADR-T1-ACCELERATOR](archive/adr/0005_derived-accelerator.md),
  ⏳ proposed). Term-major blocked postings and a fixed-width binary offset
  table under `.fux/runtime/` (derived, gitignored, `CACHEDIR.TAG`-tagged),
  rebuilt from the committed shards alone. **Prediction R3 PASS:** warm `ask`
  worst-case p95 **27.2 ms** against a 150 ms bar on 8 870 RFC documents,
  where the reference scan takes 4 248.8 ms.
  - **The differential law.** Accelerator results are **byte-identical** to
    the reference scan — asserted over 5 536 generated comparisons and every
    one of the playground's 50 graded goldens, in both skipping modes, at four
    `top` values. `ask --scan` forces the reference path.
  - Block skipping is **loss-free by construction**: terms open rarest-first
    and unopened blocks are skipped only when their combined upper bound
    provably cannot reach the k-th best score. Never by dropping postings —
    pruning stays forbidden (P1-RERUN).
- **`fux build`** — rebuild the derived accelerator from the committed index.
  `fux ingest` now builds it too; `--no-accelerator` opts out.
- **`fux find`** (ranked locations, one per line) and **`fux answer`** (the
  single best answer the index can give). `answer` is deliberately bounded to
  the index's own structure and says so — passage-level answers arrive with
  the refer plane at M4, upgrading the verb rather than adding one.
- **`fux doctor`** reports the accelerator: missing or stale is a **warning**
  (it is disposable and `ask` is correct without it); tracked-by-git is an
  error.
- **The dense lane and RRF fusion (k=60), behind `ask --hybrid`, OFF by
  default.** Int-cached Hamming over the FuxVec `code` property M1 has been
  writing; RRF ported from `archive/v0.26/` with its tests. The default is a
  measurement, not caution: on the playground's graded goldens hybrid closes
  three named gaps and breaks nine passing queries — **net −6**, including
  every no-answer query. Flipping it needs new evidence and a separate
  sign-off.

### Fixed

- `fux doctor` could crash on Windows consoles (`cp1252`) when a check
  **failed** — two failure-branch messages carried em-dashes. The existing
  ASCII guard only ever exercised the healthy path; a new test drives every
  branch.

### Changed

- **The frozen v0.19–0.26 documentation set is now an indexed source.**
  `archive/v0.26-docs` joined `fux.toml`'s `[sources].dirs` (W-42). No engine
  code changed. This closes **prediction R2 at 3/3 PASS** — the third frozen
  question's citation target had never been reachable from configured
  sources. Frozen means never *edited*; it does not mean unindexed.
  - The committed index grows **+45.1 %** (942,479 → 1,367,888 raw bytes;
    416,899 → 602,825 zlib) for +34 documents. Determinism holds: double
    ingest is byte-identical.
  - **Known consequence:** retired v0.26 documents now rank for questions
    about the *current* engine — *"what is the ingest cache"* returns five
    archived results describing a deleted subsystem. Measured post-hoc,
    filed as [W-44](work/open/W-44-archived-content-signalling.md), and
    deliberately **not** fixed here; the mechanism is Arpit's call.
    Full run: [`work/regression/2026-08-12-r2-close/`](work/regression/2026-08-12-r2-close/report.md).

### Removed

- **`examples/` is gone** ([SETUP-PLAYGROUND](work/setup/fux-playground.md)).
  The 20-document AcmePay fixture that shipped inside this repository was
  deleted. It contaminated the engine's own dogfood corpus, it entered the
  sdist by accident of layout rather than by decision, and — having no
  expected answers — it could not notice a ranking regression.

### Added

- **A graded corpus, in a sibling repository** (`fux-playground`,
  [SETUP-PLAYGROUND](work/setup/fux-playground.md)). Ten
  internal-developer-platform documents, **fifty golden queries asserting
  ranks** across seven hazard classes (supersession, near-duplicate,
  attractor, collision, precision, edges, no-answer), and ten URLs that
  exercise the CDP fetcher. Its committed index holds **file documents
  only**, and a staleness guard re-ingests and asserts `git diff --exit-code`
  on every run — the byte-determinism law, checked continuously. Goldens are
  hand-written from the corpus and never derived from engine output; there is
  no `--update-goldens` flag. Standing status: 41 pass, 9 named engine gaps.
  README reading-order item 5 now points there.
- **The `.fux/` directory is a declared layout**
  ([ADR-DOTFUX](archive/adr/0011_fux-dir-layout.md), ⏳ proposed): every child is
  committed (`index/`, `sources/`, `fetchers/`) or derived (`runtime/`,
  `cache/`). Ingest writes a self-describing `.fux/README.md` and a narrow
  `.fux/.gitignore` — derived names only, **never `*`** — both
  write-if-missing so consumer edits survive. `derived_dir()` drops a
  spec-exact `CACHEDIR.TAG` for M2/M4 to use. `fux doctor` gains two checks:
  the committed index must not be git-ignored (error), and undeclared
  top-level `.fux/` entries are reported (warning).
- **URL source via consumer-owned fetcher**
  ([ADR-URL-INGEST](archive/adr/0010_url-source-consumer-middleware.md), ⏳ proposed):
  `fux.toml [sources.url]` names a consumer-editable Python file
  (`fetcher`, `urls_file`, `meta`); `fux ingest --refresh-urls` — the only
  networked ingest path — calls its `fetch(url) -> str` and indexes the
  result as `src:"url"`. Hashed meta by default (`title_h`, the non-git
  law's first exercise); plain ingest stays offline and carries `url:`
  records forward byte-identically; a failed fetch keeps the prior record.
  Absolute http(s) links now resolve to in-corpus `url:` docs as `ref`
  edges. Core gains no network code and no dependencies.
- `.fux/fetchers/cdp.py` — the shipped, consumer-owned template: Chrome
  DevTools Protocol capture over a hand-rolled RFC 6455 WebSocket +
  deterministic HTML→markdown, pure stdlib, ported from the archived
  v0.26 `render = "cdp"` path (never bundles a browser). Its constants are
  defaults, overridable from `fux.toml` via the new optional
  `configure(config)` hook.

### Changed

- The URL list moved out of `fux.toml` into **`.fux/sources/urls`** — one URL
  per line, `#` comments allowed, deduped and sorted before fetching, with
  line-numbered errors on a bad scheme. An inline `urls = [...]` key is now a
  hard error pointing at the file. The fetcher moved from the repo root to
  `.fux/fetchers/cdp.py`. Both are breaking changes against an unreleased,
  hours-old surface, so no shims exist ([ADR-DOTFUX](archive/adr/0011_fux-dir-layout.md)).
- Fetcher tunables now live in an optional **`[sources.url.config]`** table
  passed verbatim to `configure(config)`. Fux validates only that it is a
  table and never reads a key inside it — the PEP 518 `[tool.*]` discipline,
  which keeps one fetcher's vocabulary out of fux's config schema.
- The repo's own `.gitignore` no longer blanket-ignores `.fux/*`; the narrow
  `.fux/.gitignore` carries the derived names instead.

## [0.30.0] - 2026-08-11

M0 scaffold + M1 T0 slice — the first real code of the v0.30 rebuild.
[ADR-RECORD](archive/adr/0004_index-format.md); R1 PASS, R2 2/3 PASS.

### Added

- `src/fux/` package scaffold: `store/`, `derive/` (M2 stub), `query/`,
  `ingest/`, `refer/` (M4 stub), `cli.py`, `errors.py`, `config.py`,
  `doctor.py`.
- `fux --version`, `fux doctor` (python version, repo root, `.fux/` writable).
- Canonical committed store (`store/`): sharded doc-major JSONL under
  `.fux/index/`, exactly per [`work/compare/index-format.compare.md`](work/compare/index-format.compare.md) §5/§7.
- Git-dir ingest adapter and `extracted`-mode extractors (tokenizer, heading
  phrases, `ref`/`tag`/`code` edges, FuxVec `code`); `fux ingest` is
  incremental by sha.
- `fux ask`: bytes-level prefilter scan over shards + ported BM25F, with
  citations.
- [`work/adr/0004_index-format.md`](archive/adr/0004_index-format.md) — the
  schema, canonical rules, unicode policy, and analyzer version frozen.
