---
type: Proposal
title: "Agent policy for `--hybrid` — the same guardrail archived-marking got, for a ranking flag that can also be misread"
description: A parked idea, not a build item. `--hybrid`'s output has the same misreadability shape ADR-AGENT-POLICY was built to fix for archived marks, but the four agent-policy renderings say nothing about it; this note names why, what adding it would look like, and the two conditions under which it graduates.
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# Agent policy for `--hybrid`

**Parked, not a build item.** Filed on Arpit's instruction to write the idea
down with explicit conditions, then set it aside.

## Context

[ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) ships one canonical
policy — a verbatim eight-rule block — rendered into Claude skills, Copilot
agents/instructions, and Kiro steering. Its whole premise: **"an engine whose
output is systematically misread is an engine that does not work, however
correct its index."** The concrete case it was built for is archived-content
marking: an agent seeing a ranked result has to know that `archived: true`
means something different depending on whether the question was about
history, current architecture, or a build task.

`--hybrid` has the same shape, and none of the four renderings mention it —
confirmed by grep across `src/fux/templates/agents/` and the installed
copies. Nothing wired that check; it was a direct read of the files.

**Where the two cases line up:**

- **Both are outputs an agent could take at face value and act on wrongly.**
  Archived marking: citing a retired design as current. Hybrid: trusting a
  fused ranking as if it were the default lexical answer — the risk this
  bullet names outlived the RRF lane it was written against. W-79
  (2026-08-26) deleted `src/fux/query/hybrid.py`, the module-level RRF
  fusion this bullet originally cited (`hybrid_ask`, off the live path since
  W-76 Phase 7); `--hybrid` today runs `query/dense.py`'s gated fusion, which
  multiplies a dense similarity into the BM25F score rather than producing a
  separate RRF scale. The misreadability risk this proposal argues for is
  narrower now — a boosted score, not an incomparable one — but a caller that
  does not know a boost was applied can still misattribute the ranking to
  lexical relevance alone.
- **Both are measured, not stylistic, defaults.** `--hybrid` is off on a
  measured net −6 across the graded corpus
  ([`docs/adr/0004_ask.md`](../../docs/adr/0004_ask.md) decision 9); an agent
  that flips it "to get better results" is overriding a decision made on
  evidence it has not seen.
