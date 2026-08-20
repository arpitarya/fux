# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This is the v0.30 rebuild's changelog — a fresh start. The v0.26 engine's
history is archived at [`archive/v0.26/CHANGELOG.md`](archive/v0.26/CHANGELOG.md).

## [Unreleased]

### Added

- **A TTL-bounded local fetch cache for the refer plane** (W-60,
  [ADR-REFER](docs/adr/0031_refer-plane.md) 5a-5c). `cache_ttl_seconds`
  (**default 0 — off**) and `no_cache` on the freshness policy; entries live in
  the gitignored `.fux/runtime/fetch-cache/`. Motivated by rate limits rather
  than latency: an agent asking ten questions about one runbook must not fetch
  it ten times, because at enterprise scale that is throttling, not slowness.
- **A fourth freshness verdict, `cached`**, carrying `age_seconds`. It is
  **never folded into `current`** — "we looked recently" is a different claim
  from "we just looked", and it still records whether the cached bytes matched
  the index.

- **`fux hooks` — the maintenance plane** (M5,
  [ADR-MAINTENANCE](docs/adr/0033_maintenance.md), **proposed, not accepted**).
  Installs `post-commit` / `post-merge` / `post-checkout` and registers a merge
  driver for `.fux/index/*.jsonl`. Every hook is best-effort and **cannot block
  a commit**; installation **refuses rather than overwrites** a hook fux did
  not write, and `--uninstall` removes only what it wrote.
- **`fux-merge-index` — a line-wise merge driver for the committed index.**
  Two people working at once no longer get a textual conflict in a
  machine-written file: it resolves last-writer-wins on `(ver, sha)`, sorts its
  output by id so two machines merge to the same bytes, and **refuses** on the
  four cases it cannot resolve — writing ordinary conflict markers that keep
  both sides and naming the fix. It never picks a side.
  A separate console script rather than a `fux` verb, because git invokes a
  merge driver as a bare command with positional arguments.

### Changed — **breaking**

- **L5 is enforced when a record is written, not when it is ingested.** The
  hashed-meta rule for non-git sources moved from `ingest/run.py` — one caller
  — into `write_index`, the only way bytes reach a committed shard. A non-git
  record must now **state** `meta` (a missing value is refused rather than
  defaulted), and a `hashed` record carrying `title` or `phrases` is rejected.
  **Breaking only for a caller writing records directly**; every record this
  repo already holds complied, so nothing changed on disk.

- **Only prose files are indexed now** ([ADR-TYPES](docs/adr/0032_types-list.md),
  W-55 verdict G). The git-dir walker had **no file-type filter at all**:
  anything UTF-8-decodable was a document, which on this repo meant 21 of 150
  records (14 %, and 15 % of the tokens) were `.json`, `.svg`, `.sh`, `.py` or
  `.mermaid`. A compiled-in allowlist — `*.md`, `*.markdown`, `*.txt`, `*.rst`,
  `*.adoc`, `*.org` — now applies, replaceable by committing
  `.fux/sources/types`. **Absent means the default**, never "index everything"
  and never "index nothing".
  **Migration:** re-run `fux ingest`. Records for non-prose files disappear and
  `df` moves for every surviving document, so **this changes rankings** — it is
  not claimed to improve them, and nothing has measured it.
- **`.fux/sources/dirs` accepts `!` exclusions**
  ([ADR-DIR-LIST](docs/adr/0023_dir-list.md), W-45 verdict E).
  `!work/regression/*/evidence` removes matching paths, and everything beneath
  them, from every included root. Order-independent, no un-exclude, no
  attributes. `*` does not cross a `/`; `**` is the any-depth form.
  Not breaking on its own — a file with no `!` line behaves exactly as before.
- **`fux ingest --list-skipped` names the reason for every rejection** —
  `not an indexed file type`, or `excluded by !<pattern>` with the pattern that
  did it. A filter nobody can see is what both of these items were opened
  about.
- **`fux setup` writes `.fux/sources/types`** with the default spelled out in
  comments, so a consumer can see what fux considers a document without reading
  its source.

### Added

- **The refer plane's core — `fux.refer`** (M4,
  [ADR-REFER](docs/adr/0031_refer-plane.md), **proposed, not accepted**).
  Fetches a cited document from the system that owns it, verifies it still says
  what the index thinks, cuts it into heading-delimited passages, re-scores
  those against the query, and assembles as much as fits a **byte** budget.
  **No verb exposes it yet** — its gate has not run, and wiring an unmeasured
  plane into the default surface is how it becomes load-bearing before anyone
  knows whether it works.
- **Fux still does not fetch.** The plane reuses the consumer-owned fetcher
  contract ([ADR-FETCHER](docs/adr/0019_fetcher.md)) rather than adding a
  second fetch mechanism; the callable is injected, never imported, and an AST
  test asserts no network import anywhere in the plane.
