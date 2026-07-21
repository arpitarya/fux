---
type: Reference
title: CLI examples — input and output contract
description: Worked input/output examples for every fux command; the UX contract the implementation and e2e goldens must match. Maintained — update in the same change as any CLI surface or output-format change.
timestamp: 2026-07-21T00:00:00Z
---

# CLI examples — the input/output contract

*This document is the **UX contract**: what a user types and exactly what they see.
The e2e goldens (`tests_e2e/goldens/`) derive from these formats — when behaviour
changes deliberately, update this doc and the goldens in the same change (registry
trigger). Building agents: where a handoff is silent on output formatting, this doc
decides. Examples use the running fixture from
[`compare/query-output.compare.md`](compare/query-output.compare.md) — a corpus at
`~/notes/anton/` with `decisions/db-indexing.md`.*

*Updated 2026-07-21 to the **as-shipped v1 formats** (the pre-build sketches
deviated in places; each deviation is logged in
[`implementation.md`](implementation.md) → Deviations). Scores shown are raw BM25F
magnitudes, not 0–1 — the numbers in examples are illustrative, the shapes are
normative.*

Commands are decided in [`compare/cli-surface.compare.md`](compare/cli-surface.compare.md);
output formats in [`compare/query-output.compare.md`](compare/query-output.compare.md);
exit codes in [`../CLAUDE.md`](../CLAUDE.md) (0 ok · 1 error · 2 blocking · 130
interrupted).

## `fux setup` — first-time wizard

One prompt per source type; every prompt has a flag; prior answers become the
defaults on re-run; user-edited keys and unknown sections in `fux.toml` survive.

```
$ fux setup
Docs folders (md/txt/office) [docs]: ~/notes/anton
Code folders (py/js/…) [none]: src
Data folders (json/yaml) [none]: ⏎
Image folders (png/jpg) [none]: ⏎
wrote fux.toml  (docs: ~/notes/anton · code: src · data: — · images: —)
next: run `fux ingest`
$ echo $?
0
```

Non-interactive equivalents:

```
$ fux setup -y                                   # all defaults, no prompts
$ fux setup --docs docs,notes --code src -y      # flags (repeat or comma-separate)
$ fux setup --agents --skills --hooks -y         # agent surfaces (idempotent):
  created  AGENTS.md
  created  .claude/skills/fux-query/SKILL.md
  …
```

## `fux ingest` — build/refresh the corpus

```
$ fux ingest
Scanning 2 source roots…
  converted   41 markdown   (native)
  converted    3 json       (flattened, stdlib)
  converted    2 yaml       (fenced text)
  stubbed      4 images     (metadata only — advanced tier is v1.1)
  skipped      2            (see `fux ingest --list-skipped`)
Cache: .fux/cache  (50 files, OKF bundle)   Manifest: .fux/manifest.jsonl
Index: 1204 chunks (BM25F)   Elapsed: 1.8s
$ echo $?
0
```

Re-runs are incremental (`unchanged   50            (cache reuse)`); removed
sources are pruned (`removed      1            (sources gone; cache pruned)`).

Variants:

```
$ fux ingest --check                 # drift: sources changed since conversion?
  DRIFT  notes/anton/decisions/db-indexing.md  (sha mismatch — re-ingest)
  DRIFT  notes/anton/new-note.md  (new — not in manifest)
  DRIFT  notes/anton/old.md  (missing — source deleted; cache orphan)
3 stale of 50 · run `fux ingest` to refresh
$ echo $?                            # advisory by default
0
$ fux ingest --check --strict; echo $?     # blocking for CI/hooks
2

$ fux ingest --list-inferred         # every file at inferred fidelity
notes/anton/decisions/db-indexing.md  (native-md)
$ fux ingest --list-skipped          # what didn't ingest, and why
notes/anton/report.pdf  — requires the markitdown extra (pip install 'fux-engine[ingest]')

$ fux ingest --advanced papers/spec.pdf      # one file → advanced fidelity (docling/tesseract)
upgraded papers/spec.pdf → fidelity: advanced (docling); 1210 chunks indexed

$ fux ingest --web                   # crawl [sources.web] as well (fenced network:
                                     # robots.txt obeyed, depth/budget/domain caps)
  converted    6 web        (fenced network — html→md + attachments)
```

Web-origin entries cite their URL (`https://…/runbook.html`), carry
`url`/`parent`/`depth`/`fetched_at` provenance, persist across local-only
ingests, and are excluded from `--check` (web freshness = a `--web` re-crawl).
Rendered pages: `render = "cdp"` drives your own headless Chrome (hand-rolled
RFC 6455 client; `websocket-client` extra only as a flagged fallback).

