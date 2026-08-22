# Fux

**Deterministic knowledge retrieval for AI-assisted codebases — rank from a
small git-carried index, fetch content from the systems that own it, verify
at answer time.**

> **Status (2026-08-22): `fux-engine` 1.0.0 on PyPI — M2 through M5 shipped.**
> The accelerator (M2), the graph lane (M3), the refer plane (M4) and the
> maintenance hooks (M5) are all in. From any repo:
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
> A dense lane exists behind `ask --hybrid` and is **off by default** — on the
> graded corpus it closes three known gaps and breaks nine working queries,
> so the default is a measurement rather than a preference.
>
> **The corpus is maintained with `fux add` / `fux remove` / `fux update`**
> (2026-08-21), over directories, single documents and URLs alike — the entry
> picks the list. `add` ingests by default; `remove` takes a document out of
> the index *and* the graph, deleting its line or subtracting it from a listed
> ancestor; `update` re-reads what is listed and never writes a line. They
> replace `fux url` and `fux ingest --refresh-urls`
> ([ADR-CLI](docs/adr/0002_cli-surface.md)).
>
> URLs join the corpus through a consumer-owned fetcher file. `fux setup`
> writes two — `http.py` (a plain stdlib GET, the default) and `cdp.py`
> (Chrome DevTools Protocol, also pure stdlib) — into `.fux/fetchers/`, where
> they become **your** code and fux never rewrites them. Add one with
> `fux add <URL> [--cdp] [--plain]`, which records the line **and fetches that
> one URL**. That and `fux update` are the engine's **two** networked paths;
> both say on stderr that they went out, and everything else is offline. A
> line picks its own fetcher; nothing escalates automatically
> ([ADR-URL-LIST](docs/adr/0018_url-list.md) ·
> [ADR-FETCHER](docs/adr/0019_fetcher.md)).
> **The graph lane has landed (M3, released in `0.34.0`)** — `explain`/`graph`/`path`,
> unseeded label-propagation communities, a lazy PPR walk
> ([ADR-GRAPH](docs/adr/0029_graph.md)). **Both acceptance gaps are closed**
> (2026-08-22): 24/24 on a graded 66-document corpus, and the derived
> `graph.json` hashes identically across two independent architectures
> ([the run](work/regression/2026-08-22-graph-acceptance/report.md)).
>
> **Archived content says so, and the ranking does not move.** A source
> declared `archived=true` carries `archived: true` on every verb, an
> `[archived]` marker in `ask`'s text, and a stderr disclaimer — while
> results stay byte-identical unless `[ranking] archived_weight` is set
> below its `1.0` default
> ([ADR-ARCHIVED-CONTENT](docs/adr/0037_archived-content.md)).
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
  full per-document postings, dense binary codes, an extracted link graph,
  and a source ledger, one line per document, sorted and content-sharded so
  git itself diffs and merges it —
  [`work/compare/index-format.compare.md`](work/compare/index-format.compare.md).
- **Answers verify themselves.** Rank in the index, fetch the cited
  documents live (through a version-keyed cache), re-score passages on the
  fetched bytes, cite the fresh sha. (The refer plane is M4; M1's `ask`
  cites straight from the committed index.)
- **Laws:** $0 default · stdlib-only · byte-deterministic · offline by
  default · one ADR per feature, every rule referenced.

## The `.fux/` directory

Everything fux puts in your repo lives here, and every child is declared as
**committed** or **derived** ([ADR-DOTFUX](docs/adr/0003_fux-directory.md)):

| entry | kind | what it is |
|---|---|---|
| `index/` | committed | the sharded JSONL index |
| `sources/` | committed | the source lists — `dirs` and `urls`, one entry per line |
| `fetchers/` | committed | **your** code (`http.py`, `cdp.py`) — written by `fux setup`, never rewritten |
| `runtime/` | derived | M2's accelerator segments, and M4's TTL fetch cache nested at `runtime/fetch-cache/` (gitignored, `CACHEDIR.TAG`) |

**Scaffolding has two moments.** Every `fux ingest` writes `.fux/README.md`
and a narrow `.fux/.gitignore` (derived names only, never `*`) if they are
missing, and never touches them again — a fresh clone has to be correct before
a byte is written. `fux setup` is the one that writes *code*: the fetchers and
the source lists, explicitly, once. **Ingest never puts a fetcher in a repo
that only wanted an index.**

`fux doctor` fails if the index has been git-ignored and warns about anything
undeclared.

## Reading order

1. [`work/paper/the-fux-index-paper.md`](work/paper/the-fux-index-paper.md) — architecture + falsifiable predictions
2. [`work/compare/index-format.compare.md`](work/compare/index-format.compare.md) — the committed format, measured
3. [the ADR register](docs/adr/README.md) — milestones M0–M8
4. [`archive/adr/0004_index-format.md`](archive/adr/0004_index-format.md) — the frozen M1 schema, named here for orientation only (archive is not evidence — see [`archive/README.md`](archive/README.md))
5. [`../fux-playground/PLAYGROUND.md`](../fux-playground/PLAYGROUND.md) — a graded 10-doc corpus to try it on, in a **separate sibling repository** (clone it next to this one)
6. [`work/WORKLOG.md`](work/WORKLOG.md) — the running build log

License: MIT.
