# Setup variants + hooks installation — worked examples

*How `fux setup` behaves across its variants, and exactly what
`--agents --skills --hooks` writes into a project. Every output block below is
real command output (v0.23.x). `fux setup` is **idempotent** — re-running it
never clobbers your edits; it merges managed keys and reports `unchanged`.*

The command surface (from `fux setup --help`):

| Flag | Effect |
|------|--------|
| `--docs / --code / --data / --images DIR` | Set a source folder (repeat or comma-separate); skips its prompt |
| `-y`, `--yes` | Accept defaults, no prompts (CI / scripted) |
| `--agents` | Generate `AGENTS.md` + tool-pointer files |
| `--skills` | Generate the `fux-query` / `fux-ingest` skills |
| `--hooks` | Install Claude Code + Kiro hooks |

`--agents`, `--skills`, `--hooks` are independent — pass any subset. All three
imply nothing about sources; the wizard/flags still resolve `[sources]` first.

---

## Variant 1 — interactive wizard (no flags)

Each source type is prompted, showing its default in brackets (Enter accepts,
`-` or `none` clears):

```
$ fux setup
Docs folders (md/txt/office) [docs]:
Code folders (py/js/…) [none]: src
Data folders (json/yaml) [none]:
Image folders (png/jpg) [none]:
wrote fux.toml  (docs: docs · code: src · data: — · images: —)
   wrote  .gitignore  (+.fux/index/ — derived runtime plane)
next: run `fux ingest`
```

- Only `.fux/index/` is gitignored — `fux.toml`, `fux.lock`, and `.fux/state/`
  are the committed recipe-and-state pair.
- Non-interactive stdin (a pipe with no tty) behaves like `-y`.

## Variant 2 — fully flag-driven (scriptable, no prompts)

```
$ fux setup -y --docs docs --docs '~/notes/anton' --code src --data config
wrote fux.toml  (docs: docs, ~/notes/anton · code: src · data: config · images: —)
   wrote  .gitignore  (+.fux/index/ — derived runtime plane)
next: run `fux ingest`
```

- Repeat a flag (`--docs a --docs b`) or comma-separate (`--docs a,b`) — both
  add multiple folders.
- `-y` fills every source type you did *not* pass from its existing/default
  value instead of prompting.

## Variant 3 — re-run to add a source (idempotent merge)

Only the flags you pass change; hand-edited keys (`[engine.bm25f]`,
`[sources.web]`, …) survive untouched:

```
$ fux setup -y --images assets/diagrams
wrote fux.toml  (docs: docs · code: src · data: config · images: assets/diagrams)
next: run `fux ingest`
```

Re-running with no change reports `unchanged fux.toml` and writes nothing.

---

## Full agent integration — `--agents --skills --hooks`

One command wires Fux into every agent surface it supports:

```
$ fux setup -y --docs docs --agents --skills --hooks
wrote fux.toml  (docs: docs · code: — · data: — · images: —)
   wrote  .gitignore  (+.fux/index/ — derived runtime plane)
  created  AGENTS.md
  created  CLAUDE.md
  created  .github/copilot-instructions.md
  created  .kiro/steering/fux.md
  created  .claude/skills/fux-query/SKILL.md
  created  .claude/skills/fux-ingest/SKILL.md
  created  .claude/skills/fux-debug/SKILL.md
  created  .claude/settings.json
  created  .kiro/hooks/fux-query.kiro.hook
next: run `fux ingest`
```

Each line's state is `created` / `updated` / `unchanged`. A second identical
run reports every row `unchanged` — nothing is rewritten:

```
$ fux setup -y --docs docs --agents --skills --hooks
unchanged fux.toml  (docs: docs · code: — · data: — · images: —)
unchanged  AGENTS.md
unchanged  CLAUDE.md
unchanged  .github/copilot-instructions.md
unchanged  .kiro/steering/fux.md
unchanged  .claude/skills/fux-query/SKILL.md
unchanged  .claude/skills/fux-ingest/SKILL.md
unchanged  .claude/skills/fux-debug/SKILL.md
unchanged  .claude/settings.json
unchanged  .kiro/hooks/fux-query.kiro.hook
```

### What each flag produces

| Flag | Files | Notes |
|------|-------|-------|
| `--agents` | `AGENTS.md` · `CLAUDE.md` · `.github/copilot-instructions.md` · `.kiro/steering/fux.md` | `AGENTS.md` holds the **canonical** contract; the others get a thin pointer to it |
| `--skills` | `.claude/skills/fux-query/SKILL.md` · `.claude/skills/fux-ingest/SKILL.md` · `.claude/skills/fux-debug/SKILL.md` | Agent Skills open standard — see [SKILLS.md](SKILLS.md) |
| `--hooks` | `.claude/settings.json` · `.kiro/hooks/fux-query.kiro.hook` | Claude Code + Kiro auto-injection |

- **Managed-block discipline.** `AGENTS.md`, `CLAUDE.md`, and the pointer files
  wrap Fux's content between `<!-- fux:managed:start -->` /
  `<!-- fux:managed:end -->`. Your own text outside the markers is never
  touched; re-running only refreshes what's between them.
- MCP is deferred (needs an ADR) — there is no MCP surface to install yet.

---

## The hooks, exactly as written

### Claude Code — `.claude/settings.json`

`setup --hooks` merges two entries into `hooks` without disturbing any keys you
already have (invalid JSON here is an error — fix it, then re-run):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "fux hook prompt-submit" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "fux hook session-end" } ] }
    ]
  }
}
```

### Kiro — `.kiro/hooks/fux-query.kiro.hook`

A user-triggered hook that tells the agent to query the corpus first:

```json
{
  "enabled": true,
  "name": "Fux: query the corpus first",
  "description": "Inject Fux passages so answers cite the project's own documents",
  "version": "1",
  "when": { "type": "userTriggered" },
  "then": {
    "type": "askAgent",
    "prompt": "Run `fux ask \"<the current question>\" --json` and ground your answer in the returned passages (cite their file:line). If sources changed, run `fux ingest` first."
  }
}
```

---

## What the Claude Code hooks do at runtime

Both entrypoints are **fail-open** — a hook error never breaks the host
session; failures trace only under `FUX_DEBUG=1`.

### `fux hook prompt-submit` (UserPromptSubmit)

Reads the prompt JSON on stdin, runs the equivalent of `fux ask`, and injects
the top passages as additional context. Prompts under 3 words, or an empty
corpus, produce no output (exit 0):

```
$ echo '{"prompt":"how long are crawled pages kept before expiry?"}' \
    | fux hook prompt-submit
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
"Fux corpus passages relevant to this prompt (cite file:line):\n- docs/decisions/0009-cache-ttl.md:6-8
· # Cache TTL Fux expires crawled web pages after 30 days; re-ingest refetches them.\n(from `fux ask`
— run it directly for more)"}}
```

### `fux hook session-end` (Stop)

Advisory only — if `docs/DOC-REGISTRY.md` exists, it prints a one-line nudge to
check the doc-freshness triggers; otherwise it stays silent. It never blocks:

```
$ echo '{}' | fux hook session-end
fux: docs/DOC-REGISTRY.md tracks maintained docs — if this session changed
behaviour, check the registry's triggers and update the docs.
```

---

## Related

[CLI.md](CLI.md) (the full command I/O contract) ·
[SKILLS.md](SKILLS.md) (using the generated skills) ·
[TOML.md](TOML.md) (the config `fux setup` writes) ·
[agent-integration](../compare/agent-integration.compare.md) (why AGENTS.md is
canonical and blocks are marker-delimited).
