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

*Empty since 2026-09-21 — five rows ruled in Cowork on 2026-09-21; the rulings are filed in W-204, W-205 and W-209.*

---

## Open items

### fux build

- 🟡 **W-168** · `agent`, waiting on W-204 — steps 3–10 of the ranking ideas; step 2 moved to W-205. Ruled 2026-09-20: `RF-118`-shaped ids come from set 3. [detail](open/W-168-search-improvements.md)
- 🟢 **W-205** · `agent` — part 1 shipped; **part 2 family (a) ruled 2026-09-21: SHIP on correctness**, `ANALYZER_VERSION` v3, no SR-RS d23 clause. Merge on both readers, amend records. [detail](open/W-205-identifiers-reachable-and-whole.md)

### testing

- 🟢 **W-204** · `agent` — phases A and B filed. **Ruled 2026-09-21: the key opens by `just golden-unlock`**, scored sets retire into open test data, `set-<gen>-<x|u>` naming. Build the switch, then phase D. [detail](open/W-204-golden-outputs-scoring-and-version-benchmark.md)
- 🟢 **W-209** · `agent` — the L11 hook stays as is; prose that spells a key path goes through Write/Edit, never a shell command; one test pins both behaviours. [detail](open/W-209-l11-hook-prose-convention.md)

---
