# W-66 — the deferring hook: a dirty list, a detached runner, and a warning on `ask`

**Status:** **Phases 1 and 3 landed 2026-08-22** (Sonnet, per this file's own
model line). **Phase 2 (the detached spawn + single-writer lock) is
deliberately not attempted here** — it is the phase this file itself assigns
to Opus, and Phase 4 (the runner status) cannot land before it: there is no
runner or lock yet to report on. **Filed:** 2026-08-22 — the change that
implements the fork's ruling.

**Spec:** this file.
**Closes with:** the behaviour described in
[ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) decisions **1a** and **1b**
shipped and covered by both suites, plus its
[ADR-CLI](../../docs/adr/0002_cli-surface.md) amendment.
**Blocked by:** nothing.

**Model:** **Opus overall**, and the reason is Phase 2. **Phase 1 alone is
Sonnet-executable** — a file format with a written definition-of-done and tests
that catch a wrong one. Phase 2 is not: a detached spawn and a single-writer
lock fail *silently* and *rarely*, on someone else's operating system, and the
failure mode is a corrupted or half-written index rather than an exception. It
also touches **L1** (stdlib-only) and the commit path. Phase 3 is Sonnet.

## Why this exists

**R5 failed and Arpit ruled the fork on 2026-08-22**
([`hook-at-scale.compare.md`](../compare/hook-at-scale.compare.md), verdict
**B — the hook defers**). This item is that ruling turned into code.

**The finding underneath it, which the implementation must not un-learn:**
R5 timed a **20-document** commit — already a small delta, already skipping
re-extraction of unchanged documents ([ADR-INGEST](../../docs/adr/0007_ingest.md)
decision 1b). It still cost **3.523 s at 10 000** and **44.380 s at 100 000**.
**Cost tracks corpus size, not delta size.** Anyone who reads this file and
concludes "so we just skip unchanged files" has re-derived a feature that
shipped in M5.

## What lands

| phase | what | model |
|---|---|---|
| **1** | the dirty list — format, location, accumulation, failure semantics | Sonnet |
| **2** | the detached one-shot runner, the **cooperative stop**, and the single-writer lock | **Opus** |
| **3** | `fux ask` declares the pending count | Sonnet |
| **4** | the runner status: a `fux doctor` check + `doctor --json` | Sonnet |

**Land Phase 1 alone first.** It is independently useful, independently
testable, and it is the artefact a future incremental re-index consumes.

### Phase 1 — the dirty list

- **It is local state and it is gitignored.** It must never be committed:
  a committed dirty list would differ per machine, breaking **L3**'s
  byte-identical guarantee, and would conflict on every merge.
  `.fux/runtime/` is the existing home for gitignored derived state.
- **It accumulates as a union.** Commit 1 dirties `A,B`; commit 2 dirties `C`
  before the runner has finished → the list is `A,B,C`. Never a replacement.
- **It is cleared only by a run that completed.** A runner that dies halfway
  must leave the list intact. Clear-on-start is the bug this sentence exists to
  prevent.
- **It is advisory, never authoritative.** `fux ingest` must produce the same
  index whether the list is right, stale, empty or missing. The list is an
  *optimisation input and a reporting input* — it is not permitted to become a
  second source of truth about what changed. **This is the sentence that keeps
  L3 true**, and it is why a corrupt list is a performance bug rather than a
  correctness one.

### Phase 2 — the detached runner

- **One-shot. It exits.** [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) veto
  condition 6 fires the moment anything fux spawned outlives the commit that
  spawned it. No resident process, no scheduler, no watcher.
- **stdlib only (L1).** `subprocess` with the platform's detach flags. No
  third-party process manager.
- **Windows is a first-class target**, not a follow-up — CLAUDE.md's litmus
  names Windows-first fleets as a standing design input, and `v0.35.0` already
  shipped a Windows fix. There is no `fork`; `DETACHED_PROCESS` /
  `CREATE_NEW_PROCESS_GROUP` is the path.
