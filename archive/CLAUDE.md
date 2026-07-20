# CLAUDE.md — coding-agent guide for the Fux engine repo

Fux is a portable, Claude-aware knowledge engine: one frontmatter substrate →
derived index, graph, and memory views, with `$0` deterministic maintenance. This
file is the orientation + working rules for any coding agent in this repo.

## Keep the docs in sync with the code (required)

**Whenever you change code, update the documentation in the same change.** At
minimum:

1. **[docs/fux-plan.md](docs/fux-plan.md)** — the *design of record*. Update it
   when behaviour, scope, or a resolved decision changes. Keep its status notes
   truthful.
2. **[docs/fux-implementation.md](docs/fux-implementation.md)** — the *status
   tracker* (✅ done / 🟡 partial / ⬜ not started). Flip statuses, update the
   module map, the test count, and the "Remaining / future work" list.
3. **[README.md](README.md)** — the public front door. Update it whenever the
   install/use surface, command list, guarantees, or the "what it does" summary
   change, so a newcomer never reads something the code no longer does.
4. **[docs/model-handoff-interview.md](docs/model-handoff-interview.md)** — the
   agent-succession handoff. **Read it before your first substantive change in this
   repo.** Update its "state of play" whenever project direction, strategy, or a
   major decision changes, and add yourself to its maintainer line when you do. The
   strategic design of record it points to is
   [docs/fux-fleet-vision.md](docs/fux-fleet-vision.md) — keep both true.

Then update **any other file the change touches**, e.g.:

- **[docs/implementation-notes.md](docs/implementation-notes.md)** — deltas vs the
  plan; the per-topic sections (AST scope, Recall, Verify, …) must not go stale.
- **[docs/cli.md](docs/cli.md)** — when a command, flag, or output changes.
- **[fux/data/schema.json](fux/data/schema.json)** + guides ([docs/rule.guide.md](docs/rule.guide.md),
  [docs/spec.guide.md](docs/spec.guide.md)) — when the rule schema changes.
- **[tests/](tests/)** — every behaviour change ships with a test.

A change is not "done" until the plan, the implementation file, and every other
affected doc reflect it. If you're unsure a doc is affected, check it.

## Non-negotiable constraints

- **`$0`, stdlib-only.** No third-party *runtime* dependencies — the frontmatter
  parser and schema validator are hand-rolled on purpose. The only optional extra
  is `[embeddings]` (local, off by default). No maintenance path may call an LLM.
- **Python ≥ 3.11** (`tomllib`). Match the surrounding code's style and density.
- **Deterministic.** Graph extraction, recall, check/fix, verify — all must be
  reproducible shell/AST/parse, never network or model calls.
- **Error contract.** Catch + render errors only at the boundaries (CLI `main`,
  hook entrypoints, MCP dispatch, installer); internals keep raising. Raise the one
  `FuxError` (`fux/errors.py`) for expected user-facing failures — no subclass
  hierarchy. CLI exit codes: `0` ok · `1` error · `2` blocking (strict) · `130`
  interrupted. Hooks are **fail-open** (a hook error never breaks the session) —
  but never fail-*silent*: every swallowed exception traces under `FUX_DEBUG=1`,
  and the deliberate strict `stop`→`2` is never swallowed.

## Layout

- `fux/` — the engine. CLI dispatch in [fux/cli.py](fux/cli.py); commands in
  `clicmds`/`cliquery`/`cligraph`; graph in `graph`/`astextract`/`community` +
  the viewer in `assets/`; recall in `recall`/`embed`/`hybrid` + `bench`; verify
  in `verify`/`vexamples`; quality/health/enforcement in `lint`/`stats`/`gate`;
  cost in `savings`; memory capture/governance in `capture`/`governance`; agent
  integration in `mcpserver`; dashboard in `serve`; migration/decommission in
  `importer`/`narrative`/`parity`; hooks in `hooks`/`touch`/`hookio`.
- `fux/data/` — seed assets bundled into the PyPI package: `hooks/` (shell hook
  wrappers), `global/` (best-practice rules), `skills/` (workflow skill docs),
  `packs/` (optional knowledge packs), `schema.json`. Copied to `~/.claude/fux/`
  by `fux setup` (PyPI install) or `install.sh` (dev/editable install).
- `skills/` — workflow skill docs (`plan`/`adr`/`trace`/`savings`); only
  `plan`/`adr` call the LLM. Add one → also wire it into [install.sh](install.sh)
  and `fux/data/skills/fux/SKILL.md`.
- `tests/` — pytest suite; `docs/` — plan + status + reference.

## Build & test

```bash
python -m pytest -q          # full suite (Python ≥ 3.11)
fux build && fux check       # regenerate views + validate (both $0)
```
