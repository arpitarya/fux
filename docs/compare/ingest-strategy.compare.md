---
type: Compare Doc
title: Ingest Strategy
description: Two-tier ingest (inferred → advanced/agent-triggered), OKF cache, provenance frontmatter, config-driven sources, web + CDP + OCR.
status: accepted
timestamp: 2026-07-21T00:00:00Z
---

# Ingest Strategy — Comparison

> **Verdict:** **`fux ingest` converts sources to Markdown into a config-defined
> cache, in two fidelity tiers.** A fast **inferred** pass runs by default (CLI walks
> the folders, converts everything to `.md`, marks each `fidelity: inferred`). An
> **advanced** pass (layout/table/OCR-aware) is triggered on demand — by Arpit or by
> an AI agent via the CLI — for a specific file when the inferred version is
> insufficient. A **manifest** tracks every converted file and its fidelity; the
> source directory for each file type lives in a **config file**. Extensions accepted
> 2026-07-20: every cached file carries **traceability frontmatter** (source, sha,
> fidelity, converter, origin/url/parent/depth); ingest is **library-first** (public
> `fux.ingest` API + CLI wrapper + an agent **skill**); and ingest handles **links
> and their attachments, multiple levels deep**, behind the fenced `--web` path.
> **Status:** ✅ Accepted (Arpit, 2026-07-20) — refined from the earlier "ingest
> cache" proposal · **Confidence:** High
> **Revisit when:** conversion fidelity on real Anton PDFs/decks proves inadequate,
> or the cache-staleness foot-gun bites (then add lazy auto-reconvert).

## Context

The query engine wants uniform text; real folders hold PDFs, `.docx`, `.xlsx`,
`.pptx`, and code. Conversion must never sit on the `$0` default *read* path (see
[`../../CLAUDE.md`](../../CLAUDE.md)) — it's fenced behind an explicit `fux ingest`.
Two things Arpit added over the base proposal: **(1)** conversion has two tiers — a
cheap inferred pass for everything and an expensive advanced pass on demand — so we
don't pay for high-fidelity extraction we may never need; **(2)** an agent, not just a
human, can request the advanced pass when it judges the inferred text too thin to
answer well. Plus: **source dirs per file type live in config**, and **inferred files
are tracked in a manifest** so their lower fidelity is visible and upgradable.

## The accepted design

### Two-tier extraction
- **Inferred (default, fast, cheap).** `fux ingest` walks the configured folders and
  converts every non-text file to Markdown with the fast converter (MarkItDown-class:
  ~12 s/100 pages, CPU-only, 15+ formats). Each output is stamped `fidelity: inferred`
  in the manifest. This is "good enough to search" for most docs.
- **Advanced (on demand).** `fux ingest --advanced <file>` (human) or the same command
  invoked by an agent re-converts one file with the layout-aware converter
  (Docling-class: preserves dense tables, multi-column, optional OCR). The manifest
  entry flips to `fidelity: advanced`. Trigger heuristics for the agent: the inferred
  `.md` for a hit-heavy file has broken tables, near-empty body, or the agent's answer
  confidence is low.

### The manifest (tracks inferred files)
`.fux/manifest.jsonl` — one JSON line per converted file:
```json
{"source": "papers/indexing.pdf", "type": "pdf", "sha256": "…",
 "fidelity": "inferred", "converter": "markitdown", "cache": ".fux/cache/papers/indexing.md",
 "converted_at": "2026-07-20T12:00:00Z"}
```
`fux ingest --list-inferred` prints every file still at inferred fidelity — the
"which docs could be upgraded?" view an agent (or Arpit) reads before an advanced pass.
`fux ingest --check` re-hashes sources and flags drift (source changed since convert).

### Config-driven source dirs (per file type)
`fux.toml` at the project root (parsed with stdlib `tomllib`):
```toml
[sources]
markdown = ["~/notes", "~/docs/anton"]
pdf      = ["~/papers"]
docx     = ["~/reports"]
xlsx     = ["~/finance"]
pptx     = ["~/decks"]
code     = ["~/projects/anton/src"]

[sources.web]                      # link ingestion (fenced network path — see below)
urls        = ["https://example.com/runbook"]
max_depth   = 2                    # follow links/attachments this many levels deep
same_domain = true                 # don't wander off-site by default
attachments = ["pdf", "docx", "xlsx", "pptx"]   # linked files to download+convert

[ingest]
cache             = ".fux/cache"
manifest          = ".fux/manifest.jsonl"
default_fidelity  = "inferred"        # inferred | advanced
fast_converter    = "markitdown"
advanced_converter = "docling"
```

### Per-file metadata — traceability frontmatter (Arpit's requirement)

Every converted/extracted `.md` in the cache carries a frontmatter block, so each file
is **self-describing** — maintenance and traceability don't depend on the manifest
alone (the manifest is the *index*; the frontmatter is the *provenance on the artifact
itself*):

