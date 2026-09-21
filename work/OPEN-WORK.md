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

*Empty since 2026-09-20 — every decision put to Arpit has been ruled; the next one that appears gets a row here.*

---

## Open items

### fux build

- 🟢 **W-199** · `agent` — D1–D4 and the three doctor rows **BUILT 2026-09-20**; what is left is DoD 10, the `decoder=` half of the pipe ruling, added to this item mid-session. [detail](open/W-199-fetcher-routing.md)
- 🟡 **W-168** · `agent`, waiting on W-204 — steps 3–10 of the ranking ideas; step 2 moved to W-205. Ruled 2026-09-20: Codex adds `RF-118`-shaped ids to the seed in the prompt-7 pass. [detail](open/W-168-search-improvements.md)
- 🟢 **W-205** · `agent` — part 2 **built on both readers** (33 of 33 identifiers whole, from 0) and pre-registered; run the arms on the set-3 ladder. Part 1 (front-matter ids → title) **still not started**. [detail](open/W-205-identifiers-reachable-and-whole.md)

### testing

- 🟢 **W-204** · `agent` — set 3 landed, ladder rebuilt (61 `ref` edges), **phase A re-run filed: 5 984 calls, three sets, no score**. Next: phase B, then Arpit pastes the key and one pass scores. [detail](open/W-204-golden-outputs-scoring-and-version-benchmark.md)

---
