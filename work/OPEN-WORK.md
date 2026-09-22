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
| 🔴 **W-215** — run prompt 10 or hold it? It writes the documents fux cannot find today (nicknames, short forms, look-alike IDs) plus a question set, and rebuilds the ladder. [detail](open/W-215-generation-2-corpus.md) | 2026-09-22 | 1d |
| ↳ **blocks:** nothing else in the queue — the ranking steps prompt 10 would feed are tracked inside the ranking programme's own file. | | |
| ↳ **item 1 scored 2026-09-23:** no room at the top 5, room at rank 1. **The rank question is ruled.** Still yours: run prompt 10, which adds the documents fux can't find today? | | |

---

## Open items

### fux build

- 🔴 **W-215** · `arpit` — generation 2 of the golden data, six items. **Item 1 scored 2026-09-23**; one call left — run prompt 10? [detail](open/W-215-generation-2-corpus.md)

- 🟢 **W-218** · `build` — the scorer can't score a generation-2 set by name (`--set 2-u` is refused, and `just golden-score` misses the flat hand-off). A workaround exists; it mislabels the output. [detail](open/W-218-scorer-takes-generation-set-names.md)

- 🟢 **W-168** · `agent` — the ranking ideas. **Step 5 (RM3) pre-registered 2026-09-23** at `hit@1`: 39 winnable questions, enough for a verdict. **Next: build it (Opus)**; step 9 can be pre-registered alongside. [detail](open/W-168-search-improvements.md)

- 🟢 **W-219** · `build` — the headroom tool's `min_fix` is the bar if every miss flips, not the fewest wins that clear (that is 6), and three documents read it the second way. No verdict changes. [detail](open/W-219-min-fix-mislabel.md)


### testing


---
