---
name: fux-savings
description: "measure the token + dollar cost win of Fux from your project's real file sizes — auditable ROI, not asserted ($0, no LLM)"
trigger: /fux savings
---

# /fux savings — measure the token + dollar cost win

Turns the plan's *illustrative* ROI table (fux-plan.md §12) into **measured**
numbers from this project's real file sizes. Pure byte-counting with a transparent
≈4-chars/token heuristic applied identically to both sides, priced in **dollars**
at a configurable `usd_per_mtok` (default = Claude Opus 4.8's $5/M input rate) —
deterministic, `$0`, no LLM. Use it to answer "is Fux actually saving me anything
here?" with evidence in both tokens and money.

## Inputs

```
/fux savings                       # aggregate report across all documented topics
/fux savings "<question>"          # cost one specific lookup (via recall)
/fux savings "<question>" --top 5  # widen the matched-rule set for that lookup
```

## Procedure

1. **Ensure the engine + a current INDEX.** Resolve `$FUX` exactly as in
   `skills/fux/SKILL.md` Step 1, then `"$FUX" build` so INDEX/graph are fresh.
2. **Run it.** `"$FUX" savings "<question>"` (or with no query for the aggregate).
3. **Read the three blocks the report prints:**
   - **Corpus** — active rule count, INDEX (Tier-1) tokens injected once per
     session, average rule (Tier-2) tokens opened only when relevant, and total
     governed-code tokens across the distinct `code_refs` files.
   - **Per lookup** — *without Fux* (read the governed file(s)) vs *with Fux*
     first-lookup (INDEX once + the rule) and later lookups (rule only, INDEX
     already in context), each with its savings multiplier, plus a "you save"
     line — every figure in tokens *and* dollars.
   - **Aggregate** — the same averaged over every documented topic (a rule with an
     existing governed file).
   - With `cost_tracking = true`, a **Cumulative** block follows: lifetime
     tokens/dollars saved and a per-day / week / month rate.
4. **Explain honestly.** The *ratio* is the signal, not the absolute tokens:
   "without Fux" assumes you read the whole governed file because you don't yet
   know the lines; "with Fux" assumes the rule points you straight to them. Both
   sides use the same heuristic. Missing `code_refs` are excluded from the
   baseline — call that out if the report notes any.

## How to act on the result

- **Low or `—` multiplier** usually means thin `code_refs` (rules not yet linked
  to the lines they govern) or a tiny governed surface. Suggest `fux refs <file>`
  / `fux coverage` to find undocumented hot files, then author rules for them so
  the next measurement reflects the real win.
- **High multiplier on a hot path** is the ROI case to surface to the user — that
  topic pays back its one-time authoring cost on every later session.

## Why this is a skill, not just a flag

Like `trace`, it is pure traversal/measurement (`$0`, no LLM) — but as a workflow
it adds the *interpretation*: fresh build first, read the three blocks, and turn
the numbers into a next action (link `code_refs`, cover a hot file). The number
alone is data; the skill makes it a decision.
