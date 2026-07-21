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
Cache: .fux/cache  (50 files, OKF bundle)   Lock: fux.lock
Index: 1204 chunks (BM25F)   Elapsed: 1.8s
$ echo $?
0
```

Re-runs are incremental (`unchanged   50            (cache reuse)`); removed
sources are pruned (`removed      1            (sources gone; cache pruned)`).

Variants:

```
$ fux ingest --check                 # three-way: state ↔ fux.lock ↔ sources
  DRIFT  notes/anton/decisions/db-indexing.md  (sha mismatch — re-ingest)
  DRIFT  notes/anton/new-note.md  (new — not in fux.lock)
  DRIFT  notes/anton/old.md  (missing — source deleted; cache orphan)
3 stale of 50 · run `fux ingest` to refresh
$ echo $?                            # advisory by default
0
$ fux ingest --check --strict; echo $?     # blocking for CI/hooks
2
```

`--check` reads **only `fux.toml` + `fux.lock`** — no index, no cache — so it
works on a fresh clone, before any ingest. Staleness is structural per source
kind:

- **`DRIFT`** — a `kind: file` source whose live sha ≠ the lock's (or is
  new/missing vs the lock).
- **`STALE`** — a `kind: url` source past its `max_age_days`; you cannot sha a
  page you have not re-fetched, so web freshness is age-based.

```
$ fux ingest --check
  STALE  web:vendor-wiki/sla-appendix  (fetched 41d ago, max 30d — re-run `fux ingest --web`)
1 stale of 50 · run `fux ingest` to refresh

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

## Fresh clone — queryable before you ingest

`.fux/state/` is committed (~200 B/doc), so a clone can answer at **document
level** immediately, from codes and term signatures alone. No index, no cache,
no network:

```
$ git clone git@github.com:acme/payments.git && cd payments
$ fux find "failover"
1.  web:vendor-wiki/sla-appendix        SLA appendix
2.  docs/adr/0007-vendor-selection.md   ADR 0007 — Vendor selection
2 docs · doc-level (committed state; run `fux ingest` for passages)
```

The trailing line is the honesty: these are documents, not passages, and the
ranking came from the lean plane. `fux ingest` (or `fux db pull`) builds the
runtime plane and restores full chunk-level behaviour:

```
$ fux ingest
$ fux find "failover"
1.  0.83104  web:vendor-wiki/sla-appendix
2.  0.41220  docs/adr/0007-vendor-selection.md
```

`fux ask` in state-only mode re-derives the top documents' text on demand
(deterministic converters make that equal to what was indexed) and reports it:

```
$ fux ask "what does the SLA say about failover?"
docs/adr/0007-vendor-selection.md  (doc-level)
  Contractual failover must complete within 15 minutes…

1 doc · re-derived from source · run `fux ingest` for ranked passages
```

## `fux cat` — print one document

Materializes any single document, wherever it lives: a curated cache file, a
bulk-tier row in `fux.db`, or a source Fux can re-derive on demand. The caller
does not need to know which — the doc id is the only handle.

```
$ fux cat web:vendor-wiki/sla-appendix
# SLA appendix

## Failover terms
Contractual failover must complete within 15 minutes of a declared outage.
…

$ fux cat docs/adr/0007-vendor-selection.md --out /tmp/adr7.md
wrote /tmp/adr7.md  (4812 bytes)
```

Unknown ids fail loudly rather than printing nothing, and suggest the locator:

```
$ fux cat docs/nope.md; echo $?
fux: no document 'docs/nope.md' in the corpus — try `fux find "nope"`
1
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

**Hybrid (v2, default when the bundled model ships):** the headline `score`
becomes the RRF value, `"engine": "hybrid"`, and every result carries a
`hybrid` object (`bm25f_rank`/`bm25f_score`/`dense_rank`/`similarity`/`rrf`).
`--explain` renders it as:

```
  bm25f rank 1 (score 7.412) + dense rank 2 (sim 0.8341) → rrf 0.03252
