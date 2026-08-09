# DOGFOOD.md — point Fux at Anton in 10 minutes

Fux v1 answers natural-language questions over your own documents — offline,
deterministic, `$0`, with `file:line` citations. This is the quickstart for
dogfooding it on a real folder (Anton is instance zero).

## 1. Install (2 min)

From the Fux repo (editable, so fixes flow straight back):

```bash
cd ~/my_programs/fux
uv sync
```

Run everything below with `uv --project ~/my_programs/fux run fux …`, or
activate the venv once: `source ~/my_programs/fux/.venv/bin/activate`.

## 2. Configure inside Anton (2 min)

```bash
cd ~/my_programs/anton
fux setup            # wizard: point docs/code/data/images at real folders
# or non-interactive:
fux setup --docs docs,notes --code src --data config -y
```

This writes `fux.toml`. Re-running is always safe — it preserves your edits.

## 3. Ingest (1 min)

```bash
fux ingest
```

Sources become an OKF markdown corpus in `.fux/cache/` (provenance frontmatter,
per-dir `index.md`), plus a manifest and a BM25F index. Deterministic and
incremental — re-run it any time; unchanged files are untouched.
**Commit `.fux/` to git**: the corpus is a long-term asset, and its diffs are
knowledge changes.

Useful variants: `fux ingest --check` (drift, exit 1 when stale),
`--list-skipped` (what didn't ingest and why), `--list-inferred`.
PDFs/Office need the opt-in extra: `uv sync --extra ingest`.

## 4. Ask (2 min)

```bash
fux ask "why did we choose the current order-routing design?"
fux find "risk limits"
fux answer "how are positions reconciled at end of day?" --explain
```

- `ask` → ranked passages with `file:line` + scores (`-C 0` for full passages)
- `find` → ranked files
- `answer` → extractive, cited answer (never generated prose)
- `--json` on all three is the agent path; `--explain` shows *why* each result
  ranked (per-term field hits and contributions).

## 5. Wire your agents (2 min)

```bash
fux setup --agents --skills --hooks -y
```

Generates AGENTS.md (+ CLAUDE.md/copilot/Kiro pointers), the
`fux-query`/`fux-ingest` skills, and Claude Code hooks that inject relevant
passages on every prompt (fail-open — they can never break a session).

## What to watch for (all three phases are now shipped)

- **Retrieval quality** — the engine is hybrid (BM25F + bundled embeddings,
  RRF). Build the private Anton eval set (`tests_e2e/eval/README.md`) and run
  it; those numbers are the reopen instrument for the engine decisions.
  `--lexical-only` compares against pure v1 any time.
- **Thin conversions** — a PDF/image citation looks shallow? Check its
  `fidelity`; upgrade with `fux ingest --advanced <file>` (docling/tesseract).
- **Web sources** — add `[sources.web]` urls to fux.toml and run
  `fux ingest --web`; `render = "cdp"` for JS-rendered pages.
- Anything confusing or slow: note it in `docs/WORKLOG.md`.
