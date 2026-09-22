---
inclusion: auto
name: fux-mcp-guide
description: Serving the Fux index over MCP with fux mcp - the fux_search, fux_passage and fux_related tools, registering the server in Claude Code, Codex, Copilot or Kiro, and fixing a server with no tools. Use when asked to use or add fux as an MCP server.
---

# Fux over MCP

- **Three tools:** `fux_search`, `fux_passage`, `fux_related`. No `answer`,
  `graph` or `path` - use the CLI when a shell is available.
- **Read `confidence` before `results`**; `answerable: false` (band `none`)
  means do not answer. `weak` is a near-tie signal, not a refusal.
- **The client launches the server with its own search path and working
  directory** - test the exact command before registering it.
- **Do not commit an absolute path** into a shared MCP config.
- `[mcp]` in `.fux/output.toml` is read once: restart after editing.
- Register a server only when asked, and name the file you changed.

Full procedure: the `fux-mcp` skill.
