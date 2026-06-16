---
name: fux-critic
description: "critique a proposed change against the constitution before it lands — deterministic pass first, then host-agent self-critique on judgment principles; $0 to Fux"
trigger: /fux critic
---

# /fux critic — critique → revise → act, at the boundary

Run this **before a change lands** (a PreToolUse moment, or before `git commit`). Fux does the
deterministic part and gathers the relevant principles; **you, the host agent, do the
judgment self-critique with your own tokens** (plan §7c). Fux makes no API call.

## Inputs

`/fux critic "<proposed change>"` — a diff summary, the commit message, or the change you are
about to make.

## Procedure

1. **Ensure engine + project** — `skills/fux/SKILL.md` Steps 1–2.

2. **Deterministic pass first (Fux, `$0`, no LLM).** Run:
   ```
   fux critic "<proposed change>"
   ```
   It recalls the relevant principles, runs `check:`/seals for every **`deterministic`**
   principle, records the verdicts to `.fux/out/critic.jsonl`, and exits **2** if a hard
   invariant is violated. **If it exits 2, stop and fix the proposal** — a deterministic
   principle (money / PII / numbers / audit) is never waved through, and is **never** sent to
   you for an opinion.

3. **Judgment self-critique (you, in-session).** For each principle the command lists as
   `needs-judgment`, read the principle text and critique *your own* proposal against it
   honestly → a `pass`/`fail` verdict **with a one-line rationale**. Be adversarial: look for
   the way the proposal violates the principle, don't rationalise it.

4. **Revise + re-run (bounded).** If any judgment verdict is `fail`, revise the proposal and
   re-run from step 2. Cap at **3 rounds** — if it still fails, **escalate to the human** with
   the principle, your proposal, and why they conflict. Do not land the change.

5. **Borderline → debate.** If a judgment call is genuinely contested (you can argue it both
   ways), fire `/fux debate "<the contested rule/decision>"` (two-agent debate) rather than
   deciding alone. Only borderline/escalated cases — never every change (latency + cost).

6. **Act.** Only a proposal that passes the deterministic pass **and** every judgment principle
   (or a human-approved escalation) lands. The verdicts + applied principles are already in the
   audit trail; Cage meters the tokens this critique spent.

## Why this shape

The deterministic core is `$0` and unbypassable; the judgment is the session you already pay
for. Money/PII/numbers run as code and can never be argued down; tone/completeness/grounding
get a real self-critique instead of a rubber stamp. The split is enforced structurally
(`fux/critic.py`): a deterministic principle can never reach this self-critique step, and a
judgment principle is never faked as a machine check.
