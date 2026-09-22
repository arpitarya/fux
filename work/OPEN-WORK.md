---
type: Queue
description: "The single live work queue, two lanes, plus the Blocked-on-Arpit inbox. The list only — its rules live in the record below."
governed_by: SR-WORK-OPEN-QUEUE
governed_by_path: records/0051_WORK-open-queue.md
---

# OPEN-WORK — what is still open

**This file is the LIST, plus the legend below** (Arpit, 2026-09-13).
Everything else — what the queue is, an item's lifecycle, the shape of a row,
ball precedence and the chain, ordering, how the inbox works, and what every
session owes — is stated once in
**[SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md)** and is not repeated
here. Read that record before changing anything below it.

**A ball on every row, always one:** 🔴 blocked on Arpit, directly or through another item · 🟣 gated on a named date, directly or through another item · 🟡 waiting on another item · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (Arpit only). Full legend: [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rules 20–34.

---

## Blocked on Arpit

| what he decides | filed | age |
|---|---|---|
| 🔴 **W-215** — authorise generation 2 of the golden data. Measured: one ranking step must fix **58–78 % of every remaining failure with zero regressions** to produce any verdict. Six items; item 1 alone unblocks five steps. [detail](open/W-215-generation-2-corpus.md) | 2026-09-22 | 0d |
| ↳ **blocks:** W-168, and through it steps 3–10 | | |
| ↳ **item 1 has landed and is waiting on his read:** `set-2-u` (125 questions) exists and has a baseline on `rung-01000` — [the run](regression/2026-09-22-golden-set-2u-rung-01000/report.md). It is unscored; `tools/golden-score/score.py` is his hand. | | |

---

## Open items

### fux build

- 🔴 **W-215** · `arpit` — generation 2 of the golden data, six items. **Item 1 is built and captured** — `set-2-u`, unscored; the other five and the score are his. [detail](open/W-215-generation-2-corpus.md)

- 🔴 **W-168** · `agent` — steps 3–10 of the ranking ideas, waiting on W-215. **Measured 2026-09-22: the blocker is the corpus, not engineering** — 7–23 winnable questions per set, `min_fix` 7–11; step 3 foreclosed by VERDICT-W143. [detail](open/W-168-search-improvements.md)


### testing


---
