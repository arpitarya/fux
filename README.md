# Fux

**Deterministic knowledge retrieval for AI-assisted codebases — rank from a
small git-carried index, fetch content from the systems that own it, verify
at answer time.**

> **Status (2026-08-10): T0 slice — `ingest` + `ask` work on this repo.**
> `src/fux/` exists. From a configured directory:
> ```bash
> fux ingest              # builds the committed .fux/index/*.jsonl
> fux ask "your question" # scans it, ranks with BM25F, cites the source file
> ```
> URLs can join the corpus through a consumer-owned middleware file
> (`.fux/middleware/cdp.py`, Chrome DevTools Protocol on pure stdlib) —
> list them one per line in `.fux/sources/urls`, then
> `fux ingest --refresh-urls`. ADR-0010 + ADR-0011 (both proposed).
> No accelerator yet (scan-only, ~100–200 ms class queries — correct M1
> behavior, not a bug) and no dense/graph query lanes (M2/M3). The v0.26
> engine and its docs are archived under
> [`archive/v0.26/`](archive/v0.26/), reference-only. The new architecture
> is specified in
> [`docs/paper/the-fux-index-paper.md`](docs/paper/the-fux-index-paper.md)
> (§4–§6 knowingly stale until M6) and built against
> [`docs/PLAN.md`](docs/PLAN.md).
>
> **The pruning gate closed (2026-08-09): FAIL.** Keeping only each
> document's top-*k* terms was measured, twice, against a corpus that could
> actually test it — no selector came within 35.9 points of preserving
> candidate recall at a 6 % budget. The committed index carries **full
> postings**, permanently — [ADR-0003](docs/adr/0003-pruning-criterion-rerun.md).

## The idea

- **Sources own content.** Repo docs stay in git; Confluence pages stay in
  Confluence. Fux never keeps a durable copy (except explicit per-source
  `snapshot` policy).
- **Git carries the index** — doc-major, sharded, human-readable JSONL;
  full per-document postings, dense binary codes, an extracted link graph,
  and a source ledger, one line per document, sorted and content-sharded so
  git itself diffs and merges it —
  [`docs/compare/index-format.compare.md`](docs/compare/index-format.compare.md).
- **Answers verify themselves.** Rank in the index, fetch the cited
  documents live (through a version-keyed cache), re-score passages on the
  fetched bytes, cite the fresh sha. (The refer plane is M4; M1's `ask`
  cites straight from the committed index.)
- **Laws:** $0 default · stdlib-only · byte-deterministic · offline by
  default · one ADR per feature, every rule referenced.

## The `.fux/` directory

Everything fux puts in your repo lives here, and every child is declared as
**committed** or **derived** ([ADR-0011](docs/adr/0011-fux-dir-layout.md)):

| entry | kind | what it is |
|---|---|---|
| `index/` | committed | the sharded JSONL index |
| `sources/` | committed | line-oriented source lists (`urls`) |
| `middleware/` | committed | **your** code (`cdp.py`) — fux never rewrites it |
| `runtime/` | derived | M2's accelerator segments (gitignored, `CACHEDIR.TAG`) |
| `cache/` | derived | M4's fetch cache (gitignored, `CACHEDIR.TAG`) |

Fux writes `.fux/README.md` and a narrow `.fux/.gitignore` (derived names
only, never `*`) if they are missing, and never touches them again. `fux
doctor` fails if the index has been git-ignored and warns about anything
undeclared.

## Reading order

1. [`docs/paper/the-fux-index-paper.md`](docs/paper/the-fux-index-paper.md) — architecture + falsifiable predictions
2. [`docs/compare/index-format.compare.md`](docs/compare/index-format.compare.md) — the committed format, measured
3. [`docs/PLAN.md`](docs/PLAN.md) — milestones M0–M8
4. [`docs/adr/0004-index-format.md`](docs/adr/0004-index-format.md) — the frozen M1 schema
5. [`examples/playground/PLAYGROUND.md`](examples/playground/PLAYGROUND.md) — a 20-doc fixture corpus to try it on
6. [`docs/WORKLOG.md`](docs/WORKLOG.md) — the running build log

License: MIT.
