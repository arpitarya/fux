# Handoff: fux skillgen renderer foundation

**One-liner:** Add a build-time, stdlib-only `tools/skillgen/` renderer to fux that emits every committed skill artifact from one human-edited fragment set, guarded against drift by `--check` in CI — and prove the breadth payoff by rendering the flagship `fux` skill to the existing hosts plus a new generic `agents` (AGENTS.md) target.
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Challenged as over-engineering (a codegen system for skills that barely drift today). Survives only because breadth is the payoff → this packet *must* include the `agents` target to prove it in slice 1 (pre-mortem: the #1 abandonment cause is "nobody added hosts"). `expected/` rot risk → mitigated by manual-diff-before-first-bless + an anchor test asserting non-negotiable lines survive. Residual risk: if breadth is never pursued past this, the renderer is marginal — accepted because subsequent packets add nudges/CLI/more hosts that all ride this renderer.

## 1. Context & background
fux's skill bodies (`fux/data/skills/<name>/SKILL.md`, 11 of them) and the copilot prompts (`fux/data/copilot/prompts/`) are hand-authored per surface. As fux adds agent hosts, each skill's per-host variant drifts independently. A build-time renderer solves this: one `core.md` template + per-host delta fragments → N rendered artifacts, byte-diff-guarded by `--check` against blessed `expected/` snapshots. This packet brings that renderer into fux, scoped to the **flagship `fux` skill only** as the proving ground. The other 10 skills, the always-on blocks, the hook/CLI enhancements, and more hosts are **follow-on packets** that build on this foundation.

## 2. Definition of done
The build is done when ALL are true:
- [ ] `tools/skillgen/{gen.py, platforms.toml}` + `fragments/` + `expected/` exist; `python -m tools.skillgen` renders, `--check` exits 0 on a clean tree, exits 1 on any drift, `--bless` rewrites `expected/`.
- [ ] `gen.py` is **stdlib-only** (`tomllib`, `re`, `pathlib`, `argparse`) — zero new runtime deps; nothing under `tools/skillgen/` is imported by the `fux` package at runtime.
- [ ] The committed `fux/data/skills/fux/SKILL.md` (claude) and the new per-host variants are **reproducible** from `fragments/` — editing a shared line in `core.md` updates every host in one `--bless`.
- [ ] Hosts rendered for the `fux` skill: `claude`, `codex`, `copilot`, **`agents`** (generic AGENTS.md / `~/.agents/skills` + `./.agents/skills`). The `agents` target is the breadth proof and is non-negotiable in this packet.
- [ ] `python -m tools.skillgen --check` is wired into both pre-commit and CI, alongside the existing `fux build && fux check`.
- [ ] `tools/skillgen/` is excluded from the built wheel; a test asserts it's absent from the wheel/sdist.
- [ ] An anchor test asserts each rendered `fux` skill body still contains the skill's non-negotiable lines (frontmatter `name`/`description` verbatim, the `## Usage` block, the `$0` claim).
- [ ] Render is byte-deterministic (a test renders twice and asserts identical bytes).
- [ ] Documentation updated to match (see §9.5).

## 3. Scope
**In scope:** the renderer skeleton; `platforms.toml` for `claude/codex/copilot/agents`; `core.md` + delta fragments for the **`fux` skill only**; `expected/` golden set; `--check` in pre-commit + CI; wheel exclusion; anchor + determinism tests; the doc-of-record for skillgen.

**Out of scope (explicit) — do NOT build in this packet:**
- The other 10 skills (adr, critic, debate, distill, fetch-rules, ingest, plan, propose-rules, savings, trace) — they stay hand-authored until a follow-on packet.
- Always-on CLAUDE.md/AGENTS.md block generation (§5 of the spec) — follow-on.
- `hookio.emit` envelope work, the pre-read / pre-edit nudges, `--json`, `fux doctor`, version stamping (§11–§13) — follow-on.
- `kiro` and any host beyond the four listed — follow-on.
- Do **not** refactor the existing `fux/data/skills/` consumers or `fux setup`/`install.sh` asset copy beyond pointing them at the (unchanged-location) rendered `fux` skill.

## 4. Current state
- Repo: `/Users/arpitarya/my_programs/fux`
- Read first: `fux/data/skills/fux/SKILL.md` (the body to templatize), `CLAUDE.md`, `docs/fux-plan.md`, `docs/fux-implementation.md`, `README.md`, `docs/cli.md`, `pyproject.toml`, `install.sh`, `fux/clicmds.py` (`cmd_setup`).
- Reference implementation to copy from (read-only, a separate renderer repo): its `tools/skillgen/{gen.py,platforms.toml}` and `tools/skillgen/fragments/`. Copy the *structure*, strip the migration-only validators (`--audit-coverage`, `--monolith-roundtrip`, `--schema-singleton`, `--*-roundtrip`) — keep only `load_platforms`, `Platform`, `_render_core`, `render`, `render_all`, `write_artifacts`, `check`, `bless`, `headings`/anchor helper, `main`. Target ~250 lines.
- Architecture today: `fux` is zero-dep stdlib Python ≥3.11; derived views regenerate via `fux build` ($0, AST/parse only, no LLM). Skills are static assets copied by `fux setup` / `install.sh` to `~/.claude/fux/` and skills dirs.

## 5. Technical approach (decided)
- **Per-repo copy of `gen.py`** — fux gets its own; **no shared module with any other repo** (would break fux's standalone zero-dep guarantee).
- **Buckets:** use the reference renderer's `split` model (lean core + `references/` sidecar) only if the `fux` skill is long enough to warrant it; otherwise render a single body per host. Decide by length — the current `fux` SKILL.md is ~1 screen, so **single-body per host is fine for v1**; keep the `split` code path but don't force it.
- **Slots in `core.md`:** `@@FRONTMATTER@@`, `@@TRIGGER@@` (the `/fux` invocation idiom per host), `@@DISPATCH@@` (only if a skill fans out subagents — `fux` does not, so this may be empty/omitted), `@@HOST_NOTE@@` (per-host framing: skill vs prompt vs steering). Raise on any unfilled `@@SLOT@@`.
- **`description` is the firing trigger — preserved verbatim per `[platform.<key>]`**, never normalized by the renderer.
- **`expected/` is a flat, fully-tracked dir**; `check()` byte-diffs render vs committed artifacts AND vs `expected/`.
- **`agents` host** writes to `fux/data/skills/agents/…` source-side and documents install targets `~/.agents/skills/fux/SKILL.md` (global) + `./.agents/skills/fux/SKILL.md` (project).

## 6. Non-negotiables / constraints
- **Style/patterns:** match fux house style — files small/single-purpose, absolute imports, Python ≥3.11. Follow `CLAUDE.md`.
- **Use:** stdlib only (`tomllib`, `re`, `pathlib`, `argparse`). **Avoid:** any third-party runtime dep; any LLM/network call on any path (fux's `$0` deterministic law); any cross-repo import.
- **Determinism:** same fragments ⇒ byte-identical render. Normalize to LF. Sort references. No clocks/random.
- **Compliance/safety:** N/A (no money/PII surface in skill rendering). Do not embed secrets in fragments.
- **Do not touch:** the runtime `fux/` engine modules (cli, clicmds, hooks, graph, recall, verify…) except the minimal `fux setup` pointer if a path changes (it shouldn't — keep rendered output at the existing `fux/data/skills/fux/` path). Do not change the schema, the constitution lock, or any existing skill body other than `fux`.

## 7. Dependencies & prerequisites
- Python ≥3.11 (`tomllib`). No env vars, no services, no secrets.
- Read access to the reference renderer implementation (already mounted).

## 8. Edge cases & risks
- **Unfilled slot** → `gen.py` must raise with the leftover `@@SLOT@@` name (don't emit a half-rendered file).
- **CRLF in a fragment** → `_normalise()` to LF before diff so `--check` doesn't false-positive.
- **First `--bless` blesses a wrong render** → mitigate with the mandatory manual diff in the workflow (the executor must show the render-vs-current diff for the `fux` skill and pause for confirmation before the first bless).
- **Wheel accidentally ships `tools/skillgen/`** → add the packaging exclude AND the wheel-content test in the same change.
- **`agents` install path collision** with amp/antigravity conventions → use the generic spec paths (`~/.agents/skills`, `./.agents/skills`) exactly; document them.

## 9. Testing & validation
- **Must test:** (a) render is byte-deterministic across two runs; (b) `--check` exits 0 clean, exits 1 after a deliberate fragment edit without re-bless; (c) anchor test — each rendered `fux` host body contains frontmatter name/description + `## Usage` + the `$0` line; (d) wheel/sdist excludes `tools/skillgen/`; (e) every `@@SLOT@@` is filled (no `@@` survives in any rendered artifact).
- **Verify locally:** `python -m pytest -q` · `python -m tools.skillgen --check` · `fux build && fux check` · `python -m build` then inspect the wheel contents (or the existing build smoke path).
- **Manual check:** show the diff of the rendered `fux` claude SKILL.md vs the current committed one; confirm semantic equivalence before the first `--bless`.

## 9.5 Documentation impact
- [x] **README** — required: add a short "skill artifacts are generated; edit `fragments/`, run `--bless`" note so contributors don't hand-edit rendered skills.
- [x] **AI agent files (CLAUDE.md)** — required, but ⚠️ PROPOSE for review, do not auto-write: add a "Skill artifacts are rendered by `tools/skillgen`; never hand-edit `fux/data/skills/fux/`" rule. Surface the exact diff for Arpit.
- [x] **docs/fux-plan.md + docs/fux-implementation.md** — required: skillgen is a new design-of-record component; add a section + flip a status row. Also add a new `docs/skillgen.md` design doc.
- [x] **docs/cli.md** — required only if a CLI command is added. This packet adds none (skillgen is `python -m tools.skillgen`, build-time) → note "no fux CLI surface change."
- [ ] **CHANGELOG / release notes** — N/A: build-time tooling, no user-facing runtime change (state this explicitly).
- [ ] **API / schema** — N/A: schema unchanged.
- [ ] **ADR** — optional: the "per-repo copy, no shared module" decision is worth a one-paragraph ADR if fux keeps ADRs.

## 10. Open questions
- OPEN QUESTION: does Claude Code (and codex/copilot) actually drop plain-stdout hook output for non-SessionStart events, requiring the `{"hookSpecificOutput":{...}}` envelope? This drives the *follow-on* hookio packet, not this one — verify against current Claude Code hook docs before that packet, don't assume.
- OPEN QUESTION: should the `fux` skill use the `split` (core + `references/`) bucket now, or stay single-body until a longer skill (plan/debate) forces it? Default: single-body for `fux`; revisit in the multi-skill packet.
- OPEN QUESTION: exact source-side location for the `agents` host bundle — confirm `fux/data/skills/agents/` mirrors the existing `fux/data/skills/<host>/` convention.