```

`--lexical-only` restores the pure-v1 path byte-for-byte (enforced by the
pre-v2 goldens); a missing bundle or an all-out-of-vocabulary query falls back
to lexical automatically (`"engine": "bm25f"` tells you which you got).

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

## A sample repo, end to end

A team's product repo, before Fux:

```
acme-payments/
├── src/                     # the service (agents read this natively — not fux's job)
├── docs/
│   ├── adr/0001-idempotency-keys.md
│   ├── runbooks/rollback.md
│   └── onboarding.md
├── notes/
│   ├── 2026-06-payments-postmortem.md
│   └── competitor-stripe-fees.pdf
└── README.md
```

**Day 0 — set up and build the corpus:**

```
$ cd acme-payments
$ fux setup --docs docs,notes --agents --skills --hooks -y
$ fux ingest
  converted   14 markdown   (native)
  skipped      1            (competitor-stripe-fees.pdf — install 'fux-engine[ingest]')
$ pip install 'fux-engine[ingest]' && fux ingest      # picks up the PDF
```

**After ingest — what the repo looks like:**

```
acme-payments/
├── src/  docs/  notes/  README.md          # untouched
├── fux.toml                                # the recipe's head — commit
├── fux.lock                                # sha/date ledger per source — commit
├── .fux/
│   ├── cache/                              # OKF corpus, mirrors sources
│   │   ├── docs/adr/0001-idempotency-keys.md      # + provenance frontmatter
│   │   ├── docs/runbooks/rollback.md
│   │   ├── notes/competitor-stripe-fees.md        # ← converted from the PDF
│   │   └── …/index.md                             # per-dir progressive disclosure
│   └── index/                              # DERIVED — gitignored
│       ├── manifest.jsonl                  # operational provenance (query joins)
│       ├── index.json                      # BM25F chunks (fux.db at scale)
│       └── vectors.bin                     # int8 chunk vectors
├── AGENTS.md                               # + CLAUDE.md/copilot/kiro pointers
└── .claude/skills/fux-query/  fux-ingest/  # one SKILL.md standard, all tools
```

**What git carries: the recipe, not the generated state.** `fux.toml` +
`fux.lock` are the committed pair — together they say what is in the corpus,
when it was taken, and whether it is stale. `.fux/index/` is derived and
gitignored (`fux setup` writes the rule). `.fux/cache/` is rebuilt on clone;
committing it is opt-in via `[git] commit_cache = true`, for teams that want
knowledge changes reviewable as diffs.

A fresh clone runs `fux ingest`, and every rebuilt source is verified against
`fux.lock` — a sha match proves it is provably the same corpus.

**Daily use — human:**

```
$ fux ask "do we retry failed captures?"          # → runbooks/rollback.md:31 cited
$ fux answer "why idempotency keys?"              # extractive, [1][2] cited
$ fux find "postmortem"                           # which files
$ fux ingest --check                              # anything stale?
```

**Daily use — the agent (the real customer), inside Claude Code/Copilot:**

```
Claude Code (UserPromptSubmit hook fires) →
  fux ask "capture retry policy" --json           # passages injected as context
  fux ask … --explain                             # agent verifies why it ranked
  fux ingest --list-inferred                      # sees the PDF is inferred-tier
  fux ingest --advanced notes/competitor-stripe-fees.pdf   # upgrades, re-asks
```

**Substrate-v2 era (proposed — [knowledge-substrate](proposals/knowledge-substrate.md); not shipped):** same repo,
`.fux/index/fux.db` replaces the two index files, and the one-kernel projections
arrive: `fux explain docs/adr/0001-idempotency-keys.md` (node view),
`fux graph "captures"` (map view), `fux path docs/adr/0001-… docs/runbooks/rollback.md`
(how the ADR connects to the runbook).

## Maintenance

This doc rows in [`DOC-REGISTRY.md`](DOC-REGISTRY.md). Trigger: **any change to a
command, flag, output format, or exit behaviour** — update the affected example, the
e2e goldens, and (if the surface changed) `compare/cli-surface.compare.md`, all in
the same change. Building agents (handoffs 0002–0003): treat these formats as
normative; deviations go through the implementation tracker's Deviations section
with a reason.
