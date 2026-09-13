---
type: OpenItem
id: W-103
title: "W-103 — accept ADR-LOCKS and discharge the three debts it filed against itself"
description: "ADR-LOCKS is the last `proposed` record in the register. It introduces no mechanism and overrides no decision — its three veto checks were run on 2026-08-27 and none fired — so acceptance is a ruling, not a build. What it does carry is a debt it named itself: three places still calling the file `runner.lock`. Re-derived 2026-09-01: two of the three are still there, the third is already clean."
status: open
lane: agent
timestamp: 2026-09-01T00:00:00Z
---

# W-103 — accept ADR-LOCKS

**Model: Sonnet.** Two docstring edits, a status flip and a register row. The
judgment was Arpit's and is already made.

## The ruling this implements

**Arpit, 2026-09-01: accept it.** [ADR-LOCKS](../../docs/adr/0043_locks.md) has
sat `proposed` since 2026-08-27 and is the only record in
[the register](../../docs/adr/README.md) not `accepted`.

## Why acceptance costs nothing to check

The record says it of itself, and it is true: *"This record introduces no
mechanism and overrides no decision."* It states what the code already does,
citing the record that owns each part. Its three veto conditions were checked
in the record with real command output on 2026-08-27 and all read
`not fired` — a second mutex over `.fux/index/`, a read verb taking a lock, and
`write.lock` becoming committable. **Re-run them before flipping the status**
(rule 4: re-derive, do not read) — they are three greps and a
`git check-ignore`, printed in the record's own *How to check them* block.

## The debt, re-derived 2026-09-01

The record files this under *Consequences* as **Owed, and not fixed here**:
three places naming a file that no longer exists. Grepped today, the list is
**two, not three**:

| where | line | state |
|---|---|---|
| [`src/fux/maintain/runner.py`](../../src/fux/maintain/runner.py) | 33, in the module docstring | 🔴 still says `runner.lock` |
| [`src/fux/maintain/daemon.py`](../../src/fux/maintain/daemon.py) | 52, in the module docstring | 🔴 still says `runner.lock` |
| [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) decision 11a | — | ✅ **already clean** — no occurrence in the file |

⚠ `runner.py:98` also contains the string, and is **correct**: it is the
`#: ⚠ Renamed from runner.lock 2026-08-26` note on `LOCK_NAME`, which is the one
place the old name *should* appear. Do not touch it.

## Definition of done

- [ ] The three veto checks re-run and their output pasted into the record's
      *How to check them* block with today's date. A record accepted on a
      2026-08-27 capture is a record accepted on hearsay.
- [ ] `runner.py` line 33 and `daemon.py` line 52 say `write.lock`.
- [ ] [ADR-LOCKS](../../docs/adr/0043_locks.md) `status: proposed` →
      `accepted`, `date:` unchanged (the decision was taken 2026-08-27; today
      is when it was ratified), and the *Owed, and not fixed here* bullet
      **deleted** — the queue rule against tombstones applies to records too.
- [ ] [The register](../../docs/adr/README.md) row 0043: `⏳ proposed` →
      `accepted`.
- [ ] Commit message: the change touches `src/fux/maintain/`, which
      [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) owns — **that record is
      what the freshness gate will demand**, not ADR-LOCKS, which owns nothing.
      Open both. If the docstring fix genuinely needs no ADR-MAINTENANCE
      sentence changed, say `no ADR affected` for that record out loud rather
      than touching it to satisfy the gate.

## Hazards

- 🔴 **The record owns nothing, and nothing mechanical will ever tell you it
  went stale.** It says so itself under *Consequences*. Accepting it does not
  change that; it makes the unenforced obligation live rather than pending,
  which is the whole reason to accept it rather than leave it in limbo.
- **`fcntl.flock` stays refused.** If a future reader arrives at this item
  thinking acceptance is the moment to revisit the mechanism: decision 3 and
  the *Alternatives considered* block already ruled it, twice, on
  reportability rather than on cost.

## Out of scope

Anything that changes locking behaviour. This item is a ruling and two
docstrings; a mechanism change is an ADR-MAINTENANCE amendment and a different
row.
