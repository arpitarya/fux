---
type: Compare Doc
title: The lock — one file or two
description: Arpit asked for a lock file whenever the index is updated, and for a committed list of what still needs enrichment. Those are two artifacts with opposite lifetimes and opposite git status. This fork decides whether they merge, and what the existing runner.lock's contract should be.
status: proposed
timestamp: 2026-08-26T00:00:00Z
---

# The lock — one file or two

> **VERDICT: B — TWO FILES, AND NEITHER IS NEW.** Proposed by the session,
> **not yet decided by Arpit.**
>
> The mutex and the manifest are **separate artifacts, separately named, in
> separate records**, because they are opposite on the one axis that matters
> most in this repo: **one must be gitignored, the other must be committed.**
>
> Neither is invented here. The mutex is
> [`maintain/runner.py`](../../src/fux/maintain/runner.py)'s `runner.lock`,
> already `O_CREAT|O_EXCL`, already pid-based — what changes is **who is
> required to hold it**. The enrichment pin is `.fux/enrich/<sha>.md`, already
> committed, already sha-validated ([ADR-ENRICH](../../docs/adr/0040_enrich.md)) —
> what is missing is the **queue** of work not yet done, and a **gitignored
> progress file** beside it (Arpit, 2026-08-26: *"committed queue, gitignored
> progress"*).
>
> **Neither file may be called `fux.lock`.** That name belongs to the archived
> engine's manifest and is listed out-of-scope in `CLAUDE.md` pending its own
> ADR; reusing it makes every archived reference read as if it described this.
>
> **Confidence:** high on rejecting A (merge) and E (OS advisory locks) —
> both are structural arguments, not judgement calls. **Medium** on the
> widening in B, which asserts a race nobody has yet reproduced (§6).
>
> **Reopen when:** a consumer runs `fux` against a repo on a **network
> filesystem** (NFS, SMB, a mounted enterprise home directory). `O_EXCL` is
> documented as racy on NFS, so the pid-file mutex stops being sound the day
> that is a supported surface — and it is checkable today by asking where a
> pilot's repo lives.

---

## 1 · Context — what Arpit asked, and what is already there

Two requests, in one breath:

1. **A committed list of what needs enrichment.** *"anything that needs
   enrichment, create a log file … in `.fux` … which will maintain a list of
   what all thing needs to be enriched."*
2. **A lock.** *"Lock file would be a good idea whenever index or anything
   related to index is getting updated and would have an impact."*

He was then asked whether "lock" meant a mutex or a manifest, and answered:
**both, possibly the same file — research it and make the call.** This is
that call.

**What the repo already has**, re-derived from the code rather than from a doc:

| thing | where | status |
|---|---|---|
| an index write mutex | `maintain/runner.py::acquire` — `runner.lock`, `O_CREAT\|O_EXCL`, pid inside | **built**, but held by *one* caller (§6) |
| stale-lock handling | `ingest/__init__.py::_report_takeover` — `stopped` / `stale` / `wedged` | **built** |
| a committed enrichment pin | `.fux/enrich/<sha>.md`, one file per source content sha | **built** ([ADR-ENRICH](../../docs/adr/0040_enrich.md), [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md)) |
| coverage reporting | `enrich.py::plan` / `--check`, `validate()`, `prune()` | **built** |
| a committed **queue** of undone work | — | **absent** |
| **gitignored progress** | — | **absent** |

So the question is smaller and sharper than it looked: not *invent a lock*,
but **decide whether the two concepts share a file, and widen the contract of
one that exists.**

---

## 2 · The options

| | option | shape |
|---|---|---|
| **A** | **one file, both jobs** | a single `.fux/fux.lock` that both pins enrichment provenance and serves as the write mutex |
| **B** | **two files, neither new** ✅ | widen `runner.lock` to *every* index writer; add a committed `queue` + gitignored progress beside the existing `.fux/enrich/` pins |
| **C** | two files, but a **new** mutex | leave `runner.lock` to the background runner; add a second, separate foreground lock |
| **D** | **no mutex widening** | the runner's lock is enough; two concurrent foreground `fux ingest` runs are the user's problem |
| **E** | **OS advisory lock** | `fcntl.flock` / `msvcrt.locking` instead of a pid file |

---

## 3 · Why A is rejected — they are opposite on every axis

| axis | the mutex | the manifest / queue |
|---|---|---|
| **git** | **must be gitignored** — a committed mutex means a fresh clone appears permanently locked | **must be committed** — its entire purpose is that a teammate reproduces the same ingest |
| lifetime | milliseconds to minutes, held across one write | permanent; it is a record |
| **L3** | irrelevant — never read by ingest | **central** — it is the pin that makes model output deterministic |
| L2 | a pid; no content | paths + shas + a reason; **no content, and that must be enforced** |
| failure mode | a stale lock **blocks loudly** | a drifted queue **ingests silently** |
| who reads it | the process about to write | `fux ingest`, `fux enrich`, and every teammate's clone |
| deleting it | routine and safe | destroys reproducibility |

**The decisive line is the first one.** A file that is committed in some
states and gitignored in others is precisely the defect `.fux/.gitignore`
warns about in its own comment — *"NEVER add `*` here … a blanket ignore would
drop them from git silently."* A merged file would need a rule that half its
content is committed, which no `.gitignore` can express.

**Second, and independent:** merging puts a model-provenance record on the
hot path of a mutex acquired under `O_EXCL` in a single syscall. The mutex is
correct *because* it is one atomic create of a file nobody parses for meaning.

---

## 4 · Why E is rejected — and the code already argues it

`runner.py` §"Single writer, and why the lock is a pid rather than an OS lock"
makes the case, and it is right:

> An OS-level advisory lock (`fcntl.flock`, `msvcrt.locking`) would release
> … an flock is held by a file descriptor nobody outside the process can name.

Three consequences, all against E:

- **`fcntl` is POSIX-only and `msvcrt` is Windows-only** — two code paths under
  **L1**, for one behaviour. `CLAUDE.md`'s deployment filter is Windows-first
  fleets, so neither path is the "rare" one.
- **An flock is invisible.** `fux doctor` cannot report it, a user cannot
  inspect it, and the `wedged` error message cannot name a path to delete.
- **The cost of a pid file is a stale lock**, and the answer to that is
  already built and already correct: report it, name the path, let a human
  clear it — *"never a background process silently deciding a lock is dead."*

E is also what the third-party ecosystem exists to paper over (`filelock`,
`portalocker`), and **L1 forbids the dependency** that would make it pleasant.

> ⚠ **Reconciled 2026-08-26, the same day, against
> [W-86](../open/W-86-the-decoder-plane.md) §12.** Arpit ruled that a
> **consumer** may add dependencies fux's runtime may not — the third row of
> ADR-ENRICH decision 1's table. **That ruling does not reach this rejection,
> and the distinction is the point:** a decoder is consumer code loaded from
> `.fux/`, while the index write mutex is **`src/fux/` runtime code on the
> maintenance path**, where L1 is untouched. `filelock` stays refused.
>
> **Rejections (a) and (b) above never depended on L1 anyway** — two platform
> code paths, and a lock nothing can name or report. They stand alone. This
> note exists because a later reader who knows about §12 would otherwise read
> §4 as stale, and **a record that looks stale gets "fixed" by someone who
> then reverses a correct call.**

---

## 5 · Why D is rejected — a measured hazard, on this machine

The repo's own [`MACHINE.md`](../MACHINE.md) records the failure mode:

> the remote bridge leaves an undeletable `.git/index.lock` … every later git
> *write* fails.

That is git's lock, not fux's, but it is the same class of event on the same
surface, and it cost a stranded lock before it was diagnosed. A tool that
writes an index on a machine where **two agent sessions edit one tree
concurrently** — the standing hazard in `CLAUDE.md` — does not get to treat a
second writer as hypothetical.

---

## 6 · The gap B actually closes ⚠

**`acquire()` has exactly one caller.** Grepped, not assumed:
`maintain/runner.py` claims the lock inside `run_once` and the detached runner.

**A foreground `fux ingest` never calls it.** It calls `request_stop` — it
*evicts* a background runner, then writes **without holding anything.**

Which means, today:

```
terminal 1:  fux ingest      # writes .fux/index/
terminal 2:  fux ingest      # also writes .fux/index/ — nothing stops it
```

⚠ **This is asserted from call-site reading, not reproduced.** It is written
here as the claim B rests on so that a build has to falsify it first — the
pre-registration discipline applied to a defect rather than a threshold.

**One more thing found on the way**, and it is deliberate for a runner and
wrong for a writer:

```python
except OSError:
    return False  # read-only or full filesystem: degrade, never block
```

A background runner that cannot take the lock should decline quietly. A
**foreground writer** that cannot take the lock and then writes anyway has
inverted the point of the lock. B must split these two behaviours; today they
are one line.

---

## 7 · What B is, concretely

**The mutex** — `.fux/runtime/…`, gitignored **by construction** (`runtime/`
is the only entry in `.fux/.gitignore`), so it cannot be committed by
accident. Not by a rule someone has to remember.

- Every command that **writes the committed index** takes it: `ingest`,
  `build`, `add`, `remove`, `update`, `enrich` when it writes pins.
- Read verbs (`ask`, `find`, `answer`, `graph`) take **nothing**. A lock on
  the read path would make a search fail because a re-index was running.
- ⚠ **Sub-fork for Arpit, not taken here:** the file is named `runner.lock`,
  and after the widening a foreground `fux ingest` holds a file whose name
  says *runner*. `write.lock` is truer; `index.lock` collides with git's, in
  a repo where the two sit feet apart. **Renaming touches a user-facing error
  string.** Recommendation: `write.lock`.

**The queue** — committed, and it exists because of the decoders
([W-86](../open/W-86-the-decoder-plane.md)): a decoder that meets an image or a
scanned PDF **has no way today to say "a model must read this."** It must
land somewhere durable, sorted, and deterministic (**L3**: sorted by path, no
wall clock), holding path + content sha + reason — **never content (L2)**.

**Progress** — gitignored, beside the mutex: which queued entries *this
machine* has processed. Arpit's split, and it is the right one — the backlog
is a team fact, the grinding is a local one.

⚠ **Edge case the build must check first:** `.fux/enrich/` is currently
globbed as `<sha>.md` and `prune()` deletes orphans in it. A queue file placed
in that directory must be proven invisible to both, or it lives elsewhere.

---

## 8 · Prior art (required)

- **[git's lockfile API](https://git-scm.com/docs/api-lockfile)** — the design
  B keeps: create with `O_CREAT|O_EXCL`, write beside, atomic `rename` to
  commit. Also the documented source of the **stale lock** cost, and of the
  **`O_EXCL`-on-NFS race** that is this doc's reopen-trigger.
- **[Azure Repos on `index.lock`](https://learn.microsoft.com/en-us/azure/devops/repos/git/git-index-lock?view=azure-devops)**
  — the enterprise-facing writeup of what a stranded lock does to a user, and
  the evidence that "delete it yourself" is a survivable contract at scale.
- **[`filelock`](https://py-filelock.readthedocs.io/en/latest/)** and
  **[`lockfile`](https://docs.openstack.org/pylockfile/latest/)** — the
  ecosystem that exists to hide `fcntl`-vs-`msvcrt`. Named to show what **L1**
  costs us here, and that the cost is small because the pid file is sound on
  local filesystems.
- **`Cargo.lock` / `uv.lock` / `package-lock.json`** — the *manifest* sense of
  "lock": a committed pin of resolved inputs so a build reproduces. This is
  what `.fux/enrich/<sha>.md` already is, distributed across files instead of
  gathered into one, and it is why the word "lock" collided in the first place.
- **[`MACHINE.md`](../MACHINE.md)** — the measured stranded-lock incident on
  the Cowork bridge, on this repo.

---

## 9 · What this doc does NOT decide

- **Whether `runner.lock` is renamed** (§7). Arpit's.
- **The queue's file format** — `.tsv`, `.json`, or one-line-per-entry in the
  `sources` grammar. W-86's build question, and it follows the grammar
  decision, not this one.
- **Whether `fux enrich` consumes the queue or keeps computing scope on
  demand.** ADR-ENRICH decision 4 makes scope *declared*; a queue is derived
  from a decode failure, which is a different origin. **Naming the tension is
  the point; resolving it is ADR-ENRICH's amendment, not this fork's.**
