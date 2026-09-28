---
type: Handoff
name: W-232
description: "Measure the SHIPPED combination anchor = 1.0 + mined_weight = 0.5, never measured together: W-168 step 1 passed alone at anchor 1.0, step 4 passed at anchor 0.0, and both shipped. Filed by Arpit 2026-09-28."
item: W-232
filed: 2026-09-28
ball: agent
---

# W-232 — measure `anchor = 1.0` + `mined_weight = 0.5` together

**Model: Opus** (a paired ranking measurement under SR-RS).

**Arpit, 2026-09-28:** *"4. measure it - a new work item"*, about W-168 step 4's
open warning.

## Why

- W-168 **step 1** (anchor) filed PASS on its own arms at `mined_weight` off.
- W-168 **step 4** (mined abbreviations) filed PASS on arms run at the rung's
  `anchor = 0.0`, and was ratified *knowing* the combination was unmeasured.
- Both now ship. Every consumer runs a combination no run has tested.
- The `set-4-claude` capture (2026-09-27) ran the combination, but as **one arm**:
  a baseline, not a comparison.

## Definition of done

1. **Pre-register first** (SR-RS d10b), before any row. Arms, all at one engine
   commit on one rung of the gen-3 ladder:
   - `A` anchor 1.0 + mined 0.5 (shipped)
   - `B` anchor 1.0 + mined 0.0
   - `C` anchor 0.0 + mined 0.5
   Endpoint `hit@1`, `primary@1` beside it. **The bar asks: does the pair lose
   anything either step won alone?** Keep-rule: A loses no rank-1 hit that B or C
   holds, net of the paired floor (SR-RS d19).
2. **Capture** on a re-ingested COPY of the rung, never the rung itself (the
   step-4 `_format` precedent). Set: `set-4-claude` (scored, `informed`).
3. **Arpit scores** (`just golden-score …`); a session that did not capture runs
   the frozen decider.
4. **Outcomes:**
   - PASS: file it, and close both steps' "combination unmeasured" warnings in
     W-168.
   - FAIL: back to Arpit. Which default gives way is his call.

## Status

- **2026-09-28 · bar frozen** (Claude Code, Opus). Keep-rule ruled by Arpit
  the same day: **significance**. `am-A` fails against a comparator only if
  `verdict.rule` finds the comparator better at the observed discordant count.
  A loss below the floor → INCONCLUSIVE, to Arpit.
  [Pre-registration](../regression/2026-09-28-anchor-mined/PRE-REGISTRATION.md) ·
  decider [`decide.py`](../regression/2026-09-28-anchor-mined/evidence/decide.py),
  frozen by hash.
