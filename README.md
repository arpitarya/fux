# Fux

**A search index for your written knowledge — decisions, runbooks, specs,
wiki pages — committed to git and read by agents.**

Fux ranks documents from a small, plain-text index committed to git, then reads
the answer back from the source itself. No server, no vector database, no API
key, and no model anywhere on the path.

> **Status: `2.0.0` — released on PyPI and npm.** The 2.x CLI and index format
> are what the next 2.x releases keep; a break waits for the next major. Every
> change is in [`CHANGELOG.md`](CHANGELOG.md).

## Why fux

- **Clone and ask.** The index is committed under `.fux/index/`, so every clone —
  yours, a teammate's, CI's, an agent's — searches the same thing. Nothing to host.
- **Text you can review.** One JSON line per document, sharded and sorted, so it
  diffs like code. A bundled git merge driver handles index changes from two branches.
- **Documents stay where they are.** The index holds statistics, not content.
  `answer` reads the cited lines from the source and says whether they are still current.
- **Deterministic.** Ranking is BM25F arithmetic
  ([SR-RANKING](records/0111_ranking.md)). The same sources build the same index.
- **Says when it doesn't know.** Results carry a confidence band, and an unrelated
  question gets *"No confident matches"* rather than the nearest noise
  ([SR-CONFIDENCE](records/0141_confidence.md)).
- **It indexes documents, not code.** Fux runs no parser over source files — no
  AST, no symbols, no call graph — and source extensions are not on its default
  type list. Pair it with a code-graph tool when you want structure.

The whole idea in one picture: [`work/architecture-high-level.svg`](work/architecture-high-level.svg).
How a verb actually works: [`ask`](work/architecture-ask.svg) · [`answer`](work/architecture-answer.svg) · [decoders](work/architecture-decoders.svg).
Python versus Node, component for component: [two readers](work/architecture-two-readers.svg).

## Install

```bash
pip install --pre fux-engine    # Python ≥ 3.11 · Linux, macOS, Windows
```

`--pre` is needed while fux is in alpha. The command is `fux`.

**You can also read an index without Python.** `fux setup` vendors a
zero-dependency Node reader into `.fux/node/` — **one generated file**, not
fux's source tree — so a clone answers with nothing installed at all:

```bash
.fux/fux find rollback        # the shim: correct in every shape, so it is the one to use
npx fux-engine find rollback  # from npm, without a repository
```

It only reads — `ingest`, `build` and every other writing verb stay with Python
— and it is held byte-equal to Python by a third arm of the differential law.
In a monorepo `fux setup` detects the workspace instead and declares
`.fux/node` as a member, so the reader comes from your lockfile; either way
`.fux/fux` is the command.

**And fux is importable**, not only spawnable:

```python
from fux import open as fux_open
fux_open(".").ask("how do we roll back a release")
```

## Quickstart

```console
$ cd your-repo
$ fux setup      # writes .fux/ and agent instructions; only creates missing files
$ fux ingest     # indexes what .fux/sources/dirs lists (setup seeds README.md and docs/)
ingested 2 docs (2 changed, 0 carried forward), 0 not indexed, 0 skipped, 2 shards written
accelerator: 31 terms, 31 blocks, 34 postings (derived, not committed)

$ fux ask "how do I roll back a release"
2.2044  Deploying the payments service  (docs/deploy.md)

$ fux answer "how do I roll back a release"
# Rollback
...
To roll back a bad release, run `make rollback` from the release branch.
The previous image tag is kept for 7 days.

  -- docs/deploy.md:L1-L6 (sha 18ac8c4e4d33, current)

$ fux ask --band "kubernetes autoscaling limits"
No confident matches.
confidence: none - nothing in the index scored for this query.

$ git add .fux fux.toml && git commit -m "Add fux index"
```

`.fux/` explains itself: `setup` writes a `.fux/README.md` and a `.gitignore` that
keeps the derived and fetched parts out of git ([SR-DOTFUX](records/0102_fux-directory.md)).

## Everyday commands

| I want to… | Run |
|---|---|
| Rank documents for a question | `fux ask "…"` |
| Just the file paths, for piping | `fux find "…"` |
| One answer, quoted from the source | `fux answer "…"` |
| Machine-readable output | add `--json` |
| A confidence band, or why it ranked | `fux ask --band "…"` · `fux ask --why "…"` |
| Index another folder, file or URL | `fux add <path-or-url>` |
| Mark a folder as history | `fux add old/2023-platform --archived` |
| Stop indexing something | `fux remove <entry>`, or a line in `.fux/.fuxignore` |
| Re-read sources and re-fetch URLs | `fux update` (`--check` only reports drift) |
| Follow links between documents | `fux explain <doc>` · `fux graph "…"` · `fux path <a> <b>` |
| Explore around documents you name | `fux graph --seed <doc> [--seed <doc>…]` |
| The same ranking from the words alone | `fux lexical "…"` — BM25F, frozen; the baseline, not a better `ask` |
| Re-index automatically on commit and merge | `fux hooks` |
| A re-runnable answer receipt | `fux answer --receipt "…"`, later `fux verify <receipt>` |
| Check the setup | `fux doctor` (read-only, offline) |
| See what the index looks like | `fux inspect` — boilerplate words, documents no query can reach, duplicates, orphans |

