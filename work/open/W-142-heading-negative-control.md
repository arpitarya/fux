---
type: OpenItem
id: W-142
title: "W-142 — the heading negative control is saturated and must be rebuilt"
description: "C4 returned its predicted null at 100% in both arms with zero headroom, so it never discharged its job; rebuild it with headroom by construction inside the golden ladder (W-136 phase 2)."
status: open
lane: agent
timestamp: 2026-08-28T00:00:00Z
---

# W-142 — rebuild the saturated `heading` negative control

**Model: Opus** — a control with headroom by construction is a design call no test can catch.

- **Filed 2026-08-28** as an OPEN-WORK row with no file and no id; given both on 2026-09-11.
- **Blocked on:** [W-136](W-136-golden-benchmark.md) — heading-matched `sibling` documents land in its phase 2.

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- **The `heading` negative control is saturated and must be rebuilt.** `agent`, blocked on W-136 ·
  *(record: [ADR-RS](../../docs/adr/0133_predictions.md))* ·
  [C4](../regression/2026-08-28-benchmark-contested/VERDICT-C4.md) returned its
  predicted null at **100 % in both arms with zero headroom**, so it returned
  the right answer for the wrong reason and **did not discharge its job**. Until
  it does, C1 and C3 rest on generator assertions rather than a live control.
  The fix is a control with headroom by construction — e.g. distractors that are
  *also* heading-matched. **Under [L9](../../docs/adr/0011_LAW-9-environments.md) it is rebuilt inside the golden ladder**
  (heading-matched `sibling` documents in W-136 phase 2), not on a generated suite —
  agent work, blocked on W-136. `filed: 2026-08-28`

## 2026-09-12 — the distractors exist; the headroom proof does not

The ladder's `ext/sibling/` documents are heading-matched distractors by
construction: they reuse the seed documents' headings and document types with a
different company and every number changed — 32 at `rung-00100`, 392 at
`rung-01000`. The coverage row in [`work/golden/README.md`](../golden/README.md)
now says so instead of *(filled in phase 2)*.

⚠ **That is the corpus, not the control.** ADR-RS decision 22c still wants a
feature-off/on arm or a generator `--selftest` before the headroom may be called
**proven**, and the 2026-09-12 run declares its own headroom **unproven** for
exactly that reason. ⚠ **`rung-seed` saturates** — every top-1 is trivially a
seed path — so a control built there is the 2026-08-28 failure again.
