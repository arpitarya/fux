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
| 🔴 **W-168** — score step 8's five captured arms (authority prior): `just golden-score work/regression/2026-09-28-authority-prior`, in your shell. A session that did not capture then decides. [report](regression/2026-09-28-authority-prior/report.md) | 2026-09-30 | 0d |
| ↳ **blocks:** W-228 (waits on steps 7 and 8's verdicts), and W-225 through it | | |
| 🔴 **W-237** — score RM3's five captured arms: `just golden-score work/regression/2026-09-30-rm3-grounded`, in your shell. A session that did not capture then runs the frozen `decide.py`. [report](regression/2026-09-30-rm3-grounded/report.md) | 2026-09-30 | 0d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🔴 **W-168** · `arpit` — ranking ideas. 6, 7 stop; 9 shipped; 10 → W-236, 5 → W-237. **Step 8 (authority prior) built off at `0.0` (`fux.index.v6`) and captured; Arpit scores.** [detail](open/W-168-search-improvements.md)
- 🔴 **W-225** · `agent` — L12 migration: no values hidden in code. Stages 1–7 and the 16 odd sites landed. Left: stage 5f `inspect`, **waiting on W-228**, then stage 8. **Opus.** [detail](open/W-225-values-live-in-config.md)
- 🔴 **W-228** · `agent` — document families. The lens is built; its misfit flag's threshold is still a placeholder. Arpit ruled (not built): plant known misfits in the seed once steps 7 and 8 file verdicts — waiting on W-168. [detail](open/W-228-document-families.md)
- 🟡 **W-236** · `agent` — W-168 step 10 (U2). Part A done: [SR-SECTIONS](../records/0161_sections.md) proposed, [size PASS](regression/2026-09-30-section-size/VERDICT.md) (+98.4 % index). Part B waits on W-240. **Opus.** [detail](open/W-236-section-records.md)
- 🟢 **W-240** · `agent` — a scored set with a `step10_section` pool ≥ 6 (set-4-claude: 1): recipe R10 seed, `set-5-claude`, rung rebuild, then 🔴 Arpit scores. **Opus.** [detail](open/W-240-section-pool-set.md)
- 🔴 **W-237** · `arpit` — RM3 behind the `grounded` gate: built off at `0.0` in both readers, five arms captured on `set-4-claude` (pool 20). Arpit scores; a session that did not capture decides. [detail](open/W-237-rm3-grounded-gate.md)
- 🟢 **W-242** · `agent` — one derived plane, both readers: Node reads each shard once (T0), reads `.fux/runtime/` when fresh (T1), builds it byte-identically (T2). Ratified 2026-09-30, not built. **Opus.** [detail](open/W-242-shared-runtime.md)


### testing

- 🟡 **W-243** · `agent` — CI in ~2 min. Built, uncommitted: FULL skips a cell whose code went green, Windows hot spot batched; step 1 stopped until W-242. Waiting on a push to `main` to read its first run — not a queue item. **Opus.** [detail](open/W-243-ci-two-minutes.md)

---
