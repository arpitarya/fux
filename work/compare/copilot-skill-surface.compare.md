---
type: Compare Doc
title: Copilot Skill Surface
description: Now that Copilot reads Agent Skills, does fux write .github/skills/ for it — or rely on the .claude/skills copy Copilot already reads?
status: proposed
timestamp: 2026-09-06T00:00:00Z
---

# Copilot's skill surface — write `.github/skills/`, or don't? — Comparison

> **Verdict: C — write nothing new, and record why** (proposed).
> **Status:** ⏳ awaiting Arpit · **Confidence:** medium — the deciding fact
> (whether two same-named skills collide) is **unmeasured**, and B is the
> option that becomes correct the moment it is.
> **Reopen when:** either (a) a repository is observed with
> `install = ["copilot"]` and no `claude`, so nothing writes the skills
> Copilot can read; or (b) duplicate-name behaviour across `.github/skills`
> and `.claude/skills` is measured — in **either** direction.

## Context

[ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) decision 9a shipped
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
   That is [ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) decision 13.

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

## The crux

**Nobody knows what two same-named project skills do in Copilot** — dedupe,
double-load, or an error. The docs name three directories and do not say.

A and B both ship on a guess about that. C does not, and that is its whole
case: it is the option whose correctness does not depend on the unknown.
**C's cost is a real hole** — `install = ["copilot"]` alone gets an agent file
and two ambient instruction files and **no skills** — and that hole is the
reopen-trigger, not a defect to wave away.

⚠ **Do not resolve this by "just try both and see".** The question is what
happens in *a consumer's* repository, on *their* Copilot version. A local
observation is one data point about one build.

## Consequences

Under C, `AGENT_FILES["copilot"]` is unchanged and
[ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) decision 13 is the
record of why. Under A or B it gains two rows and no template, and decision 9a
gains an amendment saying its premise changed.

## References

- GitHub Copilot agent skills, and the three project-skill directories —
  <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>
- The exclusion this reopens —
  [ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) decision 9a.
- The cross-read finding —
  [ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) decision 13.
- The precedent for refusing to ship on an unmeasured premise —
  [`CLAUDE.md`](../../CLAUDE.md) §"A pre-registered threshold may never move".

## Reopen-trigger

See the verdict block. Both halves are conditions checkable today: a
`copilot`-without-`claude` declaration in any repository fux is installed in,
or a measurement of duplicate-name behaviour.
