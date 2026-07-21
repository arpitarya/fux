---
type: Reference
title: fux.toml — the annotated example
description: A complete, maintained example of Fux's config file — every shipped key with its default and meaning, plus proposed extensions clearly fenced. Update in the same change as any config-surface change.
timestamp: 2026-07-21T00:00:00Z
---

# fux.toml — the annotated example

*The **config contract**, maintained like [cli-examples.md](cli-examples.md): every
key below matches the shipped `src/fux/config.py` (v0.23.x); when a config key is
added/renamed/re-defaulted, update this file in the same change (registry
trigger). `fux setup` writes the `[sources]` section; everything else is
hand-added, and unknown keys/sections survive re-runs of setup untouched.*

## Complete as-shipped example (v0.23.x)

```toml
# fux.toml — lives at the project root; find_root walks up to locate it.
# Every value below shows its DEFAULT unless marked otherwise.

[sources]                        # written by `fux setup`; the only required section
docs   = ["docs", "~/notes/anton"]     # md/txt (+ office/PDF with the [ingest] extra)
code   = ["src"]                       # source files, fenced by language at ingest
data   = ["config"]                    # json (flattened) / yaml (fenced text)
images = ["assets/diagrams"]           # metadata stubs; OCR via --advanced

[ingest]
max_kb  = 256                    # per-file size cap (larger files are skipped, listed)
exclude = [                      # fnmatch patterns pruned during the walk — DEFAULTS:
  ".git", ".fux", "__pycache__", ".venv", "venv",
  "node_modules", ".DS_Store", "*.egg-info", "dist", "build",
]

[engine.bm25f]                   # the lexical ranker (compare/query-engine)
heading = 3.0                    # heading-path field weight
path    = 2.0                    # file-path field weight
body    = 1.0                    # body field weight
k1      = 1.2                    # BM25 term-frequency saturation
b       = 0.75                   # BM25 length normalization (must be ≤ 1)

[engine.hybrid]                  # the bundled-model semantic stage (v2)
enabled        = true            # false = lexical-only engine, no model load
rrf_k          = 60              # Reciprocal Rank Fusion constant
candidate_pool = 200             # BM25F candidates the dense pass re-ranks

[answer]
max_sentences = 5                # extractive-answer length cap (--answer-max overrides)

[engine.graph]                   # deterministic PPR-lite expansion (v3)
damping          = 0.85          # PageRank damping
iterations       = 3             # FIXED count, not a convergence test — reproducibility
max_expanded     = 10            # most expanded nodes kept per query
min_score        = 0.01          # ppr mass below this is noise
extracted_weight = 1.0           # edges read from artifacts (links, citations, tags)
inferred_weight  = 0.6           # semantic edges, if a host session ever writes them
hop_decay        = 0.8           # path reliability decay per hop
in_rrf           = true          # graph list joins fusion (open question 2 → ADR 0009)

[index]                          # storage backend + footprint profile (v3)
format           = "auto"        # json | sqlite | auto
profile          = "auto"        # full | lean | auto
sqlite_threshold = 25000         # chunks; above this, auto picks sqlite
lean_threshold   = 10000         # docs; below this, auto stays on full (see ADR 0011)
lean_cache_mb    = 200           # bounded LRU for re-derived chunks (lean only)
prefilter_width  = 500           # FuxVec Hamming candidates re-scored exactly

[git]
commit_cache = false             # true = also commit .fux/cache (knowledge-as-diffs)

[sources.web]                    # fenced network — only fetched by `fux ingest --web`
urls         = []                # crawl roots; empty = --web does nothing
max_depth    = 1                 # link levels below each root (0 = the page only)
same_domain  = true              # stay on each root's domain…
allow        = []                # …plus these extra domains, when same_domain
attachments  = ["pdf", "docx", "xlsx", "pptx"]   # linked files to download+convert
budget       = 50                # max pages+attachments fetched per run
delay_s      = 1.0               # politeness delay between fetches (robots.txt always obeyed)
max_fetch_kb = 2048              # per-fetch size cap
render       = "off"             # "cdp" = capture rendered DOM via your own headless Chrome
cdp_port     = 9222              # Chrome --remote-debugging-port to use
settle_ms    = 500               # post-load settle before DOM capture (cdp only)
max_age_days = 30                # url staleness horizon used by `fux ingest --check`
tier         = "curated"         # "mirror" = no page files at all; text lives in fux.db
```

**What git carries** (see [ADR 0008](adr/0008-substrate-store-lock-state.md)):
`fux.toml` and `fux.lock` at the root, plus `.fux/state/` — together the recipe
and enough state to answer immediately after a clone. `.fux/index/` is derived
and gitignored (`fux setup` writes the rule). `.fux/cache/` is rebuilt on clone;
committing it is opt-in via `[git] commit_cache`.

## Minimal real-world configs

**A notes folder, nothing else:**

```toml
[sources]
docs = ["~/notes"]
```

**A code project with its docs and a crawled wiki:**

```toml
[sources]
docs = ["docs", "README.md"]     # (individual files: proposed — see below)
code = ["src", "tests"]

[sources.web]
urls      = ["https://team.example.com/wiki/runbooks"]
max_depth = 2
budget    = 200
```

## Proposed extensions — NOT yet shipped

*Fenced here so the example never lies. `[index]`, `[engine.graph]`, `[git]` and
`[sources.web] tier/max_age_days` moved **above** this line in v0.23 — they ship.
What remains below is the source-spec work, still unimplemented.*

```toml
[sources]
docs  = ["docs", "notes/**/*.md", "!notes/private/**"]  # globs + ! excludes
files = ["whitepaper.pdf"]                              # individual files, first-class
lists = ["@sources-docs.txt"]                           # huge lists in @files (one entry/line)
```

## Related

[cli-examples.md](cli-examples.md) (what the commands do with this config) ·
[proposals/knowledge-substrate.md](proposals/knowledge-substrate.md)
(scale + graph + FuxVec proposal) · [GLOSSARY.md](GLOSSARY.md) (terms) · shipped parser:
[`src/fux/config.py`](../src/fux/config.py).
