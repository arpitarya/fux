# fux

<div align="center">

## Your team's docs, as a search index your AI agent can trust.

**Ranked. Cited. Checked against the source. Committed to git.**<br>
No server · no vector database · no API key · no model · zero dependencies

[![PyPI](https://img.shields.io/pypi/v/fux-engine?label=pypi&color=3b82f6)](https://pypi.org/project/fux-engine/)
[![npm](https://img.shields.io/npm/v/fux-engine?label=npm&color=3b82f6)](https://www.npmjs.com/package/fux-engine)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3b82f6)](https://pypi.org/project/fux-engine/)
[![Node 22+](https://img.shields.io/badge/node-22%2B-3b82f6)](node/README.md)
[![Dependencies: 0](https://img.shields.io/badge/dependencies-0-16a34a)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](LICENSE)

*fux is pronounced "fox".*

[Quickstart](#60-second-quickstart) · [Agents](#plug-it-into-your-coding-agent) · [Commands](#everyday-commands) · [Measured](#measured-not-assumed) · [Is it for you?](#is-fux-for-you) · [Roadmap](#roadmap) · [FAQ](#faq)

</div>

---

Your agent can read every line of your code. It still doesn't know **why** the code is the way it is. That lives in ADRs, runbooks, specs, wiki pages, and the PDF someone attached to a ticket in 2023.

So it greps, guesses, or asks a vector database for "the nearest chunk". It gets back an answer that sounds right, from a doc that went stale six months ago.

**fux fixes that with boring, auditable arithmetic:**

```console
$ fux answer "how do I roll back a release"
# Deploying and rolling back

# Deploying and rolling back

To roll back a bad release, run `make rollback` from the release branch.
The previous image tag is kept for 7 days.

Deploys go out from `main` every weekday at 10:00.

  -- docs/deploy.md:L1-L6 (sha 6155f9c4ddf7, current)

$ fux ask --band "kubernetes autoscaling limits"
No confident matches.
confidence: none - nothing in the index scored for this query.
```

- **The first answer** quotes the exact lines it came from, and **checks that they still say that today**.
- **The second one refuses.** Your docs don't cover the question, and a confident wrong answer is worse than none.

**Edit the source, and the same answer tells you:**

```console
$ fux answer "how do I roll back a release"
note: 1 source(s) changed: docs/deploy.md.
…
  -- docs/deploy.md:L1-L7 (sha a76c0744a2dc, stale)
```

<p align="center">
  <img src="https://raw.githubusercontent.com/arpitarya/fux/main/docs/architecture-high-level.png" alt="fux in three boxes: your documents stay put, a small index is committed to git, queries return ranked, cited answers" width="820">
</p>

## In plain words

- **fux is a card catalogue for your team's documents.** It doesn't copy the books; it notes which words are on which pages.
- **The catalogue lives in your git repo**, so everyone who clones it, and every AI assistant they use, searches the same thing.
- **Ask a question and fux points to the page**, quotes the lines, and tells you whether the page has changed since it was catalogued.
- **If nothing in your documents answers it, fux says so** instead of guessing.
- **No AI runs inside fux**, so the same question gets the same answer on every machine.

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

- 🗂 **Clone and ask.** The index lives in `.fux/index/`. Every clone searches the same thing: yours, a teammate's, CI's and your agent's. Nothing to deploy.
- 🔍 **Answers you can audit.** `answer` re-reads the cited lines from the source and says whether they still match. `--receipt` records the index, settings and source shas an answer came from, and `fux verify` checks a receipt against the tree.
- 🤖 **Built for agents first.** `fux setup` writes ready-made skills and instructions for **Claude Code, Codex, GitHub Copilot and Kiro**. `fux mcp` serves the index over MCP, `fux lsp` serves it to your editor, and `fux llms` prints it as an [llms.txt](llms.txt).
- 🔒 **Offline unless you ask.** No telemetry and no network on any default path. PII is redacted before anything is committed.
- 🧾 **Your docs never move.** fux stores statistics, not content. Sources stay in the repo or in the system that owns them.

## 60-second quickstart

```bash
pip install fux-engine           # Python ≥ 3.12 · Linux, macOS, Windows · zero deps
cd your-repo
fux setup                        # writes .fux/, fux.toml and the agent instructions
fux ingest                       # indexes README.md and docs/ by default
fux ask "how do we roll back a release"
git add .fux fux.toml && git commit -m "Add fux index"
```

That's it. Your teammates, and their agents, now get the same answers from a plain `git clone`.

- **What gets indexed** is listed in `.fux/sources.yaml` (`README.md` and `docs` to start). Anything you don't want indexed goes in `.fux/.fuxignore`.
- **`fux ingest`** reports what it did: `ingested 3 docs (3 changed, 0 carried forward), 0 not indexed, 0 skipped, 3 shards written`.
- **`fux doctor`** checks the setup. It's read-only and offline.

> **No Python on the machine?** Install the single-file, zero-dependency Node reader from npm — `npm install fux-engine`, then `npx fux find rollback` (Node ≥ 22; the package's `bin` is `fux`). **That is the only way to get it**: `fux setup` no longer vendors a copy into `.fux/node/` or writes a `.fux/fux` shim, so a clone with nothing installed no longer answers from Node — one package install first. A repository pins it by listing `fux-engine` in its own `package.json`.

> **A machine that only reads, or only writes?** Since 4.0.0, fux ships as four packages on one version. `fux-engine` is all of them. `fux-reader` ranks and answers, `fux-writer` ingests and keeps the index current, and `fux-core` is what both share. A verb from a package you didn't install is refused by name.

> **Prefer a library?**
> ```python
> from fux import open as fux_open
> fux_open(".").ask("how do we roll back a release")
> ```

> [!NOTE]
> **Coming in the next release: decoders as packages** (built on `main`, not yet published). fux-engine will read Markdown and plain text on its own. Every other format will be read by a `fux-decoder-*` package that your repository declares in the committed `.fux/config/plugins.toml`, pinned to one version and digest. Upgrading will be a one-time step: run `fux setup`, run the one `pip install …` line it prints, and commit `.fux/config/plugins.toml`. The details are under *Unreleased* in [`CHANGELOG.md`](CHANGELOG.md).

## Plug it into your coding agent

```bash
fux setup        # skills + instructions for Claude Code, Codex, Copilot, Kiro, plus AGENTS.md
fux mcp          # MCP over stdio: fux_search, fux_passage, fux_related
fux lsp          # LSP over stdio: search, link hovers, backlinks, archived-link warnings
fux llms --full  # an llms-full.txt of the corpus, to stdout
```

**VS Code:** install the `.vsix` from the [latest release](https://github.com/arpitarya/fux/releases/latest) with `code --install-extension fux-<version>.vsix`. It registers `fux mcp` for agent mode automatically and runs `fux lsp`, so there's no `mcp.json` to write ([`vscode/`](vscode/README.md) · [SR-VSCODE](records/0164_vscode.md)).

- **The instructions teach the agent to search the index before grepping**, to read the JSON rather than the prose, and to treat an archived document as history rather than as the current design.
- **There's deliberately no `answer` tool over MCP.** The agent is the answerer; fux is the evidence ([SR-AGENT-POLICY](records/0132_agent-policy.md) · [SR-MCP](records/0136_mcp.md)).
- **Turn the agent files off** with `[agents] install = []` in `fux.toml`, or with `fux setup --no-agents`.

## What it can read

- **Text:** Markdown, reStructuredText, AsciiDoc, Org, plain text
- **Office & data:** PDF, Word, PowerPoint, Excel, CSV/TSV, JSON, JSONL, YAML, TOML, INI, XML, RTF
- **Everything else:** HTML, email, draw.io, SVG, images (via your agent, `fux enrich`)
- **Web pages and wikis:** `fux add <url>`, over plain HTTP or through the session your **signed-in Chrome** already holds, so internal wikis work too

In 4.1, every decoder and fetcher is copied into `.fux/` as **your** code, for you to read, edit or replace ([SR-DECODE](records/0139_decode.md), [SR-FETCHER](records/0117_fetcher.md)).

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
| List what is in the index, one line per document | `fux register` (`--json` for scripts) |
| See it all in a browser | `fux serve`: Ask, Answer, Documents, Words, Index, Identifiers |
| Check the setup | `fux doctor` (read-only, offline) |

`fux ask --why` shows its working:

```console
$ fux ask --why "how many times do we retry a card"
[why] reachable 3 -> window 2 -> placed 2 -> answered 1 (cut at 0.4903)
       #1 docs/adr-007-retries.md 2.7167  matched retry,card  absent many,times,do
       #2 README.md 0.4903  matched card  absent many,times,do,retry
```

Full surface: `fux --help` and [SR-CLI](records/0101_cli-surface.md).

## Measured, not assumed

Every claim ships with a pre-registered bar and a published run, **including the ones that failed.**

- ⚡ **27.2 ms** worst-case p95 for warm `ask --fast` over **8,870 RFCs**, against a 150 ms bar ([run](work/regression/2026-08-12-m2-accelerator/report.md)). The fast path must return byte-identical results to the full scan.
- 🕸 **24/24** on a graded 66-document graph corpus, with the derived graph hashing identically on x86-64 Linux and arm64 macOS ([run](work/regression/2026-08-22-graph-acceptance/report.md)).
- 🪦 **Failures kept on file.** Index pruning failed its gate ([verdict](work/regression/2026-08-09-pruning-rerun/VERDICT.md)). A dense embedding lane fixed 0 queries and broke 2, so it was deleted ([verdict](work/regression/2026-08-24-dense-lane-gate/VERDICT.md)).

## Is fux for you?

**Choose fux when:**

- your agents keep answering from **stale or invented** context, and you want every answer tied to lines you can check;
- your knowledge is **spread across formats**: Markdown, PDFs, Office files, wiki pages;
- you want search that works on a fresh clone and in CI, with **nothing to host and no key to manage**;
- you need answers that are **reproducible and auditable**, such as for regulated or review-heavy work.

**Look elsewhere when:**

- **you want code search.** fux has no AST, no symbols and no call graph. Pair it with a code-graph tool; fux covers what you *wrote down*.
- **you want semantic matching out of the box.** Ranking is lexical. If your docs say "revert" and you ask "undo", use `--expand`, or teach it once with `fux correct`.
- **you want a chatbot.** fux finds and verifies evidence. Your agent, or you, writes the answer.

## Roadmap

From the live queue, [`work/OPEN-WORK.md`](work/OPEN-WORK.md):

| | what | state |
|---|---|---|
| ✅ | Index-and-refer engine, Python and Node readers, MCP, LSP, VS Code extension | released, 4.1 |
| 🔜 | Decoders as `fux-decoder-*` packages, declared in `.fux/config/plugins.toml` | built on `main`; next release |
| 🔜 | Live URL-source checks: a vanished source, a real rate limit, parallel signed-in fetches | checklist written; waiting on a hands-on session |
| 🧭 | Ingest of 10,000 documents in under a second | proposal filed; order to be decided |
| 🧭 | Better abstention, ranking-parameter tuning, a stronger intent lexicon | research |

## FAQ

**Does fux call an AI model?**
No. No fux path may call a model, and nothing in the maintenance path uses one. Your agent can generate enrichment through `fux enrich`, and fux validates it.

**Does my content get copied into the repo?**
No. The committed index holds statistics, not your documents' text. `answer` fetches the cited lines from the source at answer time.

**What stops a secret from reaching git?**
`.fux/config/pii.toml` redacts matches before anything reaches the committed index, and fux won't run without it ([SR-PII](records/0148_pii.md)).

**Does it need the network?**
Only for commands you run on purpose, such as `fux add <url>`, and they say so on stderr ([L5](records/0007_LAW-5-offline-by-default.md)).

**How do teammates stay in sync?**
They pull. The index is plain JSONL in git, it merges with `fux hooks`' merge driver, and a pull request shows exactly what changed.

## Status

**`4.1.0` is the latest release** on PyPI (`pip install fux-engine`) and npm (`npx fux-engine`). The index format is versioned, and fux tells you when to run `fux ingest --full`. Every change is in [`CHANGELOG.md`](CHANGELOG.md).

⭐ **Star the repo** if fux saved your agent from one confident wrong answer. It's how other people find it. 👀 **Watch → Custom → Releases** to hear about new versions.

## Under the hood

<details>
<summary><b>Architecture diagrams</b></summary>

- [The whole idea in one picture](work/architecture-high-level.svg)
- [How `ask` works](work/architecture-ask.svg) · [how `answer` works](work/architecture-answer.svg) · [decoders](work/architecture-decoders.svg)
- [Python and Node, component for component](work/architecture-two-readers.svg)
- [Every plane, what is committed and what isn't](work/architecture-detailed.svg)
- [The paper](docs/paper/the-fux-index-paper.md), the architecture of record, with twenty diagrams

</details>

<details>
<summary><b>The fourteen laws fux is built under</b></summary>

Every decision of record lives in the [SR register](records/README.md) ([SR-LAWS](records/0001_LAWS.md)):
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
[L12 every value lives in a config file](records/0014_LAW-12-values-live-in-config.md) ·
[L13 a ranking change ships only through the standing bar](records/0015_LAW-13-the-standing-bar.md).
The laws were renumbered on 2026-09-28; an older document is read through [SR-LAWS](records/0001_LAWS.md) decision 2a.

</details>

<details>
<summary><b>Security and sensitive text</b></summary>

- `.fux/config/pii.toml` redacts matches before anything reaches the committed index; fux will not run without it ([SR-PII](records/0148_pii.md)).
- `.fux/config/refusals.toml` stops a sign-in wall being indexed as the page behind it ([SR-REFUSAL](records/0146_refusals.md)).
- Only explicit, opt-in commands touch the network, and they say so on stderr ([L5](records/0007_LAW-5-offline-by-default.md)).
- To report a vulnerability, see [SECURITY.md](SECURITY.md).

</details>

<details>
<summary><b>Reading order for contributors</b></summary>

1. [`CONTRIBUTING.md`](CONTRIBUTING.md): build, test and what a pull request owes
2. [`docs/index.md`](docs/index.md): the map of every doc in the repo
3. [The SR register](records/README.md): every decision of record
4. [The paper](docs/paper/the-fux-index-paper.md): what ships, what was measured, what was designed and not built
5. [Sibling environments](work/setup/README.md): the sandbox, measurement lab and benchmark harness
6. [`CLAUDE.md`](CLAUDE.md): how work is done here, for people and agents

</details>

## Contributing

Issues and PRs are welcome, and **a bug report with a failing query is gold.** See [CONTRIBUTING.md](CONTRIBUTING.md) for the build, the two test suites and what a change owes its record. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md), and report security issues privately ([SECURITY.md](SECURITY.md)).

## License

[MIT](LICENSE). Free forever, with FOSS-only dependencies forever ([L2](records/0004_LAW-2-zero-cost.md)).
