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
| 🔴 **W-228** — run [prompt 13](golden/prompts/13-claude-gen4-planted-misfits.md) in a fresh claude.ai chat (6 short docs, 3 planted misfits) and commit its three blocks. No key this time | 2026-10-03 | 0d |
| ↳ **blocks:** W-240, W-236, W-225 | | |
| 🔴 **W-244** — L11 event: `fux ingest` listed the locked key directory's file names (contained, never committed). Rule the cost; may ingest prune `!`-excluded dirs? [detail](open/W-244-l11-ingest-walk-2026-10-03.md) | 2026-10-03 | 0d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🔴 **W-225** · `agent` — L12 migration: no values hidden in code. Stages 1–7 and the 16 odd sites landed. Left: stage 5f `inspect`, **waiting on W-228**, then stage 8. **Opus.** [detail](open/W-225-values-live-in-config.md)
- 🔴 **W-228** · `arpit` — document families. The lens is built, but its misfit threshold is a placeholder: no known misfits exist yet. Arpit runs prompt 13 to plant 3, riding in gen 4 with W-240. [detail](open/W-228-document-families.md)
- 🔴 **W-236** · `agent` — W-168 step 10 (U2). Part A done: [SR-SECTIONS](../records/0161_sections.md) proposed, [size PASS](regression/2026-09-30-section-size/VERDICT.md) (+98.4 % index). Part B waits on W-240. **Opus.** [detail](open/W-236-section-records.md)
- 🔴 **W-240** · `agent` — a question set that can test section scoring. Prompt 12's docs and 90 questions are in (ruled: accept). Ladder rebuild waits on W-228, then 🔴 Arpit scores. **Opus.** [detail](open/W-240-section-pool-set.md)
- 🟢 **W-242** · `agent` — one derived plane, both readers. **Tier 0 PASS** ([report](regression/2026-09-30-shared-runtime/report.md)). Next: Tier 1 (Node reads `.fux/runtime/`), then Tier 2. **Opus.** [detail](open/W-242-shared-runtime.md)
- 🔴 **W-244** · `arpit` — L11 event 2026-10-03: ingest's `rglob` enumerates `work/golden/` and names its files in `.fux/.fuxignore`. Contained; Arpit rules cost and fix. [detail](open/W-244-l11-ingest-walk-2026-10-03.md)

### testing

- 🟡 **W-243** · `agent` — CI in ~2 min. Built: FULL skips a cell whose code went green, Windows hot spot batched; step 1 stopped until W-242. Waiting on a push to `main` to read its first run — not a queue item. **Opus.** [detail](open/W-243-ci-two-minutes.md)

---
