# Fux

**Ask your own documents questions — offline, deterministic, `$0`, cited.**

Fux is a portable, agent-aware knowledge engine. `fux ingest` turns the folders
you configure into a git-versionable markdown corpus with provenance; `fux ask`
answers natural-language questions over it with ranked, `file:line`-cited
passages — no network, no API keys, no external model, same answer every time.
Retrieval is **hybrid**: BM25F lexical search fused (RRF) with a **bundled
7.9 MB static-embedding model** inferred in pure stdlib — semantic recall for
paraphrased questions, still fully offline and deterministic
(`--lexical-only` preserves the pure-BM25F path byte-for-byte). Built for AI
agents as much as humans: `--json` everywhere, `--explain` shows *why* every
result ranked (per-term field hits, dense rank, RRF contribution), and
generated hooks/skills teach agents to query the corpus before guessing.

## Install

```bash
uv sync                 # dev install (Python ≥ 3.11)
uv run fux --version
```

Optional Office/PDF converters (never on the query path): `uv sync --extra ingest`.

## Use

```bash
fux setup                      # wizard → fux.toml (every prompt has a flag; -y for defaults)
fux ingest                     # sources → .fux/cache (OKF corpus) + manifest + BM25F index
fux ask "why did we pick X?"   # ranked passages with file:line + scores
fux find "deploy runbook"      # ranked files
fux answer "how do rollbacks work?"   # extractive, cited answer — never generated
```

Modifiers: `--json` (agent path) · `--explain` (why each result) · `--top N` ·
`-C N` (passage lines) · `--answer-max N`. Maintenance: `fux ingest --check`
(drift report; `--strict` exits 2) · `--list-skipped` · `--list-inferred`.

Web + fidelity upgrades (v1.1):

```bash
fux ingest --web                    # crawl [sources.web] (fenced: robots.txt obeyed,
                                    # depth/budget/domain caps — network never on the query path)
fux ingest --advanced report.pdf    # re-convert one source with Docling / tesseract OCR
                                    # → fidelity: advanced, better text, same citations
```

JS-rendered pages: set `render = "cdp"` under `[sources.web]` and Fux drives
your own headless Chrome over a hand-rolled RFC 6455 WebSocket client — no
bundled browser, no new dependencies.

Agent integration:

```bash
fux setup --agents --skills --hooks    # AGENTS.md + pointers, fux-query/fux-ingest skills,
                                       # Claude Code + Kiro hooks (fail-open, idempotent)
```

See [DOGFOOD.md](DOGFOOD.md) for the 10-minute real-project quickstart.

## What ingest understands (v1, inferred tier)

Markdown/txt natively (frontmatter preserved) · code fenced by language · JSON
flattened · YAML fenced · images as metadata stubs (dimensions via stdlib) ·
Office/PDF via the opt-in `ingest` extra · web pages (stdlib HTML→Markdown,
crawl with attachments, full `url`/`parent`/`depth` provenance) · rendered
pages via CDP. Two-tier by design: the fast inferred pass runs by default; the
advanced pass (Docling layout / tesseract OCR) upgrades exactly the files you
ask for and persists until the source changes.

## The corpus and its derived artifacts

Commit `.fux/cache/` + `.fux/manifest.jsonl` — that's the knowledge corpus,
with provenance, meant to live in git. `.fux/index/` (BM25F index + semantic
vectors) is derived and regenerable: gitignore it if you prefer a lean repo;
`fux ingest` rebuilds it incrementally either way.

## Guarantees

- **`$0`, stdlib-only runtime** — zero third-party runtime dependencies; the
  frontmatter parser, WebSocket client, and embedding inference are hand-rolled
  on purpose. The semantic model ships *inside* the wheel (≈7 MB) — nothing is
  ever downloaded at runtime.
- **Deterministic** — sorted walks, stable serialization, no wall-clock output:
  the same sources produce a byte-identical cache, index, and answers. No model
  ever sits in the maintenance path.
- **A corpus, not a disposable index** — `.fux/` is designed to be committed;
  knowledge changes become reviewable diffs.
- **Python ≥ 3.11.**

## Status

**v1 (query CLI), v1.1 (web/CDP/advanced ingest), and v2 (bundled-model hybrid
engine) are shipped** — v0.22.0, with an eval harness gating retrieval quality
([docs/fux-plan.md](docs/fux-plan.md), decisions in
[docs/adr/](docs/adr/)). Next: dogfooding in a real project
([DOGFOOD.md](DOGFOOD.md)). The previous implementation is archived under
[`archive/`](archive/). Docs are an OKF v0.1 bundle rooted at
[docs/index.md](docs/index.md).

## License

MIT — see [`LICENSE`](LICENSE).
