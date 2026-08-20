---
type: Compare Doc
title: The Hook at Scale — Where a Re-index Runs When the Corpus Is Large
description: R5 failed at 100 000 documents (44.4 s against a 1 s bound), firing ADR-MAINTENANCE veto condition 1. Four viable responses — accept a documented ceiling, defer the work off the commit, move it to pre-push, or make the corpus-wide passes incremental — compared against the measured attribution.
status: proposed
timestamp: 2026-08-20T00:00:00Z
---

# The hook at scale — Comparison

> **Proposed verdict: B — the hook defers.** `post-commit` records that the
> index is dirty and returns; the re-index runs out of band, and `fux doctor`
> already reports a stale index so the lag is visible rather than silent. It is
> the only option that reaches the bound at **every** corpus size, and it does
> so without touching the correctness argument that made `post-commit` the
> right hook in the first place.
> **Rejected:** **A — accept a documented ceiling** (honest, but it makes the
> flagship maintenance feature unavailable at the corpus size the whole plan is
> designed for); **C — move to `pre-push`** (cheaper per event, but it does not
> change the cost, only how often you pay it, and it makes the *push* the thing
> that hangs for 44 s); **D — make the corpus-wide passes incremental**
> (attacks the real cost, and **the arithmetic says it cannot reach the bound**
> — see §4; worth doing on its own merits, not as the answer here).
> **Status:** ⏳ **awaiting Arpit.** **Filed:** 2026-08-20.
> **Reopen when:** a re-run of R5 against the frozen pre-registration passes at
> 100 000 documents under whichever option is taken, or the deferred re-index
> is observed answering a query from an index the checked-out commit does not
> match.

## Context — what fired this

[R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md), 2026-08-20:
**FAIL**. A 20-document commit through the `post-commit` hook costs

| corpus | max | vs the 1 s bound |
|---|---|---|
| 1 000 | 0.651 s | passes |
| 10 000 | 3.523 s | 3.5× over |
| **100 000** | **44.380 s** | **44× over** |

[ADR-MAINTENANCE](../../docs/adr/0033_hooks.md) veto condition 1 states the
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
  10⁵–10⁶ documents, which CLAUDE.md's litmus calls **the design point, not a
  stretch goal**. "It works on small repositories" is what the archived engine
  could already do.

### B — The hook defers *(proposed)*

`post-commit` writes a dirty marker and returns. The re-index runs out of band —
on the next `fux` invocation that needs a fresh index, or a background process
the user starts, or the next `pre-push`. `fux doctor` already reports a stale
index, so the lag stays visible.

- **For:** commit cost becomes git's cost — **0.34 s at 100 000 documents**,
  and constant in the corpus. It is the only option that reaches the bound at
  every size. The one-commit-lag argument that made `post-commit` correct
  ([ADR-MAINTENANCE](../../docs/adr/0033_hooks.md) decision 1) is unchanged;
  the lag simply becomes *a few commits* instead of *one*.
- **Against:** the window in which the committed index disagrees with the
  checked-out tree gets longer and less predictable, and "out of band" needs a
  concrete mechanism — which is a real design question, not a detail. A
  background process is something this architecture has never needed
  ([`maintenance-trigger.compare.md`](maintenance-trigger.compare.md) rejected
  a watch daemon partly on those grounds), so the honest form of B is probably
  *lazy* rather than *background*: re-index on next use.

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

## Matrix

| criterion (weight) | A ceiling | **B defer** | C pre-push | D incremental |
|---|---|---|---|---|
| reaches the 1 s bound at 100k (×3) | ✗ | **✓** | ✗ | ✗ |
| holds at 10⁶ (×3) | ✗ | **✓** | ✗ | ✗ |
| index/tree agreement window (×2) | best | **worse, visible** | worse | best |
| implementation cost (×1) | none | **moderate** | low | high |
| keeps ADR-INGEST decision 1 (×2) | ✓ | **✓** | ✓ | ✗ |
| new always-on process (×2) | none | **none, if lazy** | none | none |

## References

- The measurement — [R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md)
  and its [report](../regression/2026-08-20-r5-hook-latency/report.md) §3.
- The veto that fired — [ADR-MAINTENANCE](../../docs/adr/0033_hooks.md)
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
