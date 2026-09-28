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
| 🔴 **W-168** — score step 9's arms: type `just golden-score work/regression/2026-09-28-intent-prior`. No unlock needed. [report](regression/2026-09-28-intent-prior/report.md) | 2026-09-28 | 0d |
| ↳ **blocks:** nothing else in the queue — W-168 step 9's verdict waits on it. | | |


---

## Open items

### fux build

- 🔴 **W-168** · `agent` — the ranking ideas. Step 9's five arms captured 2026-09-28 (rank 1 moved on 6–14 questions, all tagged). Waits on Arpit's score; then a non-capturing session decides. Steps 7 and 8 go; 6 and 10 stop. [detail](open/W-168-search-improvements.md)
- 🟢 **W-225** · `agent` — L12 migration, building. Stages 1–4 and 5a–5f landed (numerals → `constants.toml`; 14 keys → `fux.toml`), bar `inspect`, which waits for W-228. Next: stage 6, parameter defaults. [detail](open/W-225-values-live-in-config.md)
- 🟢 **W-228** · `agent` — document families: DoD 1–10 built 2026-09-28. Next: DoD 11, golden seed families + a rung before the misfit floor leaves PROVISIONAL; unblocked 2026-09-28 (W-230's probe denied). [detail](open/W-228-document-families.md)


### testing


---
