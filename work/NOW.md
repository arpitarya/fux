---
type: Pointer
description: "Only what is being worked on right now: one row per live session, plus what those sessions created and have not yet cleaned. Empty when nothing is running."
---

# NOW

Kept by `.claude/hooks/now-ledger.py` in Claude Code; a Cowork session adds and removes its own row by hand.
Rule: [SR-WORK-NOW](../records/0069_WORK-now.md).

## In flight

| session | surface | started | working on |
|---|---|---|---|
| f7e74b47 | Claude Code | 2026-10-25 12:39 | W-299 + W-302 built in parallel by two sub-agents in this tree; W-293 closed |
| e2598401 | Claude Code | 2026-10-25 12:53 | W-300 + W-301: waiting for f7e74b47 to land W-299, then building both (read-only until then) |
| 4aad6236 | Claude Code | 2026-10-25 15:30 | W-299 + W-302: finishing f7e74b47's stale half-built tree to green and committing; then W-300 + W-301 in parallel |

## Resources this session created

| kind | where | host | session | created |
|---|---|---|---|---|
