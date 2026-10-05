<div align="center">

# fux

### Your team's docs, as a search index your AI agent can trust.

**Ranked. Cited. Checked against the source. Committed to git.**<br>
No server · no vector database · no API key · no model · zero dependencies

[![PyPI](https://img.shields.io/pypi/v/fux-engine?include_prereleases&label=pypi&color=3b82f6)](https://pypi.org/project/fux-engine/)
[![npm](https://img.shields.io/npm/v/fux-engine/alpha?label=npm&color=3b82f6)](https://www.npmjs.com/package/fux-engine)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3b82f6)](https://pypi.org/project/fux-engine/)
[![Dependencies: 0](https://img.shields.io/badge/dependencies-0-16a34a)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](LICENSE)

*fux is pronounced "fox".*

</div>

---

Your agent can read every line of your code. It still doesn't know **why** the
code is the way it is — that lives in ADRs, runbooks, specs, wiki pages and
the PDF someone attached to a ticket in 2023.

So it greps, guesses, or asks a vector database for "the nearest chunk" — and
gets an answer that sounds right, from a doc that went stale six months ago.

**fux fixes that with boring, auditable arithmetic:**

```console
$ fux answer "how do I roll back a release"
To roll back a bad release, run `make rollback` from the release branch.
The previous image tag is kept for 7 days.

  -- docs/deploy.md:L1-L6 (sha 18ac8c4e4d33, current)

$ fux ask --band "kubernetes autoscaling limits"
No confident matches.
confidence: none - nothing in the index scored for this query.
```

The first answer quotes exact lines and **proves they still say that today**.
The second one **refuses** — because your docs don't cover it, and a confident
wrong answer is worse than none.

<p align="center">
  <img src="https://raw.githubusercontent.com/arpitarya/fux/main/docs/architecture-high-level.png" alt="fux in three boxes: your documents stay put, a small index is committed to git, queries return ranked, cited answers" width="820">
</p>

## Why people use fux

| | `grep` / `rg` | Vector-DB RAG | **fux** |
|---|---|---|---|
| Ranks by relevance | ❌ | ✅ | ✅ BM25F, field-weighted |
| Runs with nothing hosted | ✅ | ❌ server, embeddings, key | ✅ |
| Same query → same result, every machine | ✅ | ⚠️ depends on model + chunker | ✅ byte-identical |
| Cites exact line ranges | lines, unranked | chunks | ✅ plus a **current / stale** verdict |
| Says "I don't know" | — | returns the nearest neighbour | ✅ confidence band |
| Index reviewable in a PR | — | ❌ opaque vectors | ✅ plain JSONL, diffs like code |
| Reads PDF, Word, Excel, slides, wikis | ❌ | depends | ✅ editable decoders |

- 🗂 **Clone and ask.** The index lives in `.fux/index/`. Every clone — yours, a
  teammate's, CI's, your agent's — searches the same thing. Nothing to deploy.
- 🔍 **Answers you can audit.** `answer` re-reads the cited lines from the
  source and tells you whether they still match. `--receipt` + `fux verify`
  lets anyone reproduce it later.
- 🤖 **Built for agents first.** `fux setup` drops ready-made skills and
  instructions for **Claude Code, Codex, GitHub Copilot and Kiro**, and
  `fux mcp` serves the index over MCP.
- 🔒 **Offline unless you ask.** No telemetry, no network on any default path,
  PII redaction before anything is committed.
- 🧾 **Your docs never move.** fux stores statistics, not content. Sources stay
  in the repo or in the system that owns them.

## 60-second quickstart

```bash
pip install --pre fux-engine     # Python ≥ 3.12 · Linux, macOS, Windows · zero deps
cd your-repo
fux setup                        # writes .fux/ and agent instructions (only missing files)
fux ingest                       # indexes README.md and docs/ by default
fux ask "how do we roll back a release"
git add .fux fux.toml && git commit -m "Add fux index"
```

That's it. Your teammates — and their agents — now get the same answers from a
plain `git clone`.

> **No Python on the machine?** `fux setup` vendors a single-file,
> zero-dependency Node reader into `.fux/node/`, so `.fux/fux find rollback`
> works with nothing installed. Or: `npx fux-engine find rollback`.

> **Prefer a library?**
> ```python
> from fux import open as fux_open
> fux_open(".").ask("how do we roll back a release")
> ```

## Plug it into your coding agent

```bash
fux setup        # skills + instructions for Claude Code, Codex, Copilot, Kiro, plus AGENTS.md
fux mcp          # MCP over stdio: fux_search, fux_passage, fux_related
```

The instructions teach the agent to **search the index before grepping**, read
the JSON (not the prose), and treat an archived document as history rather than
as the current design. There's deliberately no `answer` tool over MCP — **the
agent is the answerer; fux is the evidence.**
([SR-AGENT-POLICY](records/0132_agent-policy.md) · [SR-MCP](records/0136_mcp.md))

## What it can read

- **Text:** Markdown, reStructuredText, AsciiDoc, Org, plain text
- **Office & data:** PDF, Word, PowerPoint, Excel, CSV/TSV, JSON, YAML, TOML, INI, XML
- **Everything else:** HTML, email, draw.io, SVG, images (via your agent, `fux enrich`)
- **Web pages and wikis:** `fux add <url>` — plain HTTP, or through the session
  your **signed-in Chrome** already holds, so internal wikis work too

Every decoder and fetcher is copied into `.fux/` as **your** code — read it,
edit it, replace it ([SR-DECODE](records/0139_decode.md), [SR-FETCHER](records/0117_fetcher.md)).

## Everyday commands

| I want to… | Run |
|---|---|
| Rank documents for a question | `fux ask "…"` |
| One answer, quoted from the source | `fux answer "…"` |
| Just file paths, for piping | `fux find "…"` |
| Know why something ranked, or how sure fux is | `fux ask --why "…"` · `fux ask --band "…"` |
| Machine-readable output | add `--json` |
| Index another folder, file or URL | `fux add <path-or-url>` |
| Re-index after changes | `fux ingest` (or `fux hooks` to do it on every commit) |
| Fix a wrong answer, durably | `fux correct "<question>" <doc-that-answers-it>` |
| Follow links between docs | `fux explain <doc>` · `fux graph "…"` · `fux path <a> <b>` |
| Find duplicate, unreachable or boilerplate docs | `fux inspect` |
| Keep IDs whole (`RF 118` = `RF-118`) | `fux identifiers` |
| See it all in a browser | `fux serve` — Ask, Answer, Documents, Words, Index, Identifiers |
| Check the setup | `fux doctor` (read-only, offline) |

Full surface: `fux --help` and [SR-CLI](records/0101_cli-surface.md).

## Measured, not assumed

Every claim ships with a pre-registered bar and a published run — **including
the ones that failed.**

- ⚡ **27.2 ms** worst-case p95 for warm `ask --fast` over **8,870 RFCs**,
  against a 150 ms bar ([run](work/regression/2026-08-12-m2-accelerator/report.md)).
  The fast path must return byte-identical results to the full scan.
- 🕸 **24/24** on a graded 66-document graph corpus, with the derived graph
  hashing identically on x86-64 Linux and arm64 macOS
  ([run](work/regression/2026-08-22-graph-acceptance/report.md)).
- 🪦 **Failures kept on file.** Index pruning failed its gate
  ([verdict](work/regression/2026-08-09-pruning-rerun/VERDICT.md)). A dense
  embedding lane fixed 0 queries and broke 2 — so it was deleted.

## What fux is *not*

Honesty up front, so you don't find out the hard way:

- **Not code search.** No AST, no symbols, no call graph. Pair it with a
  code-graph tool; fux covers what you *wrote down*.
- **Not semantic magic.** Ranking is lexical. If your docs say "revert" and you
  ask "undo", use `--expand`, or teach it once with `fux correct`.
- **Not a chatbot.** fux finds and verifies evidence. Your agent (or you) writes
  the answer.

## Status

**`3.0.0` is in alpha** (`pip install --pre fux-engine`); `2.0.x` is the latest
stable line. The index format is versioned and fux tells you when to run
`fux ingest --full`. Every change is in [`CHANGELOG.md`](CHANGELOG.md).

⭐ **Star the repo** if fux saved your agent from one confident wrong answer —
it's how other people find it. 👀 **Watch → Custom → Releases** to hear when
3.0 goes stable.

## Under the hood

<details>
<summary><b>Architecture diagrams</b></summary>

- [The whole idea in one picture](work/architecture-high-level.svg)
- [How `ask` works](work/architecture-ask.svg) · [how `answer` works](work/architecture-answer.svg) · [decoders](work/architecture-decoders.svg)
- [Python and Node, component for component](work/architecture-two-readers.svg)
- [Every plane, what is committed and what isn't](work/architecture-detailed.svg)
- [The paper](docs/paper/the-fux-index-paper.md) — the architecture of record, with twenty diagrams

</details>

<details>
<summary><b>The thirteen laws fux is built under</b></summary>

Every decision of record lives in the [SR register](records/README.md)
([SR-LAWS](records/0001_LAWS.md)):
[L0 SRs are the source of truth](records/0002_LAW-0-authority.md) ·
[L1 a retired SR is archived](records/0003_LAW-1-retired-records-archived.md) ·
[L2 `$0`, FOSS-only](records/0004_LAW-2-zero-cost.md) ·
[L3 content never durable](records/0005_LAW-3-content-never-durable.md) ·
[L4 deterministic](records/0006_LAW-4-deterministic.md) ·
[L5 offline by default](records/0007_LAW-5-offline-by-default.md) ·
[L6 say "index"](records/0008_LAW-6-say-index.md) ·
[L7 Python ≥ 3.12](records/0009_LAW-7-python-312.md) ·
[L8 Node ≥ 22](records/0010_LAW-8-node-22.md) ·
[L9 use record never committed](records/0011_LAW-9-use-record.md) ·
[L10 build output, never source](records/0012_LAW-10-bundled-output.md) ·
[L11 the sealed answer key is closed to Claude](records/0013_LAW-11-sealed-answer-key.md) ·
[L12 every value lives in a config file](records/0014_LAW-12-values-live-in-config.md).
The laws were renumbered on 2026-09-28; an older document is read through
[SR-LAWS](records/0001_LAWS.md) decision 2a.

</details>

<details>
<summary><b>Security and sensitive text</b></summary>

- `.fux/pii.toml` redacts matches before anything reaches the committed index;
  fux will not run without it ([SR-PII](records/0148_pii.md)).
- `.fux/refusals.toml` stops a sign-in wall being indexed as the page behind it
  ([SR-REFUSAL](records/0146_refusals.md)).
- Only explicit, opt-in commands touch the network, and they say so on stderr
  ([L5](records/0007_LAW-5-offline-by-default.md)).

</details>

<details>
<summary><b>Reading order for contributors</b></summary>

1. [`docs/index.md`](docs/index.md) — the map of every doc in the repo
2. [The SR register](records/README.md) — every decision of record
3. [The paper](docs/paper/the-fux-index-paper.md) — what ships, what was measured, what was designed and not built
4. [Sibling environments](work/setup/README.md) — the sandbox, measurement lab and benchmark harness
5. [`CLAUDE.md`](CLAUDE.md) — how work is done here, for people and agents

</details>

## Contributing

```bash
pip install -e ".[dev]" && pytest
```

Issues and PRs welcome — bug reports with a failing query are gold. Every change
to an SR-owned component updates its owning record in the same commit; CI checks
it. Start with [`CLAUDE.md`](CLAUDE.md).

## License

[MIT](LICENSE) — free forever, FOSS-only dependencies forever ([L2](records/0004_LAW-2-zero-cost.md)).
