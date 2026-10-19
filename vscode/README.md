# Fux for VS Code

Your repository's [fux](https://github.com/arpitarya/fux) index, in the editor.
It works in every workspace folder that has a committed `.fux/index/`.

## What it adds

| feature | what you get |
|---|---|
| **MCP for agent mode** | `fux mcp` is registered automatically. Copilot agent mode, and any other MCP client in VS Code, gets `fux_search`, `fux_passage` and `fux_related`. No `.vscode/mcp.json` needed. |
| **Fux: Search the index** | Ask a question and get the ranked documents. Picking one opens it at the heading that matched. |
| **Go to Symbol in Workspace** (`Ctrl+T`) | The same search, through the language server. VS Code filters this list by the result's title, so the command above is the better search. |
| **Hover on a link** | The linked document's title, whether it is archived or superseded, its commit date, and how many documents link to it. |
| **Find All References** (`Shift+F12`) | Backlinks: every document that links to this one, at the line where the link is. |
| **Warnings** | A link to an archived or superseded document is flagged as you type. |

## Install

Download `fux-<version>.vsix` from the
[GitHub release](https://github.com/arpitarya/fux/releases), then:

```console
code --install-extension fux-4.1.0.vsix
```

## Requirements

- VS Code 1.101 or later.
- `fux` on your `PATH`: `pip install fux-engine`. If it lives somewhere else, set `fux.command` to its full path.
- A repository with a fux index. Run `fux setup` and then `fux ingest` once.

The extension runs `fux mcp` and `fux lsp`. It has no index logic of its own,
and it reads nothing over the network.

## Settings

| setting | default | |
|---|---|---|
| `fux.command` | `fux` | the fux executable |
| `fux.mcp.enable` | `true` | register the MCP server |
| `fux.lsp.enable` | `true` | run the language server |
| `fux.search.debounceMs` | `200` | how long the search waits after a keystroke |

## Other editors

`fux lsp` is a standard stdio language server, so any LSP client can run it.
In Neovim, for example:

```lua
vim.lsp.start({ name = "fux", cmd = { "fux", "lsp" }, root_dir = vim.fs.root(0, ".fux") })
```
