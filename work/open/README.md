---
type: Index
description: "Index of the open work items, one detail file each."
---

# `work/open/` — one file per open work item

[`../OPEN-WORK.md`](../OPEN-WORK.md) is an **index**: one line per item, no
detail. The detail lives here, one file per `W-nn`, named
`W-nn-slug.md`.

**Contract**

1. An item's file is created in the same change that opens the item, and
   its one-line row is added to `OPEN-WORK.md` in that same change.
   **The row is one or two lines, always; every other word about the item lives
   in this file** (Arpit, 2026-09-11 — OPEN-WORK rule 10, gated by
   `tests/test_open_work_rows_are_short.py`). **The row opens with its ball** —
   🔴 blocked on Arpit (directly or through another item) · 🟡 waiting · 🟢 no
   blockers — then optional 🧨 broken or worsening and 🔺, which only Arpit adds
   (OPEN-WORK rule 6).
2. **When an item closes its row is deleted and its file MOVES to
   [`archive/open/`](../../archive/open/), in the same change — it is never
   deleted.** The rules are
   [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rules 8–12 and
   **54–58**, and they are not restated here.

3. A file carries only what a builder needs to start: goal, definition of
   done, blockers, the spec it implements, hazards, and the model that
   should execute it. Anything longer belongs in an SR or a
   compare/proposal doc, and is linked from here.
4. **This file is the spec as well as the state.** `PLAN.md` was archived on
   2026-08-18 and its milestone scope migrated into these files, so there is
   no second document to keep in step.

**Naming.** `W-nn` ids are never reused. Ids `W-00`…`W-14`, `W-20`,
`W-21`, `W-40`, `W-41` are retired (done); see WORKLOG for their record.
