---
type: Compare Doc
title: The Hook at Scale — Where a Re-index Runs When the Corpus Is Large
description: R5 failed at 100 000 documents (44.4 s against a 1 s bound), firing ADR-MAINTENANCE veto condition 1. Four viable responses were compared against the measured attribution. RULED 2026-08-22 by Arpit — B, the hook defers, in its detached-runner variant: post-commit writes a dirty list and spawns a one-shot re-index, and `fux ask` declares the pending count.
status: accepted
timestamp: 2026-08-20T00:00:00Z
---

# The hook at scale — Comparison

> ## VERDICT — **B, the hook defers.** Ruled by Arpit, 2026-08-22.
>
> `post-commit` **writes a list of the documents that changed and returns.**
> The re-index runs out of band; `fux doctor` already reports a stale index,
> and `fux ask` now **declares the pending count on the answer**, so the lag is
> announced rather than merely discoverable.
>
> **Three things Arpit settled, in his words and not to be re-litigated:**
>
> 1. **A dirty *list*, not a dirty *flag*.** The hook records *which* documents
>    changed. That is what makes option D a later increment rather than a
>    rewrite: D consumes exactly this list.
> 2. **A detached one-shot runner, not lazy-on-next-use.** The hook spawns a
>    re-index that runs to completion and exits. See §5 on why this is not the
>    watch daemon `maintenance-trigger.compare.md` rejected.
> 3. **`fux ask` warns on the answer** when documents are pending, mirroring the
>    refer plane's existing three-state honesty — which already refuses to
>    collapse *"we did not look"* into *"we looked and it was fine"*.
>
> **Rejected:** **A — accept a documented ceiling** (honest, but it makes the
> flagship maintenance feature unavailable at the corpus size the whole plan is
> designed for); **C — move to `pre-push`** (does not change the cost, only how
> often you pay it, and it makes the *push* the thing that hangs).
> **D — make the corpus-wide passes incremental** is **not rejected**: it is
> deferred to its own item on its own merits, and this verdict is deliberately
> shaped to feed it. See §6.
>
> **Filed:** 2026-08-20. **Ruled:** 2026-08-22.
> **Builds under:** W-66.
> **Reopen when:** a re-run of R5 against the frozen pre-registration passes at
> 100 000 documents under this option, or the deferred re-index is observed
> answering a query from an index the checked-out commit does not match.

## §0 — Re-scoped 2026-08-21: the design point moved, the fork did not close

**Arpit moved the design point to 10 000 documents** (CLAUDE.md §Litmus) and
ruled that **this fork stays open at lower urgency**. Three things follow, and
the third changes the option set.

**1. R5 still fails.** At 10 000 documents a 20-document commit costs
**3.523 s against the 1 s bound** — 3.5× over. It passes only near ~1 500.
Shrinking the target did not close this; it made it a 3.5 s problem instead of
a 44 s one.

**2. The frozen instrument is not edited.** R5's pre-registration judges at
100 000 documents and **a pre-registered threshold may never move**. The
100 000-document FAIL stands as measured. If the bound is to be re-judged at
10 000, that is a *new* pre-registration and a *new* verdict — never a rewrite
of this one. Nothing in this document restates a measurement.

**3. §4's arithmetic no longer rules D out — this is the real change.**
That table was computed at 100 000 documents, where the two O(corpus) passes
are 41.1 s of a 41.4 s commit and a 100× speedup is the only thing that
reaches the bound. **At 10 000 documents the fixed cost is 0.216 s** (git
0.190 + spawn 0.026) **and the two passes are 3.103 s**:

| hypothetical, judged at **10 000** | commit | vs the 1 s bound |
|---|---|---|
| today | 3.32 s | 3.3× over |
| both passes 2× faster | 1.77 s | 1.8× over |
| both passes **4× faster** | **0.99 s** | **passes, barely** |
| both passes 10× faster | 0.53 s | passes |
| both passes off the commit path (B) | 0.22 s | passes |

**A 4× improvement in two stdlib passes is a plan; a 100× one was not.** So at
the new design point **D — make the corpus-wide passes incremental — becomes a
live option**, where at 100 000 it was arithmetically dead. B still wins on
holding at every size and on not needing the speedup at all; D now competes on
keeping the index/tree agreement window tight, which is B's one real cost.

**What this section did not do:** it did not change the proposed verdict, and
it did not re-run the matrix. **Both were left to Arpit, and he ruled on
2026-08-22** — B, in its detached-runner variant. The matrix *has* now been
re-weighted off `holds at 10⁶ (×3)` and onto the 10 000-document design point
with 50 000 as the next staged target, in that same change, as this section
required.

## Context — what fired this

[R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md), 2026-08-20:
**FAIL**. A 20-document commit through the `post-commit` hook costs

| corpus | max | vs the 1 s bound |
|---|---|---|
| 1 000 | 0.651 s | passes |
| 10 000 | 3.523 s | 3.5× over |
| **100 000** | **44.380 s** | **44× over** |

[ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) veto condition 1 states the
consequence in its own words: *"`post-commit` is too slow to be automatic and
the hook becomes opt-in or incremental in a way it currently is not."* **Which
of those** is the fork, and it has more than two viable answers, so it is here
rather than assumed in a commit.

**This is not a re-litigation of
[`maintenance-trigger.compare.md`](maintenance-trigger.compare.md).** That
document chose *git hooks* over CI, a watch daemon and manual, and nothing
measured here disturbs that choice — the hook is still the right trigger. What
is in question is what the hook **does when it fires**.

## The measurement every option is judged against

Medians of three, hook uninstalled so each part is timed alone
([`attribute.py`](../../tools/maintenance-bench/attribute.py)):

| corpus | `git` | `ingest` (delta) | `derive` | `spawn` | sum |
|---|---|---|---|---|---|
| 1 000 | 0.183 s | 0.231 s | 0.270 s | 0.027 s | 0.711 s |
| 10 000 | 0.190 s | 1.318 s | 1.785 s | 0.026 s | 3.319 s |
| **100 000** | **0.340 s** | **21.325 s** | **19.726 s** | **0.038 s** | **41.429 s** |

Three facts the options turn on:

1. **Git is ~constant** — 1.9× across a 100× corpus. The commit itself is not
   the problem.
2. **Two O(corpus) passes are the whole cost**, split almost evenly (51.5 % /
   47.6 %).
3. **Delta ingest already took the per-document half.** The 21.3 s of `ingest`
   is *without re-extracting a single unchanged document*
   ([ADR-INGEST](../../docs/adr/0007_ingest.md) decision 1b). What remains is
   parse-everything, resolve-every-edge, write-every-shard.

## The options

### A — Accept a documented ceiling

`post-commit` stays as it is. The documentation states that automatic
re-indexing is for repositories up to ~1 500 documents, and above that the user
does not install the hook.

- **For:** zero work; nothing about the design changes; the honest reading of
  a measured limit.
- **Against:** the maintenance plane's headline capability is then absent at
  10⁵–10⁶ documents, which CLAUDE.md's litmus **then called** *the design
  point, not a stretch goal* (it moved to 10 000 on 2026-08-21 — W-65, 2026-08-22;
  §0 above already re-weighted the matrix, and this bullet is the one sentence
  that kept the old tense). "It works on small repositories" is what the archived engine
  could already do.

### B — The hook defers *(RULED 2026-08-22)*

`post-commit` writes a dirty marker and returns. The re-index runs out of band —
on the next `fux` invocation that needs a fresh index, or a background process
the user starts, or the next `pre-push`. `fux doctor` already reports a stale
index, so the lag stays visible.

- **For:** commit cost becomes git's cost — **0.34 s at 100 000 documents**,
  and constant in the corpus. It is the only option that reaches the bound at
  every size. The one-commit-lag argument that made `post-commit` correct
  ([ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) decision 1) is unchanged;
  the lag simply becomes *a few commits* instead of *one*.
- **Against:** the window in which the committed index disagrees with the
  checked-out tree gets longer and less predictable, and "out of band" needs a
  concrete mechanism — which is a real design question, not a detail.

> **Both of those were settled on 2026-08-22, and this paragraph is kept as
> written because it is what the fork looked like before the ruling.** The
> mechanism is a **detached one-shot runner** — *not* the lazy-on-next-use form
> this section guessed at, and *not* the watch daemon
> [`maintenance-trigger.compare.md`](maintenance-trigger.compare.md) rejected;
> §5 works through why the rejection does not transfer. The widened window is
> answered by **`fux ask` declaring the pending count**, which converts it from
> a silent lag into a stated one.

### C — Move the re-index to `pre-push`

The hook fires once per push instead of once per commit.

- **For:** far fewer events; the cost is paid when the user is already waiting
  on the network.
- **Against:** **it does not change the cost, only its frequency.** A push
  still hangs for 44 s at 100 000 documents, and a hang during a push is worse
  than one during a commit because a failed push leaves the question of whether
  the index went with it. It also breaks the property that a *local* commit
  carries its own index.

### D — Make the corpus-wide passes incremental

Resolve edges only for the dirty set; rebuild only the shards and runtime
segments the change touches.

- **For:** attacks the actual cost, and is valuable for `fux ingest` generally,
  not just for the hook.
- **Against:** **the arithmetic does not reach the bound** (§4). It also means
  giving up the property ADR-INGEST decision 1 keeps deliberately — a document
  that changed elsewhere can resolve an edge here — and the failure mode of
  getting it wrong is a *stale* index rather than a broken one, which nothing
  surfaces.

## §4 — Why D cannot be the answer on its own

| hypothetical | commit at 100 000 docs | vs the 1 s bound |
|---|---|---|
| today | 41.4 s | 41× over |
| both passes 2× faster | 20.9 s | 21× over |
| both passes 10× faster | 4.5 s | 4.5× over |
| both passes 100× faster | 0.79 s | passes |
| **both passes off the commit path (B)** | **0.38 s** | **passes** |

A 100× improvement in two mature, stdlib-only passes is not a plan. **D is
worth doing and cannot close this**; B closes it arithmetically and at every
size.

