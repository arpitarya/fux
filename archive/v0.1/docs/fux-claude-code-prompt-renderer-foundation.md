# Claude Code prompt: fux skillgen renderer foundation

You are adding a build-time, stdlib-only skill renderer to the **fux** repo. The full spec is in the handoff doc `fux-handoff-renderer-foundation.md` — read it first and treat its Definition of Done, Scope, and Non-negotiables as binding.

## Context to load first
- Read: `fux/data/skills/fux/SKILL.md` (the body you'll templatize), `CLAUDE.md`, `docs/fux-plan.md`, `docs/fux-implementation.md`, `README.md`, `pyproject.toml`, `install.sh`, `fux/clicmds.py` (`cmd_setup`).
- Reference implementation to copy structure from (READ-ONLY, a separate renderer repo, do not modify): its `tools/skillgen/gen.py`, `.../platforms.toml`, `.../fragments/`.
- Respect project conventions in `CLAUDE.md`, the `$0`/stdlib-only/deterministic law, and Python ≥3.11.

## Task
Create `tools/skillgen/` in fux: `gen.py` (a stripped ~250-line port of the reference renderer — keep only `load_platforms`, `Platform`, `_render_core`, `render`, `render_all`, `write_artifacts`, `check`, `bless`, an anchor/`headings` helper, and `main` with `--check`/`--bless`/`--platform`; drop all migration-only validators), `platforms.toml`, `fragments/` (the only human-edited source), and `expected/` (blessed snapshots). Templatize the **`fux` skill only** into `fragments/core/core.md` with `@@SLOT@@`s, and render it to four hosts: `claude`, `codex`, `copilot`, and a new generic **`agents`** (AGENTS.md) target. Wire `python -m tools.skillgen --check` into pre-commit and CI. Exclude `tools/skillgen/` from the wheel.

## Required workflow
1. **Explore** the reference `tools/skillgen/` and fux's current skill/asset layout before writing anything. Map its slots to what the `fux` skill actually needs (it does NOT fan out subagents, so the dispatch slot may be empty/omitted).
2. **Plan** — lay out: the files you'll create, the `platforms.toml` table per host, the `@@SLOT@@` set, the rendered output paths (keep the claude `fux` skill at its EXISTING path `fux/data/skills/fux/SKILL.md` so consumers don't move), and the test list. **Pause for my confirmation before implementing.**
3. **Implement incrementally** — renderer skeleton first (prove `--help` + render run stdlib-only), then fragments for the `fux` skill, then the four hosts, then `--bless`, then CI wiring, then wheel exclusion, then tests. Keep the build green at each step.
4. **Manual bless gate** — before the FIRST `--bless`, print the diff between your rendered `fux` claude SKILL.md and the current committed one, and STOP for my confirmation that they're semantically equivalent. Do not bless a render I haven't reviewed.
5. **Update docs to match** — README (contributors edit fragments, not rendered skills), `docs/fux-plan.md` + `docs/fux-implementation.md` (new skillgen component + status row), a new `docs/skillgen.md`. For `CLAUDE.md`: PROPOSE the "never hand-edit rendered skills; edit fragments + `--bless`" rule as a diff and flag it for my review — do NOT silently rewrite it. CHANGELOG/schema/cli.md are N/A here — say so.
6. **Verify** after changes: `python -m pytest -q`, `python -m tools.skillgen --check`, `fux build && fux check`, and a wheel build + contents inspection. Fix what you break. Do not report done until these pass.

## Constraints (hard)
- Use: stdlib only (`tomllib`, `re`, `pathlib`, `argparse`). Do NOT use: any third-party runtime dependency; any LLM or network call on any path; any import that shares code across repos (fux's `gen.py` is its own copy).
- Determinism: same fragments ⇒ byte-identical render; normalize to LF; sort references; no clocks/random.
- Preserve each host's `description` (the firing trigger) VERBATIM from `platforms.toml` — never normalize it.
- Do not modify: the runtime `fux/` engine modules, the schema, the constitution lock, or any existing skill body other than `fux`. Keep the rendered `fux` claude skill at its current path.
- `tools/skillgen/` must never be imported by the `fux` package at runtime and must not ship in the wheel.

## Acceptance criteria (self-check before finishing)
- [ ] `--check` exits 0 clean, exits 1 on an un-blessed fragment edit; `--bless` rewrites `expected/`.
- [ ] `fux` skill renders for claude/codex/copilot/agents; editing one shared `core.md` line updates all four in one `--bless`.
- [ ] `gen.py` stdlib-only; nothing under `tools/skillgen/` imported at runtime.
- [ ] Anchor test (frontmatter name/description + `## Usage` + `$0` line present per host), determinism test (render twice = identical), no-unfilled-slot test, wheel-excludes-skillgen test — all passing.
- [ ] `--check` in pre-commit + CI.
- [ ] Docs updated (README, fux-plan, fux-implementation, docs/skillgen.md); CLAUDE.md rule proposed for review; CHANGELOG/schema/cli.md noted N/A.

## Tests
Add tests covering: byte-determinism; `--check` pass/fail; per-host anchor lines; no surviving `@@` in any artifact; wheel/sdist excludes `tools/skillgen/`. Run with `python -m pytest -q`.

## Guardrails
- Ask before: deleting any existing skill asset, moving the rendered `fux` skill path, changing `pyproject.toml` packaging beyond the skillgen exclude, or editing the constitution lock.
- Do not auto-edit `CLAUDE.md` — propose the diff for review.
- If a requirement is ambiguous or conflicts with the code (e.g. the `agents` source path convention, or whether `split` bucket is needed), STOP and ask rather than guessing.
- This packet is the renderer foundation ONLY. Do not build hookio/`--json`/nudges/`fux doctor`/other skills/more hosts — those are explicit out-of-scope follow-on packets.
