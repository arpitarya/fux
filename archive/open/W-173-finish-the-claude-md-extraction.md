---
type: Handoff
name: W-173
description: "The rest of the accepted CLAUDE.md extraction: fold six sections into the records that already state them (SR-RS, SR-LAW-0, the register, docs/index.md, MACHINE.md, SR-CLI), move the hard-won lessons into a work/ log because a record carries no history, and build the one enforcement test SR-WORK-LIFECYCLE decision 12 owes. Target: 668 lines to about 330."
item: W-173
filed: 2026-09-14
ball: agent
---

# W-173 — finish the `CLAUDE.md` extraction: the folds, the lessons log, and one owed test

**Model: Opus for the folds, Sonnet for the test.** Every fold is a judgement
about whether a sentence is already stated elsewhere or only looks like it — the
exact call that produced W-83's self-contradicting amendment. The test is a
written definition-of-done against files that exist.

**Ratified:** Arpit, 2026-09-14 — *"I accept the proposal. Go ahead and create
the new SR records."* The eight new records (`0057`–`0064`) **are built and
landed**; this item is the remainder of the same accepted proposal. Ratified,
not built.

**His one ruling on scope:** asked whether the generated laws block should
shrink to handles plus links, he chose **keep the full block**. So the floor for
`CLAUDE.md` is **~330 lines, not ~260**, and `scripts/gen-laws.py` gains no
`--brief` mode.

**Its inventory is [W-146](W-146-the-rest-of-l0.md) §1, reconciled in the same
change.** Every numbered item below cites the row it executes; **this item does
not keep a second list**, and W-146 retains only its §2 ruling and the rows it
still marks open.

## Context

- `CLAUDE.md` went **1059 → 668** lines when the eight WORK records took their
  sections. The remaining ~340 lines are the six folds below plus what should
  stay: the header, the index table, the scope section, the laws block, the
  golden-key paragraph, the trimmed layout and the test commands.
- **Each fold moves prose into a record that already states the rule**, which is
  why none of them needs a new record. The risk is the opposite of the last
  change's: deleting a sentence from `CLAUDE.md` whose claimed home turns out not
  to carry it.

## Definition of done

1. **§Conformance runs + §A pre-registered threshold may never move → [SR-RS](../../records/0133_predictions.md).**
   The blind/informed split, the paired-comparison floor, the per-query-rows
   rule and *a verdict is not an SR* are already decisions 11–19 there; the
   six-step filing procedure belongs in
   [`work/regression/README.md`](../regression/README.md). ~96 lines out.
   ⚠ `tests/test_regression_runs.py` and `tests/test_doc_links.py` both quote
   *"CLAUDE.md (§Conformance runs)"* in a message and a docstring — repoint both
   in the same change.
2. **§Law zero → [SR-LAW-0](../../records/0002_LAW-0-authority.md) and [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md).**
   This section is a hand-written second copy of L0's freshness obligation — a
   restatement by L0's own test — plus the freshness gate, which is
   SR-WORK-OWNERSHIP's subject. Keep the `commit-msg` install line as a fact.
   ~43 lines out.
3. **§The SR standing rules → [`records/README.md`](../../records/README.md).**
   All six bullets are already in the register. ~39 lines out.
4. **§Layout → [`docs/index.md`](../../docs/index.md)**, keeping a ~12-line
   top-level tree in `CLAUDE.md`. ~40 lines out.
5. **§Hard-won build knowledge → a `work/` log, NOT a record.** A record states
   what is true now and carries no history, so these dated lessons are not SR
   material. Either `work/LESSONS.md` (`type: Log`, date-grouped newest first)
   or INTERVIEW's *lessons learned* section. The two v0.19–0.26 items that still
   bind (BM25F weight-then-saturate; no wall-clock on the maintenance path) go
   to the records that own the code, not to the log. ~57 lines out.
6. **§Build & test gotchas → [`work/MACHINE.md`](../MACHINE.md)**, keeping the
   five canonical commands in `CLAUDE.md`. The `node --test` glob trap and the
   `.fux/pii.toml` requirement are surface quirks. ~35 lines out.
7. **§Error contract → [SR-CLI](../../records/0101_cli-surface.md)**, which the
   ownership table already credits with *"the boundary error contract"*. ~6 lines
   out.
8. **§Triage first → [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md).**
   The inbox rules are already rules 10 and 39–45 there. ⚠ **Check first whether
   `tests/test_work_queue_rules_have_one_home.py::test_no_live_document_restates_a_rule`
   should already be failing on this section** — if it should, that is a defect
   in the fingerprint set and it is fixed in the same change. ~19 lines out.
9. **The one owed test — [SR-WORK-LIFECYCLE](../../records/0058_WORK-lifecycle.md) decision 12.**
   Every file under `work/open/` carries a `**Model:**` line, and no handoff
   directory exists. The record then claims it in `owns:` and in the register's
   ownership table. **It stays in `_UNREACHABLE_BY_THE_GATE`** — that pin tracks
   records with no `src/` component, and a test is not one — but the comment's
   stated reason for it changes, and leaving a stale reason standing is the
   drift this repo gates against.

## Out of scope

- **A `--brief` laws block.** Arpit ruled the full block stays (above).
- **SR-WORK-SCALE decision 15 and SR-WORK-SESSION decision 13.** Both records
  argue that a checker would grade the wrong thing — *what a sentence may claim*,
  and *whether a handoff is true*. **Do not build one to close a gap the record
  deliberately declares open.** Reopening either is Arpit's call.
- **Re-litigating any of the eight new records.** They are accepted.

## Key files

- [`CLAUDE.md`](../../CLAUDE.md) — 668 lines as landed on 2026-09-14.
- [`records/0133_predictions.md`](../../records/0133_predictions.md) ·
  [`records/0002_LAW-0-authority.md`](../../records/0002_LAW-0-authority.md) ·
  [`records/README.md`](../../records/README.md) ·
  [`records/0101_cli-surface.md`](../../records/0101_cli-surface.md)
- [`docs/index.md`](../../docs/index.md) · [`work/MACHINE.md`](../MACHINE.md) ·
  [`work/regression/README.md`](../regression/README.md)

## Tests

- `tests/test_claude_md_laws.py` must stay green with the laws block untouched.
- `tests/test_doc_links.py`, `tests/test_doc_registry.py`,
  `tests/test_work_queue_rules_have_one_home.py`, `tests/test_okf_bundle.py`.
- The new `work/open/` model-line test from item 9.
- **Both suites, whole**, before believing it is done — a red test on an
  uncommitted tree is invisible to every mechanism here.

## Open questions

- **Does §What we are building (scope) belong in a record?** It is 49 lines and
  its parts are spread across SR-EXTRACTED, SR-ENRICH, SR-PORT-LIST and the
  paper. Nobody has ruled whether it becomes `0065` SR-WORK-SCOPE or stays as
  the orientation paragraph it reads as today.
- **Does the golden-key paragraph stay verbatim?** It is the only cover Cowork
  has, so this change left it alone deliberately.
