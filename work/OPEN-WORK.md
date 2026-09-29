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

*Empty since 2026-09-28 — W-232 decided PASS. Next decision: Arpit scores W-168 steps 7 and 8, once each is pre-registered and captured.*

---

## Open items

### fux build

- 🟢 **W-168** · `agent` — ranking ideas. 6, 7 stop; 9 shipped; 10 → W-236, 5 → W-237. **Step 8 (authority prior), ruled A3 · S2 · L1 and [pre-registered](regression/2026-09-28-authority-prior/PRE-REGISTRATION.md); build next. Opus.** [detail](open/W-168-search-improvements.md)
- 🟡 **W-225** · `agent` — L12 migration: no values hidden in code. Stages 1–7 and the 16 odd sites landed. Left: stage 5f `inspect`, **waiting on W-228**, then stage 8. **Opus.** [detail](open/W-225-values-live-in-config.md)
- 🟡 **W-228** · `agent` — document families. The lens is built; its misfit flag's threshold is still a placeholder. Arpit ruled (not built): plant known misfits in the seed once steps 7 and 8 file verdicts — waiting on W-168. [detail](open/W-228-document-families.md)
- 🟢 **W-236** · `agent` — W-168 step 10 as ruled U2: section records in the index. First the design record and a size measurement; the build waits for a `step10_section` pool ≥ 6. **Opus.** [detail](open/W-236-section-records.md)
- 🟢 **W-237** · `agent` — RM3 back behind a `grounded`-only gate (R1 · G3, 2026-09-29). Pre-register on `set-4-claude` (pool 20), amend SR-EXPAND d17, build off at `0.0`; Arpit scores. **Opus.** [detail](open/W-237-rm3-grounded-gate.md)
- 🟢 **W-238** · `agent` — slow commands say nothing while they work. Show the progress bar on every command that walks the whole index, after measuring which ones are slow. **Sonnet.** [detail](open/W-238-progress-on-every-slow-verb.md)
- 🟢 **W-239** · `agent` — `fux ingest` got slower while reading documents. Three hot spots found (ID-family matching, decoders reloaded per file, a config file re-read per file); fix them without changing the index. **Opus.** [detail](open/W-239-extract-phase-speed.md)


### testing


---
