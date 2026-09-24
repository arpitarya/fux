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
| 🔴 **W-215** — type `just golden-score work/regression/2026-09-24-golden-gen2-rung-01000`: both gen-2 sets on the rebuilt ladder. It says whether gen 2 holds questions today's engine misses. [report](regression/2026-09-24-golden-gen2-rung-01000/report.md) | 2026-09-24 | 0d |
| ↳ **blocks:** W-168 — every step's pool needs this score. | | |
| 🔴 **W-168** — step 9: take D2 (a `[doctype]` glob table), I1 (a fixed cue lexicon) and S1 (step 3's intent stays out)? [compare doc](compare/intent-doctype-prior.compare.md) | 2026-09-24 | 0d |
| ↳ **blocks:** nothing else in the queue — only step 9. | | |

---

## Open items

### fux build

- 🔴 **W-215** · `arpit` — golden data gen 2. Ladder rebuilt, inputs measured (17 anchor terms, 9 `Term (ABBR)`), baseline captured 2026-09-24. Waits on Arpit's score. [detail](open/W-215-generation-2-corpus.md)

- 🔴 **W-168** · `arpit` — the ranking ideas. Step 9 is a compare doc (2026-09-24) awaiting three rulings, and its pool awaits the gen-2 score. [detail](open/W-168-search-improvements.md)


### testing


---
