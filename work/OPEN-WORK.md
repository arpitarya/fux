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

*Empty since 2026-09-23 — W-168's RM3 filed FAIL and W-220 fully ruled the same day.*

---

## Open items

### fux build

- 🟢 **W-215** · `agent` — golden data gen 2. **Prompt 10 ran 2026-09-23** (14 seeds, `set-3-u`). Next: rebuild the ladder, prompt 4, Opus, **in a fresh session**. [detail](open/W-215-generation-2-corpus.md)

- 🟢 **W-168** · `agent` — the ranking ideas. **Step 5 (RM3) filed FAIL 2026-09-23** — it made rank 1 worse at every setting. Next: step 9, judged on whether the right document comes first. [detail](open/W-168-search-improvements.md)

- 🟢 **W-220** · `build` — the index X-ray. **Fully ruled 2026-09-23:** `fux serve` alone — tabs for Ask, Documents and Index, each report built when you open it. Not built. [detail](open/W-220-index-xray.md)


### testing


---
