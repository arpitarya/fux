---
type: Handoff
name: W-286
description: "Arpit asked on 2026-10-19 for a VS Code extension that registers `fux mcp` and runs `fux lsp`, shipped as a .vsix on the release."
item: W-286
filed: 2026-10-19
filed_by: "Arpit (Claude Code, Opus 5.5)"
updated: 2026-10-19
updated_by: "Claude (Claude Code, Opus 5.5)"
ball: agent
closed: 2026-10-19
---

# W-286 — the VS Code extension: MCP and LSP in one install

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | One dependency-free extension file: registers `fux mcp` with VS Code's MCP API for every folder with `.fux/` | Copilot / agent mode sees fux's three tools with no `mcp.json` | ✅ |
| 2 | The same file runs `fux lsp` through a small hand-rolled LSP client | search, hover, backlinks and warnings in the editor | ✅ |
| 3 | `scripts/build-vsix.py` zips it deterministically; `publish.yml` attaches it to the GitHub release | `code --install-extension fux-<version>.vsix` | ✅ |

**Arpit, 2026-10-19 (Claude Code):** *"create llms-full.txt and llms.txt files as well as mcp and lsp for vscode research and build it out create work items then implement it and close them then commit push and publish a new version"*

**Model:** Sonnet: the shape is ruled (C1, S1) and the checks are mechanical; the VS Code API is pinned by its typings.

## Goal

`vscode/` holds the extension: `package.json` (engine `^1.101.0`, `mcpServerDefinitionProviders`), `src/client.js` (the LSP client, no `vscode` import, unit-testable), `src/extension.js`. The build wraps both into one `dist/extension.js` (L10) and packs a `.vsix`.

## Definition of done

- The `.vsix` installs into a scratch `--extensions-dir` with `code --install-extension`.
- Node unit tests for the client's framing and request routing.
- Its version is a site in `check-version-parity.py`.
- SR-VSCODE written; README, CHANGELOG.

## Outcome

**Done, 2026-10-19** — shipped in fux 4.1.0. Live successor: [SR-VSCODE](../../records/0164_vscode.md).

## Blockers

None for S1. **A Marketplace listing (S2) needs a publisher Arpit creates** — not filed as an inbox row, since nothing waits on it.

## Record affected

**SR-VSCODE** (new) · SR-WORK-RELEASE (a version site; the release asset).

## Hazards

- `McpStdioServerDefinition` is positional (`@types/vscode@1.101.0`); `cwd` is a property.
- `fux` must be on PATH or set in `fux.command`; the extension says so once rather than failing silently.

## Reference

[compare doc](../../work/compare/editor-and-llms-surfaces.compare.md) Forks 2–3 · [VS Code MCP guide](https://code.visualstudio.com/api/extension-guides/ai/mcp).
