# Fux

**Ask your own documents questions — offline, deterministic, `$0`, cited.**

Fux is a portable, agent-aware knowledge engine. `fux ingest` turns the folders
you configure into a git-versionable markdown corpus with provenance; `fux ask`
answers natural-language questions over it with ranked, `file:line`-cited
passages — no network, no API keys, no model calls, same answer every time.
Built for AI agents as much as humans: `--json` everywhere, `--explain` shows
*why* every result ranked, and generated hooks/skills teach agents to query the
corpus before guessing.

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
(drift; exit 1 when stale) · `--list-skipped` · `--list-inferred`.

Agent integration:

```bash
fux setup --agents --skills --hooks    # AGENTS.md + pointers, fux-query/fux-ingest skills,
                                       # Claude Code + Kiro hooks (fail-open, idempotent)
```

See [DOGFOOD.md](DOGFOOD.md) for the 10-minute real-project quickstart.

## What ingest understands (v1, inferred tier)

Markdown/txt natively (frontmatter preserved) · code fenced by language · JSON
flattened · YAML fenced · images as metadata stubs (dimensions via stdlib) ·
Office/PDF via the opt-in `ingest` extra. Two-tier by design: the fast inferred
pass runs by default; the advanced pass (OCR/layout, web, rendered pages) is
v1.1 — see `docs/handoff/`.

## Guarantees

- **`$0`, stdlib-only runtime** — zero third-party runtime dependencies; the
  frontmatter parser is hand-rolled on purpose.
- **Deterministic** — sorted walks, stable serialization, no wall-clock output:
  the same sources produce a byte-identical cache, index, and answers. No model
  ever sits in the maintenance path.
- **A corpus, not a disposable index** — `.fux/` is designed to be committed;
  knowledge changes become reviewable diffs.
- **Python ≥ 3.11.**

## Status

Rebuild in progress — **v1 (query CLI) shipped**; web/CDP/advanced ingest and
the hybrid engine are next ([docs/fux-plan.md](docs/fux-plan.md), build specs in
[docs/handoff/](docs/handoff/)). The previous implementation is archived under
[`archive/`](archive/). Docs are an OKF v0.1 bundle rooted at
[docs/index.md](docs/index.md).

## License

MIT — see [`LICENSE`](LICENSE).
