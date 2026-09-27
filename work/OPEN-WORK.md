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

*Empty since 2026-09-27 — step 4 ratified PASS at `0.5`. Next decision: scoring `set-4-claude` after the rung rebuild (W-168).*

---

## Open items

### fux build

- 🟢 **W-168** · `agent` — the ranking ideas. **Step 4 (abbreviations) SHIPPED 2026-09-27** at `mined_weight = 0.5` (`8d401423`). Next: a fresh prompt-4 session rebuilds the eight rungs for generation 3. [detail](open/W-168-search-improvements.md)
- 🟢 **W-225** · `agent` — L12 migration, building. Stage 1 landed (`constants.toml`, fixed names); R7–R10 ruled strict. Next: `tune.toml` without fallback. [detail](open/W-225-values-live-in-config.md)


### testing


---
