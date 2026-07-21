---
type: Reference
title: fux.toml — the annotated example
description: A complete, maintained example of Fux's config file — every shipped key with its default and meaning, plus proposed extensions clearly fenced. Update in the same change as any config-surface change.
timestamp: 2026-07-21T00:00:00Z
---

# fux.toml — the annotated example

*The **config contract**, maintained like [cli-examples.md](cli-examples.md): every
key below matches the shipped `src/fux/config.py` (v0.22.x); when a config key is
added/renamed/re-defaulted, update this file in the same change (registry
trigger). `fux setup` writes the `[sources]` section; everything else is
hand-added, and unknown keys/sections survive re-runs of setup untouched.*

## Complete as-shipped example (v0.22.x)

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
```

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

*Fenced here so the example never lies. These are the
[knowledge-substrate](proposals/knowledge-substrate.md) proposals awaiting
Arpit's verdict; they move above this line only when implemented.*

```toml
[sources]
docs  = ["docs", "notes/**/*.md", "!notes/private/**"]  # globs + ! excludes
files = ["whitepaper.pdf"]                              # individual files, first-class
lists = ["@sources-docs.txt"]                           # huge lists in @files (one entry/line)

[index]
format = "auto"                  # json | sqlite | auto — SQLite index v2 at scale
```

## Related

[cli-examples.md](cli-examples.md) (what the commands do with this config) ·
[proposals/knowledge-substrate.md](proposals/knowledge-substrate.md)
(scale + graph + FuxVec proposal) · [GLOSSARY.md](GLOSSARY.md) (terms) · shipped parser:
[`src/fux/config.py`](../src/fux/config.py).
