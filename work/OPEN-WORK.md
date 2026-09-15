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

*Empty since 2026-09-15* — W-168 step 1 was the last row and he ruled it (c) the
day it was filed. Nothing in the queue waits on a decision of his.

---

## Open items

### fux build

- 🟣 **W-161** · `agent`, waiting on **2026-09-30** — **BUILT 2026-09-15**, both readers, 0 discordant; both tiers ship on and unmeasured. Only the two arms remain, and they need Codex's link-dependent questions. [detail](open/W-161-graph-composed-ask.md)
- 🟣 **W-168** · `agent`, waiting on **2026-09-30** — the ten search improvements. **Step 1 BUILT 2026-09-15**: both readers, `[bm25f] anchor` default 0, `_format` v3, 0 discordant. Steps 8 and 10 need Codex's questions. [detail](open/W-168-search-improvements.md)
- 🟣 **W-176** · `agent`, waiting on **2026-09-30** — **steps 1–3 landed 2026-09-15**: `weak` ⇒ `answerable: false`, the steering text, `failed`. The seven measured gates need Codex's key. [detail](open/W-176-abstention-gates.md)
- 🟡 **W-148** · `agent`, waiting on W-179 — **rows 1–3 done 2026-09-15**: CI's corpus arm removed, §4 local, SR-WORK-BENCHMARK 12–13. N4 unmeasured; row 4 out of scope. [detail](open/W-148-what-the-two-readers-still-owe.md)
- 🟢 **W-140** · `agent` — row 21 answered: the stranding is **unreproduced** in 104 deliberate trials and the race that did fire is fixed (W-185). What is left is whether to close it or put it to Arpit. [detail](open/W-140-guide-authoring-defects.md)
- 🟢 **W-179** · `agent` — run the **Node latency column** in `fux-benchmark` (SR-WORK-BENCHMARK d12); split out W-161's in-memory graph rebuild or the number blames the reader. Unblocks W-148. [detail](open/W-179-node-latency-column.md)

### testing


- 🟢 **W-186** · `agent` 🧨 — **every golden rung is unreadable by HEAD**: `fux.index.v2` plus two retired config keys, on all eight. Unblocks W-180 · W-154 · W-175. [detail](open/W-186-golden-ladder-unreadable.md)
- 🟡 **W-180** · `agent`, waiting on W-186 — run the **frozen `b`-sweep** on the golden ladder in `fux-lab`; the threshold may not move, a null closes W-144. Unblocks W-144. [detail](open/W-180-b-sweep-run.md)
- 🟡 **W-154** · `agent`, waiting on W-186 — the instrument exists (W-183, `agreement` 0.4141); the ladder it runs on does not load. ⚠ The `ask` arm's document-level screen runs FIRST. [detail](open/W-154-rerank-weight-cost.md)
- 🟣 **W-136** · `arpit`, waiting on **2026-09-30** — everything an agent can do is done; **phase 5 scoring is Codex's hands** and is all that is left. [detail](open/W-136-golden-benchmark.md)
- 🟣 **W-145** · `arpit`, waiting on **2026-09-30** — Codex regenerates the golden answer key; until then every golden number is `informed`. [detail](open/W-145-codex-regenerates-the-key.md)
- 🟣 **W-87** · `agent`, waiting on W-145 — P2's `unanswerable` gate is measured (0/124); recall needs phase 5 and **Part B needs an uncontaminated key**. [detail](open/W-87-what-good-means.md)
- 🟣 **W-175** · `agent`, waiting on **2026-09-30** — does a correction help OTHER phrasings? Ruled 2026-09-14: three arms (dogfood · fux's own tree · Codex), N=12 / M=5. Harness now; the numbers wait for Codex's blind paraphrases. [detail](open/W-175-correction-generalisation.md)
- 🟡 **W-144** · `agent`, waiting on W-180 — **step 1 done 2026-09-15**: the sweep is [pre-registered](regression/2026-09-15-b-sweep/PRE-REGISTRATION.md) and frozen. Steps 2–4 are the run. [detail](open/W-144-structure-aware-extraction.md)


---
