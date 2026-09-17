---
type: Handoff
name: W-164
description: "Four mechanical checks the records say are owed and nothing runs: the backlog row-shape test (its own record lands `built: no` without it), a test holding `.fux/README.md`'s verb table equal to SR-CLI §1, a test deriving the doctor register from the code's checks, and a flag on a confidence floor tuned to zero. Promoted from BACKLOG B-001, B-064, B-067, B-070."
item: W-164
filed: 2026-09-14
ball: agent
---

# W-164 — four small gates

**Model: Sonnet.** Each is a test against a rule already written down; the rule
text is the specification.

**Promoted 2026-09-14 from [`BACKLOG.md`](../BACKLOG.md)** rows B-001, B-064,
B-067, B-070 (deleted there). Ratified-not-built.

## Definition of done

1. **`tests/test_backlog_rows_are_short.py`** — enforces
   [SR-WORK-BACKLOG](../../records/0055_WORK-backlog.md) rules 11–16: `B-nnn`
   ids in filing order and unique, one line per row, ≤ 400 characters, no body,
   every row cites a source that exists (a path under `records/` or
   `work/proposals/`) and names what closes it. Mirror
   `tests/test_open_work_rows_are_short.py`'s shape. SR-WORK-BACKLOG then owns
   it and its `built:` flips.
2. **`.fux/README.md` verb table ≡ SR-CLI §1** — a test that parses both
   tables and fails on a verb present in one and not the other, or grouped
   differently ([SR-DOTFUX](../../records/0102_fux-directory.md) 2026-09-12
   amendment).
3. **Doctor register derived from code** — a test that enumerates the `Check`
   producers in `doctor.py` and fails when one has no row in SR-DOCTOR's
   register, or a row names a check that no longer exists
   ([SR-DOCTOR](../../records/0152_doctor.md) Consequences).
4. **A floor tuned to zero is flagged** — `separation_floor = 0.0` (or
   `doc_coverage_floor` when it is on) in `.fux/tune.toml` produces a `doctor`
   row *and* a one-line stderr note on the first `ask` of a process, because
   it silently turns `weak` off ([SR-CONFIDENCE](../../records/0141_confidence.md)
   decision 13). Report, never refuse.
5. Records: SR-WORK-BACKLOG (`built: yes`, ownership row), SR-DOTFUX,
   SR-DOCTOR, SR-CONFIDENCE — each sentence that says *nothing checks this*
   changes in the same commit. Ownership table + `test_sr_ownership.py`.

## Out of scope

- The other ~19 unenforced queue rules (B-047) — a separate sweep.
- Coherence or restatement checks (B-048–B-053) — no mechanism exists; those
  stay `ungated` on purpose.

## Where the work is

`tests/test_open_work_rows_are_short.py` (the template for 1),
[`src/fux/doctor.py`](../../src/fux/doctor.py), [SR-CLI](../../records/0101_cli-surface.md)
§1, [`src/fux/query/confidence.py`](../../src/fux/query/confidence.py).

## Records this will touch

SR-WORK-BACKLOG · SR-DOTFUX · SR-DOCTOR · SR-CONFIDENCE · SR-WORK-OWNERSHIP
(the table).

## Verification, and the keep/remove call (gap check 2026-09-14)

Order: **implement → run red on the current tree where a defect exists →
fix or file → green.**

- Each gate must be **shown red at least once** — on a deliberately broken
  fixture, or on the live tree if it already has the defect (gate 2 may: the
  `.fux/README.md` table has never been checked). A gate that has never been
  red proves nothing about itself.
- **Keep** a gate that stayed green across the suite for one release without
  a false alarm. **Remove** (delete the test and restore the record's *nothing
  checks this* sentence, with the reason) a gate that fires on legitimate
  changes more than it catches defects — the `tests/test_doc_links.py`
  exemption list is the precedent for what "legitimate" looks like.
- Gate 4 is the one with a behaviour: the stderr note must not appear under
  `--json` or in the MCP transport (test both).
