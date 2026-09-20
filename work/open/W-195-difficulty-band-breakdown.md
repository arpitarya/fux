---
type: OpenItem
id: W-195
title: "W-195 — the rung-00100 counts have no per-difficulty-band breakdown"
description: "Prompt 6E step 7 asks every count to be broken down by the key's difficulty_band. key_version 1 carries no such field, so the breakdown was not produced for the 2026-09-16 rung-00100 run. The band must be computed from the key by Arpit or Codex, never by a Claude session."
status: open
lane: agent
timestamp: 2026-09-17T00:00:00Z
filed: 2026-09-17
ball: arpit
---

# W-195 — the missing difficulty-band breakdown

**Model: NONE for the blocking half.** Computing the band needs a key, so it is
Arpit's and Codex's hands ([SR-WORK-GOLDEN](../../records/0066_WORK-golden.md)
decision 12). What an agent does afterwards is re-file the breakdown beside the
run.

**Waiting on [W-190](W-190-question-difficulty.md).**

## What is missing

[Prompt 6E](../golden/prompts/6E-codex-score-ephemeral.md) step 7: *"Break every
count above down by the key's `difficulty_band`. The band comes from the key,
never from the hand-off rows."*

**It was not produced for [the 2026-09-16 `rung-00100` run](../regression/2026-09-16-golden-rung-00100/ANALYSIS.md),
and could not be.** As reported by the scoring session, **neither key carries
`difficulty`, `difficulty_static` or `difficulty_band`**; the fields present are
`id`, `question`, `answer`, `answerable`, `relevant`, `primary`, `evidence`,
`type`, `sealed`, `key_version`, `intent`, `exercises`.

⚠ **Recorded as reported, not verified** — checking a key's shape is Arpit's and
Codex's work, permanently
([SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 12).

**It matches [`work/golden/README.md`](../golden/README.md):** the band is
**computed** by [`tools/golden-difficulty/`](../../tools/golden-difficulty/), and
**nothing carries a label yet**. **So step 7 is unsatisfiable against
`key_version 1`** — a defect in the prompt, not in the run.

## 🔴 The three ways it must NOT be produced

Stated because each is cheap, available, and wrong:

1. **From `type`.** [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision
   13 and [W-190](W-190-question-difficulty.md) both forbid a re-encoding of
   `type`; difficulty earns its place only by varying **within** a type.
2. **From the hand-off rows.** They carry what fux did, not what the question is.
3. 🔴 **From fux's own results.** *Hard = fux got it wrong* makes every stratified
   claim a tautology.

## Definition of done

- **`difficulty_static` computed from each key** by `tools/golden-difficulty/`,
  **by Arpit or Codex and never by a Claude session** — that is W-190's remaining
  work, and it is why this item waits on it rather than on a run.
- **`distractors_at_rung` recomputed for `rung-00100`.**
- **The breakdown filed beside the run**, per set, never pooled.

⚠ **It will not be filed off the 2026-09-17 numbers.** Those came from a breached
key and are non-citable ([W-196](../../archive/open/W-196-l11-breach-2026-09-17.md)); a band
breakdown of a non-citable count is a non-citable count with more columns. **The
breakdown that counts comes from [prompt 6](../golden/prompts/6-codex-score.md).**

⚠ **W-190's bands are still provisional** — `d <= 1 / 2 / >= 3` was chosen before
any distribution over a real key existed, and moving them is legal **only before a
number is scored against them** ([SR-RS](../../records/0133_predictions.md)
decision 10b). **The 2026-09-17 scoring did not score against them**, because they
do not exist, so that window is still open.

## Also owed: fix the prompt

**6E step 7 and [prompt 6](../golden/prompts/6-codex-score.md) both ask for a
field the key does not have.** Either the prompts gain a *"skip if absent, and say
so"* clause, or the key gains the field first. **Whichever way, a prompt that asks
for something impossible gets silently half-obeyed** — this run is the evidence,
and the half-obedience was only visible because the scoring session said so.
