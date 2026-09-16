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

*Empty since 2026-09-16 — W-144 and W-193 both ruled; the next gate is W-136 phase 5, prompt 5 then scoring in a chat Arpit attends.*

---

## Open items

### fux build

- 🟢 **W-193** · `agent` — RULED 2026-09-16: `2` stays argparse's usage code; SR-CLI decision 5 is amended to say so and the dead strict-mode reservation retired. [detail](open/W-193-argparse-exit-two.md)
- 🟡 **W-161** · `agent`, waiting on W-191 — **BUILT 2026-09-15**; both tiers ship on and unmeasured. 🔴 **Both arms inert — 0 `ref` edges on the ladder**; they need linked documents, and Codex's questions are not that. [detail](open/W-161-graph-composed-ask.md)
- 🟢 **W-168** · `agent` — the ten search improvements. **Step 1 BUILT 2026-09-15**; both question sets released, so steps 2–7 and 9 are runnable now. Step 8 is inert until W-191 lands. [detail](open/W-168-search-improvements.md)
- 🟡 **W-176** · `agent`, waiting on W-136 — **steps 1–3 landed 2026-09-15**. Gates 4–9 need a SCORED run (prompt 6), not a key — no key exists (L11). ⚠ **Step 10 needs links, W-191.** [detail](open/W-176-abstention-gates.md)
- 🟡 **W-191** · `agent` 🧨, waiting on W-136 — **specified 2026-09-16**: [prompt 7](golden/prompts/7-codex-link-bearing-seed.md) written, `ref` census generated and gateable. The documents are **Codex's**. [detail](open/W-191-the-ladder-carries-no-links.md)

### testing


- 🟡 **W-190** · `agent`, waiting on W-136 — difficulty is a **count of discriminations**, not a label; schema + scorer BUILT 2026-09-15. The questions exist; the first real number needs a **scored** rung (prompt 6). [detail](open/W-190-question-difficulty.md)
- 🟢 **W-136** · `agent` — **prompt 4 RAN 2026-09-15 and the ladder was STALE**: all eight rungs rebuilt from the current seed, `ext/` byte-identical, gate shipped. Next is **prompt 5** (run both sets), then scoring in a chat Arpit attends. [detail](open/W-136-golden-benchmark.md)
- 🟡 **W-87** · `agent`, waiting on W-136 — P2's `unanswerable` gate is measured (0/124). ✅ **Part B's blocker is gone** (set 1 is Codex-authored), so both halves now wait on phase 5. [detail](open/W-87-what-good-means.md)
- 🟢 **W-175** · `agent` — does a correction help OTHER phrasings? **Pre-registration frozen and the Codex prompt written 2026-09-15** (W-192). The harness is what is left; every number waits on paraphrases only Codex may write. [detail](open/W-175-correction-generalisation.md)
- 🟢 **W-144** · `agent` — RULED 2026-09-16: `dump` is a CONTROL, not a benefit family; range and first-that-clears stand. Re-freeze the pre-registration, then run. [detail](open/W-144-structure-aware-extraction.md)


---
