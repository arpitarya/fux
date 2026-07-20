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

Commands are decided in [`compare/cli-surface.compare.md`](compare/cli-surface.compare.md);
output formats in [`compare/query-output.compare.md`](compare/query-output.compare.md);
exit codes in [`../CLAUDE.md`](../CLAUDE.md) (0 ok · 1 error · 2 blocking · 130
interrupted).

## `fux setup` — first-time wizard

```
$ fux setup
fux setup — let's configure this project.

Source folders (markdown/text) [./docs]: ~/notes/anton
Add another source type? (pdf/docx/xlsx/pptx/code/none) [none]: code
  Code folders: ~/projects/anton/src
Cache location [.fux/cache]: ⏎
Generate agent files (AGENTS.md, skills, hooks)? [Y/n]: y

Wrote fux.toml
Wrote AGENTS.md, .github/copilot-instructions.md, .kiro/steering/fux.md
Wrote skills/fux-query/SKILL.md, skills/fux-ingest/SKILL.md
Installed hooks: claude-code (UserPromptSubmit, Stop), kiro

Next: fux ingest
$ echo $?
0
```

Non-interactive equivalents:

```
$ fux setup -y                                  # all defaults
$ fux setup --sources ~/notes/anton --code ~/projects/anton/src --agents --skills --hooks
$ fux setup --agents        # re-run just the agent-file step (idempotent)
```

## `fux ingest` — build/refresh the corpus

```
$ fux ingest
Scanning 2 source roots…
  converted  41 markdown   (native)
  converted   3 json       (flattened, stdlib)
  converted   2 yaml       (fenced text)
  stubbed     4 images     (metadata only — run --advanced for OCR)
  skipped     2 office     (markitdown extra not installed — see --list-skipped)
Cache: .fux/cache  (50 files, OKF bundle)   Manifest: .fux/manifest.jsonl
Index: 1,204 chunks (BM25F)                 Elapsed: 1.8s
$ echo $?
0
```

Variants:

```
$ fux ingest --check                 # drift: sources changed since conversion?
  DRIFT  notes/anton/decisions/db-indexing.md  (sha mismatch — re-ingest)
  1 stale of 50; exit 2 (blocking) when --strict, else exit 0 with report

$ fux ingest --list-inferred         # upgrade candidates (fidelity: inferred)
$ fux ingest --advanced papers/spec.pdf      # one file, layout/OCR converter (0002)
$ fux ingest --web                   # fenced web ingestion ([sources.web]) (0002)
```

## `fux ask` — ranked passages (the default intent)

```
$ fux ask "why did we pick a composite index for trades?"

notes/anton/decisions/db-indexing.md:12  (score 0.82)
  ## 2026-05 — Indexing the trades table
  We chose a composite index on (symbol, ts) over per-column indexes because
  every hot query filters by symbol then range-scans time. Rejected a covering
  index — write amplification on the tick ingest path was too high.

notes/anton/schema/trades.md:5  (score 0.32)
  trades(symbol, ts, price, qty, status) — composite PK on (symbol, ts).

2 passages · corpus 50 docs · 12ms
```

No confident hit (honest fallback, per query-output verdict):

```
$ fux ask "what is our kubernetes strategy?"
No confident matches (best score 0.04).
Try: fux find "kubernetes" · broaden the question · fux ingest new sources
$ echo $?
0
```

## `fux find` — which files

```
$ fux find "composite index decision"
1.  0.82  notes/anton/decisions/db-indexing.md
2.  0.32  notes/anton/schema/trades.md
3.  0.19  notes/anton/perf/ingest-path.md
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

`--json` — machine-readable, the agent path:

```
$ fux ask "composite index" --json --top 1
{
  "query": "composite index",
  "results": [
    {
      "path": "notes/anton/decisions/db-indexing.md",
      "line_start": 12,
      "line_end": 15,
      "score": 0.82,
      "heading_path": ["2026-05 — Indexing the trades table"],
      "fidelity": "inferred",
      "text": "We chose a composite index on (symbol, ts) …"
    }
  ],
  "corpus": {"docs": 50, "chunks": 1204},
  "engine": "bm25f"
}
```

`--explain` — why each result ranked (rendered under each passage):

```
$ fux ask "composite index" --explain
notes/anton/decisions/db-indexing.md:12  (score 0.82)
  …passage text…
  ├─ heading match: "Indexing the trades table"  (weight 3.0 → +0.51)
  ├─ path match:   "db-indexing.md"              (weight 2.0 → +0.19)
  └─ body tf:      composite×2, index×3          (weight 1.0 → +0.12)
```

With hybrid (v2, handoff 0003) `--explain` adds RRF detail:
`bm25f rank 1 + dense rank 2 → rrf 0.0325`; `--lexical-only` restores the pure-v1
path.

## Errors (the contract in practice)

```
$ fux ask "anything"                # no fux.toml in this tree
fux: no fux.toml found — run `fux setup` first
$ echo $?
1

$ fux ingest --check --strict       # drift found
$ echo $?
2

$ fux ask "…"                       # Ctrl-C mid-query
$ echo $?
130
```

## Maintenance

This doc rows in [`DOC-REGISTRY.md`](DOC-REGISTRY.md). Trigger: **any change to a
command, flag, output format, or exit behaviour** — update the affected example, the
e2e goldens, and (if the surface changed) `compare/cli-surface.compare.md`, all in
the same change. Building agents (handoffs 0001–0003): treat these formats as
normative; deviations go through the implementation tracker's Deviations section
with a reason.
