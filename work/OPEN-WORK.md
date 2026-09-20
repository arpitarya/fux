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
| 🔴 **W-168** — **measured 2026-09-18: code search already works ~90 % at every rung** (chopped codes still match). Room for a fix: 3–4 of 33, below the floor. His: drop step 2, or ask Codex for a seed with `PROJ-123`-style codes. [detail](open/W-168-search-improvements.md) | 2026-09-16 | 4d |
| ↳ **blocks:** W-168 · W-203 | | |
| 🔴 **W-201** — **a code that appears only in a file's front-matter (`doc_id:`) can't be searched at all** — that header block is never indexed. His: which header keys get indexed, and as title-strength or body-strength. [detail](open/W-201-frontmatter-scalars-not-indexed.md) | 2026-09-18 | 2d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-199** — **three calls, and the first changes what fux writes into every URL line from now on.** The shape is agreed; the defaults are not, and building on the wrong one makes every route dead on every existing line. [detail](open/W-199-fetcher-routing.md) | 2026-09-20 | 0d |
| ↳ **blocks:** W-199, and nothing else in the queue | | |

---

## Open items

### fux build

- 🔴 **W-199** · `arpit` — **three calls are yours before anything can be built**, and the first one decides what fux writes into every URL line from now on. The shape is agreed; the defaults are not. [detail](open/W-199-fetcher-routing.md)
- 🔴 **W-168** · `agent` — step 1 (link text) shipped. **Step 2 measured 2026-09-18: code search already works ~90 %, room for a fix is 3–4 of 33** — prompt 8 won't change that. Waits on his call. [detail](open/W-168-search-improvements.md)
- 🔴 **W-201** · `arpit` — **front-matter values are never indexed**, so a `doc_id:` that lives only there is unreachable. 3 of 33 seed codes. Which keys, which field — his. [detail](open/W-201-frontmatter-scalars-not-indexed.md)
- 🔴 **W-203** · `agent`, waiting on W-168 — the two lines that chop a code up: the tokenizer stops at a hyphen, and the stemmer eats acronyms. Four shipped fixes compared. [detail](open/W-203-identifier-analyzer-defects.md)

### testing

- 🟢 **W-204** · `agent` — one output document per rung at HEAD, then v1.0.0 · v2.0.1 · HEAD on the same rungs; Arpit opens the key once both are frozen, one pass writes the final score. Absorbs eight items. [detail](open/W-204-golden-outputs-scoring-and-version-benchmark.md)
- 🟢 **W-202** · `agent` — write down what the analyzer does to each of the 33 codes today, as a test. The "before" half of the before/after; blocks on nothing. [detail](open/W-202-identifier-analyzer-gate.md)

---
