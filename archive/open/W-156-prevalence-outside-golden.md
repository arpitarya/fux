---
type: OpenItem
id: W-156
title: "W-156 — may a prevalence capture run outside golden data?"
description: "SR-WORK-ENVIRONMENTS puts every measurement on golden data only. Golden is one constructed corpus. So never ship a ranking change off a single synthetic corpus can never be satisfied — the two rules are jointly unsatisfiable for any ranking change. Arpit rules which gives."
status: open
lane: arpit
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-156 — the two rules that cannot both hold

**Model: Opus.** It is a conflict between two of Arpit's own rulings, and the
resolution changes what evidence any future ranking change is allowed to have.

## The conflict, in two sentences

- **[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md):**
  *"`fux-lab` runs every measurement and evaluation, on the **golden test data
  only**."*
- **`CLAUDE.md` §Conformance runs:** *"Never ship a ranking/behaviour change off
  a single synthetic corpus."*

**`work/golden/` is one constructed corpus.** So every measurement a ranking
change is allowed to have comes from a single synthetic corpus, and no ranking
change can ever clear the second rule. **They are jointly unsatisfiable**, and
[W-144](W-144-structure-aware-extraction.md) is where it first bites: its
evidence is strong, its controls hold, and it cannot ship.

⚠ **This is not a loophole to route around.** It is two correct rules meeting,
and the fix is a ruling, not a reading that suits today's item.

## The three ways out

**(i) A corpus-statistics capture is a SURFACE CAPTURE, not an evaluation.**
Counting table tokens per document grades nothing, scores nothing and ranks
nothing. The conformance rule already exempts a surface capture from
blind/informed classification, **so the category exists** — this reading only
says where the boundary of *"measurement and evaluation"* falls.
⚠ **The risk:** *surface capture* becomes the label anything wears to leave the
lab. It needs a definition in the record, not a precedent in a work item.

**(ii) Amend SR-WORK-ENVIRONMENTS** to permit prevalence captures outside golden
data explicitly, with their own rule — no relevance judgement, no arms, no
verdict, statistics only.
⚠ **The cost:** it is an amendment to a WORK record, and the environments rule
was written because the three siblings had drifted into doing each other's jobs.

**(iii) Read the single-corpus rule as *"never without a stated
reopen-trigger"***, which [the compare doc](../compare/table-tokens-in-flen.compare.md)
already satisfies.
⚠ **The cost:** it weakens the rule that has prevented at least one bad ranking
change, and it does it in the change that benefits from the weakening — which is
the moving-threshold failure in its usual costume.

## What each unblocks

- **(i) or (ii)** → the prevalence capture runs today: table share per document
  over fux's own `records/` + `work/` + `docs/` tree, a human-written corpus
  outside `work/golden/` **and** outside `tools/quality-controls/` — which is
  exactly what the compare doc's reopen-trigger already names as the condition
  that would reopen it.
- **(iii)** → W-144 can be accepted on the evidence it already has.
- **None of them** → W-144 cannot ship, and neither can any future ranking
  change, and that should be written down rather than discovered again.

## Out of scope

- Running the capture. **It is blocked on this ruling, deliberately.**
- Deciding W-144. This unblocks the evidence, it does not make the call.
