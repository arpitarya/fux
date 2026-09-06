---
type: Compare Doc
title: Copilot Skill Surface
description: Now that Copilot reads Agent Skills, does fux write .github/skills/ for it — or rely on the .claude/skills copy Copilot already reads?
status: accepted
timestamp: 2026-09-06T00:00:00Z
---

# Copilot's skill surface — write `.github/skills/`, or don't? — Comparison

> **Verdict: A — write `.github/skills/`.** ✅ **Ruled by Arpit 2026-09-06,
> overruling this document's proposed C.** Shipped for `fux-enrich`; the
> decoder and usage rows were not asked for and did not ship.
> **Confidence:** medium-high — see *The crux, corrected* below: the collision
> this doc called *unknown* is bounded much more tightly than it was written,
> because the two copies are **byte-identical by construction**.
> **Reopen when:** Copilot is observed to **error** (not merely double-load) on
> two project skills sharing a `name:`, in any repository where both
> `.github/skills/fux-enrich/` and `.claude/skills/fux-enrich/` exist.

## Context

[ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md) decision 9a shipped
`fux-decoder` to Claude and Kiro and **not** Copilot, on a fact that was true
when it was written: *"a Kiro skill is progressive-disclosure; only Kiro
steering is ambient — which admits Kiro while still excluding Copilot's
`instructions/`."* Copilot had **no progressive-disclosure surface**, so the
only rendering available to it was ambient, and a committed-write skill may
never be ambient.

**That fact expired.** Copilot now supports Agent Skills, and reads project
skills from **three** directories: `.github/skills`, `.agents/skills`, and
`.claude/skills`.

Two consequences, and they pull opposite ways:

1. **The exclusion's reason is gone.** Copilot has a progressive-disclosure
   surface now, so 9a no longer excludes it.
2. **The exclusion is already moot in practice.** Copilot reads
   `.claude/skills` — so in the default install it *already* loads
   `fux-decoder`, and `fux-enrich`, and everything else fux writes for Claude.
   That is [ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md) decision 13.

## Options

- **A — write `.github/skills/fux-decoder/SKILL.md` and
  `.github/skills/fux-usage/SKILL.md`.** Vendor-owned path, consistent with
  every other row in `AGENT_FILES`, and correct under decision 5
  (declared-never-derived): fux must not assume `claude` also installs.
- **B — write `.agents/skills/`.** The vendor-neutral directory Copilot also
  reads. One rendering, potentially several readers.
- **C — write nothing new; record decision 13 and stop.** *(proposed verdict)*
  Copilot already loads these skills from `.claude/skills` in the default
  install. Writing a second copy buys coverage only in the
  `install = ["copilot"]`-without-`claude` case, which **no observed
  repository has**.

## Matrix

| criterion (weight) | A `.github/skills` | B `.agents/skills` | C nothing |
|---|---|---|---|
| covers `["copilot"]` alone (H) | **yes** | yes | **no** |
| duplicate-name risk in the default install (H) | 🔴 **unknown** — two folders, same `name:` | 🔴 unknown, same shape | **none** |
| ambient tax (H) | none — progressive disclosure | none | none |
| honours declared-never-derived (H) | yes | yes | ⚠ **strains it** — C is correct only *because* claude usually installs, which is an assumption about the filesystem in all but name |
| new templates (M) | 0 | 0 | 0 |
| reversibility (M) | high — two rows | high | high |
| standing on a measured fact (H) | no | no | **no** — C's advantage is that it does not need one |

## The crux, corrected

**As written:** *nobody knows what two same-named project skills do in Copilot
— dedupe, double-load, or an error*, so A and B ship on a guess and C does not.

🔴 **That framing overstated the unknown, and the correction is this document's
own.** The two copies are **byte-identical by construction** — one template,
N destinations, [ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md)
decision 10 — so *dedupe* and *double-load* are **the same outcome**: the same
instructions, once or twice, idempotent either way. The only branch that costs
anything is a **hard error on duplicate names**, and that is a much narrower
claim than *unknown behaviour*.

**Against that, C's hole is concrete and certain:** `install = ["copilot"]`
without `claude` gets an agent file, two ambient instruction files, and **no
skills at all** — and C is correct only *because* `claude` usually installs,
which is an assumption about the filesystem that decision 5 refuses by name.

**A certain hole beats a narrow, idempotent-in-two-of-three-branches risk.**
Ruled A.

⚠ **The residual risk is real and is the reopen-trigger**, and it is still not
resolvable by *"try it and see"* locally: the question is what happens in *a
consumer's* repository on *their* Copilot build. What changed is not that the
unknown was measured — **it was bounded by construction, which is the cheaper
move and the one this project already relies on for the verbatim block.**

## Consequences

**Shipped under A:** `AGENT_FILES["copilot"]` gains
`.github/skills/fux-enrich/SKILL.md` and no template;
[ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md) decision 9a is amended
(its *"the two skill surfaces — Claude and Kiro"* was a count doing a rule's
job), decision 14 records the ruling, and decision 13 is marked superseded **in
effect, not in substance** — the cross-read is unchanged, it is simply no
longer how Copilot reaches this skill.

⚠ **`fux-decoder` and `fux-usage` did NOT get `.github/skills/` rows.** The
ruling named `fux-enrich`. That leaves a roster difference between two skills
of the same risk class — the *inverse* of the asymmetry this session opened by
finding — and it is held by
`test_the_two_rosters_differ_only_where_a_record_says_so` rather than by a
sentence, so closing it is a deliberate act and leaving it is a visible one.

## References

- GitHub Copilot agent skills, and the three project-skill directories —
  <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>
- The exclusion this reopens —
  [ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md) decision 9a.
- The cross-read finding —
  [ADR-AGENT-POLICY](../../docs/adr/0042_agent-policy.md) decision 13.
- The precedent for refusing to ship on an unmeasured premise —
  [`CLAUDE.md`](../../CLAUDE.md) §"A pre-registered threshold may never move".

## Reopen-trigger

See the verdict block: **an observed duplicate-name error**, not a double-load.
Checkable today by anyone with both directories populated. ⚠ The
`copilot`-without-`claude` half of the original trigger is **retired** — A is
what closes that hole, so it can no longer fire.
