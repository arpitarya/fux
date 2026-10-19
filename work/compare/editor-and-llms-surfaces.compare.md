---
type: Compare
description: "W-284/W-285/W-286 — llms.txt and llms-full.txt from the index, a Language Server, and a VS Code extension that wires both the MCP server and the Language Server. Four forks: where the LSP runs (Python verb · Node verb · inside the extension), how the extension speaks LSP (hand-rolled client · vscode-languageclient), how it ships (VSIX on the GitHub release · Marketplace), and what llms-full.txt carries. Proposed and built on Arpit's direction of 2026-10-19."
---

# Editor and llms surfaces — `fux llms`, `fux lsp`, and the VS Code extension

> **Verdict:** ✅ **built on Arpit's direction, 2026-10-19 (Claude Code):**
> *"create llms-full.txt and llms.txt files as well as mcp and lsp for vscode
> research and build it out"*. **L1 · C1 · S1 · F1** below. Each fork is his to
> override; the reopen-trigger says what would make it worth his time.

| | |
|---|---|
| **status** | ✅ built — W-284 (`fux llms`), W-285 (`fux lsp`), W-286 (the VS Code extension) |
| **the call** | both new verbs are **Python, stdlib, reader layer**, siblings of `fux mcp`; the extension is **one dependency-free CommonJS file** speaking LSP and registering MCP through VS Code's own API; it ships as a **`.vsix` attached to the GitHub release**; `llms-full.txt` is **the operator's selection, read off disk, to stdout** |
| **confidence** | **high** on L1 and C1 — both copy decisions fux already made for MCP ([SR-MCP](../../records/0136_mcp.md) decision 1). **medium** on S1 — it is the honest default while no Marketplace publisher exists, not a preference |
| **reopen-trigger** | (1) a second editor (Neovim, JetBrains, Zed) asks for the server and finds the Python start-up too slow on a cold call — then L2; **or** (2) the hand-rolled client needs a fourth LSP feature it does not map — then C2 is cheaper than growing it; **or** (3) Arpit creates a Marketplace / Open VSX publisher — then S2 is one job in `publish.yml` |

## Context

- **`fux mcp` already exists** and is the agent's door: three tools, stdio,
  stdlib-only ([SR-MCP](../../records/0136_mcp.md)). VS Code has spoken MCP
  natively since 1.101, and an extension can register a server through
  `contributes.mcpServerDefinitionProviders` +
  `vscode.lm.registerMcpServerDefinitionProvider` — the typings,
  `@types/vscode@1.101.0` line 20270, are positional:
  `new McpStdioServerDefinition(label, command, args?, env?, version?)` with a
  settable `cwd`.
- **A human editing docs has no fux in front of them.** The index knows which
  documents exist, what links to what, what is archived and what was
  superseded — none of which the editor shows. That is an LSP's job:
  `workspace/symbol`, `textDocument/hover`, `textDocument/references`,
  `textDocument/publishDiagnostics`.
- **llms.txt** ([llmstxt.org](https://llmstxt.org/)) is a Markdown file: one H1,
  an optional blockquote, optional prose, then H2 sections of
  link lists (a name, its URL, an optional note); a section titled `Optional` may be skipped
  when context is short. **`llms-full.txt` is a convention, not part of the
  spec** — the linked documents' text, concatenated.
- **Fux has no third-party dependency anywhere in the tree** (4.0.0,
  CHANGELOG), and L2 says any one needs an accepted record.

## Fork 1 — where the Language Server runs

| | L1 · Python verb `fux lsp` | L2 · Node verb in `fux.mjs` | L3 · inside the extension |
|---|---|---|---|
| editors served | **any** — Neovim, Helix, Zed, JetBrains, VS Code | any with Node ≥ 22 | VS Code only |
| index access | the reader's own `read_index` + `Graph`, as `fux mcp` | the Node reader's | would re-implement the reader |
| L10 | nothing new is served to a consumer | grows the one bundle | a second bundle per plane |
| cold start | ~100 ms once per editor session | ~50 ms | none |
| cost | one module, mirrors `mcp.py` | a twin the differential arm would expect | a third reader |

**Proposed L1.** The start-up cost is paid once per editor session, not per
request — the same argument that made `fux mcp` a resident process. A Node
twin is not built: no parity test claims one, and the verb is not a ranking
surface.

## Fork 2 — how the extension speaks LSP

| | C1 · hand-rolled client (~250 lines) | C2 · `vscode-languageclient` (MIT) |
|---|---|---|
| dependency | none | one, plus a bundler for L10 |
| features | the four the server has, mapped to VS Code providers | every LSP feature, free |
| L2 | nothing to decide | needs an accepted record naming it |
| risk | a framing bug is ours | a version skew is theirs |

**Proposed C1.** It is [SR-MCP](../../records/0136_mcp.md) decision 1's
reasoning one protocol over: Content-Length framing is `Buffer` and
`JSON.parse`, and the server has four features. Reopen when a fifth is wanted.

## Fork 3 — how the extension ships

| | S1 · `.vsix` on the GitHub release | S2 · VS Code Marketplace + Open VSX |
|---|---|---|
| needs | `contents: write` in `publish.yml` | a publisher id and a token per registry — **Arpit's accounts** |
| install | `code --install-extension fux-<v>.vsix` | search *Fux* in the Extensions view |
| built by | `scripts/build-vsix.py` — stdlib `zipfile`, deterministic | the same file, uploaded |

**Proposed S1 now, S2 when Arpit opens the accounts.** The `.vsix` is built
by a stdlib script rather than `vsce`, so it adds no dev dependency and the
same tree always zips to the same bytes.

## Fork 4 — what `llms.txt` and `llms-full.txt` carry

| | F1 · index membership, text read off disk, stdout only | F2 · committed artefacts fux writes | F3 · titles only, no full |
|---|---|---|---|
| L3 | **content leaves the source only to stdout** — the operator decides where it goes | fux would write a second copy of the corpus | trivially safe |
| what it lists | every indexed document under the `--in` prefixes, archived ones under `## Optional` | same | same |
| notes on a link | the document's own `description:` frontmatter, read from the file | same | none |

**Proposed F1.** The index decides *which* documents and their titles; the
working tree supplies the text, exactly as `fux_passage` reads a span. **URL
documents are listed, never fetched** — `--full` writes only `file:` documents,
so the verb is offline (L5). This repository commits its own two files at the
root, generated by `just llms`: a copy inside the system that owns the source,
which is what L3 permits.

## Reference

- [llmstxt.org](https://llmstxt.org/) — the llms.txt format.
- [VS Code — MCP developer guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
  and `@types/vscode@1.101.0` — the provider API.
- [Language Server Protocol 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) — base protocol framing and the four methods.
- [SR-MCP](../../records/0136_mcp.md) decision 1 — the stdlib precedent C1 and L1 follow.