```
```

## `fux ask` — ranked passages (the default intent)

```
$ fux ask "why did we pick a composite index for trades?"

notes/anton/decisions/db-indexing.md:12  (score 7.412)
  ## 2026-05 — Indexing the trades table
  We chose a composite index on (symbol, ts) over per-column indexes because
  every hot query filters by symbol then range-scans time. Rejected a covering
  index — write amplification on the tick ingest path was too high.

notes/anton/schema/trades.md:5  (score 3.121)
  trades(symbol, ts, price, qty, status) — composite PK on (symbol, ts).

2 passages · corpus 50 docs · 12ms
```

Long passages truncate at 4 lines (`… (N more lines; use -C 0 for all)`);
`-C N` controls it. Synthetic bodies (JSON, images, office) cite file-only —
no fabricated line numbers.

No confident hit (honest fallback, per query-output verdict):

```
$ fux ask "what is our kubernetes strategy?"
No confident matches.
Try: fux find "kubernetes strategy" · broaden the question · fux ingest new sources
$ echo $?
0
```

## `fux find` — which files

```
$ fux find "composite index decision"
1.  7.412  notes/anton/decisions/db-indexing.md
2.  3.121  notes/anton/schema/trades.md
3.  1.190  notes/anton/perf/ingest-path.md
```

## `fux answer` — extractive, cited answer

```
$ fux answer "why did we pick a composite index for trades?"

We chose a composite index on (symbol, ts) over per-column indexes because every
hot query filters by symbol then range-scans time. [1] Rejected a covering index —
write amplification on the tick ingest path was too high. [2]

Sources:
  [1] notes/anton/decisions/db-indexing.md:12
  [2] notes/anton/decisions/db-indexing.md:14

(extractive — sentences are verbatim from sources)
```

## Modifiers (all query verbs)

`--json` — machine-readable, the agent path. Emitted as one compact line;
pretty-printed here for readability:

```
$ fux ask "composite index" --json --top 1
{
  "query": "composite index",
  "results": [
    {
      "path": "notes/anton/decisions/db-indexing.md",
      "line_start": 12,
      "line_end": 15,
      "score": 7.412,
      "heading_path": ["2026-05 — Indexing the trades table"],
      "fidelity": "inferred",
      "text": "## 2026-05 — Indexing the trades table\nWe chose a composite index …"
    }
  ],
  "corpus": {"docs": 50, "chunks": 1204},
  "engine": "bm25f"
}
```

`fux find --json` results carry `path`/`score`/`matching_passages`/`fidelity`;
`fux answer --json` carries `answer`, `sentences` (`text`/`path`/`line`/
`citation`/`score`), and `sources` (`id`/`path`/`line`); all include
`corpus` + `engine`.

`--explain` — why each result ranked (rendered under each passage; contribution
apportioned per field by its share of the weighted tf):

```
$ fux ask "composite index" --explain
notes/anton/decisions/db-indexing.md:12  (score 7.412)
  …passage text…
  ├─ heading: index×1  (weight 3.0 → +0.512)
  ├─ path: indexing×1  (weight 2.0 → +0.190)
  └─ body: composite×2, index×3  (weight 1.0 → +0.121)
```

In `--json`, `explain` is per-term: `{"term", "idf", "tf": {heading,path,body},
"contribution"}`. `fux answer --explain` shows the per-sentence factor product
(`passage × (overlap + 0.05) × (0.5 + 0.5·centrality)`).

With hybrid (v2, handoff 0003) `--explain` adds RRF detail:
`bm25f rank 1 + dense rank 2 → rrf 0.0325`; `--lexical-only` restores the pure-v1
path.

## Errors (the contract in practice)

```
$ fux ask "anything"                # no fux.toml in this tree
fux: no fux.toml found (searched from /path upward) — run `fux setup` first
$ echo $?
1

$ fux ingest --check --strict       # drift found
$ echo $?
2

$ fux ask "…"                       # Ctrl-C mid-query
$ echo $?
130
```

Staleness is also surfaced passively: any query against a drifted corpus prints
`warning: sources changed since the last ingest — run `fux ingest` to refresh`
on stderr (stat-only probe; `--check` does the full sha comparison).

## Maintenance

This doc rows in [`DOC-REGISTRY.md`](DOC-REGISTRY.md). Trigger: **any change to a
command, flag, output format, or exit behaviour** — update the affected example, the
e2e goldens, and (if the surface changed) `compare/cli-surface.compare.md`, all in
the same change. Building agents (handoffs 0002–0003): treat these formats as
normative; deviations go through the implementation tracker's Deviations section
with a reason.
