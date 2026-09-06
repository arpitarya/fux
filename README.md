# Fux

**Deterministic knowledge retrieval for AI-assisted codebases — rank from a
small git-carried index, fetch content from the systems that own it, verify
at answer time.**

> **Status (2026-09-02): `fux-engine` 2.0.0-alpha.7 on PyPI.** M2 through M5
> (accelerator, graph lane, refer plane, maintenance hooks) are in. `alpha.0`
> moved the record shape to `fux.index.v2` and added five-field BM25F,
> per-source tuning (`.fux/tune.toml`), proximity reranking, `fux enrich` and
> `fux mcp`. **Seven releases since**, each in
> [`CHANGELOG.md`](CHANGELOG.md):
>
> | | |
> |---|---|
> | `alpha.1` | the dense lane **removed** — see below |
> | `alpha.2` | the URL freshness loop closes: `ttl=`, `cached` and `as-ingested` as verdicts of their own |
> | `alpha.3` | `.fux/output.toml` — how a result is *shown*, never which documents come back; `ask --sections` |
> | `alpha.4` | three more built-in decoders: `jsonl`, `svg`, images |
> | `alpha.5` | the **acquired plane** (`keep=`), declarative refusal detection (`.fux/refusals.toml`), and **PII redaction** of the committed index (`.fux/pii.toml`) |
> | `alpha.6` | enrichment moves inside the PII boundary; `fux enrich <TARGET>`; a CDP fetcher that survives concurrency |
> | `alpha.7` | one enrichment-report path spelling on every platform |
>
> From any repo:
> ```bash
> fux setup                # writes the files you own, write-if-missing
> fux ingest               # builds the committed .fux/index/*.jsonl (+ the accelerator)
> fux ask "your question"  # ranks with BM25F, cites the source file
> fux find "your question" # ranked locations, one per line
> fux answer "a question"  # the single best answer the index can give
> ```
> **What fux indexes is two committed files, not config.**
> `.fux/sources/dirs` and `.fux/sources/urls`, one entry per line, on one
> grammar — so a 5 000-entry corpus diffs and merges line by line, and the
> loader sorts so file order can never change a committed byte.
> **Warm `ask` is measured at a worst-case p95 of 27.2 ms on 8 870 RFC
> documents** — against a pre-registered 150 ms bar, where the reference
> scan takes 4.2 s (prediction **R3 PASS**,
> [the run](work/regression/2026-08-12-m2-accelerator/report.md)).
>
> The speed comes from a **derived** index under `.fux/runtime/` — never
> committed, rebuilt from the committed shards by `fux build`. It is bound by
> a **differential law**: its results are *byte-identical* to the reference
> scan's, asserted over thousands of comparisons rather than spot-checked.
> **`ask`/`find`/`answer` scan by default** (no build step needed); pass
> `--fast` to opt into the accelerator when one exists and is fresh — same
> results, faster (Arpit, 2026-08-21). `--scan` still forces the reference
> path explicitly, for bug reproduction.
>
> **There is no dense lane and no bundled model** (2026-08-25). One existed
> behind `ask --hybrid`, shipped off by default, and was deleted after its own
> gate measured **0 fixed / 2 broken** — the bundled embedding mean-pooled
> static token vectors, so it was as order-blind as the lexical scorer it was
> meant to complement. Removing it took the wheel from **6.84 MB to 233 KB**
> (measured 2026-08-25, and it stands — though wheel size stopped being the
> binding constraint when L1 was amended on 2026-09-06; the lane was removed
> for measuring worse, never for its size).
> Ranking is unchanged; the flag is gone.
>
> **The corpus is maintained with `fux add` / `fux remove` / `fux update`**
> (2026-08-21), over directories, single documents and URLs alike — the entry
> picks the list. `add` ingests by default; `remove` takes a document out of
> the index *and* the graph, deleting its line or subtracting it from a listed
> ancestor; `update` re-reads what is listed and never writes a line. They
> replace `fux url` and `fux ingest --refresh-urls`
> ([ADR-CLI](docs/adr/0011_cli-surface.md)).
>
> URLs join the corpus through a consumer-owned fetcher file. `fux setup`
> writes two — `http.py` (a plain stdlib GET, the default) and `cdp.py`
> (Chrome DevTools Protocol, also pure stdlib, which **borrows the session
> your own signed-in Chrome already holds** and hands fux the bytes the server
> sent) — into `.fux/fetchers/`, where they become **your** code and fux never
> rewrites them. Neither renders a page; both return bytes plus a content type
> and the decoder plane does the rest. Add one with
> `fux add <URL> [--cdp] [--plain]`, which records the line **and fetches that
> one URL**. That and `fux update` are the engine's **two** networked paths;
> both say on stderr that they went out, and everything else is offline. A
> line picks its own fetcher; nothing escalates automatically
> ([ADR-URL-LIST](docs/adr/0026_url-list.md) ·
> [ADR-FETCHER](docs/adr/0027_fetcher.md)).
> **The graph lane has landed (M3, released in `0.34.0`)** — `explain`/`graph`/`path`,
> unseeded label-propagation communities, a lazy PPR walk
> ([ADR-GRAPH](docs/adr/0036_graph.md)). **Both acceptance gaps are closed**
> (2026-08-22): 24/24 on a graded 66-document corpus, and the derived
> `graph.json` hashes identically across two independent architectures
> ([the run](work/regression/2026-08-22-graph-acceptance/report.md)).
>
> **Archived content says so, and the ranking does not move.** A source
> declared `archived=true` carries `archived: true` on every verb, an
> `[archived]` marker in `ask`'s text, and a stderr disclaimer — while
> results stay byte-identical unless `[ranking] archived_weight` is set
> below its `1.0` default
> ([ADR-ARCHIVED-CONTENT](docs/adr/0044_archived-content.md)).
>
> The v0.26 engine and its docs are archived under
> [`archive/v0.26/`](archive/v0.26/), reference-only. The new architecture
> is specified in
> [`work/paper/the-fux-index-paper.md`](work/paper/the-fux-index-paper.md)
> (§4–§6 knowingly stale until M6) and built against
> [the ADR register](docs/adr/README.md).
>
> **The pruning gate closed (2026-08-09): FAIL.** Keeping only each
> document's top-*k* terms was measured, twice, against a corpus that could
> actually test it — no selector came within 35.9 points of preserving
> candidate recall at a 6 % budget. The committed index carries **full
> postings**, permanently — [P1-RERUN](work/regression/2026-08-09-pruning-rerun/VERDICT.md).