- **Freshness is verified by content, not by age.** `never` (the default,
  offline) and `always`, plus a timeout — and a three-state verdict
  `current`/`stale`/`unverified`, so nothing can collapse "we did not look"
  into "we looked and it was fine". **`max_age_seconds` was deliberately not
  built**: the committed record carries no ingest time, so the bound could not
  have been honoured, and a knob that silently does nothing is worse than a
  missing one.
- **ARC content cache**, keyed `(loc, sha)` and byte-budgeted. The content
  address is in the key, so a hit is byte-identical to what a fetch would have
  returned — asserted by a differential test.

- **The graph lane — `fux explain`, `fux graph`, `fux path`** (M3,
  [ADR-GRAPH](docs/adr/0030_graph-lane.md)). The `ref`/`tag`/`code` edges
  ingest has extracted since M1 become answerable. `explain` lists a
  document's outbound edges and its community; `graph` returns the
  neighbourhood around a query's best answers, PPR-expanded; `path` returns
  every simple directed route between two documents with a reliability that
  decays per hop. Flat verbs, as ever — `fux graph path` would have been the
  first subcommand tree on this surface.
- **Communities, assigned deterministically and without a seed.** Label
  propagation with sorted visit order, ties broken on the smallest label, and
  a fixed sweep cap — there is no `random` import in the module and a test
  parses its AST to keep it that way. A fixed seed would have been the weaker
  guarantee. Labels are canonicalised (`c0`, `c1`, …) by size, so adding one
  document cannot rename a partition that did not change.
- **`.fux/runtime/graph.json`** — the derived graph plane, written by
  `fux build`, gitignored, and part of the byte-identity assertion. Communities
  are derived rather than committed because a community label is *global*:
  committing it would turn a one-file commit into a corpus-wide diff.

### Changed

- **`ask` is untouched, and now asserted so from the graph fixture too.** The
  graph plane is built by the same `fux build` as the accelerator, so a leak
  into the lexical path is a live possibility rather than a theoretical one.

### Fixed

- **`fux ask --hybrid` no longer crashes on a source install.** `get_model()`
  returns `None` when the embedding bundle is not shipped, and `None.embed(...)`
  raised an `AttributeError` that the guard written for exactly this case did
  not list — so a documented, supported state printed a traceback instead of
  falling back. It now returns the lexical answer at exit 0. Fixed with an
  explicit `None` check rather than a wider `except`, so a real bug inside
  `embed()` still propagates; both halves are asserted
  ([ADR-CLI](docs/adr/0002_cli-surface.md)).

### Changed

- **`ask --json --explain` now carries `"path"`** — `"accelerator"`, `"scan"`
  or `"hybrid"`. `--explain` was text-only, so the one fact worth logging about
  a slow query was the one a caller could not read. The key appears only when
  `--explain` is passed, so the default payload is unchanged
  ([ADR-ASK](docs/adr/0004_ask.md)).
- **`answer --json` now carries `"source"` on the no-match branch too.**
  [ADR-ANSWER](docs/adr/0006_answer.md) tells callers to key on `"source"` to
  detect the M4 upgrade, so its absence on one branch was a trap. The payload
  is now `{"answer": null, "citation": null, "source": "index"}`.

## [0.33.0] - 2026-08-19

**The sources rewrite — what fux indexes becomes two committed files, and the
URL path works for the first time.**

Five defects closed. Every one of them was **latent**: this repo does not use
URL ingest, so nothing in its own corpus reached four of the five, and a green
test suite said nothing about them. They were fixed anyway, because the first
consumer hits all five on day one, on the documented default. The evidence is
[`work/regression/2026-08-19-w54/`](work/regression/2026-08-19-w54/report.md),
a fixture that builds a repo from nothing and runs the whole path offline.

**Two breaking changes**, both retired config keys, both a stopped run with the
migration in the message. Both are cheapest now.

**The honest limits.** Nothing here exercises real HTTP — `http.py`'s transport
is covered by reading it, and the first consumer to point `fetch=http` at a
real server is its first real exercise. The `archived=` declaration parses and
is deliberately **not read**: changing what a verb says about a document needs
an instrument, and that instrument does not exist yet. And seven documents
measures nothing about speed, so this release reports no new timing.

### Added

- **`fux setup`** — writes the files you own into your repo, **write-if-missing**:
  `fux.toml`, `.fux/sources/dirs`, `.fux/sources/urls`, and both fetchers
  ([ADR-DOTFUX](docs/adr/0003_fux-directory.md) decision 6). Optional, explicit,
  once per repo, and a second run is a no-op that never clobbers an edit. It is
  the only verb that may run before a repo root exists — it is what creates one.
- **Two fetchers ship in the wheel**, `http.py` and `cdp.py`
  ([ADR-HTTP-FETCHER](docs/adr/0021_http-fetcher.md),
  [ADR-CDP-FETCHER](docs/adr/0020_cdp-fetcher.md)). They travel as **package
  data with an extension Python cannot import**, so fux copies them and never
  imports them — the adapter cap is structural, not remembered. `http.py` is a
  plain stdlib GET and is what a URL with no `fetch=` attribute gets; it never
  escalates to the browser on its own.
