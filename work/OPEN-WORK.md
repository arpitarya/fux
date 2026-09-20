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
| 🔴 **W-136** — the detailed scoring pass over the benchmark is PAUSED by your 2026-09-18 ruling ("6E is enough for now"), so no per-question scores exist. Only you can restart it, and most of the queue sits behind that. [detail](open/W-136-golden-benchmark.md) | 2026-09-16 | 4d |
| ↳ **blocks:** W-87, W-176, W-190, W-191, W-195, and through W-191 also W-161 | | |
| 🔴 **W-175** — the test needs the questions reworded by Codex, blind, and only you can run that prompt. The harness is built and refuses to start without them; no agent may write them. [detail](open/W-175-correction-generalisation.md) | 2026-09-16 | 4d |
| ↳ **blocks:** W-175, and nothing else in the queue | | |
| 🔴 **W-168** — **measured 2026-09-18: code search already works ~90 % at every rung** (chopped codes still match). Room for a fix: 3–4 of 33, below the floor. His: drop step 2, or ask Codex for a seed with `PROJ-123`-style codes. [detail](open/W-168-search-improvements.md) | 2026-09-16 | 4d |
| ↳ **blocks:** W-168, and nothing else in the queue | | |
| 🔴 **W-201** — **a code that appears only in a file's front-matter (`doc_id:`) can't be searched at all** — that header block is never indexed. His: which header keys get indexed, and as title-strength or body-strength. [detail](open/W-201-frontmatter-scalars-not-indexed.md) | 2026-09-18 | 2d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🟢 **W-199** · `agent` — **agreed 2026-09-18, not built**: every URL source states up front how to download it and how to read what comes back, fixed once at `fux add`. **Breaking** by your ruling. [detail](open/W-199-fetcher-routing.md)
- 🟢 **W-200** · `agent` — **agreed 2026-09-18, not built**: keep a local log of how each document got indexed — which downloader and reader made it, from which bytes, and whether it worked. [detail](open/W-200-ingest-provenance.md)
- 🔴 **W-161** · `agent`, waiting on W-191 — built 2026-09-15 and shipped switched on, but never measured: no document in the test corpus links to another, so both arms of the feature have nothing to work on. [detail](open/W-161-graph-composed-ask.md)
- 🔴 **W-168** · `agent` — step 1 (link text) shipped. **Step 2 measured 2026-09-18: code search already works ~90 %, room for a fix is 3–4 of 33** — prompt 8 won't change that. Waits on his call. [detail](open/W-168-search-improvements.md)
- 🔴 **W-201** · `arpit` — **front-matter values are never indexed**, so a `doc_id:` that lives only there is unreachable. 3 of 33 seed codes. Which keys, which field — his. [detail](open/W-201-frontmatter-scalars-not-indexed.md)
- 🔴 **W-176** · `agent`, waiting on W-136 — steps 1–3 landed 2026-09-15; the rest need scored benchmark results that are paused, so the "say nothing when unsure" fix may end up built, unmeasured and left off. [detail](open/W-176-abstention-gates.md)
- 🔴 **W-191** · `agent` 🧨, waiting on W-136 — spec'd 2026-09-16: [prompt 7](golden/prompts/7-codex-link-bearing-seed.md) is written and the count of document-to-document links can now be gated on. Codex writes the documents. [detail](open/W-191-the-ladder-carries-no-links.md)

### testing


- 🔴 **W-190** · `agent`, waiting on W-136 — a question's difficulty is counted, not labelled by hand; the scorer was built 2026-09-15, but the answer key carries no difficulty yet, so no question is rated. [detail](open/W-190-question-difficulty.md)
- 🔴 **W-195** · `agent`, waiting on W-190 — we cannot yet say "fux does well on easy questions and badly on hard ones": the key has no difficulty field to split the results by, and it may not be guessed. [detail](open/W-195-difficulty-band-breakdown.md)
- 🔴 **W-136** · `arpit` — the benchmark ran 2026-09-16 and produced a rough score with no per-question detail. The detailed pass is paused by your ruling; W-87, W-176 and W-191 sit behind you restarting it. [detail](open/W-136-golden-benchmark.md)
- 🔴 **W-87** · `agent`, waiting on W-136 — what a good answer means: the refuse-to-answer half is measured (0 of 124 missed), and the other half is unblocked now Codex wrote set 1. Both need the scored run. [detail](open/W-87-what-good-means.md)
- 🔴 **W-175** · `agent` — run of 2026-09-18: correcting a question helped none of its 60 rewordings, and the original itself reached the top 3 only 4 times in 12. A weight sweep comes first. [detail](open/W-175-correction-generalisation.md)


---
