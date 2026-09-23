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
| 🔴 **W-168** — RM3 (step 5) came back INCONCLUSIVE by the frozen table: no weight wins, and every weight loses 6–11 rank-1 hits. File it as FAIL, or keep it INCONCLUSIVE? Nothing in the engine changes either way. [verdict](regression/2026-09-23-rm3/VERDICT.md) | 2026-09-23 | 0d |
| ↳ **blocks:** nothing else in the queue — only closing step 5. | | |
| 🔴 **W-220** — the index X-ray. **Ruled:** it lives in `fux inspect`; data files get both bars. Still yours: build the serve/trace views on it? Probe titles only, or titles + headings? [detail](open/W-220-index-xray.md) | 2026-09-23 | 0d |
| ↳ **blocks:** nothing else in the queue — its four rungs and the findings' levers are tracked inside its own file. | | |

---

## Open items

### fux build

- 🟢 **W-215** · `agent` — golden data gen 2. **Prompt 10 ran 2026-09-23** (14 seeds, `set-3-u`). Next: rebuild the ladder, prompt 4, Opus, **in a fresh session**. [detail](open/W-215-generation-2-corpus.md)

- 🔴 **W-168** · `arpit` — the ranking ideas. **Step 5 (RM3): INCONCLUSIVE 2026-09-23**; the filing is his (inbox). [detail](open/W-168-search-improvements.md)

- 🔴 **W-220** · `arpit` — the index X-ray, per document and whole index. Home and data-file bars **ruled 2026-09-23**; not built. Waiting on two rulings. [detail](open/W-220-index-xray.md)


### testing


---
