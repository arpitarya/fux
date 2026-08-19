# `work/open/` — one file per open work item

[`../OPEN-WORK.md`](../OPEN-WORK.md) is an **index**: one line per item, no
detail. The detail lives here, one file per `W-nn`, named
`W-nn-slug.md`.

**Contract**

1. An item's file is created in the same change that opens the item, and
   its one-line row is added to `OPEN-WORK.md` in that same change.
2. When an item closes, **delete its index row and move its file to
   [`archive/open/`](../../archive/open/)** — in the same change as the work.
   *(Arpit, 2026-08-19: archive the file rather than delete it. The row still
   goes, so the queue's length keeps meaning what it meant; what is kept is the
   argument that produced the call, which outlives the call.)* Closing is legal
   only once the outcome is recorded in
   [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md) and any evidence is filed
   under [`../regression/`](../regression/README.md). The durable record of a
   closed item is still its ADR plus the [`WORKLOG`](../WORKLOG.md) entry — the
   archived file is history, and **archive is not evidence**.
3. A file carries only what a builder needs to start: goal, definition of
   done, blockers, the spec it implements, hazards, and the model that
   should execute it. Anything longer belongs in an ADR or a
   compare/proposal doc, and is linked from here.
4. **This file is the spec as well as the state.** `PLAN.md` was archived on
   2026-08-18 and its milestone scope migrated into these files, so there is
   no second document to keep in step.

**Naming.** `W-nn` ids are never reused. Ids `W-00`…`W-14`, `W-20`,
`W-21`, `W-40`, `W-41` are retired (done); see WORKLOG for their record.
