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
| e2598401 | Claude Code | 2026-10-25 12:53 | stood down: W-299 landed (9688d479); W-300 + W-301 claimed by 4aad6236, so not built here; no code changed |
| 4aad6236 | Claude Code | 2026-10-25 15:30 | W-304: releasing 5.1.0 — fixing two Windows-only test failures before the GitHub release |
| 0c27e2d0 | Claude Code | 2026-10-25 17:36 | W-304: read-only registry check — 5.1.0 not yet on PyPI/npm (no v5.1.0 release); no code changed |

## Resources this session created

| kind | where | host | session | created |
|---|---|---|---|---|
