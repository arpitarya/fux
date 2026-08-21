---
type: Compare Doc
title: "How agents call Fux — CLI, library, or MCP"
status: proposed
filed: 2026-08-21
laws_bracketed: []
---

# How agents call Fux — CLI, library, or MCP

## What exists

- CLI verbs: `ask`, `find`, `answer`, `explain`, `graph`, `path`, with
  `--json`. Citations are `loc#p<ordinal>` (passage ordinal in the
  heading-chunked document).
- MCP is a parked proposal, explicitly out of scope.

## Observations about the consumer

- The consumer is an agent in a coding session. Today's agents navigate with
  `grep`/`glob`/`read` tools and no index (Claude Code's stance —
  [Vadim](https://vadim.blog/claude-code-no-indexing/)); the cost is tokens
  and latency on large repos, which is the published critique
  ([Milvus](https://milvus.io/blog/why-im-against-claude-codes-grep-only-retrieval-it-just-burns-too-many-tokens.md))
  and the gap Cursor's local index fills ([Cursor](https://cursor.com/blog/fast-regex-search)).
- An agent acts on a citation by **opening a file at a line**. A passage
  ordinal forces a second call to find the lines.
- Agents call the same tool many times per task. A CLI spawn per call costs
  ~50–150 ms of Python start-up before any ranking — more than the ranking.

## Options

| | A · CLI + `--json` (today) | B · Python library API | C · MCP server (stdio) | D · A + C |
|---|---|---|---|---|
| discoverable by agent without prompting | no (needs CLAUDE.md instructions) | no | **yes** — tool schema is advertised | yes |
| per-call overhead | interpreter start + index open | none | process stays warm: index, model, caches resident | warm |
| works in Claude Code / Cursor / Codex / Copilot | via shell | no | **native in all four** | both |
| humans | yes | no | no | yes |
| state across calls (answer cache, fetch cache, reranker loaded) | re-opened each call | in-process | **persistent** | persistent |
| effort | exists | thin | ~200 lines over the library | + docs |

## The tool surface an agent actually needs

| tool | returns | why |
|---|---|---|
| `fux_search(query, k)` | ranked `{path, title, line_start, line_end, score, sha, freshness}` | the 90 % call |
| `fux_passage(path, line_start, line_end)` | verbatim bytes + sha | lets the agent read *only* the cited span |
| `fux_related(path)` | outbound/inbound edges, supersedes/superseded-by, community | "what else was decided with this?" |
| `fux_path(a, b)` | routes | rarely; keep |

Drop `answer` as an agent tool: the agent *is* the answerer. Keep it for
humans on the CLI.

## Citation shape

Change `loc#p3` → `path:L12-L40` everywhere (CLI, JSON, MCP). The chunker
already splits on `splitlines()`; carrying the first/last line index through
`Passage` is a two-field change. Keep the
passage ordinal as a secondary field for stability across reflows.

## Proposed verdict

**D.** Build the MCP server over the library the CLI already wraps; make
line-range citations the one citation format; keep a per-process answer
cache keyed on `(index root sha, query, policy)` — deterministic, so it is
safe — and a warm reranker (doc 04).

## Reopen trigger

Reopen if a major agent host drops MCP in favour of a different tool
protocol; the library layer (B) is what makes that a thin port.
