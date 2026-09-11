---
type: OpenItem
id: W-118
title: "W-118 — fux-decoder and fux-usage reach every skill surface"
description: "Arpit ruled YES 2026-09-11: fux-decoder and fux-usage ship as skills for Claude, Copilot, Kiro and Codex. Only .github/skills/ (Copilot) is missing them today."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-118 — `fux-decoder` and `fux-usage` on every skill surface

**Model: Sonnet** — two roster rows, a test, and record edits against a written
definition of done; the only judgment (double-loading) is already recorded.

## The ruling

- **Arpit, 2026-09-11:** *yes* — `fux-decoder` and `fux-usage` go into skills for
  **Claude, Copilot, Kiro and Codex**.
- **Re-derived 2026-09-11 from `src/fux/setup.py`:**

| surface | `fux-decoder` | `fux-usage` | `fux-enrich` |
|---|:---:|:---:|:---:|
| `.claude/skills/` | ✅ | ✅ | ✅ |
| `.kiro/skills/` | ✅ | ✅ | ✅ |
| `.codex/skills/` | ✅ | ✅ | ✅ |
| `.github/skills/` (Copilot) | ❌ | ❌ | ✅ |

- **So the build is Copilot only.** The other three already comply.

## Definition of done

1. **`src/fux/setup.py`:** the Copilot roster gains
   `.github/skills/fux-decoder/SKILL.md ← DECODER-SKILL.md` and
   `.github/skills/fux-usage/SKILL.md ← USAGE-SKILL.md`; the comment block above it
   stops describing an asymmetry.
2. **This repo's own `.github/skills/`** is rendered through fux's install path and committed.
3. **`tests/test_setup_agents.py`:**
   - `test_the_two_rosters_differ_only_where_a_record_says_so` loses its exception —
     both set differences are empty; rewrite the docstring (or replace the test).
   - Add: each of `DECODER-SKILL.md`, `USAGE-SKILL.md`, `ENRICH-SKILL.md` reaches all
     four skill surfaces. `fux-archived-results` is ambient policy — out of scope.
4. **Records, in place (Law zero):**
   - [ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md) decision 14 widens to all
     three skills; the alternative *"Write `.github/skills/fux-decoder/`… deferred to a
     compare doc"* is rewritten as accepted by ruling; §1 diagram + ASCII twin if they list surfaces.
   - [ADR-DECODE](../../docs/adr/0049_decode.md) decision 12 (the `fux-decoder` skill's vendors).
   - Every record the freshness gate demands for `setup.py` (owner **and** describers) —
     run the gate, don't guess.
   - [`compare/copilot-skill-surface`](../compare/copilot-skill-surface.compare.md): the
     verdict block covers all three skills, ruled 2026-09-11; reopen-trigger unchanged.
5. `uv run pytest -q tests tests_e2e` green; `CHANGELOG.md` unreleased entry.
6. **Close-out:** delete the W-118 row from `OPEN-WORK.md`; `IMPLEMENTATION.md` +
   `WORKLOG` entries; DOC-REGISTRY bump; move this file to `archive/open/`.

## Hazards — recorded, not resolved by guessing

- ⚠ **Copilot will see two same-name copies** — it reads `.claude/skills` as well
  (ADR-AGENT-POLICY decision 13). The compare doc's reopen-trigger is an **observed
  error**, not a double-load. Keep it.
- ⚠ **Copilot already gets `fux-usage` ambiently** via
  `.github/instructions/fux-usage.instructions.md`. The skill is additive; say so in
  the record rather than removing either.
- Land after [W-132](W-132-freshness-baseline-to-head.md), or the suite is red for a reason unrelated to this change.
- Commit only your own paths. Do not push.

## Prompt

```
Execute work/open/W-118-decoder-usage-skill-surfaces.md exactly, after W-132 has landed.
Read CLAUDE.md, then that file. Explore → plan → implement → verify.
Re-derive the roster table from src/fux/setup.py before editing. Run
tests/test_adr_freshness.py to find every record setup.py demands.
Commit only your own paths; do not push. Finish with the close-out list.
```
