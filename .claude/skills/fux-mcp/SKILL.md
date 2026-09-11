---
name: fux-mcp
description: Serve a Fux index over MCP with `fux mcp` — the fux_search, fux_passage and fux_related tools, the [mcp] output defaults, registering the server in Claude Code, Codex, VS Code/Copilot or Kiro with a command the client can launch, and fixing a server that shows no tools. Use when asked to "use fux over MCP", "add fux as an MCP server" or when fux tools are not showing. Writes client config only when explicitly asked.
---

# Fux over MCP — `fux mcp`

`fux mcp` is a **long-running stdio server**: the client spawns it, sends
newline-delimited JSON-RPC on stdin, and reads one JSON line per reply on
stdout. **One process serves one repository** — the one it finds from its
working directory. A human never runs it interactively except to test it.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · MCP or the CLI?

**The MCP surface is three tools, deliberately smaller than the CLI.**

| you need | over MCP | on the CLI |
|---|---|---|
| ranked documents + confidence | `fux_search` | `fux ask --json` |
| the text of lines in a file | `fux_passage` | read the file |
| a document's links in **and** out, archived / superseded | `fux_related` | `fux explain` (outbound only) |
| a fetched, re-scored, cited answer with a freshness verdict | ❌ not exposed | `fux answer` |
| a query neighbourhood, routes, communities | ❌ | `fux graph`, `fux path` (`fux-graph`) |
| fused `-q` phrasings, `--why`, receipts | ❌ | the CLI flags |

**If you have a shell and need anything in the ❌ rows, run the CLI.** MCP's
advantage is a warm process with no per-call start-up, and a client with no shell.

## 2 · The tools

### `fux_search` — `query` (required), `k`, `expand`

```json
{"results": [{"path": "docs/retry-policy.md", "title": "Retry policy", "score": 3.706,
              "sha": "f9421e09…", "archived": false, "superseded": false,
              "headings": ["Retry and backoff"]}],
 "ranked_by": "accelerator",
 "confidence": {"band": "partial", "answerable": true, "missing": ["mtls"], "verified": "unverified",
                "coverage": 0.5, "separation": 0.4, "separation_floor": 0.1,
                "doc_coverage": 1.0, "doc_coverage_floor": 0.0, "support": 1},
 "next": "call fux_passage with a path to read a span, or fux_related for neighbours"}
```

**Read `confidence` before `results`** — treat a `null` `confidence` like `none`:

| `band` | do |
|---|---|
| `grounded` | use the results and cite them |
| `partial` | answer, but **name every term in `missing`** — or retry with `expand` (below) |
| `weak` | the top hits are not separable — **report the candidates, not a conclusion** |
| `none` (`answerable: false`) | **do not answer from these results.** Say what was searched and stop |

- **`k`** defaults to the server's resolved `[mcp] top` (§3), and the tool schema
  advertises that value. An explicit `k` wins.
- **`expand`** is words you expect the document to use when they differ from the
  question's. Scored below the query's own terms; a document matching *only*
  them is never returned. Use it after a `partial` with non-empty `missing`.
- **Results are documents, not spans.** `headings` (at most three, `[]` is a real
  answer) tells you *where* to look; `fux_passage` reads it.
- **`archived: true`** — follow the `fux-archived-results` policy.
  **`superseded: true`** — it has been declared replaced; prefer its successor.
- `ranked_by` is `accelerator` or `scan`; results are identical either way.

### `fux_passage` — `path` (required), `line_start`, `line_end`

Returns `{"path", "line_start", "line_end", "sha", "text"}`.

- **`path` is repo-root relative**, exactly as `fux_search` returned it — no `file:` prefix.
- Lines are **1-based and inclusive**; omit both to read the whole file. A
  `line_start` past the end returns empty `text`, not an error.
