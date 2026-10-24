---
type: Handoff
name: W-297
description: "Clean the ten agent worktrees under .claude/worktrees/ (≈4 GB) that the work/NOW.md resource ledger found on its first day, and prune the four stale /private/tmp entries."
item: W-297
filed: 2026-10-24
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-24
updated_by: "Claude Code (Opus 5.5)"
ball: arpit
---

# W-297 — clean the leftover agent worktrees

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | For each worktree listed below: is its branch merged into `main`, and is its tree clean (`git -C <path> status --porcelain`)? | which are safe to remove | ✅ 2026-10-24 — §Verdicts |
| 2 | `git worktree remove <path>` each merged, clean one; `git branch -d` its branch | ≈400 MB back per worktree; its row drops from NOW.md by itself | ✅ `integrate` removed; `agent-a02544a49dceb592f` removed after W-294 merged from it |
| 3 | An unmerged or dirty one: to the inbox with its branch, last commit and `git diff --stat main...` | nothing unmerged is lost | 🔴 8 worktrees + 1 branch → Arpit (§Verdicts) |
| 4 | `git worktree prune` for the four `/private/tmp/claude-501/…/scratchpad/{build,engine,own,pre}` entries whose folders are gone | `git worktree list` matches the disk | ✅ pruned |

**Arpit, 2026-10-24 (Cowork):** *"what work trees got created … if they aren't cleaned, then create a work item to clean them."*

**Model:** Sonnet — mechanical, but every removal is checked against `main` first.

## The worktrees

- `.claude/worktrees/agent-a02544a49dceb592f`
- `.claude/worktrees/agent-a2570686adcc6ddc9`
- `.claude/worktrees/agent-a38e816dfc2a41296`
- `.claude/worktrees/agent-a67362f1e29c7a55a`
- `.claude/worktrees/agent-a74b1ff1496b3655e`
- `.claude/worktrees/agent-a925c8c801993a7e5`
- `.claude/worktrees/agent-a945211e6ff2eb2dc`
- `.claude/worktrees/agent-af9290761f26b62ad`
- `.claude/worktrees/integrate`
- `.claude/worktrees/merge-w29x`

## How, since SR-WORK-CLEANUP

`python3 .claude/hooks/worktree-cleanup.py` gives each worktree's verdict; `--apply` removes the safe ones (HEAD in `main`, nothing unsaved, only build output ignored, no live lock). Every red one goes to the inbox as Arpit's keep-or-drop call — never `--force`, never `branch -D` ([SR-WORK-CLEANUP](../../records/0070_WORK-cleanup.md)).

## Verdicts — 2026-10-24 (Claude Code, Opus 5.5)

`worktree-cleanup.py`, which §How names, **does not exist yet** (SR-WORK-CLEANUP
decision 6 describes it); the check was run by hand against decision 1's four
tests. **pid 44149 is dead**, and neither lock file was still present. Two
removed: `integrate` (HEAD in `main`, clean), and `agent-a02544a49dceb592f` once
W-294 was merged from it.

**The other nine hold nothing `main` lacks, and every one fails decision 1 on a
technicality,** so by decision 3 they are untouched and the call is Arpit's:

| worktree / branch | tip | in `main`? | uncommitted |
|---|---|---|---|
| `agent-a2570686adcc6ddc9` | `753363d9` W-292 | patch-equal (cherry-picked), not ancestor | 26 files, all `.fux/index/` |
| `agent-a38e816dfc2a41296` | `e69740b5` W-296 | patch-equal, not ancestor | 21, all `.fux/index/` |
| `agent-a67362f1e29c7a55a` | `d14330ee` | **ancestor** | 39, all `.fux/index/` |
| `agent-a74b1ff1496b3655e` | `2f658b48` W-291 | patch-equal, not ancestor | none |
| `agent-a925c8c801993a7e5` | `79378367` W-281 | patch-equal, not ancestor | 12, all `.fux/index/` |
| `agent-a945211e6ff2eb2dc` | `4699251a` | **ancestor** | 16, all `.fux/index/` |
| `agent-af9290761f26b62ad` | `31bc5e00` W-295 | patch-equal, not ancestor | 67, all `.fux/index/` |
| `merge-w29x` | `c066ec7c` merge | its merges' patches all in `main`, not ancestor | none |
| branch `worktree-agent-a02544a49dceb592f` (no worktree) | `c42c45ee` W-294 WIP | **2 commits not patch-equal** — the WIP that W-294 (`2ecba902`) finished and superseded | — |

The uncommitted `.fux/index/` bytes are the post-commit hook's background
re-index inside each worktree: derived, and regenerated on `main` by any ingest.

**Recommendation: drop all nine** — `git worktree remove --force` the eight,
`git branch -D` the nine branches. Nothing in them is absent from `main`. Only
Arpit's word permits `--force` / `-D` (decision 3).

## Goal

None of them is left, and `git worktree list` shows only the main checkout plus worktrees a live session is using.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · merged ones gone | every merged, clean worktree removed and its branch deleted | ⏳ |
| 2 · nothing lost | every unmerged or dirty one is on the inbox with its diff, not removed | ⏳ |
| 3 · disk agrees | none of the paths below in `git worktree list`; fux back under its 5 GB budget ([L14](../../records/0016_LAW-14-machine-budget.md), the machine-budget law) | ⏳ |

## Hazards

- 🔴 **Two are `locked`** — `agent-a2570686adcc6ddc9` and `agent-a38e816dfc2a41296`, by pid 44149 (started 08:01 on 2026-10-24). A lock means an agent may still be running. Check `ps -p 44149`; never `git worktree remove --force` past a live lock.
- **Run it on the Mac (Claude Code), not the Cowork bridge** — the bridge cannot unlink, so `git worktree remove` fails half-way there ([MACHINE](../MACHINE.md)).
- `merge-w29x` and `integrate` are merge branches from the 2026-10-24 parallel run — confirm `main` contains their tips before removing.

## Record affected

None — this executes [SR-WORK-NOW](../../records/0069_WORK-now.md) decision 4.
