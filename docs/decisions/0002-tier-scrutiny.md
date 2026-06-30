---
id: adr-tier-scrutiny
type: adr
status: active
date: 2026-06-20
decided_by: Arpit (chair)
method: debate
---

# ADR 0002 — Which tiers require a debate (scrutiny ∝ bite × irreversibility)

## Decision
A full two-agent **debate is reserved for the constitutional tier only.** Lower tiers get
**proportional** scrutiny, not debate:

- **constitutional** → `/fux debate` (two-agent) → human `fux ratify`. Justified by **maximum bite
  AND supersession-only irreversibility**.
- **standard** → **no debate**; the existing proportional gate (`fux check` + `fux gate` + PR +
  `ai-review`) **plus a critic pass on promotion-to-active** so auto-proposed drafts face a real
  adversarial check before going live. Reversible via a normal PR ⇒ no up-front debate.
- **advisory** → no scrutiny gate; it only warns, it cannot block.

## Why
The thing that earns a debate is **not "this rule blocks"** — it is **"this rule is expensive to
undo."** Constitutional is supersession-only (you cannot edit it back), so the up-front debate is
worth it. Standard is reversible by a normal PR, so the cost of a bad one slipping is low and an
up-front debate is over-insurance. Requiring debate on every standard rule would collapse the tiers,
kill velocity, and make the rule-proposer pointless (it just moves cost from authoring to debating).

## Crux
The axis is **irreversibility + bite**, not "does it block the gate." Surfaced by the rule-proposer
volume question: auto-drafted standard rules need *real* scrutiny on promotion — but the cheap critic
pass, not a debate.

## Strongest surviving dissent
A standard rule still has teeth (it blocks), and at auto-proposer scale a thin human glance is weak.
Mitigation accepted: the **critic pass on promotion-to-standard** is mandatory and deterministic-first,
so junk auto-drafts can't sail to active — that closes the gap without paying for a debate.

## What would reverse this
If standard rules become effectively irreversible in practice (e.g. widely depended-on, painful to
change), their cost-of-being-wrong rises and a lightweight debate (single-reviewer, not two-agent)
could be warranted. Re-decide if standard stops being cheaply reversible.

Links: [[adr-fux-elgar-relationship]] · governs the `con-amendment` tier model + the rule-proposer
promotion path.
