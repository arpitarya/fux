---
type: Handoff
name: W-276
description: "Arpit's ask (2026-10-11, Cowork): every commit must run fux ingest. The post-commit hook was installed, yet the index had not refreshed since 2026-10-04 across 39 commits, and nothing said so. CLOSED 2026-10-11: suspect 1, in a worse form (a pyenv shim); the hook now pins its interpreter and is never silent."
item: W-276
filed: 2026-10-11
ball: agent
---

# W-276 — the post-commit hook runs, but the index never refreshes

**Status: CLOSED 2026-10-11 — built (Claude Code, Opus 5.5).** Cause and evidence in §Outcome below.

**Arpit, 2026-10-11 (Cowork):** *"I want a work item for a hook created where
whenever on commit fux ingest gets executed."* Told that the hook already
exists and is installed, he chose **"fix the existing hook"** over moving to
`pre-commit` (the same-commit index stays rejected —
[`hooks.py`](../../src/fux/maintain/hooks.py) docstring, SR-MAINTENANCE).

**Model:** Claude Code, **Sonnet** to diagnose; **Opus** if the fix touches the
lock or the runner's loop.

## What was seen (Cowork, read-only, 2026-10-11)

- `.git/hooks/post-commit` is fux's: `fux ingest --spawn-runner || exit 0`,
  preceded by `command -v fux >/dev/null 2>&1 || exit 0` (the preamble).
- `.fux/runtime/` was last rebuilt **2026-10-04 18:16 UTC**; `.fux/index/` was
  last committed **2026-10-05**. **39 commits** since, on
  `claude/gracious-galileo-aqrg8b`; the working tree's `.fux/index/` is clean —
  so no runner has written an index since.
- No `dirty` list and no `runner.status` in `.fux/runtime/`. A `write.lock`
  (`{"pid": 26810}`) was written 2026-10-11 09:01 UTC.

## Suspects, in the order to check

1. **`fux` is not on git's `PATH`.** It lives in `.venv/bin/fux`. A commit from
   a shell without the venv activated, from an IDE, or from Claude Code hits
   `command -v fux || exit 0` and exits **silently** — though the hook's own
   header promises it *"reports and gets out of the way"*.
2. **A stale or wedged `write.lock`** — a second spawn that loses the lock exits
   quietly by design (`runner.py`), so a lock nobody clears stops every later
   run without a word.
3. **The spawned runner fails** and `|| exit 0` plus a detached process with no
   terminal swallow the error.

## Definition of done

1. **The cause is named** in this file with the evidence (a reproduced commit
   that does not re-index, and the line that explains it).
2. **The fix:** a commit in this repo, made from a plain shell with the venv
   **not** activated, refreshes `.fux/runtime/` and `.fux/index/`. If suspect 1:
   `fux hooks --install` writes the absolute path of the `fux` that installed it
   (falling back to `PATH`), and `fux doctor` flags a hook whose path no longer
   exists.
3. **Never silent again:** when the hook cannot run, it prints one line saying
   why and what to type — and still exits 0 (a hook never blocks a commit). A
   runner that fails leaves a reason `fux doctor` shows.
4. **Records first** (L0): amend [SR-MAINTENANCE](../../records/0129_hooks.md)
   (and [SR-LOCKS](../../records/0140_locks.md) if the lock is the cause).
5. **Tests:** a hook installed, `fux` removed from `PATH`, a commit → the
   message appears and the index still refreshes (or doctor names why); the
   two-strikes rule applies if this class recurs.
6. Both suites green, whole; the maintain skill says what changed.

## Out of scope

- `pre-commit` / the index landing in the same commit — rejected, Arpit
  re-confirmed 2026-10-11.
- Ingest speed — [W-268](W-268-ingest-under-one-second.md).
- The network: the hook stays `--no-fetch`-style local-only (L5).

## Records this will touch

SR-MAINTENANCE · possibly SR-LOCKS · the fux-maintain skill.

## Outcome (2026-10-11, Claude Code, Opus 5.5)

**DoD 1 — the cause is suspect 1, in a form worse than the item guessed.** On
this machine `command -v fux` succeeds, because the PATH holds a **pyenv shim**
(`~/.pyenv/shims/fux`). The global pyenv version is `system`, and fux is
installed only under 3.14.2, so the shim prints `pyenv: fux: command not found`
and **exits 127**. The hook's `fux ingest --spawn-runner || exit 0` swallowed
that. From a bare PATH (`env -i PATH=/usr/bin:/bin`) the preamble's
`command -v fux || exit 0` skipped with **no output at all**. Both reproduced by
running `.git/hooks/post-commit` directly: rc 0 both times, no dirty list, no
runner. Suspects 2 and 3 were not live: the `write.lock` was gone and
`runner.status` was absent. Suspect 2 was still a latent silence of its own: a
dead holder made `--spawn-runner` print *"already running"* forever.

**DoD 2–3 — the fix:**

- `fux hooks --install` writes `fux_python=<absolute sys.executable>` into
  every hook, and the hook runs `"$fux_python" -m fux.cli`. PATH is the
  fallback only, for when that interpreter is gone.
- **Never silent.** With no runnable fux, the hook prints one line naming
  `fux hooks --install`. When `post-commit`'s fux fails, it prints one line
  with the exit code and names `fux doctor`. A stale lock is named with
  `fux ingest --stop` and never cleared. Every hook still exits 0.
- **`fux doctor` → `git hooks`** (warn) flags a pinned interpreter that is
  gone (`missing`) and a hook written before this change (`unpinned`). A failed
  runner was already reported by `background runner` (`runner.status`).
- This repository's hooks were reinstalled, and the closing commit was made
  from `env -i PATH=/usr/bin:/bin`.

**DoD 4 —** [SR-MAINTENANCE](../../records/0129_hooks.md) decision 3 amended,
**3a** added, veto 11 restated. [SR-DOCTOR](../../records/0152_doctor.md)'s
register gained the row. SR-LOCKS was not touched, because the lock was not the
cause.

**DoD 5–6 —** `tests/maintain/test_hooks.py` has 5 new tests: the pin, missing
and unpinned, the one-line skip, the failing-shim shape, and the doctor row.
`tests_e2e/test_maintenance.py::test_a_commit_with_fux_off_path_still_re_indexes`
covers a commit with `PATH=/usr/bin:/bin` that still re-indexes, and the absent
case now asserts the message. The fux-maintain skill and its three seeded copies
say what changed.

**Left as it was, on purpose:** the merge driver is still `fux-merge-index`
resolved on PATH (SR-MAINTENANCE decision 6). It is the same class of failure,
but that decision is not this item's to change. SR-MAINTENANCE 3a names the gap.