```markdown
---
fux_ingest: 1                     # metadata schema version
source: papers/indexing.pdf       # original path, or URL for web ingests
source_sha256: "9f2c…"            # hash of the source at conversion time
origin: file                      # file | url | attachment
fidelity: inferred                # inferred | advanced
converter: markitdown             # tool + version that produced this text
converted_at: 2026-07-20T12:00:00Z
fux_version: 0.19.0
# web-ingested files additionally carry:
url: https://example.com/runbook/setup.pdf
parent: https://example.com/runbook          # the page whose link led here
depth: 1                                     # levels below the configured root
---
```

Parsed by the same hand-rolled stdlib frontmatter parser that is Fux's long-term core
— this is its first dogfood. **The cache is an OKF bundle** (accepted 2026-07-21):
each cached file adds the OKF-required `type: Ingested Document` plus recommended
`title`/`description`/`timestamp`; our provenance keys ride along as legal OKF
extensions (unknown keys must be preserved); per-directory `index.md` gives agents
progressive disclosure. Any OKF consumer can read a Fux cache cold — see CLAUDE.md
§"Follow the OKF pattern." `fidelity: inferred` in the file itself is what lets an
agent reading a cached doc *know* it's looking at a cheap extraction and request the
advanced pass. `fux ingest --check` compares `source_sha256` against the live source
to flag drift, per file, with no external index needed.

### File-type coverage — images, JSON, YAML, txt (accepted 2026-07-21)

Beyond office docs and code, ingest handles (each lands in the cache with the same
provenance frontmatter):

- **`.txt`** — native text; chunked directly, no conversion.
- **`.json`** — parsed with stdlib `json`; rendered to Markdown as a flattened
  key-path outline (`servers[0].host: alpha`) so keys become searchable terms, with
  the raw block preserved in a code fence. Large/machine-generated JSON can be capped
  (`max_kb`) or listed-not-inlined.
