# Fux — Debate/Council Decision Capture: One-Shot Prompt

Paste into Claude Code in the `fux` repo. Full spec: `docs/decision-capture-handoff.md`.

```
Make debate/council capture a fux capability per docs/decision-capture-handoff.md: when a /fux debate or
decision-council concludes, fux writes a tamper-evident decision record (ADR) and routes it to the right
store BY CONTENT. Read that handoff plus the existing debate skill, cli.py, fux/check.py, fux/seal.py, and
fux/data/schema.json first. Plan briefly, show me the plan, then implement.

HARD CONSTRAINTS:
- $0, stdlib, deterministic CAPTURE path (no LLM/network). The debating is the host agent's tokens; the
  capture — format ADR, classify route, seal, write — is deterministic fux harness. Guard test proves it.
- FIREWALL (per ADR 0001, fux/docs/decisions/0001-fux-elgar-relationship.md): a money-related decision
  record goes to ELGAR; fux stores ONLY an `elgar://decision/<id>` link and NEVER the money body. fux is
  decider + link-keeper, not custodian.
- Tamper-evident: every record carries debate_hash (transcript) + content_seal (body); fux check flags an
  altered record. Files ≤100 lines. No new deps. Docs in this change.

DO:
1. new decisioncapture.py (≤100): format the ADR (id, date, decided_by, method[debate|decision-council],
   decision, why, crux, strongest_dissent, what_would_reverse) from the agent's transcript+verdict; compute
   debate_hash + content_seal (reuse seal/hash helpers); route + write per the table below. Deterministic.
2. ROUTING by content (agent suggests, human confirms; CONFIRM MANDATORY for money/elgar):
   - world/code/architecture/tool-design → fux (fux/docs/decisions/NNNN-*.md, content-sealed)
   - Anton-app-specific → anton (.fux/ type: adr, content-sealed)
   - money/personal-figures/portfolio → ELGAR: the agent/elgar writes the record; fux records ONLY
     elgar://decision/<id> — never the body.
3. cli.py: add `fux capture-decision` and wire /fux debate + the council skill to CALL capture on
   conclusion (surface the suggested store; require confirm for money/elgar).
4. data/skills/debate/SKILL.md (+ council skill doc): hand transcript+verdict to capture at the end.
5. schema.json: ensure type: adr carries decided_by, method, debate_hash, content_seal (additive).
6. check.py: verify a captured ADR's content_seal (tamper finding on mismatch); GUARD — a money/elgar
   decision in fux must be a link only; flag any fux-side record containing money content (firewall, ADR 0001).

TESTS + PROVE IT:
- concluding a debate/council writes a routed record with debate_hash + content_seal.
- a money-classified decision routes to elgar with fux holding only elgar://decision/<id> (no money body);
  routing required explicit confirm.
- editing a captured ADR trips a content_seal tamper finding.
- the firewall guard flags a fux-side record that contains money content.
- GUARD TEST: no LLM/network import on the capture/check path.
Run `python -m pytest -q` and paste output. Update cli.md/fux-plan/README in this change. Keep ADR 0001 as
the format exemplar.
```
