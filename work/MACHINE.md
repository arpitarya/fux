---
type: Runbook
description: "Environment and surface quirks: what breaks where, and the workaround."
---

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
| **Cowork device VM** (`device_bash`) | repo mounted at `$HOME/mnt/fux` | **none** | 3.10 | cannot delete; no `pytest`; **every call fails silently once its `/sessions` disk is full** — see below |
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
  that has to run here — `tests/test_sr_freshness.py` uses it for exactly this
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

**🔴 The silent shell failure is a FULL SESSION DISK — not a broken VM, and a
reinstall is the wrong fix.** Diagnosed 2026-09-12, and it explains every
earlier occurrence recorded below.

- **What the guest actually says**, in
  `~/Library/Logs/Claude/cowork_vm_node.log`:

  ```text
  Error: listen ENOSPC: no space left on device
         /sessions/rcw-<session>/tmp/srt-mux-3855-0.sock
  Error: Failed to create bridge sockets after 5 attempts
  ```

- **The VM is healthy the whole time.** `cowork_vm_swift.log` shows
  `guest_ready`, `Network: CONNECTED`, `API: REACHABLE`, boot in **1 971 ms**.
  What fails is the per-call **bridge socket**, created under `/sessions`.
- **`/sessions` is `sessiondata.img` inside the bundle**, and it fills up with
  accumulated per-session users — `coworkd` reported
  `user recovery complete: recovered=16` on the failing boot.
- ⚠ **The error never reaches the tool result.** `device_bash` returns only
  *"device_bash failed in the device workspace"*, which is why two prior
  sessions diagnosed a dead VM. **The cause is in the log, always — read it
  before concluding anything.**

**The fix, in order — no reinstall, no loss of app data or logins:**

```bash
osascript -e 'quit app "Claude"'; sleep 5; pkill -f "/Applications/Claude.app"
B="$HOME/Library/Application Support/Claude/vm_bundles/claudevm.bundle"
rm -rf "$HOME/Library/Application Support/Claude/vm_bundles.broken"   # dead weight
mv "$B/sessiondata.img" "$B/sessiondata.img.full-$(date +%F)"          # app recreates it
open -a Claude
```

- **`vm_bundles.broken` is reclaimable outright.** On 2026-09-12 it held
  **16 GB** beside 14 GB live — the app renames a bundle it has given up on and
  never collects it. Those two directories were **all 32 GB** of
  `Application Support/Claude`.
- ⚠ **A fresh disk leaves the CURRENT session broken — start a new one.** After
  the swap this session's calls turned into
  `EACCES: permission denied /sessions/rcw-<session>/tmp/…`: a session id
  carried over from the old disk lands on a freshly formatted one it does not
  own, and nothing outside the VM can chown it. **Two app relaunches did not
  clear it; a new Cowork task worked immediately.** Budget a new session as
  part of the fix, not as a failure of it.
- **A named error is good news.** Silent = full disk. `EACCES` and friends mean
  the VM is up and talking.

**Why "just reinstall the app" appeared to work, for three occurrences.** A
reinstall hands over an empty `sessiondata.img`. That is the *only* part of it
that mattered — the 32 GB wipe, the lost desktop project memory, the lost local
MCP config and scheduled tasks were all collateral, every time.

**The VM can fail to START AT ALL — a different failure from the wedge above,
and the tell is `scratchFolder`.** ⚠ **Superseded as a DIAGNOSIS on 2026-09-12** —
the section above has the real cause (a full `/sessions` disk, with the VM healthy
throughout). The observations below stand exactly as recorded; the conclusion that
the VM *never booted*, and the reinstall advice that followed from it, do not.
Observed 2026-09-06, in two consecutive
sessions: every `device_bash` call, `echo ok` included, returned

```text
device_bash failed in the device workspace.
```

with **no underlying error text at all** — nothing to grep, nothing naming a
cause. Unlike 2026-08-27's `useradd` message, there is no string to search for.

- ⚠ **`scratchFolder` does NOT prove the VM never booted** — it is reported only
  once `device_bash` has *succeeded* once, and a full-disk VM boots fine while
  never letting a single call succeed. Read `cowork_vm_node.log` for the cause;
  this bullet's original claim is kept below because the observation was real.
