# MACHINE — where this actually runs, and what breaks there

**How to use this file.** Fux is developed from at least four surfaces, and
they do not agree about what is possible. This file records the **surface**
quirks — path, sandbox, network, tooling — so a session does not lose an hour
rediscovering that a command cannot work where it is standing.

Anything here is about the *environment*, never the code. A defect in `src/`
belongs in [`OPEN-WORK.md`](OPEN-WORK.md); "this works locally but not over
the bridge" belongs here.

Add an entry the moment a surface surprises you, with the date and the exact
error text.

---

## The surfaces

| surface | filesystem | network | python | notes |
|---|---|---|---|---|
| **Local terminal** (macOS, arpits-macbook) | the real repo | yes | project `.venv` | the only surface with no caveats |
| **Cowork device VM** (`device_bash`) | repo mounted at `$HOME/mnt/fux` | **none** | 3.10 | cannot delete; no `pytest`; see below |
| **Cowork cloud container** (`Bash`) | its own scratch tree | yes | ≥3.11 | where measurement runs and installs happen |
| **GitHub Actions** | clean checkout, **Linux** | yes | matrix | case-**sensitive**; catches what macOS hides |

---

## The Cowork device VM — what it cannot do (2026-08-18)

**It cannot delete anything.** `rm`, `rmdir` and `unlink` on a mounted file
fail with `Operation not permitted`. The consequences are not obvious:

- `git checkout -- .`, `git stash`, `git reset --hard` and `git clean` all
  **fail mid-way**, because each needs to unlink. There is no undo on this
  surface — a bad bulk edit is fixed by editing forward, not by reverting.
- `git mv` **works** (rename, not unlink). So do truncating writes (`>`).
- **`git --no-optional-locks <cmd>` strands nothing.** This is the fix, found
  2026-08-18: `git --no-optional-locks status --porcelain` and
  `git --no-optional-locks diff --name-only HEAD` both run clean on the bridge
  and leave no lock behind, because git skips the index refresh that needs one.
  **Prefer it for every read-only git call on this surface**, and in any tooling
  that has to run here — `tests/test_adr_freshness.py` uses it for exactly this
  reason. Plain `git status` still strands one.
- A stranded `.git/index.lock` cannot be removed, and `mv`-ing it *out* of the
  mount fails too (that is a copy plus an unlink). **Rename it in place** —
  `mv .git/index.lock .git/index.lock.stranded` — which is a pure rename and
  does work. `git add -A` strands one every time on this surface.
- To delete a file, `mv` it into a `_to_delete/` folder and tell Arpit.

**A written file can vanish from the mounted tree.** Observed 2026-08-18:
`archive/adr/README.md` was created, verified by `ls`, verified again by a
link checker, staged into the git index — and was gone from the working tree an
hour later, while `git ls-files` still listed it. No command in the session
could have deleted it (this surface cannot unlink). Cause unknown; assume the
mount can lose a write.

**So verify deliverables exist at the end of a session**, rather than trusting
that a successful write persisted. A repo-wide link check catches it, which is
how this one surfaced.

**The shell can be wedged for a whole session, with the file tools still
working.** Observed 2026-08-27: every `mcp__workspace__bash` call — including
`echo ok` — failed with

```text
RPC error: ensure user: useradd failed: exit status 12:
useradd: cannot create directory /sessions/<name>
```

on five consecutive attempts, and did not recover. `Read`, `Write`, `Edit` and
`Grep` over `/Users/…/my_programs/fux` were unaffected throughout.

- **What this costs is precisely the things that are not file *content*:** no
  `git` (so no ground-truth check against `git log`/`status`/`tag`), no
  `pytest`, and **no `mv`** — which removes even the `_to_delete/` workaround
  above, because the file tools have no rename and no unlink. A session in this
  state **cannot remove a file by any means.**
- **Do not retry past two attempts.** The failure is identical every time and
  the harness itself stops offering after five.
- **Say it in the deliverable, not just in chat.** The hazard is a session that
  writes documentation asserting a deletion or a green suite it had no way to
  perform. Write the docs as *ruled, pending a command Arpit runs*, and hand him
  the exact command.