- **`.yaml`/`.yml`** — v1 ingests as fenced text (fully searchable lexically — BM25F
  doesn't need a parse). Structured flattening like JSON's is a later upgrade: the
  stdlib has **no YAML parser**, so that path needs either the hand-rolled subset
  parser (the held core's, once built) or an opt-in extra — never a runtime dep.
- **Images (`.png`/`.jpg`/…)** — the two-tier design absorbs these naturally:
  - **Inferred tier ($0, stdlib):** a metadata stub — filename, folder path, EXIF
    basics, dimensions — so an image is at least *findable* by name/context.
  - **Advanced tier (opt-in):** **OCR** — Tesseract (open-source, fully offline,
    100+ languages; the privacy/air-gap-friendly choice) or Docling's built-in OCR
    pipeline for scanned docs. Frontmatter records `converter: tesseract-ocr` so a
    citation reveals the text came from OCR. Research note: OCR quality is a
    first-class retrieval bottleneck — bad transcription, not ranking, is usually
    what loses the passage — which is exactly why OCR sits in the *advanced* tier
    where an agent can judge and re-extract.

### Rendered-page ingestion — Chrome DevTools Protocol (accepted 2026-07-21)

Plain `urllib` fetches raw HTML; JS-rendered pages (SPAs, docs portals, dashboards)
come back as empty shells. Arpit's call: ingest must also work **via the Chrome
DevTools Protocol (CDP)** so the *rendered* DOM can be captured.

**How CDP actually works (researched):** Chrome launched with
`--remote-debugging-port=9222` exposes an HTTP endpoint listing targets plus a
WebSocket URL per target; CDP is JSON-RPC over that WebSocket — any client that can
speak WebSockets and JSON can drive the browser, navigate, wait for render, and pull
the built DOM (`Runtime.evaluate` / `DOM.getDocument`).

**Design:** a `render = "cdp"` mode on the web source (per-URL or per-domain):

```toml
[sources.web]
urls   = ["https://spa-docs.example.com"]
render = "cdp"          # off (urllib, default) | cdp
```

- Uses the user's **existing Chrome/Chromium install** (headless) — we never bundle a
  browser.
- The stdlib has no WebSocket client, so the CDP client is **hand-rolled on stdlib
  `socket`/`hashlib`/`base64`** (RFC 6455 handshake + frames — a few hundred lines,
  same ethos as the hand-rolled frontmatter parser), with `websocket-client` as an
  optional extra fallback if the hand-rolled path proves brittle.
- Same fence as all web ingest: never on the query path; rendered captures carry the
  same provenance frontmatter (`origin: url`, `renderer: cdp`), so a cited answer
  reveals it came from a rendered page.
- Default stays `urllib` — CDP only fires where configured, since it's slower and
  requires a local Chrome.

### Link ingestion — crawl links and their attachments (fenced)

`fux ingest --web` (or configured `[sources.web]`) fetches each URL with stdlib
`urllib`, converts the page to Markdown, then follows links **multiple levels deep**
(up to `max_depth`), including **attachments found in links** (PDF/docx/… hit the same
convert pipeline as local files). Guardrails, because crawling is where scope creep
lives: depth-capped, `same_domain` by default, an allowlist override, per-run page
budget, and robots.txt respected. Every fetched artifact lands in the cache with
`origin: url|attachment`, `parent`, and `depth` frontmatter, so any answer citing it
traces back to the exact page it came from. **Network never touches the query path** —
it exists only inside the explicit ingest fence, keeping the air-gap story intact for
anyone who doesn't configure web sources.

### Reusable by other Python scripts + as a skill

Ingest is built **library-first**: the CLI is a thin wrapper over a public API —

```python
from fux.ingest import ingest_paths, ingest_url, list_inferred, check_drift
entries = ingest_paths(["~/reports"], fidelity="inferred")   # -> manifest entries
entry   = ingest_url("https://example.com/runbook", max_depth=2)
stale   = check_drift()                                       # sha mismatches
```

— so any Python script (Anton included) can ingest programmatically without shelling
out. On top of that, a **skill** (`skills/ingest/SKILL.md`, wired for Claude
Code/Cowork) teaches an agent the workflow: run inferred ingest, read
`--list-inferred`, judge extraction quality, trigger `--advanced` on thin files. The
skill is documentation over the same API/CLI — no separate code path.

## Options (top-level, for the record)

- **A — Ingest cache, two-tier.** As above. *(verdict)*
- **B — Parse-native at query time.** No ingest; parse every PDF/docx per query.
- **C — Lazy hybrid.** Ingest cache + auto-reconvert stale sources on query.

## Comparison matrix

| Criterion (weight) | A: Two-tier ingest | B: Parse-at-query | C: Lazy hybrid |
|--------------------|--------------------|-------------------|----------------|
| Keeps `$0` default read path (H) | Yes | No | Yes |
| Query latency (H) | Fast (pre-converted) | Slow | Fast |
| Pay only for fidelity you need (H) | **Yes (inferred→advanced)** | No (always full) | Partial |
| Agent can upgrade a file (M) | **Yes, by design** | N/A | Possible |
| Freshness (M) | Manual `--check` | Always fresh | Auto |
| Inspectability (M) | High (read the `.md` + manifest) | None | High |
| Implementation cost (M) | Moderate | Low | Higher |
| **Fit** | **Verdict** | Prototype only | Later upgrade |

## Converter choice

MarkItDown (Microsoft) as the fast/inferred converter — fast, CPU-only, many formats.
Docling (IBM Research) as the advanced converter — layout/table/OCR aware. pandoc as a
stable docx alternative. Code files need no converter (treat as text, language-fenced).
All converters are **opt-in extras**, never runtime deps; the query read path stays
pure text.

## References

- Internal: [`../../CLAUDE.md`](../../CLAUDE.md) — the `$0`/stdlib default read path the ingest fence protects.
- Internal: [`query-engine.compare.md`](query-engine.compare.md) — consumer of the converted text; [`packaged-model.compare.md`](packaged-model.compare.md) — the confidence signal that can trigger an advanced pass.
- External: [MarkItDown (Microsoft) — GitHub](https://github.com/microsoft/markitdown) — fast/inferred converter (accessed 2026-07-20).
- External: [Docling (IBM Research) — GitHub](https://github.com/docling-project/docling) — advanced, structure-aware converter (accessed 2026-07-20).
- External: [MarkItDown vs Docling vs Marker — deep dive](https://www.danilchenko.dev/posts/markitdown-vs-docling-vs-marker/) — the speed/fidelity split behind the two tiers (accessed 2026-07-20).
- External: [pandoc](https://pandoc.org/) — stable docx/text converter (accessed 2026-07-20).
- External: [Chrome DevTools Protocol — official docs](https://chromedevtools.github.io/devtools-protocol/) — the JSON-RPC-over-WebSocket protocol behind rendered ingestion (accessed 2026-07-21).
- External: [Using headless Chrome via the WebSockets interface](https://medium.com/@lagenar/using-headless-chrome-via-the-websockets-interface-5f498fb67e0f) — driving CDP with a bare WebSocket client, the pattern our hand-rolled client follows (accessed 2026-07-21).
- External: [RFC 6455 — The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455) — what the stdlib CDP client implements (accessed 2026-07-21).
- External: [Tesseract OCR](https://tesseractocr.org/) — open-source, fully offline OCR for the advanced image tier (accessed 2026-07-21).
- External: [Docling — OCR models](https://deepwiki.com/docling-project/docling/4.1-ocr-models) — OCR as a pluggable stage in the advanced converter (accessed 2026-07-21).
- External: [Reassessing benchmark gaps in visually rich RAG (arXiv:2603.04238)](https://arxiv.org/pdf/2603.04238) — OCR quality as a first-class retrieval bottleneck; grounds putting OCR in the judge-able advanced tier (accessed 2026-07-21).

## Additional things to look into

- **Provenance mapping:** cache must map converted-line → source file (+ PDF page) so
  citations point at the *original*. Advanced passes should preserve/improve this.
- **Cache in git?** `.fux/cache/` git-ignored by default; decide if converted `.md` is
  ever committed (good for review, noisy in diffs).
- **Agent trigger contract:** define the exact CLI surface the agent calls to request
  an advanced pass, and what signal (low answer confidence, empty body) justifies it.
- **Excel/PowerPoint fidelity:** keep a couple of real Anton files as a conversion
  smoke test — these convert unevenly.
