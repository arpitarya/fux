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

*Empty since 2026-09-28 — W-232 decided PASS. Next decision: Arpit scores W-168 steps 7 and 8, once each is pre-registered and captured.*

---

## Open items

### fux build

- 🟢 **W-168** · `agent` — the ranking ideas. Steps 6, 7 and 10 stop; 9 shipped. **Step 8 (authority prior) is ruled A3 · S2 · L1 and [pre-registered](regression/2026-09-28-authority-prior/PRE-REGISTRATION.md); the build is next. Opus.** [detail](open/W-168-search-improvements.md)
- 🟡 **W-225** · `agent` — L12 migration: no values hidden in code. Stages 1–7 and the 16 odd sites landed. Left: stage 5f `inspect`, **waiting on W-228**, then stage 8. **Opus.** [detail](open/W-225-values-live-in-config.md)
- 🟡 **W-228** · `agent` — document families. The lens is built; its misfit flag's threshold is still a placeholder. Arpit ruled (not built): plant known misfits in the seed once steps 7 and 8 file verdicts — waiting on W-168. [detail](open/W-228-document-families.md)


### testing


---