- **`fux url`** — records a URL in the committed list, writing **every**
  attribute explicitly ([ADR-URL-LIST](docs/adr/0018_url-list.md) decisions 12
  and 13). Flags, not a subcommand tree: `--cdp`/`--http`, `--plain`/`--hashed`,
  `--remove`; no argument lists what the loader sees. **It never fetches** —
  `fux ingest --refresh-urls` remains the only networked path in the engine.
- **Per-URL attributes in `.fux/sources/urls`** — `fetch=http|cdp` routes to a
  file under `.fux/fetchers/`, `meta=plain|hashed` decides whether the index may
  hold readable display text for that one document. A line beats the source-wide
  `[sources.url]` setting, which beats the built-in default. `meta` only ever
  *loosens* per line: there is deliberately no way to make one URL stricter.
- **`.fux/sources/dirs`** — the committed directory list, on the same grammar
  ([ADR-DIR-LIST](docs/adr/0023_dir-list.md)). A line may declare
  `archived=true`; it is parsed and validated today and **not yet read** — the
  marker in results is gated on a pre-registered query set.

### Changed

**Two breaking changes, both retired keys, both a stopped run with
instructions.** A retired key that silently does nothing is worse than one that
stops the run — here "silently does nothing" would mean indexing the wrong
corpus or fetching through the wrong file.

- **BREAKING — `[sources] dirs` is retired.** The corpus moves to
  `.fux/sources/dirs`, one entry per line, so a 5 000-entry list diffs and
  merges line by line instead of colliding in a single TOML array.

  ```diff
  # fux.toml
   [sources]
  -dirs = ["docs", "work", "README.md", "archive/v0.26-docs"]

  # .fux/sources/dirs
  +docs
  +work
  +README.md
  +archive/v0.26-docs        archived=true
  ```

  `[sources] dirs_file` points elsewhere if you want. **The key errors whatever
  its value** — `dirs = []` stops the run exactly as a populated list does.

- **BREAKING — `[sources.url] middleware` is retired, renamed `fetcher`**, and
  `.fux/middleware/` is `.fux/fetchers/`
  ([ADR-FETCHER](docs/adr/0019_fetcher.md)). Middleware names a pattern whose
  defining property is composition, and nothing here composes: one file, one
  `fetch(url)`, exactly one running per URL.

  ```diff
   [sources.url]
  -middleware = ".fux/middleware/cdp.py"
  +fetcher    = ".fux/fetchers/cdp.py"
  ```

  ```console
  $ git mv .fux/middleware .fux/fetchers
  ```

- **`[sources.url] fetcher` defaults to `.fux/fetchers/http.py`** (was
  `cdp.py`), because a URL line with no `fetch=` means `fetch=http`. The key
  now carries two things: the file an unattributed line uses, **and** the
  directory a `fetch=<name>` resolves in.
- **`fux.toml` has no required keys.** It holds policy; the source lists hold
  the corpus.
- **ADR-DOTFUX, ADR-URL-INGEST and ADR-CONFIG are ratified** (Arpit,
  2026-08-19), closing W-31. Their `⏳ proposed` qualifiers in the `0.32.0`
  entry below are stale as of that date; the register
  ([`docs/adr/README.md`](docs/adr/README.md)) is the live statement of every
  record's status, and released entries are left as written.

### Fixed

- **`meta = "hashed"` produced an index no `fux build` would accept** — and it
  is the default, and an L5 safety default. A bare 16-hex `title_h` is a quoted
  16-hex token outside `terms`, which the build refuses because the scan would
  count it toward that term's `df` and the accelerator would not. Any corpus
  with one hashed URL record was stuck on the reference scan permanently: 27.2 ms
  becomes 4 248.8 ms at RFC scale. **Fixed in the field's shape, not the check** —
  `title_h` is now `"h:" + <hash>` and the two paths agree by construction.
  **Migration: re-run `fux ingest --refresh-urls`.** No `_format` or `analyzer`
  bump ([ADR-INDEX-LIFECYCLE](docs/adr/0009_index-lifecycle.md) decision 9), and
  the build's refusal names the migration.
- **A URL fragment was silently truncated.** `#` began a comment anywhere on a
  line, so `https://x/page#section` loaded as `https://x/page`, two URLs
  differing only by fragment collapsed into one, and **a document disappeared
  with no error**. `#` now begins a comment only at the start of a line or after
  whitespace.
- **`[sources.url] fetcher`'s default named a file that did not exist.** Nothing
  in fux wrote it and nothing shipped it, so a consumer following the documented
  default got *"fetcher not found"*. `fux setup` writes it.
- **Two docstrings claimed fux shipped a fetcher when it did not.** Now true.

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