## §5 — Why the detached runner is *not* the daemon that was rejected

**This verdict was checked against
[`maintenance-trigger.compare.md`](maintenance-trigger.compare.md) before it was
taken, because that document is `accepted` and rejected an option that sounds
like this one.** It is not the same option.

| | **C — watch daemon** (rejected there) | **B's runner** (ruled here) |
|---|---|---|
| lifetime | always on, indefinitely | starts, re-indexes, **exits** |
| trigger | every file save, live | one commit |
| watches the filesystem | yes | **no** — the hook hands it a list |
| process to run and manage | **yes** | none between commits |
| helps the merge story | no | not its job — the driver already does |

Its three stated objections land on C and miss this:

1. *"Doesn't touch the merge-conflict problem"* — correct, and irrelevant:
   [ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md) owns that, and R6
   is ruled.
2. *"Requires an always-on background process this codebase has never needed"* —
   **this is the objection that does not transfer.** A one-shot that exits is
   not always-on. The matrix row below scores it `none` for that reason.
3. *"Does nothing for a contributor editing over SSH or on a machine where the
   daemon isn't running"* — the runner is spawned *by the commit*, so it runs
   wherever the commit happens. That is strictly better than a daemon.

**And that document did not close the door anyway.** Its own consequences say a
daemon *"is not eliminated forever — a plausible later layer on top of A"*.
This is less than that: not a layer, one process invocation per commit.

**What the sidestep does not buy:** a detached spawn still has to be
stdlib-only (L1) and still has to work on a Windows-first fleet, and two
commits in quick succession still need a single-writer discipline. Those are
W-66's problems and they are real; they are just not *this* objection.

## §6 — D is deferred, not rejected, and this verdict is shaped to feed it

The dirty **list** is the concession that makes D cheap later. D's definition —
*"resolve edges only for the dirty set; rebuild only the shards and segments the
change touches"* — needs exactly one input: the dirty set. B now produces it
and writes it down.

So the sequencing is **B closes this fork; D becomes its own item, judged on its
own merits**, and when it lands it makes the *runner* faster rather than
changing what the hook does. Two consequences worth stating:

- **The list alone buys no speedup.** The runner still calls today's
  `fux ingest`, which walks the corpus. B's win is that you are not waiting for
  it — not that it got smaller.
- **D's arithmetic is bounded.** At 10 000 documents a 4× speedup of the two
  O(corpus) passes reaches 0.99 s. At 50 000 — the next staged target — the
  same 4× does not: the passes scale to ~15.5 s and would need ~20×. **D is a
  10k-only answer; B is size-independent.** That asymmetry is why D could never
  have closed this fork on its own, at either design point.

## Matrix

**Re-weighted 2026-08-22 for the 10 000-document litmus, as §0 required of
whoever ruled.** The old `reaches the bound at 100k (×3)` and `holds at 10⁶
(×3)` rows are replaced by the design point and the *next staged target*; the
100 000-document FAIL stands as measured and is not restated here.

| criterion (weight) | A ceiling | **B defer** | C pre-push | D incremental |
|---|---|---|---|---|
| reaches the 1 s bound at **10k**, the design point (×3) | ✗ (3.3 s) | **✓ (0.22 s)** | ✗ | ~ (0.99 s at an unbuilt 4×) |
| **holds at 50k, the next staged target** (×2) | ✗ | **✓ — constant** | ✗ | ✗ (needs ~20×) |

> **This row is an ARGUMENT, not a measurement, and since 2026-08-22 it can only ever be one.** Arpit capped measurement at 10 000 documents, so nobody may go and bench 50 000 to settle it. B's ✓ is *structural* — commit cost becomes git's cost, which does not track corpus size — and D's ✗ is arithmetic from the measured 10k passes. **Both remain legitimate under the ceiling**, which forbids measuring a larger size, not reasoning about one. The verdict is unaffected: B also wins the 10k row outright, needs no unbuilt speedup, and is already shipped.
| index/tree agreement window (×2) | best | **worse — and now declared on the answer** | worse | best |
| implementation cost (×1) | none | **moderate** | low | high |
| keeps ADR-INGEST decision 1 (×2) | ✓ | **✓** | ✓ | ✗ |
| new always-on process (×2) | none | **none — one-shot, exits (§5)** | none | none |

## References

- The measurement — [R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md)
  and its [report](../regression/2026-08-20-r5-hook-latency/report.md) §3.
- The veto that fired — [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md)
  condition 1.
- The trigger choice this does **not** reopen —
  [`maintenance-trigger.compare.md`](maintenance-trigger.compare.md).
- Prior art for deferring index maintenance off the write path: Lucene's
  near-real-time segment model, where writes append and merging is a background
  concern rather than part of the commit —
  https://lucene.apache.org/core/9_0_0/core/org/apache/lucene/index/IndexWriter.html
- Prior art for lazy rebuild on next use rather than a daemon: Git's own
  `gc --auto`, which piggybacks maintenance onto the next command that would
  benefit — https://git-scm.com/docs/git-gc