**It has no network and Python 3.10.** fux-engine needs ≥3.11 and installs
from PyPI, so **the test suite and `fux-lab`'s `setup.sh` cannot run here.**
Run them in the cloud container (network + 3.11) or in a local terminal.
`pytest` is not installed on the VM; a pure-stdlib script can stand in for a
single test file, but that is a spot check, not a suite run.

**No `gh`, and the fux remote is SSH** (`git@github.com:arpitarya/fux.git`).
Push and PR are not possible from a Cowork session at all: the cloud container
has the network but not the key, the device has the key but not the network.
**Write the files, then hand Arpit the commit/push command.**

---

## macOS vs CI — the case-insensitivity trap

The macOS filesystem is case-**insensitive**. A link written as
`docs/glossary.md` resolves locally and 404s on GitHub, on Linux, and for
anyone using a case-sensitive volume. A link checker run on the Mac will call
it healthy.

Observed 2026-08-18: an automated link repair "fixed" a reference to
`GLOSSARY.md` by pointing it at `glossary.md`, and every local check passed.

**Rule:** verify link case against the actual filename, not against whether
the path opens.

---

## The measurement lab

`~/my_programs/fux-lab/` is the measurement environment. It is **scratch and
commits nothing** — what survives a run is what lands in
[`regression/`](regression/README.md).

**Never delete or rebuild it.** New test work is a new *environment* inside it
(`shared/new-env.sh <name>`), because the existing environments' baselines
(`1k/`, `5k/`, `10k/`, `acme`, `rfc`) are what a new number is measured
against. Environments are already isolated — own venv, corpus, results,
version pin — so replacing one buys nothing and costs every baseline.

`shared/` is common to every tier, so a bug there corrupts all tiers
identically. When a quality number looks surprising, hand-verify
`_score_pairs()`'s matcher on one known-good hit before believing it.

**Byte budgets and quality metrics are deterministic and comparable across
machines. Wall-clock is not** — never compare a latency measured on one
surface to one measured on another.

---

## Merge and release

- **There are no required status checks on `main`.** `enforce_admins: true`,
  no force-push, no deletion — history is protected, quality is not. Read
  `gh pr checks <n>` yourself and do not merge on red.
- Releases publish to PyPI as `fux-engine`. `v0.31.x` was tagged but never
  published; its work shipped inside `v0.32.0`.

## Windows is a first-class target

The design point is a Windows-first enterprise fleet, so Windows breakage is a
real defect, not an edge case — `v0.32.0` shipped a `fux doctor` crash fix
that only reproduced there. Nothing in the maintenance path may assume POSIX
paths, a case-sensitive filesystem, or a shell.

## Cowork remote bridge — `git status` leaves an undeletable `index.lock`

**Surface:** Cowork session reaching the repo through the remote-devices bridge
(`device_bash`), 2026-08-22.

**Symptom.** Any git command that refreshes the index — `git status`,
`git diff` — prints:

```
warning: unable to unlink '.../.git/index.lock': Operation not permitted
```

and **leaves the lock file behind**. Every subsequent git write then fails with
`Unable to create '.git/index.lock': File exists`.

**Cause.** The bridge's shell blocks `unlink`/`rm` by design. Git creates
`index.lock` while refreshing, then cannot remove its own lock.

**Fix — use the read-only form:**

```bash
git --no-optional-locks status --porcelain    # leaves no lock
```

**If a lock is already stranded**, it cannot be deleted from this surface —
`mv` it aside instead:

```bash
mkdir -p .git/_stale_locks
mv .git/index.lock .git/_stale_locks/index.lock.stale
```

**Verify it is actually stale before moving it** — a lock held by a live git
process is not stale, and this repo is edited by concurrent sessions. A 0-byte
lock whose mtime matches a `git status` you just ran is yours.

⚠ **`git mv` strands one too, and there is no read-only form of it** (2026-08-26,
W-84). `git mv work/open/W-84… archive/open/W-84…` failed with the file not yet
tracked, and left the same undeletable `index.lock` behind on the way out —
so a session retiring a **new, untracked** detail file into `archive/open/`
gets the worst of both: no move, and a locked repo.

**Use a plain `mv` for an untracked file.** Git records the move at
`git add` time from the paths, not from having been told; `git mv` buys nothing
here and costs a lock.

```bash
mv work/open/W-nn-….md archive/open/     # untracked: plain mv, no lock
```
