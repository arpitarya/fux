# Handoff 02: Multi-assistant support — Claude Code, Cowork, Codex, Copilot, Kiro (CLI + VS Code)

**One-liner:** Extend Fux's agent-surface so it installs and drives itself from
Claude Code, Claude Cowork, Codex, GitHub Copilot (CLI + VS Code), and Kiro — via
generated per-platform skill/steering files, per-surface hook wiring, and a thin VS
Code extension, all from one `fux hooks`/skillgen source of truth.
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Devils-advocate — "you're chasing graphify's 20-platform surface;
that's a treadmill and most have no payload hooks, so it degrades to a static
AGENTS.md nudge anyway." **Survived, but scope-cut:** target only the five surfaces
you named, not 20; accept that non-Claude platforms get **query-first steering files**
(not live hooks) — that's exactly what graphify does and it's honest. **Blocked
one item:** a *true* VS Code extension (TS, marketplace, packaging) is a
disproportionate build for the value — **downgraded to a steering-file install +
optional lightweight extension** and flagged as an open question, not committed.
**Residual risk:** each platform's config format drifts; the generated approach
(skillgen) contains that blast radius to fragments, not hand-maintained files.

## 1. Context & background

Today Fux wires Claude/Codex/Copilot/git via `fux hooks` and renders skill artifacts
via `tools/skillgen` (`platforms.toml` + fragments → `SKILL.md`, `AGENTS.md`, copilot
prompt). Graphify demonstrates the target: per-platform skill files
(`skill-kiro.md`, `skill-vscode.md`, …) + `graphify <platform> install`. Fux already
has the generator; this extends it to the surfaces you use. Claude Cowork is the
newest and least-documented target — treat as an open question (§10).

## 2. Definition of done

- [ ] `fux hooks install --kiro` (and status/uninstall) wires Kiro
      (`.kiro/skills/` + `.kiro/steering/fux.md`), mirroring graphify's Kiro layout.
- [ ] skillgen renders a Kiro skill fragment and a Copilot-VS-Code prompt from
      `platforms.toml` + fragments — no hand-authored rendered files (CI `--check` guards).
- [ ] Codex + Copilot (CLI) wiring verified end-to-end (already partial): PreToolUse
      hook where supported, AGENTS.md steering where not.
- [ ] Claude Cowork: **OPEN QUESTION resolved** — either documented as "same as
      Claude Code (skills + MCP)" or a Cowork-specific pointer, decided with Arpit.
- [ ] VS Code: at minimum a steering-file install; the true extension is scoped as a
      separate, optional deliverable (see §10) — not silently built.
- [ ] Each surface has a query-first instruction (prefer `fux recall`/`why`/`refs`
      over grep), matching graphify's query-first steering.
- [ ] `fux hooks status` reports all wired surfaces; `uninstall` removes only Fux
      entries (existing idempotent/migrating behaviour preserved).
- [ ] Docs updated (§9.5), including a platform matrix in the README/cli.md.

## 3. Scope

**In scope:** Kiro install/uninstall/status; skillgen fragments for Kiro + Copilot-
VS-Code; verifying Codex/Copilot-CLI; a Cowork decision; a VS Code steering install.
**Out of scope (explicit):** the 15 other assistants graphify supports (Cursor,
Aider, Amp, Gemini, OpenCode, …) — not requested; a published VS Code Marketplace
extension unless the §10 open question says yes; changing any hook's *behaviour*
(this is surface wiring, not new engine logic); anything that calls an LLM.

## 4. Current state

- Read first: `fux/hooks.py` + `fux/hookio.py` (hook entrypoints/IO), the `fux hooks`
  command impl, `tools/skillgen/platforms.toml` + `tools/skillgen/fragments/` +
  `tools/skillgen/gen.py`, `fux/data/hooks/*.sh`, `docs/skillgen.md`, `docs/cli.md`
  (hooks section + internal hook entrypoints table).
- Reference (graphify, read-only for shape): `graphify/skill-kiro.md`,
  `graphify/skill-vscode.md`, `graphify/skill-copilot.md`, its per-platform install
  layout (`.kiro/skills/` + `.kiro/steering/`, `.cursor/rules/*.mdc alwaysApply`).
