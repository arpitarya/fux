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

*Empty since 2026-09-15 — W-144 and W-177 were the last rows and both were
ruled the day they were filed. Nothing in the queue waits on a decision of his.*

---

## Open items

### fux build

- 🟢 **W-177** · `agent` — **`fux update` is deleted; `fux ingest` absorbs its whole surface**, ruled 2026-09-15; reverses W-63 decision 3, no law edit. **Hook's offline invocation ruled: `--no-fetch`** (same flag `fux add` carries); L4's fence test names it. Buildable now. [detail](open/W-177-ingest-absorbs-update.md)
- 🟢 **W-178** · `agent` — `fetch=` becomes a **typed attribute validated by name shape**, not an enum of shipped fetchers; a consumer drops in `.fux/fetchers/<name>.py`. Ratified not built. [detail](open/W-178-consumer-planes-open-sets.md)
- 🟡 **W-161** · `agent`, waiting on W-191 — **BUILT 2026-09-15**; both tiers ship on and unmeasured. 🔴 **Both arms inert — 0 `ref` edges on the ladder**; they need linked documents, and Codex's questions are not that. [detail](open/W-161-graph-composed-ask.md)
- 🟢 **W-168** · `agent` — the ten search improvements. **Step 1 BUILT 2026-09-15**; both question sets released, so steps 2–7 and 9 are runnable now. Step 8 is inert until W-191 lands. [detail](open/W-168-search-improvements.md)
- 🟡 **W-176** · `agent`, waiting on W-136 — **steps 1–3 landed 2026-09-15**. Gates 4–9 need a SCORED run (prompt 6), not a key — no key exists (L11). ⚠ **Step 10 needs links, W-191.** [detail](open/W-176-abstention-gates.md)
- 🟢 **W-191** · `agent` 🧨 — **the ladder carries no links**: 0 `ref` edges on all eight rungs, none in `seed/`. A data defect under SR-RS d23, not a null. Unblocks W-161, W-168 step 8, W-176 step 10. [detail](open/W-191-the-ladder-carries-no-links.md)

### testing


- 🟢 **W-154** · `agent` 🧨 — Part B RAN and is **VOID**: 75 % of the `ask` regression is the query's own source document winning. Fix named (exclude the citing document); needs a NEW pre-registration. [detail](open/W-154-rerank-weight-cost.md)
- 🟡 **W-190** · `agent`, waiting on W-136 — difficulty is a **count of discriminations**, not a label; schema + scorer BUILT 2026-09-15. The questions exist; the first real number needs a **scored** rung (prompt 6). [detail](open/W-190-question-difficulty.md)
- 🟢 **W-136** · `agent` — **prompt 4 RAN 2026-09-15 and the ladder was STALE**: all eight rungs rebuilt from the current seed, `ext/` byte-identical, gate shipped. Next is **prompt 5** (run both sets), then scoring in a chat Arpit attends. [detail](open/W-136-golden-benchmark.md)
- 🟡 **W-87** · `agent`, waiting on W-136 — P2's `unanswerable` gate is measured (0/124). ✅ **Part B's blocker is gone** (set 1 is Codex-authored), so both halves now wait on phase 5. [detail](open/W-87-what-good-means.md)
- 🟢 **W-192** · `agent` — **write the Codex prompt for the blind paraphrases** and name the arm order; (iii) has no upstream. Unblocks W-175. [detail](open/W-192-codex-blind-paraphrases.md)
- 🟡 **W-175** · `agent`, waiting on W-192 — does a correction help OTHER phrasings? Three arms, N=12 / M=5. ⚠ **Codex's question sets are NOT the paraphrases**; the harness is agent work and does not wait. [detail](open/W-175-correction-generalisation.md)
- 🟢 **W-144** · `agent` — the `b` sweep FAILED its frozen range; **ruled (b) 2026-09-15**: pre-register a LOWER descending range as a separate run, **after** adding a control family with regression headroom (both existing controls are saturated). [detail](open/W-144-structure-aware-extraction.md)
- 🟢 **W-188** · `agent` — Node in CAP-1/2/3/4: **harness, parity file and report BUILT 2026-09-15**; the run is what is left, on Arpit's machine. [detail](open/W-188-node-column-every-capture.md)


---
