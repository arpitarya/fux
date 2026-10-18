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
4. **A `research` item's file says `**Model:** Cowork`** and its row's lane is
   `cowork`: it runs in Cowork, never in Claude Code
   ([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rule 37a).
5. **This file is the spec as well as the state.** `PLAN.md` was archived on
   2026-08-18 and its milestone scope migrated into these files, so there is
   no second document to keep in step.
6. **A file opens with its meeting view** — `## At a glance` directly under
   the title, and a table or a diagram directly under that, saying in plain
   English what we are going to do
   ([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rules 59–61,
   gated by `tests/test_open_work_rows_are_short.py`). Write every new file
   from the template below.
7. **A file names who filed it and who last updated it** — `filed_by`,
   `updated` and `updated_by` in its frontmatter, each `_by` as
   `"<person> (<surface>, <model>)"`, e.g. `"Arpit (Cowork, Opus 5.5)"`; every
   change re-sets `updated` and `updated_by`. Its *Open items* row ends
   `Filed by <person> (<surface>).` before the detail link
   ([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rules 62–64,
   gated by the same test).

**The template — copy it for every new item.**

```markdown
---
type: Handoff
name: W-nn
description: "<one sentence: who asked, when, for what>"
item: W-nn
filed: YYYY-MM-DD
filed_by: "<person> (<surface>, <model>)"
updated: YYYY-MM-DD
updated_by: "<person> (<surface>, <model>)"
ball: agent | arpit | cowork
---

# W-nn — <title, in plain words>

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | <a plain-English action, readable aloud> | <what it buys, in one phrase> | ⏳ |
| 2 | Arpit picks <the choice> | <the decision it unblocks> | 🔴 Arpit decides |

**Arpit, YYYY-MM-DD (<surface>):** *"<the ask, in his words>"*

**Model:** <Opus | Sonnet | Haiku | Cowork | NONE — who, and why>: <one sentence why>.

## Goal

## Definition of done

## Blockers

## Record affected

<SR-NAME decision n> — or **no SR affected**.

## Hazards

## Reference
```

State is ✅ done · ⏳ not yet · 🔴 Arpit decides. When the item's shape is a
flow or a dependency rather than a list of steps, the table may be a fenced
`mermaid` or `text` diagram, or an image, instead.

**Naming.** `W-nn` ids are never reused. Ids `W-00`…`W-14`, `W-20`,
`W-21`, `W-40`, `W-41` are retired (done); see WORKLOG for their record.
`W-167`, `W-171`, `W-172` are retired unused — a 2026-09-14 id collision
between two concurrent sessions (the item became W-173); they are holes by
design, not lost items.
