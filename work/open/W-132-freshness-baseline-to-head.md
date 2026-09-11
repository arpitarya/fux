---
type: OpenItem
id: W-132
title: "W-132 — move the freshness gate's baseline to HEAD; stop auditing old commits"
description: "Arpit, 2026-09-11: the ADR freshness gate is red on 94231b2 (W-114). Fix it by moving docs/adr/RULE-SINCE to HEAD so old commits are no longer audited. No rebase, no key-scoped describes, no waiver."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-132 — move the freshness gate's baseline to HEAD

**Model: Sonnet** — a baseline move, a record amendment and a suite run against a
written definition of done. Close to Opus only because the ADR-OWNERSHIP text
must state the cost honestly rather than tidily.

## The ruling

- **Arpit, 2026-09-11:** *"fix only the latest, leave the old ones"* — confirmed
  in the same session as **stop auditing old commits**.
- **Declined in the same exchange:** (a) rebase `94231b2` to touch three
  records, (b) key-scoped `describes`, (d) a one-sha waiver.

## Why it is red

- `94231b2` changed `src/fux/config.py` **only** to add `"codex"` to
  `[agents] install`.
- `describes` is **file-scoped**, so the gate demands every record describing
  `config.py`: ADR-ACQUIRED, ADR-PII, ADR-URL-FRESHNESS — none of whose keys
  that commit touched.

## Definition of done

1. **Re-derive first.** Run `uv run pytest -q tests/test_adr_freshness.py` and
   confirm it fails on `94231b2` and **only** there. If it fails elsewhere, stop
   and report — the ruling was made about one commit.
2. **`docs/adr/RULE-SINCE`:** the current baseline (`9bb870e…`) moves to
   *Previous baselines*; the new baseline is **HEAD at execution time** (the last
   commit before this change — `894990a` when filed; re-check `git log`).
   A dated comment block states:
   - the ruling, in Arpit's words;
   - the cause — **file-scoped `describes` against key-scoped descriptions**,
     which is *not* the cause decision 9 fixed (reassignment / renumber / new record);
   - the cost — every commit before the new sha is no longer re-auditable.
3. **ADR-OWNERSHIP** (`docs/adr/0056_ownership.md`), written in place, no
   `Amended` section:
   - **veto condition 6 has fired by ruling**, with the cause above named;
   - decision 9 stays in force (commits after the baseline are still judged
     against the register as it stood at that commit);
   - ⚠ **the over-firing is NOT fixed** — the next commit touching `config.py`
     will again demand every describer. Key-scoped `describes` was the declined
     alternative; record it as declined, not rejected on merit.
4. `uv run pytest -q tests tests_e2e` green; the commit passes
   `scripts/adr-guard.sh`.
5. Close-out in the same change: delete the W-132 row from `OPEN-WORK.md`, add an `IMPLEMENTATION.md`
   entry, a `WORKLOG` entry, bump DOC-REGISTRY, move this file to `archive/open/`.

## Hazards

- 🔴 **Concurrent sessions stage files in this tree** (one committed `894990a`
  mid-filing). **Commit only your own paths** — `git commit -- <paths>` — never a bare `git commit`.
- **Do not rebase, amend or push.**
- **Do not "improve" the gate** while here — no key scoping, no waiver list.

## Prompt

```
Execute work/open/W-132-freshness-baseline-to-head.md exactly.
Read CLAUDE.md, then that file. Explore → plan → implement → verify.
Re-derive the failure before changing anything; stop and report if it is not
exactly 94231b2. Commit only the paths you changed (git commit -- <paths>).
Do not push. Finish with the close-out list.
```