## The idea

- **Sources own content.** Repo docs stay in git; Confluence pages stay in
  Confluence. Fux never keeps a durable copy (except explicit per-source
  `snapshot` policy).
- **Git carries the index** — doc-major, sharded, human-readable JSONL;
  full per-document postings, an extracted link graph, and a source ledger,
  one line per document, sorted and content-sharded so
  git itself diffs and merges it —
  [`work/compare/index-format.compare.md`](work/compare/index-format.compare.md).
- **Answers verify themselves.** Rank in the index, fetch the cited
  documents live (through a version-keyed cache), re-score passages on the
  fetched bytes, cite the fresh sha. (The refer plane is M4; M1's `ask`
  cites straight from the committed index.)
- **Laws:** `$0`, FOSS-only (OSI-approved licences, SPDX-declared) ·
  byte-deterministic · offline by default · one ADR per feature, every rule
  referenced.
  ⚠ **`stdlib-only` was withdrawn 2026-09-06** — dependencies are permitted,
  must be OSI-licensed, and ship packaged. **Source-available licences (BSL,
  SSPL, Elastic v2, Commons Clause) do not qualify**
  ([ADR-LAW-1](docs/adr/0003_LAW-1-zero-cost.md)).

## The `.fux/` directory

Everything fux puts in your repo lives here, and **every child is declared** —
as `committed`, `derived`, or `acquired`
([ADR-DOTFUX](docs/adr/0012_fux-directory.md)). `fux doctor` warns about
anything that is not on this list.