- **`get_device_info` is the diagnostic that separates the two cases.** It
  reports a `scratchFolder` field **only once `device_bash` has succeeded at
  least once in the session**. Absent field + failing shell = **the workspace
  VM never booted**. Present field + failing shell = the VM is up and the
  command itself failed. On 2026-09-06 the field was absent, which ruled out
  every command-level explanation before any were tried. **Make this the first
  move, not the fifth.**
- 🔴 **The bridge is NOT down, and assuming it is costs the whole session.**
  `get_device_info`, `device_list_dir`, `device_stage_files` and
  `device_commit_files` all worked normally throughout. The repo was fully
  readable **and fully writable**.
- **So a docs-only session still completes here** — unlike the 2026-08-27
  wedge, which had no write path. `device_commit_files` writes whole files, so
  any document can be updated by **stage → rewrite in the cloud container →
  commit back to the same path**. There is no in-place edit and no append: a
  change to an 800 KB file means rewriting all of it, which is fine as a shell
  operation in the container and ruinous if you try to read it into context
  first. What stays impossible is everything that is not file *content* — no
  `git`, no `pytest`, no `fux`, no `mv`, no delete.
- ⚠ **Restarting does not fix it — true, and now explained**: a relaunch remounts
  the same full `sessiondata.img`. Swapping that one file is what a restart was
  missing.
- **Restarting does not fix it, and this is worth knowing before spending an
  evening on it.** Arpit restarted the desktop app, restarted the laptop, and
  tried CLI scripts; the failure was byte-identical after each. The workspace
  VM image is per-**install**, not per-session, so a relaunch reuses the same
  broken image.
- ⚠ **The reinstall trap — and the deeper one.** A reinstall is not needed at all
  (see the 2026-09-12 section); what follows is why the *ordinary* reinstall
  people reach for also fails. On macOS, trashing the `.app` leaves
  `~/Library/Application Support` intact — so an ordinary reinstall most likely
  preserves the broken image *and* fixes nothing. The lever that rebuilds the
  VM is the same lever that deletes local app data: the desktop app's project
  memory, locally-stored scheduled tasks, and local MCP config. **Those are
  local-only; account-side things (chats, cross-surface memory, account skills)
  and the repo itself are untouched by any of it.** Rule out disk starvation
  first — it is the cheaper suspect and costs nothing to check.
- **Do not retry past two attempts.** The harness counts to five and the
  failure is identical every time.

⚠ **THIRD occurrence as of 2026-09-12** (2026-08-27, 2026-09-06, 2026-09-12) of
the class "the shell is wedged for a whole session while the file tools keep
working". The 2026-09-12 pass is the first that found a cause, and the gate it
earns is a **procedure**: read `cowork_vm_node.log` before any other move. The
paragraph below records why nothing mechanical was written, and still holds.

⚠ **This was the SECOND recorded occurrence of the class "the shell is wedged
for a whole session while the file tools keep working"** — 2026-08-27 was the
first — which is what CLAUDE.md's two-strikes rule makes a gate trigger.
**No check was written, and the reason is that this repo has nothing to
check:** the fault is in a VM fux does not ship, reached through a tool fux
does not own, and a test asserting "`device_bash` works" can only ever run on a
surface where it already does. The gateable part is a **procedure, not an
assertion** — the `scratchFolder` first move recorded above. Named here rather
than mechanised, on the same reasoning W-83's gate was.

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

## Two test invocations that fail for reasons that are not failures (2026-09-14)

**Both are surface quirks and neither is a defect in the code**, which is why
they live here rather than in `CLAUDE.md` (W-173).

| you typed | what happens | what to type |
|---|---|---|
| `node --test node/test` | `MODULE_NOT_FOUND` | `node --test node/test/*.test.mjs` |
| a hand-built test repo with no `.fux/pii.toml` | **every CLI verb refuses**, `ingest` included | `: > .fux/pii.toml` — an empty file is enough |

🔴 **`node --test node/test` reads as a test failure and is not one.** Without
the glob, Node resolves the bare directory as a **module path** rather than as a
test directory, so it reports a missing module — and a session that has just
changed the Node reader reads `MODULE_NOT_FOUND` as *I broke the reader*.

**The `pii.toml` refusal is by design** — [SR-PII](../records/0148_pii.md)
decision 17: a repository with no ruleset does not get to index anything, and
the gate sits before dispatch so a verb added later is covered without anyone
remembering. It costs one line in every fixture that builds a repo by hand, and
the alternative is a repo that silently indexes with no redaction policy.