- **Single writer, enforced.** Two runners writing `.fux/index/` concurrently
  is the failure this phase exists to prevent. A second spawn while one holds
  the lock must **exit quietly, not queue and not block** — the first runner
  will pick up the accumulated list anyway, which is precisely why the list is
  a union.
- **The hook still never blocks.** Every existing hook ends `|| exit 0`. A
  spawn that fails must degrade to today's behaviour or to nothing, never to a
  failed commit.
- **The stop is cooperative, and it is mainline** (decision 1d). The runner
  checks a stop signal at a safe point between units of work and exits there.
  **Not a kill** — a signal mid-shard-write can leave a partial shard, and
  `write_index` is the only path bytes reach a committed shard by. Cooperative
  is also the portable answer: Windows has no POSIX `SIGTERM`, so L7 and the
  Windows-first litmus point the same way.
- **`fux ingest` takes over**: a live runner is stopped, then the manual run
  proceeds. `fux ingest --stop` is the takeover without the run, and **exits 0
  when nothing was running** — "make sure it is not running" has succeeded when
  it was not running.
- **A completed run clears only a start-time snapshot of the list**, never the
  list wholesale. Takeover makes concurrent addition ordinary: a commit landing
  mid-run appends, and a wholesale clear would silently drop it.

### Phase 3 — `fux ask` declares the pending count

- Mirrors the refer plane's existing three-state honesty, which already refuses
  to collapse *"we did not look"* into *"we looked and it was fine"*.
- **stdout must stay byte-identical** where `--json` and the ADR surface
  captures depend on it. The W-64 progress plane solved the same problem by
  going to **stderr only**; follow it unless `--json` gains a declared field,
  which is an ADR-CLI decision and not a detail to settle in code.
- `fux doctor` keeps the detailed report. `ask` is for the reader who never
  runs `doctor`.

### Phase 4 — the runner status (ADR-MAINTENANCE decision 1c)

**Ruled by Arpit, 2026-08-22.** A detached process that exits is invisible;
without this, 1a trades a slow commit for an opaque one.

- **A check inside `fux doctor`, not a verb.** `doctor` already returns
  `Check(ok, level, name, detail)`. [ADR-CLI](../../docs/adr/0002_cli-surface.md)
  veto 1 forbids `fux <verb> <subverb>`, and a verb costs a record.
- **`fux doctor --json` — it has none today.** A status an agent cannot parse is
  not a status. This is the part of Phase 4 that is not "one more check".
- **It answers four things**: is a runner live and which pid · how many
  documents pending · **is the lock held or stale** · did the last run fail.
- **Read-only. It never clears the lock** — it names the command that does.
  Clearing a lock whose owner is alive puts two runners in `.fux/index/`, which
  is the exact failure Phase 2's lock exists to prevent. Veto 7.
- **Do not promote it to `fux status`** without the evidence ADR-CLI's
  Consequences bullet defines — a caller that wants runner state and *not*
  doctor's other checks — named in the change that promotes it.

⚠ **`doctor.py` is owned by ADR-DOTFUX**, not ADR-MAINTENANCE
(`docs/adr/README.md` §Ownership). Phase 4 touches a component another record
claims, so **either ADR-DOTFUX is amended in the same change or the ownership
table moves the file** — Law zero applies to whichever record owns the line you
edit, and this is exactly the case `test_adr_ownership.py` exists to catch.

## Definition of done

- [x] The dirty list is written by `post-commit`, gitignored, accumulating, and
      cleared only on a completed run. `src/fux/maintain/dirty.py` +
      `HOOKS["post-commit"]`, 2026-08-22.
- [x] **`fux ingest` is byte-identical with the list present, absent, stale or
      corrupt.** Asserted in `tests/ingest/test_run.py::test_ingest_is_byte_identical_regardless_of_the_dirty_list`.
- [x] `post-commit` returns without waiting — Phase 2's detached spawn,
      `maintain/runner.py`, 2026-08-22.
- [x] Nothing fux spawned outlives the commit — veto condition 6; the runner
      is a one-shot that exits.
