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
| 🔴 **W-227** — L11 breach: my recursive grep walked `work/golden/` (nothing printed); the traversal guard did not fire on a multi-line command. Does it cost anything, and may a session harden the guard? [detail](open/W-227-l11-breach-2026-09-27.md) | 2026-09-27 | 0d |
| ↳ **blocks:** nothing else in the queue — W-168's phase-5 run may go ahead in any other session. | | |

---

## Open items

### fux build

- 🔴 **W-227** · `arpit` — L11 breach, 2026-09-27: the recursive grep and the guard gap. [detail](open/W-227-l11-breach-2026-09-27.md)
- 🟢 **W-168** · `agent` — the ranking ideas. Step 4 shipped at `mined_weight = 0.5`; gen-3 ladder rebuilt 2026-09-27. Next: a phase-5 run of `set-4-claude` (`fux doctor --fix` on the rung first), by a session other than W-227's. [detail](open/W-168-search-improvements.md)
- 🟢 **W-225** · `agent` — L12 migration, building. Stages 1–3 landed (`constants.toml`; `tune.toml`, `output.toml`, `fux.toml` strict + `doctor --fix`). Next: stage 4, the other `.fux/*.toml`. [detail](open/W-225-values-live-in-config.md)


### testing


---