⚠ **A test file that predates the rule is the likeliest thing to trip it**, and
the symptom is the same refusal on every verb rather than a message about
fixtures.

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

## 🔴 Two sessions on one machine destroy a benchmark run — silently, both ways (2026-09-12)

**It happened.** Two Claude Code sessions were running `fux-benchmark/bin/bench.py`
under the **same run id** (`2026-09-12-l9`) on the same Mac, neither aware of the
other. The damage is two separate kinds and the second is the one people miss.

**1. The files.** `cmd_latency` opens its row files with `open("w")`. The second
process **truncated the first's `latency-docs-10000-scan.csv` mid-write**, and
nothing warned either side — no lock, no error, no differing mtime anyone was
watching. The first session's docs-10000 rows were gone.

**2. The numbers, and this reaches rows nobody overwrote.** While one session
timed queries, the other was generating and indexing a 10 000-document corpus —
several sustained cores for two hours. **Every latency taken in that window is
high by an unknown amount, in both sessions' rows**, including the ones that
survived. The harness's own rule says it: *every timing in one run comes from one
machine in one session.* A second session breaks the second half of that sentence
while looking like it only broke the first.

🔴 **3. And contention does not merely inflate a number — it MANUFACTURES A
PLAUSIBLE ENGINE FINDING.** Reconstructed from both sides after the fact: the
timing session's whole window (13:29–14:23) sat inside the indexing session's
(≈13:00–15:10), so *no* corpus in that run was clean, and the split into "five
good tiers and two bad ones" was itself an artefact.

**The sharp case is the one that nearly got filed.** The 10 000-document tier's
**ingest ratio came out at 0.77 against ~0.46 at every other tier** — a clean,
specific, tier-localised anomaly, exactly the shape a real regression takes. It
was the run's one unresolved item. That tier was ingested 12:58–13:17, **inside
the other session's load**, and the honest reading is the machine.

**So the failure mode is not "the numbers look noisy".** Noise is visible and
gets distrusted. **This produced a quiet, internally-consistent result that
pointed at the engine**, and only a disclosure from the other session — *a
conversation, not a mechanism* — kept it off the record.

⚠ **Nothing detects this.** An owner-lock on `runs/<id>/` sees a neighbour in the
same run directory; **nothing sees a neighbour indexing ten thousand documents
next door.** That gap is real, unguarded, and larger than the collision that
exposed it. `SETUP-BENCHMARK` carries it as an unguarded gap rather than a solved
problem.

**What follows, and the ordering matters:**

- **A distinct run id fixes the file collision and NOT the contention.** It is
  the obvious fix and it is half a fix; a session that takes a fresh id and keeps
  timing is still sharing a CPU. ✅ **`bench.py` now opens its row files with
  `"x"`**, so a second run into the same id **fails by name** instead of
  replacing anything — the lock's own failure mode was silent, and a stale lock
  someone clears by hand put you straight back here.
- **Before timing anything, check for another `bench.py`** — `pgrep -f bench.py`
  — and for other heavy local work. Killing your own build is not enough if a
  peer is running one.
- **A killed run's partial rows are deleted, never kept.** They are contaminated
  in both directions and worth nothing.
- **Say what you were running, and when, to anyone who shares the machine.** The
  only thing that caught the false ingest finding was one session volunteering
  its load window to the other. Cheap, and there is no substitute for it.
- **The corpus is never touched.** Stop the **run**, delete its **rows**. Arpit,
  2026-09-12: the built corpora are kept and reused.

⚠ **This is the same failure class `CLAUDE.md` §Two hazards names for `work/*.md`
— *concurrent sessions are real* — on a surface its gate does not reach.** The
`PreToolUse` per-asset lock covers files this repo's agents `Write`/`Edit`; it
sees nothing a subprocess opens in a sibling directory. **A gate is being added
in `bench.py` by the session that was hit** (an owner-lock refusing a `runs/<id>/`
another live pid is writing); this entry is the record that the class recurred,
so the second occurrence is written down rather than re-learned.

⚠ **Ranked lists survive what latency does not.** They are deterministic, so a
contaminated session's `ranked-*.jsonl` is still comparable — which is why the
benchmark README calls them the half that survives a split session. Do not throw
them away with the timings unless they were truncated.

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
