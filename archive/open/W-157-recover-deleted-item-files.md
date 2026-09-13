---
type: OpenItem
id: W-157
title: "W-157 — closed items were deleted instead of archived; recover what survives"
description: "The 2026-08-19 archive-on-close ruling held for 76 items and failed for 40 ids: their detail files were deleted, so the argument behind each call existed only in git. Recovery ran 2026-09-13 — 20 files are archived with map rows, 20 ids are unrecoverable (no bytes in any commit or loose object), and 12 of the audited ids were never files at all. Open on the invariant test and its own close."
status: implemented
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-157 — recover the deleted item files, then archive them

**Model: Sonnet** — it is mechanical recovery against a fixed list. Escalate to
Opus only for the map rows, which need a judgment about what superseded what.

**CLOSED 2026-09-13 · ARCHIVED.** Recovery executed and gated; see §Disposition
for the per-id result. Live successors: the rule is
[SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rules 54–58, the
gate is `tests/test_no_work_item_is_lost.py`, the map is `archive/README.md`
§*Recovered 2026-09-13*, and the outcome is in `work/IMPLEMENTATION.md`.

## The ruling

> **Arpit, 2026-09-13:** *"In open work, once a work item is implemented,
> archive it. Do not delete it. Even closure, archive it — update the SR and
> see what can be recovered. Recover them then archive them."*

Stated as rules 54–58 of
[SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) in the same change
that filed this item. **This item is the *recover* half; the rule is already
landed.**

## The evidence

`archive/open/` holds **76** files. `work/open/` holds **12** live items.
`W-nn` ids run to `W-156`, and **50 ids resolve to neither directory**. Of
those, **35 were closed after the 2026-08-19 archive ruling** and each one has
a `WORKLOG` entry, an `IMPLEMENTATION` row, or both — so the close is real, the
file is gone, and nothing in the live tree holds its bytes.

**Why it failed** — two artifacts contradicted the ruling without looking like
rules, and both are corrected as of 2026-09-13:

- `work/DOC-REGISTRY.md`'s trigger for `work/open/` read *"its file is created
  with its index row and **deleted with it**"*;
- SR-WORK-OPEN-QUEUE rule 10's *"a resolved thing leaves the file entirely"*,
  which is about the queue, reads as deletion out of context.

## The list

**Tier A — closed post-ruling, recover and archive all 35:**

`W-68` · `W-70` · `W-71` · `W-94` · `W-95` · `W-96` · `W-99` · `W-100` ·
`W-101` · `W-102` · `W-103` · `W-104` · `W-105` · `W-114` · `W-115` · `W-116` ·
`W-117` · `W-119` · `W-120` · `W-121` · `W-123` · `W-124` · `W-125` · `W-126` ·
`W-127` · `W-128` · `W-129` · `W-131` · `W-141` · `W-142` · `W-149` · `W-150` ·
`W-151` · `W-152` · `W-153`

**Tier B — pre-ruling or possibly never allocated; confirm, do not fabricate:**

`W-15` · `W-16` · `W-17` · `W-18` · `W-19` · `W-22` · `W-28` · `W-29` · `W-34` ·
`W-35` · `W-36` · `W-37` · `W-39` · `W-42` · `W-43`

⚠ **Three ids in tier A are not simple deletions** and must be read before they
are recovered — a wrong recovery here invents history:

- **`W-114`** — the WORKLOG says it was **renumbered to `W-122`** because the id
  was already spent. `W-122` is archived. Expect **no separate `W-114` file**;
  record the renumber in the map row instead.
- **`W-99`** — the WORKLOG says the id *"was already taken by the decoder-map"*.
  Resolve which item actually held it before archiving anything under it.
- **`W-142`** — recorded as **retired**, not completed. It still archives
  (rule 55); the map row says *retired*, never *shipped*.

## Definition of done

1. **The bytes come from git history, never from reconstruction.** For each id:
   `git log --diff-filter=D --name-only -- 'work/open/W-<n>-*'` to find the
   removing commit, then `git show <commit>^:<path> > archive/open/<basename>`.
   ⚠ **A file rebuilt from `WORKLOG.md` is a forgery** — it is this session's
   prose wearing the original's name. If history has nothing, the id is
   reported as unrecoverable and gets a map row saying so; it does not get a
   file.
2. **Every recovered file lands in `archive/open/` unmodified.** No header, no
   *"recovered on"* banner, no reformatting. The file is the artifact.
3. **An `archive/README.md` §`open/` row per recovered file** — the file, its
   close date, and its live successor — per SR-WORK-OPEN-QUEUE rule 57 and
   `tests/test_archive_law.py`. This is the part that needs judgment, and it is
   the part the map is for.
4. **A written result for every one of the 50 ids**, tier B included: recovered,
   never existed, or unrecoverable-and-why. **A silent gap is how this defect
   started.**
5. **`tests/test_no_work_item_is_lost.py`** — every `W-nn` id resolves to
   exactly one of `work/open/` or `archive/open/`, with the pre-convention ids
   (`W-00`–`W-14`, `W-20`, `W-21`, `W-40`, `W-41`) plus whatever tier B proves
   never existed exempted **by name, never by range**. A range grows to swallow
   the next loss; a name list has to be edited deliberately.
6. **The outcome recorded in `work/IMPLEMENTATION.md`** and the row deleted from
   `OPEN-WORK.md` with this file moved to `archive/open/` — this item closes by
   its own rule or it has not understood itself.

## Disposition — the result for every id, 2026-09-13

**Of the 51 ids audited: 19 recovered (20 files), 20 unrecoverable, 12 never
files.** A further 18 pre-convention ledger ids, outside the audit, were never
files either. No file was reconstructed; where history had nothing, the hole is
reported, not filled (DoD 1 and the hazard).

**One correction to the audit above:** the list of 50 was short by one.
**`W-155`** was also deleted, is recovered here, and belonged in tier A. The
tier A/B split was otherwise sound; the two tiers are collapsed below, because
what actually decides an id's fate is whether its bytes survive, not when it
closed.

**Where the bytes came from.** Two sources, both original:

- **committed history** — `git show <commit>:<path>`, for files that reached a
  commit before being deleted;
- **unreachable loose objects** — `git fsck --unreachable` over 3 769 orphaned
  blobs, matched on `type: OpenItem` frontmatter and the `id:` field. These are
  files that were **staged and never committed**: the commit cadence here is
  coarse (*"chore: commit the working tree — several sessions' work"*), so an
  item opened and closed between two commits leaves an object and no history.
  ⚠ **`git fsck` is the only reason ten of these came back**, and a `git gc`
  would have taken them. Everything recovered from a loose object is a
  *staged snapshot*, dated no later than its item's close.

⚠ **Every recovered file still reads `status: open`.** Each is the last version
git ever saw, which is earlier than the state its item closed in. The closure
fact lives in `WORKLOG.md`, not in these files.

### Recovered — 20 files, 19 ids

`W-22` · `W-42` · `W-43` · `W-70` **(two files — see below)** · `W-71` ·
`W-102` · `W-103` · `W-104` · `W-105` · `W-114` · `W-115` · `W-141` · `W-142` ·
`W-149` · `W-150` · `W-151` · `W-152` · `W-153` · `W-155`

Each has an `archive/README.md` row naming its provenance and its live
successor, under §*Recovered 2026-09-13*. The three flagged ids resolved as the
audit predicted, except one:

- **`W-114`** — a file **did** exist, contrary to the audit's expectation, and
  is recovered. It is the pre-renumber original; `W-122` is the successor and
  the row says so.
- **`W-142`** — recovered; its row says **retired**, never *shipped*.
- **`W-99`** — no file, no blob, no path in any commit. The id resolves to the
  decoder-map item as the WORKLOG says; there is nothing to archive under it.
- **`W-70` was allocated TWICE** — the playground-sandbox item *and* an earlier
  per-document-cap item filed the same day out of `W-59`'s budget sweep. Both
  files are recovered; the second is filed as
  `W-70-per-document-cap.md` to break the filename collision. **The id inside
  each file is untouched** — the collision is a fact of the record, not a
  defect to edit away.

### Unrecoverable — 20 ids, allocated and closed, bytes gone

`W-68` · `W-94` · `W-95` · `W-96` · `W-99` · `W-100` · `W-101` · `W-116` ·
`W-117` · `W-119` · `W-120` · `W-121` · `W-123` · `W-124` · `W-125` · `W-126` ·
`W-127` · `W-128` · `W-129` · `W-131`

Each is real: every one carries a `WORKLOG.md` entry, a `DOC-REGISTRY.md` row,
an `IMPLEMENTATION.md` row, or several — `W-101` is named 40 times across the
live tree, `W-151`'s neighbours `W-126` and `W-116` more than 18 each. **And
none of their bytes exists anywhere**: not in any commit that ever touched
`work/open/`, not in a loose object, not under any other path. Each was created
and deleted inside one working tree without ever being staged. They get no
file, by DoD 1 — **a file rebuilt from `WORKLOG.md` would be this session's
prose wearing the original's name.**

The durable record of each is its `WORKLOG` entry plus its record, which is what
`archive/README.md` §`open/` already says is the durable record of any closed
item. **What is lost is the argument, not the decision.**

### Never a file — 12 audited ids, plus 18 pre-convention ledger ids

- **Pre-convention ledger rows (18):** `W-1`…`W-14`, `W-20`, `W-21`, `W-40`,
  `W-41`. These were rows in a `W-00…W-12` ledger inside `PLAN-v0.30.md`
  (archived) and the pruning-eval verdict — never detail files. This is the set
  DoD 5 already exempts by name.
- **No trace anywhere (12):** `W-15` · `W-16` · `W-17` · `W-18` · `W-19` ·
  `W-28` · `W-29` · `W-34` · `W-35` · `W-36` · `W-37` · `W-39`. Not one appears
  in any live document, any archived document, or any git object — the only
  place they are named is this item's own tier B list. `W-15` alone has a single
  `WORKLOG` trace, a *"**Next:** W-15 — re-measure with a realistic
  short/keyword query workload"* that was never filed. **They cannot be shown to
  have existed**, and per DoD 4 that is the written result: not recovered, not
  lost — never allocated. They join DoD 5's exemption list **by name**.

### What is still owed

**Nothing. All six DoD items are satisfied** (Arpit, 2026-09-13: *"I meant
implement it, then close it"*).

- **DoD 5 — [`tests/test_no_work_item_is_lost.py`](../../tests/test_no_work_item_is_lost.py)** is written and green.
  Every `W-nn` id resolves to a file in `work/open/` or `archive/open/`; no id
  lives in both; the two known double allocations (`W-70`'s reused id, and
  `W-76`/`W-82`/`W-107`'s second artifact) are named with their reason; and **an
  exemption that stops being true fails the test**, so the three lists shrink as
  things are found and never rot. Exemptions are **ids by name, never ranges**.
  ⚠ It was written by a Cowork session, which normally leaves `tests/` to Claude
  Code — said out loud here rather than folded in silently. Owned by
  [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md), whose `owns:`
  gains it and whose row lands in the ownership table in the same change.
- **DoD 6** — the `IMPLEMENTATION.md` row is written, the queue row deleted, and
  this file is in `archive/open/`. **The item closes by its own rule.**

## In scope / out of scope

- **IN:** recovery, archiving, map rows, the new test, the per-id report.
- **OUT:** re-opening or re-litigating any recovered item. They are **closed**;
  this restores the record of why, nothing more.
- **OUT:** editing a recovered file's content to match what later turned out to
  be true. An archived file is allowed to be wrong — that is what makes it
  history (rule 58).
- **OUT:** `archive/handoff/`, `archive/compare/` and the other archive tiers.

## Records affected

- [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) — rules 54–58 and
  decision 7 are already landed; this item adds no rule. It **will** own
  `tests/test_no_work_item_is_lost.py`, so the `owns:` list gains that path in
  the same change that writes the test.

## Hazard

⚠ **The recovery is only as good as history.** A file created and deleted
inside one un-pushed working tree, or lost to a `delete-plus-overwrite` that
`git log --follow` cannot see, is gone for good — the same failure mode
`archive/README.md` already records against `W-32`. **Report the hole; do not
fill it.**
