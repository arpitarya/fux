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
| 🔴 **W-204** — **paste the key.** Phases A and B are filed (5 984 + 8 976 rows, no score), both frozen before any key existed; phase D is all that is left. [detail](open/W-204-golden-outputs-scoring-and-version-benchmark.md) | 2026-09-21 | 0d |
| ↳ **blocks:** W-168 | | |
| 🔴 **W-205** — part 2: ship family (a) on correctness, hold for a better corpus, or drop it. INCONCLUSIVE at **+4 with 0 regressions**. [detail](regression/2026-09-21-identifier-analyzer/VERDICT.md) | 2026-09-21 | 0d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-205** — should SR-RS d23 gain a clause? **Two** data-shaped thresholds were frozen today on premises nobody probed, and both were wrong. [detail](regression/2026-09-21-frontmatter-reachable/VERDICT.md) | 2026-09-21 | 0d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-204** — the L11 hook fires on PROSE that names the sealed path, 4th occurrence. Narrow it, forbid the spelling, or accept it. [detail](regression/2026-09-21-ladder-set-3-rebuild/ANALYSIS.md) | 2026-09-21 | 0d |
| ↳ **blocks:** W-168 | | |

---

## Open items

### fux build

- 🟢 **W-199** · `agent` — D1–D4 and the three doctor rows **BUILT 2026-09-20**; what is left is DoD 10, the `decoder=` half of the pipe ruling, added to this item mid-session. [detail](open/W-199-fetcher-routing.md)
- 🔴 **W-168** · `agent`, waiting on W-204 — steps 3–10 of the ranking ideas; step 2 moved to W-205. Ruled 2026-09-20: Codex adds `RF-118`-shaped ids to the seed in the prompt-7 pass. [detail](open/W-168-search-improvements.md)
- 🔴 **W-205** · `arpit` — **part 1 PASSED and shipped**; **part 2 INCONCLUSIVE and NOT shipped**. Three ways forward on part 2, and a candidate SR-RS rule after two unmeasured premises in one day. [detail](open/W-205-identifiers-reachable-and-whole.md)

### testing

- 🔴 **W-204** · `arpit` — **phases A and B are FILED** (5 984 + 8 976 rows, no score). **Next is his paste**: the key, then phase D scores A and B in one pass. [detail](open/W-204-golden-outputs-scoring-and-version-benchmark.md)

---