| entry | kind | what it is |
|---|---|---|
| `index/` | committed | the sharded JSONL index |
| `sources/` | committed | the source lists — `dirs`, `urls` and `types`, one entry per line |
| `fetchers/` | committed | **your** code (`http.py`, `cdp.py`) — written by `fux setup`, never rewritten |
| `decoders/` | committed | **your** code, one module per format. **These copies are what run**, not the ones inside the installed package |
| `enrich/` | committed | pinned enrichment text plus `queue.tsv` — committed, because a backlog is a team fact |
| `tune.toml` | committed | **how** results are ordered — never what is indexed |
| `output.toml` | committed | **how** a result is shown — never which documents come back |
| `.fuxignore` | committed | what is **not** indexed, in `.gitignore`'s grammar |
| `pii.toml` | committed | what is **redacted from the committed index, and only from it** |
| `refusals.toml` | committed | what a **refusal** looks like here — the sign-in walls and error shells a server returns *instead of* the document |
| `runtime/` | derived | the accelerator segments, the TTL fetch cache at `runtime/fetch-cache/`, the write lock (gitignored, `CACHEDIR.TAG`) |
| `acquired/` | **acquired** | the bytes a fetch actually returned, for URLs whose line says `keep=true` |

⚠ **`acquired/` is a third kind, and the distinction is load-bearing.** It is
gitignored like `runtime/` and it is **not rebuildable** — a blob can only be
re-*acquired*, and only while the source is still reachable and you are still
signed in to it. That is exactly why it is worth keeping: it is what lets a
citation be checked when the source cannot be reached at all.

**Scaffolding has two moments.** Every `fux ingest` writes `.fux/README.md`
and a narrow `.fux/.gitignore` (derived names only, never `*`) if they are
missing, and never touches them again — a fresh clone has to be correct before
a byte is written. `fux setup` is the one that writes *code*: the fetchers and
the source lists, explicitly, once. **Ingest never puts a fetcher in a repo
that only wanted an index.**

**`fux doctor` is the one command that reads everything and changes nothing.**
It is offline and read-only by contract — it never fetches and never repairs.
It *fails* on the two things that break a repo silently: the committed index
git-ignored, and a `.fux/sources/types` with no live pattern. Everything else
is a **warning**, because a dead URL, a refused sign-in wall or a corpus with
no git history is a fact about the world rather than a broken install, and
failing on those trains people to ignore a red doctor. It reports the URL half
of the corpus, the acquired plane's size, whether your PII and refusal rules
compile *and what they actually redacted or refused*, whether every
`decoder=` binding still resolves, whether any document carries an `mtime`
(a corpus copied out of its git repository loses the whole recency prior and
nothing else says so), and the `as-ingested` share — which is the veto
condition of two accepted records. `fux doctor --json` is the machine-readable
form.

## Reading order

1. [`work/paper/the-fux-index-paper.md`](work/paper/the-fux-index-paper.md) — architecture + falsifiable predictions
2. [`work/compare/index-format.compare.md`](work/compare/index-format.compare.md) — the committed format, measured
3. [the ADR register](docs/adr/README.md) — milestones M0–M8
4. [`archive/adr-old/0004_index-format.md`](archive/adr-old/0004_index-format.md) — the frozen M1 schema, named here for orientation only (archive is not evidence — see [`archive/README.md`](archive/README.md))
5. [`../fux-playground/PLAYGROUND.md`](../fux-playground/PLAYGROUND.md) — a graded 10-doc corpus to try it on, in a **separate sibling repository** (clone it next to this one)
6. [`work/WORKLOG.md`](work/WORKLOG.md) — the running build log

License: MIT.