- Constraint context: CLAUDE.md — skill artifacts are **generated**; hand-edits fail
  `python -m tools.skillgen --check` in CI. New surface ⇒ new fragment + platforms.toml
  entry + `--bless` snapshot, never a hand-written rendered file.

## 5. Technical approach (decided)

1. **Extend skillgen, don't fork it.** Add Kiro + Copilot-VS-Code targets to
   `platforms.toml`; author fragments; re-render + `--bless`. This keeps every
   surface's steering text single-sourced.
2. **Extend `fux hooks` surface flags** to include `--kiro` (and pass-through in
   `--all`), writing the platform's native steering/skill files + any supported hook.
   Reuse the existing idempotent/migrating installer machinery.
3. **Tier the integration honestly** by platform capability: payload-hook platforms
   (Claude Code; Codex PreToolUse) get the live pre-search nudge; steering-only
   platforms (Kiro, Copilot-VS-Code, Cursor-style) get an always-on instruction file.
   Document which is which (graphify does exactly this).
4. **VS Code:** phase 1 = steering-file install (`.vscode`/Copilot instructions).
   Phase 2 (optional, gated) = a thin extension that shells `fux recall`/`serve`.
5. **Cowork:** most likely identical to Claude Code (skills + MCP + hooks). Confirm
   with Arpit; if bespoke, add a minimal pointer.

## 6. Non-negotiables / constraints

- **Generated, not hand-authored** steering files — respect the skillgen `--check`
  gate; wire any new skill into `install.sh` + `fux/data/skills/fux/SKILL.md` per CLAUDE.md.
- **Stdlib-only, `$0`, deterministic.** Installers copy/generate files; no LLM, no network.
- **Fail-open hooks unchanged** — never regress the exit-code/fail-open contract.
- **Agent-steering files (CLAUDE.md/AGENTS.md):** propose edits for review; the
  *installer* may write project-local steering, but repo-level steering-doc changes
  are surfaced, not auto-applied.
- **Do not touch:** hook *behaviour*, the error contract, engine internals.

## 7. Dependencies & prerequisites

Knowledge of each target's config path/format (Kiro `.kiro/`, Copilot VS Code
instructions file, Cowork). No external services. VS Code extension phase-2 would add
a Node/TS toolchain — out of the stdlib engine, packaged separately if pursued.

## 8. Edge cases & risks

- Platform changes its config path → contained to a fragment/`platforms.toml` entry.
- A pre-existing foreign hook/steering file → preserve it (existing `uninstall` backs
  up git pre-commit to `.pre-fux`; mirror that care per surface).
- Cowork wiring unknown → do not guess; gate behind the §10 decision.
- Copilot has both a CLI and a VS Code Chat surface — keep them distinct targets.

## 9. Testing & validation

- Unit: installer writes the right files per surface into a tmp dir; `status`
  detects them; `uninstall` removes only Fux entries; idempotent re-install.
- skillgen: `python -m tools.skillgen --check` passes; snapshots refreshed via `--bless`.
- Manual: install into a throwaway Kiro/Copilot-VS-Code project; confirm the
  query-first steering is present and the MCP/skill resolves.
- `python -m pytest -q` green.

## 9.5 Documentation impact

- [ ] **README** — required: platform matrix (which surfaces, hook vs steering).
- [ ] **docs/cli.md** — required: `fux hooks` flag list + internal-hook table updates.
- [ ] **docs/skillgen.md** — required: new fragments/targets.
- [ ] **install.sh** + **fux/data/skills/fux/SKILL.md** — required per CLAUDE.md when adding a skill surface.
- [ ] **CLAUDE.md / AGENTS.md** — propose: note the expanded surface list for future agents.
- [ ] CHANGELOG/whats-new — required (user-facing capability).

## 10. Open questions

- OPEN QUESTION: **Claude Cowork wiring** — same as Claude Code (skills+MCP+hooks), or
  a Cowork-specific mechanism? Needs Arpit's confirmation before implementing.
- OPEN QUESTION: **true VS Code extension** — build the thin TS extension (phase 2) or
  stop at steering-file install? Recommendation: steering-file now; extension only if
  you actually live in VS Code and want a `fux` panel.
- OPEN QUESTION: do you want the other graphify platforms (Cursor/Gemini/Aider) now or
  later? Default: later — this handoff covers only the five you named.
