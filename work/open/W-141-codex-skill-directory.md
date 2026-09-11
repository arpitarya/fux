---
type: OpenItem
id: W-141
title: "W-141 — Codex reads repository skills from .agents/skills/, and fux writes .codex/skills/"
description: "ADR-AGENT-POLICY veto 3 (a shipped rendering no longer loads) may have fired for Codex: current Codex docs list .agents/skills for repository skills. Moving the rendering interacts with Copilot, which reads .agents/skills too. Arpit's ruling."
status: open
lane: arpit
timestamp: 2026-09-11T00:00:00Z
---

# W-141 — the Codex skill directory

**Model: Opus** for the change after the ruling — a roster edit, the two Codex
tests, and decisions 11, 13 and 14a in ADR-AGENT-POLICY.

**Found** 2026-09-11 while checking decision 15's guides against each vendor's
docs (see [W-140](W-140-guide-authoring-defects.md)).

OpenAI's Codex skills page (<https://developers.openai.com/codex/skills>) lists
repository skills at `$CWD/.agents/skills`, `$CWD/../.agents/skills` and
`$REPO_ROOT/.agents/skills`, and no `.codex/skills`. A third-party write-up calls
`.codex/skills` legacy. fux writes all thirteen Codex skills to `.codex/skills/`
(ADR-AGENT-POLICY decision 11). **Options:** (a) move to `.agents/skills/` —
Copilot reads it too, so a default install shows Copilot three same-name copies;
(b) write both; (c) keep `.codex/skills/` until a load failure is observed. The
same page says Codex shortens skill descriptions once the listing passes ~8 000
characters, which is why decision 15's guides cap descriptions at 500.

## Definition of done

Arpit picks (a), (b) or (c). For (a) or (b): the `codex` rows in `setup.AGENT_FILES`,
`test_codex_*` in `tests/test_setup_agents.py`, ADR-AGENT-POLICY decisions 11/13/14a
amended in the same change, and this repo's renderings refreshed.
