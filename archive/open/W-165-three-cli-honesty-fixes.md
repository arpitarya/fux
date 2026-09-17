---
type: Handoff
name: W-165
description: "Three shipped-surface fixes the records already owe: `fux remove` writes its exclusion into `.fux/.fuxignore` instead of a `!` line in `.fux/sources/dirs`; `No confident matches.` moves from stdout to stderr on `ask`, `find` and `answer` together; the ingest summary line counts deletions. Promoted from BACKLOG B-024, B-029, B-030."
item: W-165
filed: 2026-09-14
ball: agent
---

# W-165 — three CLI honesty fixes

**Model: Sonnet.** Each fix is named in its record with the remedy spelled out;
the only care is that the second one is a documented-surface change and needs
its e2e goldens updated deliberately, never regenerated blindly.

**Promoted 2026-09-14 from [`BACKLOG.md`](../BACKLOG.md)** rows B-024, B-029,
B-030 (deleted there). Ratified-not-built.

## Definition of done

1. **`fux remove <dir>` writes to `.fux/.fuxignore`.** The `!`-line form in
   `.fux/sources/dirs` keeps being *read* ([SR-DIR-LIST](../../records/0120_dir-list.md)
   decision 2a) but is no longer *written*; `fux remove` on a path that is
   currently excluded by a `!` line leaves that line alone and says so.
   [SR-FUXIGNORE](../../records/0144_fuxignore.md) Consequences called this
   *"a migration we now owe"*. A `doctor` note lists surviving `!` lines with
   the one-line move.
2. **`No confident matches.` goes to stderr** on all three verbs in one change
   ([SR-FIND](../../records/0104_find.md) Consequences), so a pipe expecting a
   path gets empty stdout and exit code as today. `--json` is unaffected (it
   never printed the sentence). The e2e goldens for the three verbs are
   updated by hand and the CHANGELOG names the change.
3. **The ingest summary counts deletions** — `N shards written, M records
   deleted` where the second clause appears only when M > 0
   ([SR-INGEST](../../records/0106_ingest.md) Consequences).
4. Both readers for 2 (Node prints the sentence too).
5. Records: SR-FUXIGNORE + SR-DIR-LIST (the write path), SR-FIND + SR-ASK +
   SR-ANSWER (the stream), SR-INGEST (the line); SR-CLI if the summary line's
   shape is stated there.

## Out of scope

- `--json` for the write verbs (B-031) — waits for a caller who needs it.
- The `fused`/`confidence` key order (B-151) and exit code 2 (B-152) —
  `unruled`, Arpit's.

## Where the work is

[`src/fux/sources.py`](../../src/fux/sources.py) (`remove`),
[`src/fux/query/__init__.py`](../../src/fux/query/__init__.py) (the three
verbs' empty-result print), `src/fux/ingest/` (the summary), `tests_e2e/`.

## Records this will touch

SR-FUXIGNORE · SR-DIR-LIST · SR-FIND · SR-ASK · SR-ANSWER · SR-INGEST ·
SR-NODE-SEARCH.

## Verification, and the keep/remove call (gap check 2026-09-14)

Order: **implement → test (e2e goldens updated by hand) → call.**

- **Fix 1** (`remove` → `.fuxignore`): e2e — `fux add`, `fux remove`, ingest;
  the excluded path is gone from the index; `dirs` carries no new `!`; an old
  `!` line still excludes. Keep on the tests; nothing to measure.
- **Fix 2** (stderr): e2e on all three verbs — stdout empty, stderr carries
  the sentence, exit code unchanged, `--json` unchanged, Node identical. The
  call: **keep unless a consumer script in this repo or the lab depended on
  the stdout sentence** — grep the tree and `fux-lab` for the string before
  landing; if one exists, it is fixed in the same change, not used as a
  reason to keep the defect.
- **Fix 3** (deletions count): a unit test on the summary formatter; keep.
- These are surface fixes, not ranking changes: **no golden measurement**;
  `test_the_graph_lane_does_not_move_ask` and the differential arm stay green.
