# Claude Code prompt: Fux multi-assistant support

You are extending Fux's agent surface to Claude Code, Claude Cowork, Codex, GitHub
Copilot (CLI + VS Code), and Kiro. Full spec: `docs/handoff-02-multi-assistant.md` —
read it first; Definition of Done and Non-negotiables are binding.

## Context to load first
- Read: `fux/hooks.py`, `fux/hookio.py`, the `fux hooks` command impl,
  `tools/skillgen/platforms.toml`, `tools/skillgen/fragments/`, `tools/skillgen/gen.py`,
  `fux/data/hooks/*.sh`, `docs/skillgen.md`, `docs/cli.md` (hooks section), `CLAUDE.md`.
- Reference for shape only (read-only): `graphify/skill-kiro.md`, `skill-vscode.md`,
  `skill-copilot.md` in the graphify repo, and graphify's per-platform install layout.

## Task
1. Add Kiro + Copilot-VS-Code targets to skillgen (`platforms.toml` + fragments),
   re-render and `--bless`. 2. Add `--kiro` to `fux hooks install/uninstall/status`
   (and `--all`), writing native steering/skill files + any supported hook, reusing the
   existing idempotent installer. 3. Verify Codex + Copilot-CLI wiring end-to-end.
   4. Add a VS Code steering-file install. 5. Add a query-first steering instruction on
   every surface. Tier integration honestly: live hooks where the platform supports
   payload hooks, always-on steering files where it doesn't.

## Required workflow
1. **Explore** skillgen + the hooks installer before writing.
2. **Plan** the fragments, `platforms.toml` entries, and per-surface file layout; pause
   for my confirmation. **Do not implement the Cowork or true-VS-Code-extension items
   until I resolve the handoff §10 open questions.**
3. **Implement incrementally**, keeping `python -m tools.skillgen --check` and the test
   suite green at each step.
4. **Update docs**: README platform matrix, `docs/cli.md` hooks flags, `docs/skillgen.md`,
   `install.sh` + `fux/data/skills/fux/SKILL.md` (per CLAUDE.md), whats-new. Propose any
   CLAUDE.md/AGENTS.md edit for review — don't auto-apply.
5. **Verify**: `python -m tools.skillgen --check`, `python -m pytest -q`, and a manual
   install into throwaway Kiro/Copilot-VS-Code projects.

## Constraints (hard)
- **Generated, not hand-authored** rendered files — never hand-edit a rendered skill;
  edit fragments + `platforms.toml`, then `--bless`. Honour the CI `--check` gate.
- **Stdlib-only, `$0`, deterministic.** Installers copy/generate; no LLM, no network.
- Do NOT change hook *behaviour* or the fail-open/exit-code contract.
- Do NOT build the 15 other graphify platforms or a Marketplace VS Code extension
  unless §10 says so.

## Acceptance criteria (self-check)
- [ ] `fux hooks install --kiro` writes `.kiro/skills/` + `.kiro/steering/fux.md`;
      `status` detects it; `uninstall` removes only Fux entries; re-install idempotent.
- [ ] skillgen renders Kiro + Copilot-VS-Code from fragments; `--check` passes.
- [ ] Codex/Copilot-CLI verified; each surface carries query-first steering.
- [ ] Cowork + true-VS-Code items gated on §10, not silently built.
- [ ] Docs + install.sh + SKILL.md updated; tests green.

## Tests
Extend the hooks installer tests: per-surface file writes into `tmp_path`, status
detection, uninstall isolation, idempotency. Add a skillgen snapshot for each new target.

## Guardrails
- Resolve handoff §10 (Cowork mechanism; VS Code extension yes/no; other platforms)
  with me before touching those.
- If a platform's real config format differs from graphify's, follow the platform's
  docs and flag the difference — don't copy blindly.
- Ask before writing outside the project or modifying shared installer internals.