- **Both fail silently.** The worked `--explain` example in
  [`docs/adr/0002_cli-surface.md`](../../docs/adr/0002_cli-surface.md) §"`fux
  ask --hybrid`" shows it padding one correct lexical hit with two unrelated
  documents — a wrong-looking-right answer, exactly the failure class
  ADR-AGENT-POLICY's own motivating case (the 5/5-archived probe,
  [W-44](../../archive/open/W-44-archived-content-signalling.md)) was measured
  evidence of.
- **Both have a specific reachability trap.** The semantic-lane compare doc
  ([`work/proposals/ideal/03-semantic-lane.compare.md`](ideal/03-semantic-lane.compare.md))
  names it precisely: a binary prefilter always has a nearest neighbour, so
  hybrid can manufacture a false hit exactly where the lexical path would
  correctly return "No confident matches." An agent that doesn't know this
  will not think to ask.

**Where they don't line up, and why this stays parked rather than built:**

- ADR-AGENT-POLICY's veto condition 6 is explicit: *"The policy tells an
  agent what the answer is, rather than how to read the fact... the moment a
  rendering starts encoding Fux's opinion about a document rather than about
  what [the field] means, the engine has smuggled the intent taxonomy back in
  through the policy layer."* Archived-marking policy is about reading a
  **field on every result** (`archived: true/false`). Hybrid guidance would be
  about reading a **flag's own measured status** — a different kind of fact,
  arguably outside what "one canonical policy" was scoped to carry. Whether it
  belongs in the *same* policy artifact, a *sibling* one, or nowhere until the
  default itself changes is a real fork (§Shape below), not a foregone
  conclusion.
- The evidence bar ADR-AGENT-POLICY set for itself was a **measured
  incident** — the 5/5-archived probe — not a hypothetical. Nothing analogous
  has happened yet for `--hybrid`; this note is reasoning from the shape of
  the risk, not from an observed failure.
- [`ranking-tuning.md`](ranking-tuning.md) already names `--hybrid`'s default
  as "the candidate that would trip [its own graduation trigger] first" — a
  ranking decision, separately parked. Building agent guidance around a
  default that might move soon risks writing a policy line that goes stale
  the same day it ships.

## §Shape — if this is picked up

Three ways to add it, named so the cost is visible without picking one:

| | what it looks like | cost |
|---|---|---|
| **A. Extend the existing block** | A second verbatim block (`fux:policy:hybrid:begin`) in `POLICY.md`, carried into all four renderings alongside the archived-marking block | Cheapest; reuses the exact-match conformance test in `tests/test_agent_policy_agreement.py`. Risks growing the two **ambient** renderings (Copilot instructions, Kiro steering) past ADR-AGENT-POLICY's own veto 5 (`wc -c`, ~2 KB ceiling) |
| **B. A separate policy scoped to ranking-path disclosure** | Its own record, covering `--fast`/`--scan`/`--hybrid` and `--explain`'s `[accelerator]`/`[scan]`/`[hybrid]` marker generally, forward-compatible with any future off-by-default flag | Right shape long-term, but a new record for one flag today is arguably over-built ahead of the evidence bar in §Graduation trigger |
| **C. Fold into the hybrid-default decision itself** | No standalone agent-policy work; whichever way `ranking-tuning.md`'s graduation trigger resolves the default, write the agent guidance in that same change | Avoids the stale-the-same-day risk above; costs nothing until that decision fires |

No verdict proposed here — this is Arpit's call, same as ADR-AGENT-POLICY's
own layering was.

## Graduation trigger

**Either of these fires it — neither has yet:**

1. **`--hybrid`'s measured status changes.** [ADR-ASK](../../docs/adr/0004_ask.md)'s
   own veto condition — a new run under `work/regression/` shows hybrid
   net-positive (or re-confirms net-negative with new numbers) on a graded
   corpus. At that point this note's cited evidence (net −6, the `--explain`
   padding example) is stale by construction, so writing the fresh agent
   guidance belongs in the *same* change as the measurement — not a
   follow-up. This is also `ranking-tuning.md`'s named trigger, so the two
   proposals are coupled: whichever fires, check the other.
2. **A real misread is observed** — an agent (Claude Code, Cowork, or any
   consumer) invoking `--hybrid` unprompted in a session against this repo
   and treating its ranking, or an RRF score, as directly comparable to the
   default lexical path without being told to compare the two. That is the
   same evidence bar ADR-AGENT-POLICY required of itself before it shipped
   anything — a measured incident, not a hypothetical.

Until one of these fires, the honest position is that `--hybrid` carries a
real misreadability risk with the same shape as the one ADR-AGENT-POLICY
solved, and nothing has yet made it worth building the fix.

## Reference

- [ADR-AGENT-POLICY](../../docs/adr/0035_agent-policy.md) — the precedent
  this proposal extends, including veto condition 6 (the constraint this note
  reasons against) and veto condition 5 (the ambient-rendering size ceiling
  option A would risk)
- [ADR-ASK](../../docs/adr/0004_ask.md) decision 9 and its veto condition —
  `--hybrid`'s measured off-by-default status
- [`docs/adr/0002_cli-surface.md`](../../docs/adr/0002_cli-surface.md)
  §"`fux ask --hybrid`" — the worked `--explain` example showing the padding
  failure
- `src/fux/query/dense.py` (deleted 2026-08-25) — the live fusion
  `--hybrid` runs today; a multiplicative boost on the BM25F score, not the
  RRF lane this proposal was originally written against (deleted by W-79,
  2026-08-26 — see [ADR-ASK](../../docs/adr/0004_ask.md) decision 9's
  amendment)
- [`work/proposals/ideal/03-semantic-lane.compare.md`](ideal/03-semantic-lane.compare.md) —
  the reachability-collapse and attractor-collision failure classes
- [`work/regression/2026-08-12-m2-accelerator/report.md`](../regression/2026-08-12-m2-accelerator/report.md) —
  the `known_failure` class-3 measurement and its unresolved DoD discrepancy
- [`ranking-tuning.md`](ranking-tuning.md) — the coupled proposal naming
  `--hybrid`'s default as the decision most likely to move first