- **It reads the working-tree file now.** Compare its `sha` with the one
  `fux_search` returned: **different means the file changed since it was
  indexed** — the ranking is behind; say so. (The hash is fux's own, not a git sha.)
- ⚠ **It cannot read a URL document** (`… is not a file in this repository`), and on
  a PDF, DOCX or other binary it returns undecoded bytes. Use `fux answer` on the CLI.
- It refuses any path that resolves outside the repository.

### `fux_related` — `path` (required)

```json
{"path": "docs/decisions/storage.md", "title": "Storage", "archived": false, "superseded": true,
 "outbound": [{"path": "docs/runbook-rollback.md", "kind": "ref"}, {"path": "tag:storage", "kind": "tag"}],
 "inbound":  [{"path": "docs/decisions/storage-v2.md", "kind": "supersedes"}]}
```

- Accepts the `path` from `fux_search`, or an id with `file:` / `url:`. ⚠ **A URL
  document needs the `url:` prefix** — a bare URL is looked up as a file.
- **`kind`** is `ref` (link), `supersedes`, `tag`, or `code` (a quoted file path).
  An inbound `supersedes` means *this document was replaced by that one*.
- Outbound targets keep a `url:` or `tag:` prefix when they have one; `file:` is dropped.
- **`archived` and `superseded` describe this document only**, not its neighbours —
  call `fux_related` on a neighbour before relying on it.
- No grades, communities or routes here — that is the CLI (`fux-graph`).

**A tool that fails answers with `isError: true`** and a one-line reason
(`'x' is not in the index`). Act on the reason; do not retry unchanged.

## 3 · Output defaults — `[mcp] top` is the only knob

- **`[mcp]` in `.fux/output.toml` configures this server, and it inherits nothing
  from `[cli]`.** Its one key is `top`. `band` and `json` are refused there —
  the confidence block is unconditional and a result is always JSON.
- **Read once, at start-up.** After editing `.fux/output.toml`, restart the server.
  Index changes (`fux ingest`, `fux build`) are picked up on the next call.
- **No file** → the built-in default (5). **A file that exists but has no
  `[mcp] top`** → the server refuses to start (§6).
- **`fux mcp --no-output-config`** ignores the file entirely. In a client config it
  goes in `args`: `["run", "fux", "mcp", "--no-output-config"]`.

**Offline, always.** No tool fetches anything: `fux_search` ranks from the
committed index (hence `verified: "unverified"`), `fux_related` reads the
index, `fux_passage` reads a local file. Freshness is the `sha` comparison above.

## 4 · The command the CLIENT launches — the ladder problem

**The client spawns the server with its own `PATH` and working directory, not
your shell's.** A `fux` that works in your terminal can be `command not found`
for the client. Probe with the ladder, then write the rung that answered:

| rung that answered | `command` | `args` |
|---|---|---|
| `uv run fux --version` | `uv` | `["run", "fux", "mcp"]` |
| `./.venv/bin/fux --version` | `/abs/path/to/repo/.venv/bin/fux` | `["mcp"]` |
| `python -m fux --version` | the absolute path of that `python` | `["-m", "fux", "mcp"]` |
| `fux --version` | `fux`, or its absolute path if the client cannot find it | `["mcp"]` |

**The repository is found from the working directory** — the nearest ancestor
holding `fux.toml` or `.git`. There is no flag or environment variable for it.
Where a client has `cwd`, set it; where it does not, use
`["run", "--directory", "/abs/path/to/repo", "fux", "mcp"]` with `uv` — **in a
user-scope config only** (see below).

- ⚠ **Committed config is shared.** `.mcp.json`, `.vscode/mcp.json`,
  `.kiro/settings/mcp.json` and `.codex/config.toml` reach every teammate — an
  absolute path works on one machine. Prefer `uv run fux mcp` there.
- On Windows the venv binary is `.venv\Scripts\fux.exe`; escape the backslashes in JSON.

**Test the exact command before registering it**, from the directory the client will use:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
              '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | uv run fux mcp
```

**Pass:** two JSON lines — `"serverInfo": {"name": "fux", …}`, then a `tools` list
naming `fux_search`, `fux_passage`, `fux_related`. **No JSON on stdout and an
`error:` line on stderr is a start-up failure** — §6 names each one.

## 5 · Register it

**Only when asked.** Each writes a config file; say which file you changed.

**Claude Code** — project scope writes `.mcp.json` at the repo root:

```bash
claude mcp add --scope project fux -- uv run fux mcp
```

```json
{"mcpServers": {"fux": {"type": "stdio", "command": "uv", "args": ["run", "fux", "mcp"]}}}
```

Check with `claude mcp list` or `/mcp`. A project server must be **approved** in an
interactive session before its tools appear.

**Codex** — `~/.codex/config.toml` (user scope, so the absolute `cwd` below never
reaches a teammate):

```toml
[mcp_servers.fux]
command = "uv"
args = ["run", "fux", "mcp"]
cwd = "/abs/path/to/repo"
startup_timeout_sec = 30
```

`codex mcp add fux -- uv run fux mcp` adds it from the command line; set `cwd` in the
`[mcp_servers.fux]` table. In a committed `.codex/config.toml`, omit `cwd` and
launch Codex from the repo root. The default start-up timeout is 10 s — raise it if `uv`
has to sync on first launch. Check with `/mcp`.

**VS Code / GitHub Copilot** — `.vscode/mcp.json`:

```json
{"servers": {"fux": {"type": "stdio", "command": "uv", "args": ["run", "fux", "mcp"], "cwd": "${workspaceFolder}"}}}
```

Start it from **MCP: List Servers**, accept the trust prompt, and use **Show Output**
for its log.

**Kiro** — `.kiro/settings/mcp.json` (workspace; wins over `~/.kiro/settings/mcp.json`):

```json
{"mcpServers": {"fux": {"command": "uv", "args": ["run", "fux", "mcp"], "disabled": false}}}
```

Kiro has no `cwd` key — if the server cannot find the repo, put the `--directory`
form from §4 in the **user** file `~/.kiro/settings/mcp.json`, never the committed
workspace one. Check the MCP server panel.

## 6 · Troubleshooting

| symptom (client log / test output) | cause | fix |
|---|---|---|
| `command not found`, `ENOENT`, "failed to connect" | the client's `PATH` lacks `fux` or `uv` | an absolute `command` (§4) |
| `error: no fux.toml or .git found …` | launched outside the repo | set `cwd`, or `uv run --directory` |
| `error: .fux/pii.toml is missing …` | the repo never ran `fux setup` | ask a human — setup writes committed files |
| `error: .fux/output.toml does not set …` naming `[mcp]` | the file predates the key | add `[mcp]` with `top = 5`, or `--no-output-config` |
| connected, but no tools | not approved / not trusted / `disabled` / Codex timed out | approve in the client; raise `startup_timeout_sec` |
| tools work, results are from another repo | the nearest `.git` above `cwd` is a different repo | point `cwd` at the right root |
| `k` default did not change after editing | `[mcp]` is read once | restart the server |
| client reports parse or protocol errors | something else writes to stdout | launch fux directly, not via a wrapper that prints |

## Don't

- **Don't answer from `fux_search` when `answerable` is `false`**, or skip `missing` on `partial`.
- **Don't pass a bare URL to `fux_related`** — prefix `url:`.
- **Don't expect `fux_passage` to fetch** — it reads local files; URL documents need `fux answer`.
- **Don't write a bare `fux` into a GUI client's config** without testing that the client can launch it.
- **Don't commit an absolute path** into a shared config file.
- **Don't assume a neighbour is live** because the document you asked about is.
- **Don't reach for MCP when a shell is there and you need `answer`, `graph` or `path`.**

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-config, fux-index, fux-pii, fux-archived-results.
