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

*Empty since 2026-09-28 — W-227, W-168's score and W-230 all ruled or taken. Next decision: none filed.*

---

## Open items

### fux build

- 🟢 **W-168** · `agent` — the ranking ideas. Key pools on set-4-claude (L11 d13a): 9 → 14, 7 → 8, 8 → 8 go; 6 → 3, 10 → 1 stop. Next: step 9 pre-registers (D2 · I1 · M1 · S1). [detail](open/W-168-search-improvements.md)
- 🟢 **W-225** · `agent` — L12 migration, building. Stages 1–4 landed; stage 5a–5b too (analyzer, hashes, parsers, decoders → `constants.toml`). Next: 5c–5f (wire/store, protocols/CLI, leftover tunables, doctor/inspect). [detail](open/W-225-values-live-in-config.md)
- 🟢 **W-228** · `agent` — document families: DoD 1–10 built 2026-09-28. Next: DoD 11, golden seed families + a rung before the misfit floor leaves PROVISIONAL; unblocked 2026-09-28 (W-230's probe denied). [detail](open/W-228-document-families.md)


### testing


---
