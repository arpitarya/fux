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
| 4aad6236 | Claude Code | 2026-10-25 15:30 | W-299…W-302 built and merged; W-300's L13 ruling is with Arpit; cleaning up the two agent worktrees |

## Resources this session created

| kind | where | host | session | created |
|---|---|---|---|---|
| worktree | /Users/arpitarya/my_programs/fux/.claude/worktrees/agent-a42da0f618cb59aa3 | Arpits-MacBook.local | 4aad6236 | 2026-10-25 16:00 |
| worktree | /Users/arpitarya/my_programs/fux/.claude/worktrees/agent-a4c6bc315d09e4640 | Arpits-MacBook.local | 4aad6236 | 2026-10-25 16:00 |
