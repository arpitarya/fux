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
| 🔴 **W-258** — **on hold by his word** (2026-10-04): say when to run the live URL-source checks. Recommended: §1 vanishing source + §2 real 429; park §3. [the item](open/W-258-live-network-captures.md) | 2026-10-04 | 5d |
| ↳ **blocks:** nothing else in the queue | | |
| 🔴 **W-268** — ingest of 10 000 docs in under a second, in Rust (his direction; no consumer installs Rust). Pick the order and the no-wheel fallback — rec. Python incremental first; Python engine as fallback. [the item](open/W-268-ingest-under-one-second.md) | 2026-10-10 | 0d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🟢 **W-236** · `agent` — W-168 step 10 (U2). Bar frozen 2026-10-10 ([pre-reg](regression/2026-10-10-section-records/PRE-REGISTRATION.md)). Next: build on branch `w236-sections`, gates G0–G2, capture four arms. **Opus.** [detail](open/W-236-section-records.md)

### testing

- 🟢 **W-257** · `agent` — full rung ruled 2026-10-10; pre-registered ([bar](regression/2026-10-10-enriched-rung/PRE-REGISTRATION.md)): B-108–B-110 at `hit@1`, `informed`. Next: the author prompt → Arpit launches. **Opus.** [detail](open/W-257-enriched-rung.md)
- 🔴 **W-258** · `arpit` — one hands-on session on his machine: a journalled answer whose source then vanishes, a real 429 from a real host, and parallel CDP fetches in signed-in Chrome. Checklist and bars are written. [detail](open/W-258-live-network-captures.md)

### adr update


### research

- 🔴 **W-268** · `cowork` — ingest of 10 000 docs in under a second. Proposal + compare doc filed; Rust is his direction. Arpit picks the order and the fallback. **Cowork.** [detail](open/W-268-ingest-under-one-second.md)
- 🟢 **W-263** · `cowork` — research and propose the never-built `enriched` ingest mode: its overlap with `fux enrich`, and whether it may write index records itself. No code. **Opus.** [detail](open/W-263-enriched-mode-proposal.md)
- 🟢 **W-265** · `cowork` — deep research: how fux can better spot a question it cannot answer (the coverage floor tested no better than chance). No code. **Opus.** [detail](open/W-265-abstention-research.md)
- 🟢 **W-266** · `cowork` — the register file (`.fux/index/REGISTER`) needs a better shape: a new column makes the whole file unreadable; one column says the same word on every row. Compare doc, Arpit picks, build filed after. **Cowork.** [detail](open/W-266-register-structure.md)

---