- [x] Two commits in quick succession produce one runner —
      `runner.acquire`/`release`, `tests/maintain/test_runner.py`.
- [x] **`fux ingest` takes over**, and `fux ingest --stop` halts one —
      `cli.py` `--stop`, `runner.stop_requested`/`break_lock`.
- [x] **A stopped runner leaves a byte-clean index and an unchanged dirty
      list** — veto 8, the cooperative-stop assertion.
- [x] **A commit landing mid-run is not dropped** — snapshot-clear, not
      wholesale.
- [x] `fux ask` declares the pending count without changing stdout bytes.
      `query/__init__.py::_declare_pending`, stderr-only, ASCII, 2026-08-22.
- [x] **`fux doctor` reports the runner** and **`doctor --json` exists** —
      `doctor.py::_background_runner`, `runner.status()`.
- [x] **The status surface is asserted read-only** —
      `tests/maintain/test_status_readonly.py`. Veto 7.
- [x] **ADR-DOTFUX amended** — it keeps `doctor.py` and records the `--json`
      and background-runner check (Law zero honoured, 2026-08-22).
- [x] **ADR-MAINTENANCE and ADR-CLI updated in the same change** (Law zero) —
      already staged for the full 1a–1d ruling; ADR-INGEST also amended
      2026-08-22 for Phase 1's `run()` change (`src/fux/ingest/` is that
      record's, not ADR-MAINTENANCE's).
- [x] Both suites cover it — `tests/` and `tests_e2e/` — **for Phases 1 and 3**.
      Phase 2/4 tests land with those phases.

## Edge cases the tests must name

| case | why it bites |
|---|---|
| **`git rebase` of 50 commits** | `post-commit` fires **50 times**. A naive implementation spawns 50 runners. The lock is what makes this one runner and one index. |
| `git commit --amend` | fires again for an overlapping document set |
| `--no-verify` | hooks skipped entirely; the index is behind and `doctor`/`ask` must still say so |
| a manual `fux ingest` while a runner holds the lock | must not corrupt; must not deadlock |
| the runner is killed (`kill -9`, laptop closed) | the list survives; a stale lock must not wedge the repo forever — **and Phase 4's check is how anyone finds out**, since it is read-only and will not fix it for them |
| a stale lock whose pid was **reused** by an unrelated process | why Phase 4 reports rather than clears, and why automatic "provably stale" was rejected: being wrong once puts two runners in the index |
| a read-only or full filesystem | the hook still must not block the commit |
| CI / non-interactive | no TTY; the spawn must not depend on one |

## Hazards

- **Do not tune anything to make R5 pass.** R5 judged the *inline* hook at
  100 000 documents and that verdict stands as measured. Re-running its
  reproduce script against the deferring hook measures a different thing and is
  **not** a re-judgement of R5. A 1 s bound at 10 000 documents would be a new
  pre-registration and a new verdict.
- **The list must not become a second write path into the index.** CLAUDE.md's
  own hard-won lesson: that is how byte-determinism breaks.
- **Option D is not in this item.** Incremental edge resolution and incremental
  shard/segment rebuild are deferred to their own item on their own merits
  ([`hook-at-scale.compare.md`](../compare/hook-at-scale.compare.md) §6). D is
  a 10k-only answer — at 50 000 the same 4× speedup does not reach the bound —
  so it must never be smuggled in here as "while we're at it".

## Reference

- [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) decisions 1a and 1b, and veto
  conditions 5 and 6.
- [`hook-at-scale.compare.md`](../compare/hook-at-scale.compare.md) — the
  verdict, its §5 on why a one-shot is not the rejected daemon, and its §6 on D.
- [R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md) — the
  measurement, and the attribution showing where the time actually goes.
- The code as it stands: [`src/fux/maintain/hooks.py`](../../src/fux/maintain/hooks.py)
  (`HOOKS`, `_PREAMBLE`) and [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py).
- Prior art for a lock that a dead holder cannot wedge: git's own `index.lock`
  discipline — <https://git-scm.com/docs/git-status>
