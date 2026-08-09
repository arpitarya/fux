# skillgen — the build-time skill renderer

`tools/skillgen/` renders fux's committed per-host skill artifacts from one human-edited
fragment set, and guards them against drift with `--check`. It is **build-time tooling**:
stdlib-only, never imported by the `fux` package at runtime, and never shipped in the wheel.

## Why this exists

fux's skill bodies and the copilot prompt were hand-authored per surface. As fux adds agent
hosts, each per-host variant drifts on its own — a fix to the claude `SKILL.md` silently
fails to reach the copilot prompt or a future AGENTS.md target. The fix is a build-time
renderer: one `core.md` body + per-host slots → N rendered artifacts, byte-diff guarded
against blessed `expected/` snapshots. It is **self-contained** — no shared module with any
other repo, which would break fux's standalone, zero-dependency guarantee.

**Scope (foundation):** the flagship `fux` skill only, to three hosts. The other 10 skills
and additional hosts stay hand-authored until follow-on packets ride this same renderer.

## The contract

- **`$0`, stdlib-only, deterministic.** `gen.py` imports only `argparse`, `re`, `sys`,
  `tomllib` (+ `dataclasses`/`pathlib`). No LLM, no network, no clocks, no random. Same
  fragments ⇒ byte-identical render (LF newlines, one trailing newline).
- **Fragments are the only thing a human edits.** The files under `fux/data/skills/…` and
  `fux/data/copilot/…` are **generated** — never hand-edit them.
- **`description` is the firing trigger** — preserved **verbatim** from `platforms.toml` per
  host, never normalized by the renderer.
- **Nothing under `tools/skillgen/` is importable at runtime** or present in the wheel/sdist
  (`exclude = ["tools*"]` in `pyproject.toml`; asserted by a test).

## Layout

```
tools/skillgen/
  gen.py             # the renderer (load_platforms, render, check, bless, headings, main)
  __main__.py        # python -m tools.skillgen entry point
  platforms.toml     # one [platform.<key>] table per rendered host
  fragments/core/    # the human-edited source bodies
    core.md          #   shared by claude + agents (slots: @@FRONTMATTER@@, @@POINTER_FILE@@)
    copilot.md       #   copilot's own agent:ask body (slot: @@FRONTMATTER@@)
  expected/          # blessed golden snapshots (flat; "/" -> "__" in the filename)
```

## Hosts

| host | body | rendered artifact (committed) | frontmatter | pointer file |
|---|---|---|---|---|
| `claude` | `core/core.md` | `fux/data/skills/fux/SKILL.md` | `name` + `description` | `CLAUDE.md` |
| `agents` | `core/core.md` | `fux/data/skills/agents/SKILL.md` | `name` + `description` | `AGENTS.md` |
| `copilot` | `core/copilot.md` | `fux/data/copilot/prompts/fux.prompt.md` | `agent` + `description` | — |

**`claude` + `agents` share `core/core.md`** — editing one shared line there re-renders both
in a single `--bless`. The only per-host delta is `@@POINTER_FILE@@` (the always-on pointer
file `fux init` writes: `CLAUDE.md` vs `AGENTS.md`). This is the breadth proof: a shared-line
edit can never touch only one of them.

**`codex` is not a render target.** It is served by the `claude` artifact verbatim — `fux
setup` copies `fux/data/skills/fux/` into `~/.codex/skills/fux/` (see
[fux/clicmds.py](../fux/clicmds.py)), so codex inherits every `core.md` edit through that
copy.

**`agents` install targets** (generic Agent-Skills spec, documented — installer wiring is a
follow-on packet): `~/.agents/skills/fux/SKILL.md` (global) and `./.agents/skills/fux/SKILL.md`
(project).

## Slots

`core.md` carries `@@FRONTMATTER@@` and `@@POINTER_FILE@@`; `copilot.md` carries only
`@@FRONTMATTER@@`. The renderer raises if any `@@SLOT@@` survives a render — a half-rendered
file is never emitted. (A dispatch/trigger slot and a references-sidecar split are
deliberately omitted: the `fux` skill fans out no subagents and is single-body.)

Frontmatter is rendered per `kind` (the description text is verbatim either way; the YAML
quoting is the host's convention, not an edit):
- `kind = "skill"` → `name: fux` + `description: "<verbatim>"` (Agent Skills spec).
- `kind = "prompt"` → `agent: ask` + `description: <verbatim>` (copilot `.prompt.md`).

## Workflow

```bash
python -m tools.skillgen                 # re-render every host's artifact
python -m tools.skillgen --platform claude
python -m tools.skillgen --check         # byte-diff render vs committed + expected/, exit 1 on drift
python -m tools.skillgen --bless         # rewrite expected/ from the current render
```

**To change a skill:** edit the fragment under `tools/skillgen/fragments/`, run
`python -m tools.skillgen` to re-render the committed artifacts, then
`python -m tools.skillgen --bless` to refresh the `expected/` snapshots. Commit the fragment,
the rendered artifacts, and the snapshots together.

## Drift guard

`python -m tools.skillgen --check` byte-diffs the render against both the committed artifacts
and the `expected/` snapshots, exiting 1 on any mismatch. It runs in:
- **CI** — the `skillgen-check` job in [.github/workflows/ci.yml](../.github/workflows/ci.yml).
- **pre-commit** — a local hook in [.pre-commit-config.yaml](../.pre-commit-config.yaml)
  (`pre-commit install` to enable).

A hand-edit to a generated file, or a forgotten `--bless`, fails the check the same way in
both places.

## Out of scope (follow-on packets)

The other 10 skills (adr, critic, debate, distill, fetch-rules, ingest, plan, propose-rules,
savings, trace); always-on CLAUDE.md/AGENTS.md block generation; the `agents` installer
wiring; more hosts; `--json`/hookio/nudges/`fux doctor`/version stamping.
