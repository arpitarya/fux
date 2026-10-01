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
| 🔴 **W-168** — step 8 is INCONCLUSIVE by the table; every arm loses 2–10 rank-1 hits. Rule FAIL (drift)? (recommended) — and do the `M/` counts and code stay off at `0.0` or go? [verdict](regression/2026-09-28-authority-prior/VERDICT.md) | 2026-09-30 | 0d |
| ↳ **blocks:** W-228 (waits on steps 7 and 8's verdicts), and W-225 through it | | |
| 🔴 **W-240** — run [prompt 12](golden/prompts/12-claude-gen4-section-seed.md) in a fresh claude.ai chat (A1 bars any Claude Code session that has seen a score), commit blocks 1–3, and put block 4 in `golden-answers/` yourself | 2026-09-30 | 0d |
| ↳ **blocks:** W-236 Part B | | |
| 🔴 **W-237** — FAIL (no gain) by the table. Say go to remove the RM3 code again (step 5): the permission classifier refused the reverse-apply in-session. It is off at `0.0` meanwhile. [verdict](regression/2026-09-30-rm3-grounded/VERDICT.md) | 2026-09-30 | 0d |
| ↳ **blocks:** nothing else in the queue | | |

---

## Open items

### fux build

- 🔴 **W-168** · `arpit` — ranking ideas. 6, 7 stop; 9 shipped; 10 → W-236, 5 → W-237. **Step 8 (authority prior) decided INCONCLUSIVE by the table 2026-09-30; every arm broke the drift clause. Arpit rules.** [detail](open/W-168-search-improvements.md)
- 🔴 **W-225** · `agent` — L12 migration: no values hidden in code. Stages 1–7 and the 16 odd sites landed. Left: stage 5f `inspect`, **waiting on W-228**, then stage 8. **Opus.** [detail](open/W-225-values-live-in-config.md)
- 🔴 **W-228** · `agent` — document families. The lens is built; its misfit flag's threshold is still a placeholder. Arpit ruled (not built): plant known misfits in the seed once steps 7 and 8 file verdicts — waiting on W-168. [detail](open/W-228-document-families.md)
- 🔴 **W-236** · `agent` — W-168 step 10 (U2). Part A done: [SR-SECTIONS](../records/0161_sections.md) proposed, [size PASS](regression/2026-09-30-section-size/VERDICT.md) (+98.4 % index). Part B waits on W-240. **Opus.** [detail](open/W-236-section-records.md)
- 🔴 **W-240** · `arpit` — a scored set with a `step10_section` pool ≥ 6 (set-4-claude: 1). [Prompt 12](golden/prompts/12-claude-gen4-section-seed.md) written; Arpit runs it, then a rung rebuild (**Opus**), then 🔴 Arpit scores. [detail](open/W-240-section-pool-set.md)
- 🔴 **W-237** · `arpit` — RM3 behind the `grounded` gate: **FAIL (no gain)** 2026-09-30. The removal (step 5) waits on Arpit's go-ahead; it is off at `0.0` meanwhile. [detail](open/W-237-rm3-grounded-gate.md)
- 🟢 **W-242** · `agent` — one derived plane, both readers. **Tier 0 PASS** ([report](regression/2026-09-30-shared-runtime/report.md)). Next: Tier 1 (Node reads `.fux/runtime/`), then Tier 2. **Opus.** [detail](open/W-242-shared-runtime.md)


### testing

- 🟡 **W-243** · `agent` — CI in ~2 min. Built: FULL skips a cell whose code went green, Windows hot spot batched; step 1 stopped until W-242. Waiting on a push to `main` to read its first run — not a queue item. **Opus.** [detail](open/W-243-ci-two-minutes.md)

---
