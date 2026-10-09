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
| 🔴 **W-257** — ruled 2026-10-09: the ~50-doc pilot. Arpit opens one fresh, blind Claude Code session in `fux-lab` with the item's prompt, then brings its report back. [the item](open/W-257-enriched-rung.md) | 2026-10-04 | 5d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-258** — **on hold by his word** (2026-10-04): say when to run the live URL-source checks. Recommended: §1 vanishing source + §2 real 429; park §3. [the item](open/W-258-live-network-captures.md) | 2026-10-04 | 5d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🟡 **W-236** · `agent` — W-168 step 10 (U2). Part A done: [SR-SECTIONS](../records/0161_sections.md) proposed, [size PASS](regression/2026-09-30-section-size/VERDICT.md) (+98.4 % index). Part B waits on W-240. **Opus.** [detail](open/W-236-section-records.md)
- 🟢 **W-240** · `agent` — ladder rebuilt as gen 4 ([run](regression/2026-10-05-ladder-gen4-rebuild/report.md)). Next: a session other than the rebuild's captures the `set-5-claude` baseline; 🔴 Arpit scores. **Opus.** [detail](open/W-240-section-pool-set.md)

### testing

- 🔴 **W-257** · `arpit` — an enriched rung to measure doc2query, authored blind. Ruled 2026-10-09: pilot ~50 docs first; Arpit launches the blind session with the item's prompt. **Opus.** [detail](open/W-257-enriched-rung.md)
- 🟢 **W-267** · `agent` — re-time the no-change ingest at rung-10000 on the fixed engine, against the same 5 s bar, so Arpit can rule B-002. **Sonnet.** [detail](open/W-267-ingest-split-remeasure.md)
- 🔴 **W-258** · `arpit` — one hands-on session on his machine: a journalled answer whose source then vanishes, a real 429 from a real host, and parallel CDP fetches in signed-in Chrome. Checklist and bars are written. [detail](open/W-258-live-network-captures.md)

### adr update


### research

- 🟢 **W-263** · `cowork` — research and propose the never-built `enriched` ingest mode: its overlap with `fux enrich`, and whether it may write index records itself. No code. **Opus.** [detail](open/W-263-enriched-mode-proposal.md)
- 🟢 **W-265** · `cowork` — deep research: how fux can better spot a question it cannot answer (the coverage floor tested no better than chance). No code. **Opus.** [detail](open/W-265-abstention-research.md)
- 🟢 **W-266** · `cowork` — the register file (`.fux/index/REGISTER`) needs a better shape: a new column makes the whole file unreadable; one column says the same word on every row. Compare doc, Arpit picks, build filed after. **Cowork.** [detail](open/W-266-register-structure.md)

---
