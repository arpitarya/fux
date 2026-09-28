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
| 🔴 **W-228** — when to plant family misfits in `seed/`? It rebuilds the ladder under W-168's pools. **After W-168 steps 6–10** (recommended), now, or never. [report](regression/2026-09-28-families-lens-ladder/report.md) | 2026-09-28 | 0d |
| ↳ **blocks:** nothing else in the queue; W-228's `misfit_floor` stays PROVISIONAL. | | |
| 🔴 **W-232** — **score** the three captured arms: `just golden-score work/regression/2026-09-28-anchor-mined-set3`, in your shell (no unlock). Then a session that did not capture runs the frozen `decide.py`. [report](regression/2026-09-28-anchor-mined-set3/report.md) | 2026-09-28 | 0d |
| ↳ **blocks:** W-232 only — W-168's two *combination unmeasured* warnings stay open until it is decided. | | |
| 🔴 **W-225** — rule L12's open calls: the `output.toml [api]` root, whether R8 reaches boolean dataclass fields, and 16 `for-arpit` sites. [compare doc](compare/l12-classify.compare.md) | 2026-09-28 | 0d |
| ↳ **blocks:** nothing else in the queue — W-225 cannot close without it. | | |
| 🔴 **W-168** — amend L11 d13 so `score.py` emits per-question facet-coverage counts at k = 5 for step 7 (MMR, recommended), or stop step 7? And judge step 8 (authority) at `hit@1` like steps 1, 4 and 9 (recommended)? [detail](open/W-168-search-improvements.md) | 2026-09-28 | 0d |
| ↳ **blocks:** W-168 steps 7 and 8's pre-registrations; W-228's recommended timing waits on those steps. | | |

---

## Open items

### fux build

- 🔴 **W-168** · `agent` — the ranking ideas. Step 9 shipped (`intent_weight = 0.1`); 6 and 10 stop. **Steps 7 and 8 wait on Arpit's ruling on their endpoints.** Meanwhile, step 8's compare doc can be written. [detail](open/W-168-search-improvements.md)
- 🔴 **W-225** · `agent` — L12 migration. Stages 1–7 landed (AST veto test + allow-list). Closing needs Arpit's ruling on the open calls; stage 5f `inspect` is still to do. [detail](open/W-225-values-live-in-config.md)
- 🔴 **W-228** · `agent` — document families. DoD 11's rung is filed: the seed has 0 misfits; title headings are out (rung-01000: 16 → 1). Waits on Arpit's timing for seed misfits. [detail](open/W-228-document-families.md)
- 🔴 **W-232** · `Arpit` — the shipped pair `anchor = 1.0` + `mined_weight = 0.5`. Set-4-claude STOPped (no question reaches the mined fold); re-captured on set-3-claude at step 4's gen-2 copy, precondition held. **Arpit scores**; then a non-capturing session runs `decide.py`. **Opus.** [detail](open/W-232-anchor-mined-combination.md)
- 🟢 **W-233** · `agent` — identifiers retained whole. Ruled F1–F5: inspect detects ID families → `.fux/identifiers.toml` (`[detected]` templates via a verb; `[user]` hand-authored, templates or guarded expert regex, wins) → analyzer reads the file only; whole unstemmed + parts; a serve "Identifiers" test tab. Fixture first. **Opus.** [detail](open/W-233-identifiers-retained-whole.md)


### testing


---
