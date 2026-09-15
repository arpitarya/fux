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
| 🔴 **W-144** — the `b` sweep FAILED its frozen rule and **the lever works below the range**: **(a)** the pre-registered fallback · **(b)** pre-register a LOWER range · **(c)** stop at `0.75`. [verdict](regression/2026-09-15-b-sweep/VERDICT.md) | 2026-09-15 | 0d |
| ↳ **blocks:** W-144, and nothing else in the queue | | |

⚠ **It blocks W-144 and nothing else.** Every other item below is
agent-closable; this row is a session output, not a stop.

---

## Open items

### fux build

- 🟣 **W-161** · `agent`, waiting on **2026-09-30** — **BUILT 2026-09-15**, both readers, 0 discordant; both tiers ship on and unmeasured. Only the two arms remain, and they need Codex's link-dependent questions. [detail](open/W-161-graph-composed-ask.md)
- 🟣 **W-168** · `agent`, waiting on **2026-09-30** — the ten search improvements. **Step 1 BUILT 2026-09-15**: both readers, `[bm25f] anchor` default 0, `_format` v3, 0 discordant. Steps 8 and 10 need Codex's questions. [detail](open/W-168-search-improvements.md)
- 🟣 **W-176** · `agent`, waiting on **2026-09-30** — **steps 1–3 landed 2026-09-15**: `weak` ⇒ `answerable: false`, the steering text, `failed`. The seven measured gates need Codex's key. [detail](open/W-176-abstention-gates.md)

### testing


- 🟢 **W-154** · `agent` — the instrument exists (W-183, `agreement` 0.4141) and the ladder loads again. ⚠ The `ask` arm's document-level screen runs FIRST. [detail](open/W-154-rerank-weight-cost.md)
- 🟣 **W-136** · `arpit`, waiting on **2026-09-30** — everything an agent can do is done; **phase 5 scoring is Codex's hands** and is all that is left. [detail](open/W-136-golden-benchmark.md)
- 🟣 **W-145** · `arpit`, waiting on **2026-09-30** — Codex regenerates the golden answer key; until then every golden number is `informed`. [detail](open/W-145-codex-regenerates-the-key.md)
- 🟣 **W-87** · `agent`, waiting on W-145 — P2's `unanswerable` gate is measured (0/124); recall needs phase 5 and **Part B needs an uncontaminated key**. [detail](open/W-87-what-good-means.md)
- 🟣 **W-175** · `agent`, waiting on **2026-09-30** — does a correction help OTHER phrasings? Ruled 2026-09-14: three arms (dogfood · fux's own tree · Codex), N=12 / M=5. Harness now; the numbers wait for Codex's blind paraphrases. [detail](open/W-175-correction-generalisation.md)
- 🔴 **W-144** · `arpit` — the `b` sweep is RUN and **no pre-registered value clears**; the lever reaches the endpoint below the frozen range and nothing regresses down to `b = 0`. Three options in the inbox. [detail](open/W-144-structure-aware-extraction.md)


---
