# Consumer policy files — MOVED

**These graduated on 2026-08-22 and no longer live here.** Keeping a second copy
of a shipped artifact beside its proposal is how the two drift apart.

**They now live at [`src/fux/templates/agents/`](../../../src/fux/templates/agents/)**,
owned by [ADR-AGENT-POLICY](../../../docs/adr/0035_agent-policy.md), shipped as
wheel package data:

| file | consumer | installs as |
|---|---|---|
| `POLICY.md` | — | **not shipped**; the canonical source, and the verbatim block every rendering carries |
| `SKILL.md` | Claude (Code · Cowork) | a skill directory |
| `fux.agent.md` | GitHub Copilot | `.github/agents/fux.agent.md` |
| `fux-archived-results.instructions.md` | GitHub Copilot | `.github/instructions/…` |
| `steering-fux-archived-results.md` | Kiro (AWS) | `.kiro/steering/…` |

The reasoning is in [`../consumer-intent-policy.md`](../consumer-intent-policy.md);
the decision is the ADR.