Full surface: `fux --help` and [SR-CLI](records/0101_cli-surface.md).

## With coding agents

Agents are fux's primary reader.

- **Instructions out of the box.** `fux setup` adds skills and instructions for
  Claude Code, Codex, GitHub Copilot and Kiro, plus a root `AGENTS.md`. They tell
  the agent to search the index before grepping and how to read a result. Skip
  with `--no-agents` ([SR-AGENT-POLICY](records/0132_agent-policy.md)).
- **MCP.** `fux mcp` serves the index over stdio as three tools: `fux_search`,
  `fux_passage` and `fux_related`. There is no `answer` tool — the agent is the
  answerer ([SR-MCP](records/0136_mcp.md)).
- **Read the JSON, not the prose.** `--json` and `--band` carry the fields an agent
  should branch on, including whether a result is archived
  ([SR-ARCHIVED-CONTENT](records/0134_archived-content.md)).

## Beyond Markdown

- **File formats.** Markdown, reStructuredText, AsciiDoc, Org and plain text,
  plus decoders for PDF, Word, PowerPoint, Excel, CSV/TSV, HTML, email,
  draw.io, JSON, YAML, TOML, INI, XML, SVG and images. The decoders are copied
  into `.fux/decoders/` as your code, to edit or replace
  ([SR-DECODE](records/0139_decode.md)).
- **Web pages and wikis.** `fux add <url>` fetches through a fetcher in
  `.fux/fetchers/`: `http.py` for a plain GET, or `cdp.py` (`--cdp`) to use the
  session your signed-in Chrome already holds. Both are yours to edit
  ([SR-FETCHER](records/0117_fetcher.md)).
- **Offline unless you ask.** Only explicit, opt-in commands touch the network,
  and they say so on stderr ([L4](records/0006_LAW-4-offline-by-default.md)).
- **Sensitive text.** `.fux/pii.toml` redacts matches from the committed index
  ([SR-PII](records/0148_pii.md)). `fux setup` writes it, and fux will not run
  without it. `.fux/refusals.toml` stops a sign-in wall
  being indexed as the page behind it ([SR-REFUSAL](records/0146_refusals.md)).
- **Images and scans.** Fux never calls a model. `fux enrich` plans the work for
  your coding agent and validates what it writes
  ([SR-ENRICH](records/0137_enrich.md)).

## Measured, not assumed

Claims ship with a pre-registered bar and a published run — including the ones that failed.

- **Speed.** Warm `ask --fast` on 8,870 RFCs: worst-case p95 **27.2 ms** against a
  150 ms bar ([run](work/regression/2026-08-12-m2-accelerator/report.md), 2026-08-12, pre-2.0).
  The accelerator must return byte-identical results to the default scan.
- **Graph.** 24/24 on a graded 66-document corpus; the derived graph hashes
  identically on x86-64 Linux and arm64 macOS
  ([run](work/regression/2026-08-22-graph-acceptance/report.md)).
- **Kept the failures.** Pruning the index to top terms failed its gate
  ([verdict](work/regression/2026-08-09-pruning-rerun/VERDICT.md)). A dense
  embedding lane measured 0 fixed / 2 broken queries and was deleted in `alpha.1`.

## Design rules

Fux is built under ten laws, each with its own record in the
[SR register](records/README.md) ([SR-LAWS](records/0001_LAWS.md)):
[L0 SRs are the source of truth](records/0002_LAW-0-authority.md) ·
[L1 `$0`, FOSS-only](records/0003_LAW-1-zero-cost.md) ·
[L2 content never durable](records/0004_LAW-2-content-never-durable.md) ·
[L3 deterministic](records/0005_LAW-3-deterministic.md) ·
[L4 offline by default](records/0006_LAW-4-offline-by-default.md) ·
[L5 hashed meta](records/0007_LAW-5-hashed-meta.md) ·
[L6 say "index"](records/0008_LAW-6-say-index.md) ·
[L7 Python ≥ 3.11](records/0009_LAW-7-python-311.md) ·
[L8 use record never committed](records/0010_LAW-8-use-record.md) ·
[L10 build output, never source](records/0011_LAW-10-bundled-output.md).

## Reading order

1. [`docs/index.md`](docs/index.md) — the map of every doc in the repo
2. [The SR register](records/README.md) — every decision of record
3. [Detailed architecture diagram](work/architecture-detailed.svg) — every plane, what is committed and what is not, and the two query paths
4. [The paper](work/paper/the-fux-index-paper.md) — design and falsifiable predictions (a draft; its status note lists what changed)
5. [Sibling environments](work/setup/README.md) — the sandbox, the measurement lab and the benchmark harness that sit next to this repo
6. [`CLAUDE.md`](CLAUDE.md) — how work is done here, for people and agents

## Contributing

```bash
pip install -e ".[dev]" && pytest
```

Every change to an SR-owned component updates its owning record in the same
commit; CI checks it. Start with [`CLAUDE.md`](CLAUDE.md).

## License

[MIT](LICENSE)
