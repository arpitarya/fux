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

*Empty since 2026-09-20 — every decision put to Arpit this day was ruled; the next one that appears gets a row here.*

---

## Open items

### fux build

- 🟢 **W-199** · `agent` — **ruled 2026-09-20**: `fetch=` mandatory on every line and on `fux add`, no default fetcher, regex routes + `ROUTES` claims, and a committed ingest register beside the index. Breaking, by ruling. [detail](open/W-199-fetcher-routing.md)
- 🟡 **W-168** · `agent`, waiting on W-204 — steps 3–10 of the ranking ideas; step 2 moved to W-205. Ruled 2026-09-20: Codex adds `RF-118`-shaped ids to the seed in the prompt-7 pass. [detail](open/W-168-search-improvements.md)
- 🟢 **W-205** · `agent` — identifiers, reachable then whole. Ruled 2026-09-20: part 1 (front-matter ids → title, decoder claim + `formats.toml` binding) builds now; part 2 (the analyzer chops `KFS-2014`) measures on set 3. [detail](open/W-205-identifiers-reachable-and-whole.md)

### testing

- 🟢 **W-204** · `agent` — phase A filed; next: Claude authors **set 3** (`RF-118`-shaped ids + links), ladder rebuilt, A re-run; then v1.0.0 · v2.0.1 · HEAD; Arpit opens the key; one pass writes the final score. [detail](open/W-204-golden-outputs-scoring-and-version-benchmark.md)
- 🟢 **W-202** · `agent` — write down what the analyzer does to each of the 33 codes today, as a test. The "before" half of the before/after; blocks on nothing. [detail](open/W-202-identifier-analyzer-gate.md)

---
