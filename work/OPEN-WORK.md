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

✅ **W-189 cleared 2026-09-15 and the golden lane is open.** He ran **prompt 2**
(Codex, set 1 — 125 questions) and **prompt 3** (Claude, set 2 — 124); both
`questions/set-N.jsonl` are in the tree — **staged, his to commit** — questions-only,
and both keys are his.
**W-145 closed as overtaken in the same change.** ⚠ **One row is left and it
blocks only itself** — nothing in the queue is waiting on Arpit for the benchmark
now; the next golden step is an agent's (W-136, prompt 4).

---

## Open items

### fux build

- 🟣 **W-161** · `agent`, waiting on **2026-09-30** — **BUILT 2026-09-15**; both tiers ship on and unmeasured. 🔴 **Both arms inert on the ladder — 0 `ref` edges**; they need linked documents, not questions. [detail](open/W-161-graph-composed-ask.md)
- 🟣 **W-168** · `agent`, waiting on **2026-09-30** — the ten search improvements. **Step 1 BUILT 2026-09-15.** 🔴 **Step 8 needs linked documents, not questions** — 0/124 flips at every weight, a data defect (23b). [detail](open/W-168-search-improvements.md)
- 🟣 **W-176** · `agent`, waiting on **2026-09-30** — **steps 1–3 landed 2026-09-15**. The seven gates need Codex's key; ⚠ **step 10 also needs links** — `unknown` is its only reachable outcome today. [detail](open/W-176-abstention-gates.md)

### testing


- 🟢 **W-154** · `agent` 🧨 — Part B RAN and is **VOID**: 75 % of the `ask` regression is the query's own source document winning. Fix named (exclude the citing document); needs a NEW pre-registration. [detail](open/W-154-rerank-weight-cost.md)
- 🟡 **W-190** · `agent`, waiting on W-136 — difficulty is a **count of discriminations**, not a label; schema + scorer BUILT 2026-09-15. The questions exist; the first real number needs a **scored** rung (prompt 6). [detail](open/W-190-question-difficulty.md)
- 🟢 **W-136** · `agent` — **both question sets landed 2026-09-15.** Next is **prompt 4** (verify the eight rungs), and 🔴 **it needs a session that has never read `questions/`**. Scoring stays a chat he attends. [detail](open/W-136-golden-benchmark.md)
- 🟡 **W-87** · `agent`, waiting on W-136 — P2's `unanswerable` gate is measured (0/124). ✅ **Part B's blocker is gone** (set 1 is Codex-authored), so both halves now wait on phase 5. [detail](open/W-87-what-good-means.md)
- 🟣 **W-175** · `agent`, waiting on **2026-09-30** — does a correction help OTHER phrasings? Ruled 2026-09-14: three arms (dogfood · fux's own tree · Codex), N=12 / M=5. Harness now; the numbers wait for Codex's blind paraphrases. [detail](open/W-175-correction-generalisation.md)
- 🔴 **W-144** · `arpit` — the `b` sweep is RUN and **no pre-registered value clears**; the lever reaches the endpoint below the frozen range and nothing regresses down to `b = 0`. Three options in the inbox. [detail](open/W-144-structure-aware-extraction.md)
- 🟢 **W-188** · `agent` — Node in CAP-1/2/3/4: **harness, parity file and report BUILT 2026-09-15**; the run is what is left, on Arpit's machine. [detail](open/W-188-node-column-every-capture.md)


---
