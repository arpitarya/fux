# CLI examples — the input/output contract

*This document is the **UX contract**: what a user types and exactly what they see.
The e2e goldens (`tests_e2e/goldens/`) derive from these formats — when behaviour
changes deliberately, update this doc and the goldens in the same change (registry
trigger). Building agents: where a handoff is silent on output formatting, this doc
decides. Examples use the running fixture from
[`compare/query-output.compare.md`](../compare/query-output.compare.md) — a corpus at
`~/notes/anton/` with `decisions/db-indexing.md`.*

*Updated 2026-07-21 to the **as-shipped v1 formats** (the pre-build sketches
deviated in places; each deviation is logged in
[`IMPLEMENTATION.md`](../IMPLEMENTATION.md) → Deviations). Scores shown are raw BM25F
magnitudes, not 0–1 — the numbers in examples are illustrative, the shapes are
normative.*

Commands are decided in [`compare/cli-surface.compare.md`](../compare/cli-surface.compare.md);
output formats in [`compare/query-output.compare.md`](../compare/query-output.compare.md);
exit codes in [`../CLAUDE.md`](../../CLAUDE.md) (0 ok · 1 error · 2 blocking · 130
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

## `fux explain` — one document, deep

`ask` seeded by a node instead of a question: the document's own distinguishing
terms become the query, so there is no second retrieval path to keep in sync.

```
$ fux explain docs/adr/0007-vendor-selection.md
docs/adr/0007-vendor-selection.md   ADR 0007 — Vendor selection
fidelity: inferred · 14 chunks

Outline: Context › Decision › SLA terms › Consequences

Edges:
  ├─ cites       → web:vendor-wiki/sla-appendix        [EXTRACTED]
  ├─ references  → docs/runbooks/failover.md           [EXTRACTED]
  └─ tagged      → tag:vendor                          [EXTRACTED]

Key passages:
  docs/adr/0007-vendor-selection.md:41  (score 3.219)
    Contractual failover must complete within 15 minutes of a declared outage.
```

`--json` returns `{node, outline, edges[], passages[]}`.

## `fux graph` — the neighbourhood of a topic

```
$ fux graph "vendor failover"
3 nodes · 4 edges

  docs/adr/0007-vendor-selection.md      ADR 0007 — Vendor selection      (seed)
  web:vendor-wiki/sla-appendix           SLA appendix                     (expanded)
  docs/runbooks/failover.md              Failover runbook                 (expanded)

  docs/adr/0007-vendor-selection.md ──cites──▶ web:vendor-wiki/sla-appendix
  docs/adr/0007-vendor-selection.md ──references──▶ docs/runbooks/failover.md
```

List form, not ASCII art: a rendered graph stops being readable past a handful
of nodes, and the list stays greppable and diff-friendly (handoff open
question 4).

## `fux path` — how two documents connect

```
$ fux path docs/adr/0007-vendor-selection.md docs/runbooks/failover.md
1 path (reliability 0.800):
  docs/adr/0007-vendor-selection.md ──references──▶ docs/runbooks/failover.md   [EXTRACTED]
```

When several routes exist each carries its own reliability, best first, and
`--hops N` widens the search (default 1):

```
$ fux path docs/adr/0007-vendor-selection.md docs/runbooks/failover.md --hops 2
2 paths:
  (reliability 0.800)
    docs/adr/0007-vendor-selection.md ──references──▶ docs/runbooks/failover.md   [EXTRACTED]
  (reliability 0.512)
    docs/adr/0007-vendor-selection.md ──cites──▶ web:vendor-wiki/sla-appendix   [EXTRACTED]
    web:vendor-wiki/sla-appendix ──references──▶ docs/runbooks/failover.md   [EXTRACTED]
```

Reliability is the product of per-edge grade weights (EXTRACTED 1.0, INFERRED
0.6) times a 0.8 decay per hop, so a long chain of inferences never outranks
one recorded fact. When nothing connects them, it says so rather than
manufacturing a route:

```
$ fux path docs/a.md docs/unrelated.md; echo $?
no recorded path from docs/a.md to docs/unrelated.md (within 1 hop)
0
```

## Fresh clone — queryable before you ingest

`.fux/state/` is committed (~200 B/doc plus the df sidecar), so a clone answers
immediately, with **no index, no cache and no network**:

```
$ git clone git@github.com:acme/payments.git && cd payments
$ fux find "failover"
1.  0.83104  web:vendor-wiki/sla-appendix
2.  0.41220  docs/adr/0007-vendor-selection.md
```

Those are the **same rankings and the same scores** `fux ingest` would produce.
Not an approximation: the clone re-derives its candidate documents from the
sources (deterministic converters, verified against `fux.lock`) for exact term
frequencies, and reads exact document frequencies and corpus statistics from
the committed `state/df/` sidecar. Every input the scorer sees is the input the
full profile would have handed it.

`fux ingest` (or `fux db pull`) then builds the runtime plane, which changes
speed, not answers.

**When sources aren't there to re-derive** — a corpus of crawled pages, or a
clone taken without its documents — the lean path cannot score, and Fux says so
rather than guessing. It falls back to doc-level ranking from codes and Bloom
signatures alone:

```
$ fux find "failover"
1.  web:vendor-wiki/sla-appendix        SLA appendix
2.  docs/adr/0007-vendor-selection.md   ADR 0007 — Vendor selection
2 docs · doc-level (committed state; run `fux ingest` for ranked passages)
```

The trailing line is the honesty: those are documents, not scored passages.

## `fux db pull` — fetch a prebuilt index

Nobody should re-crawl 100k pages on a laptop. CI builds `fux.db` once, and
everyone else pulls it — **sha-verified against `fux.lock`**, so a pulled index
is provably the corpus the lock describes:

```
$ fux db pull https://artifacts.acme.internal/payments/fux.db
  fetched  148.2 MB
  verified sha256 9f2c… against fux.lock
  wrote    .fux/index/fux.db
```

Auth is an env var, not a flag, so credentials stay out of shell history:

```
$ FUX_DB_AUTH="Bearer $CI_TOKEN" fux db pull https://…/fux.db
```

A mismatch is refused outright — a wrong index is worse than no index, because
it answers confidently:

```
$ fux db pull https://…/stale.db; echo $?
fux: sha256 mismatch — the artifact is not the corpus fux.lock describes
     expected 9f2c…  got 41ab…
     (run `fux ingest` to build locally, or ask for a rebuilt artifact)
1
```

This is the one place besides ingest where Fux touches the network, and it is
always an explicit user action — never a query.

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

## `fux doctor` — diagnose the whole install/corpus

Seven groups (environment, capabilities, config, corpus, consistency, agent
surface, self-test); exit 0 healthy, 1 problems found. Every failing check
prints **what is wrong, why it matters, and the exact fix command**:

```
$ fux doctor
[✓] environment
  ok  fux version: fux 0.24.0
  ok  python version: 3.12.4
  ok  install path: /…/site-packages/fux
  ok  bundled model: present, sha256 verified (7926518 bytes)
[✓] capabilities
  ok  markitdown: not installed — pip install 'fux-engine[ingest]'
  ok  docling: not installed — pip install docling
  ok  tesseract: not installed — brew install tesseract (macOS) / apt install tesseract-ocr (Linux)
  ok  Chrome for CDP: not installed — install Google Chrome/Chromium, …
  ok  websocket-client (CDP fallback): not installed — pip install websocket-client (optional)
[✗] config
  ok  fux.toml: /repo/fux.toml
  ok  [sources] docs = 'docs': 41 files
  FAIL  [sources] docs = 'notes/private': directory exists but matches 0 files
        why: the #1 silent misconfig — this entry contributes nothing, and `fux ingest` will not warn you
        fix: check fux.toml — did you mean a different directory for [sources] docs?
  ok  [ingest] exclude: .git, .fux, __pycache__, .venv, venv, node_modules, .pytest_cache, dist
[✓] corpus
  ok  manifest: 50 sources tracked
  ok  fux.lock: present
  ok  state plane (.fux/state/): present
  ok  index: json · 50 docs · 1204 chunks
  ok  cache (.fux/cache/): 812004 bytes
  ok  index (.fux/index/): 2140812 bytes
[✓] consistency
  ok  drift (source ↔ lock): 0 drifted
  ok  stale (web max_age_days): 0 stale
  ok  desync (state ↔ lock): 0 desynced
[✓] agent surface
  ok  AGENTS.md: present
  ok  skill: fux-query: present
  ok  skill: fux-ingest: present
  ok  skill: fux-debug: present
  ok  hooks (.claude/settings.json): wired
[✓] self-test
  ok  ingest → index → query → citation: ok

problems found — see FAIL rows above
$ echo $?
1
```

`--json` mirrors the same structure (`{"healthy": bool, "groups": [{"name",
"ok", "checks": [{"name","ok","detail","why"?,"fix"?}]}]}`) — stable enough for
CI gating (handoff 0005 open question 2 → ADR 0012). **Capabilities never fail
health** (they're optional paths, reported for information); every other group
can. A missing `fux.toml` short-circuits after the `config` group — there is no
corpus to diagnose yet. The **self-test** group ingests a throwaway canary
document in a scratch temp dir, queries it, and asserts its own citation
resolves — proving ingest→index→query end to end without touching the real
corpus.

## `fux why` — negative-result explanation

`--explain` only explains results that *appeared*; `why` walks the pipeline for
**one named document** and reports the first place it fell out, ending in a
single verdict sentence — everything above the verdict is evidence:

```
$ fux why "install the widget" --doc docs/guide.md
docs/guide.md
  in corpus: True  (cache=.fux/cache/docs/guide.md  fidelity=inferred)
  chunks: 1
    ✓ Widget Guide:6-35
  lexical: rank=1 score=6.0213 in_pool=True (pool=200)
    install: idf=1.8971 tf={'heading': 0, 'path': 0, 'body': 4} contribution=2.7095
    …
  dense: similarity=0.83 in_prefilter=True hamming=41 (width=500)
  graph: reached=True as=seed via=None edge=None

verdict: returned: rank 1 at --top 5
```

A document that ranks but falls outside the requested `--top`:

```
$ fux why "install the widget" --doc "docs/unicode-café.md" --top 1
…
verdict: not returned at --top 1: rank 6 overall (raise --top to 6 to see it)
```

A document skipped at ingest (never reaches the pipeline at all):

```
$ fux why "anything" --doc docs/binary.md
docs/binary.md
  in corpus: False  (binary content)

verdict: not in corpus: binary content
```

The **full negative case** — no lexical overlap, no dense rescue, no graph edge:

```
verdict: not returned: no lexical overlap, no dense candidate (cosine 0.19, not
among the 500 nearest FuxVec codes), no edge from any seed
```

`--json` mirrors the same walk (`{doc, in_corpus, corpus_detail, chunks[],
lexical, dense, graph, verdict}`); `--lexical-only` evaluates the pure BM25F
path and omits `dense` entirely. `--top N` matches the `--top` a normal query
would use, so the verdict answers "would a normal call have shown me this?"

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

**Substrate-v2 era (proposed — [knowledge-substrate](../proposals/knowledge-substrate.md); not shipped):** same repo,
`.fux/index/fux.db` replaces the two index files, and the one-kernel projections
arrive: `fux explain docs/adr/0001-idempotency-keys.md` (node view),
`fux graph "captures"` (map view), `fux path docs/adr/0001-… docs/runbooks/rollback.md`
(how the ADR connects to the runbook).

## Maintenance

This doc rows in [`DOC-REGISTRY.md`](../DOC-REGISTRY.md). Trigger: **any change to a
command, flag, output format, or exit behaviour** — update the affected example, the
e2e goldens, and (if the surface changed) `compare/cli-surface.compare.md`, all in
the same change. Building agents (handoffs 0002–0003): treat these formats as
normative; deviations go through the implementation tracker's Deviations section
with a reason.
