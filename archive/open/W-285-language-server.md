---
type: Handoff
name: W-285
description: "Arpit asked on 2026-10-19 for a stdio Language Server over the committed index (`fux lsp`)."
item: W-285
filed: 2026-10-19
filed_by: "Arpit (Claude Code, Opus 5.5)"
updated: 2026-10-19
updated_by: "Claude (Claude Code, Opus 5.5)"
ball: agent
closed: 2026-10-19
---

# W-285 — `fux lsp`: a Language Server over the index

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Add `fux lsp`, a stdio LSP server beside `fux mcp`, stdlib only | any editor that speaks LSP can use the index | ✅ |
| 2 | Workspace symbol search = a fux ranked search | Ctrl+T finds documents by meaning, not by file name | ✅ |
| 3 | Hover on a link, backlinks as references, warnings on links to archived or superseded documents | the index's graph shows up where docs are edited | ✅ |

**Arpit, 2026-10-19 (Claude Code):** *"create llms-full.txt and llms.txt files as well as mcp and lsp for vscode research and build it out create work items then implement it and close them then commit push and publish a new version"*

**Model:** Opus: the protocol mapping is a design choice no test can judge, though each feature is then testable.

## Goal

`fux lsp` speaks LSP 3.17 over stdio (Content-Length framing), holds the index resident like `fux mcp` (`store.resident.Holder`), and serves four features: `workspace/symbol`, `textDocument/hover`, `textDocument/references`, `textDocument/publishDiagnostics`.

## Definition of done

- `src/fux/lsp.py`, reader layer, no dependency; framing, lifecycle (`initialize`/`shutdown`/`exit`), full text sync.
- Constants in `constants.toml [lsp]` (L12); excluded from observers like `mcp`.
- Unit tests over an injected stream; an e2e test spawning the real verb; SR-LSP written.

## Outcome

**Done, 2026-10-19** — shipped in fux 4.1.0. Live successor: [SR-LSP](../../records/0163_lsp.md).

## Blockers

None.

## Record affected

**SR-LSP** (new) · SR-CLI (the verb list).

## Hazards

- A notification must never be answered; an unknown request must get `MethodNotFound` (-32601), not silence, or the client hangs.
- Positions are UTF-16 code units in LSP; links are ASCII-located on the line, so the column is computed on the UTF-16 encoding.

## Reference

[compare doc](../../work/compare/editor-and-llms-surfaces.compare.md) Fork 1 · [LSP 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) · [SR-MCP](../../records/0136_mcp.md).
