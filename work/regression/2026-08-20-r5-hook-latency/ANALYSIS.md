# ANALYSIS — 2026-08-20, R5 and the cost of an automatic re-index

## The diagnosis

**A 20-document commit costs whatever touching the whole corpus costs**, and at
the size this plan is designed for that is 44 seconds against a 1-second bound.

The attribution says where, and it is not where a reader would guess:

| corpus | git | ingest | derive | spawn |
|---|---|---|---|---|
| 1 000 | 0.183 s | 0.231 s | 0.270 s | 0.027 s |
| 10 000 | 0.190 s | 1.318 s | 1.785 s | 0.026 s |
| **100 000** | **0.340 s** | **21.325 s** | **19.726 s** | **0.038 s** |

- **Git is not the problem.** Staging and committing twenty changed files out of
  100 000 rises only 1.9× across a 100× corpus, because git works from the
  index rather than the tree.
- **Process spawn is 38 ms** and irrelevant at every size.
- **Two O(corpus) passes are the entire cost, split almost evenly** —
  `fux ingest` 51.5 %, `fux build` 47.6 %.

**Delta ingest already took the easy half.** At 100 000 documents `ingest` costs
21.3 s *without re-extracting a single unchanged document*
([ADR-INGEST](../../../docs/adr/0007_ingest.md) decision 1b). What is left is
parsing every file, resolving every edge, and writing every shard — passes that
decision 1 keeps corpus-wide **on purpose**, because a document that changed
elsewhere can resolve an edge here.

## The arithmetic that closes off the obvious answer

The obvious response to a slow path is to make it faster. **It does not
work here**, and this is the single most useful thing the run produced:

| hypothetical | 100 000-document commit | vs the 1 s bound |
|---|---|---|
| today | 41.4 s | 41× over |
| both passes **2× faster** | 20.9 s | 21× over |
| both passes **10× faster** | 4.5 s | 4.5× over |
| both passes **100× faster** | 0.79 s | passes |
| both passes **removed from the commit** | 0.38 s | passes |

A 100× improvement in two mature stdlib-only passes is not a plan. **The bound
is reachable only by taking the work off the commit path**, which is an
architectural choice rather than an optimisation.

## Changes made in the same change as this run

**1. [ADR-MAINTENANCE](../../../docs/adr/0033_hooks.md) records both verdicts
and stays `proposed`.** Its consequences section said *"R5 AND R6 ARE NOT
MEASURED"*; it now says what they measured, and its veto conditions 1 and 2
name this run and its reproduce command instead of saying "held".

**2. Veto condition 1 has fired, and the record says so rather than absorbing
it.** Its own text — *"`post-commit` is too slow to be automatic and the hook
becomes opt-in or incremental in a way it currently is not"* — is the
consequence, not a reinterpretation of the threshold.

**3. The fork goes to Arpit as a compare doc**, not to an agent as a fix:
[`hook-at-scale.compare.md`](../../compare/hook-at-scale.compare.md).

**4. `tools/maintenance-bench/attribute.py` is a permanent component.** A
verdict of "it is slow" that cannot say *where* is an anecdote; this repo
learned that in M1 and the attribution is now part of the harness.

## Specific improvements, each with a repro command

**A — Decide where the re-index runs.** The compare doc's options, with the
number each one has to beat: today's commit path is 41.4 s at 100k, and the
floor with both passes removed is 0.38 s.

```bash
.venv/bin/python tools/maintenance-bench/attribute.py --sizes 1000 10000 100000
```

**B — `fux hooks --install` should say what it is about to cost.** It installs
a hook that is comfortable at 1 000 documents and unusable at 100 000, and it
currently says nothing about which side of that line the repository is on. The
corpus size is already known at install time.

```bash
# the repository being wired, and the number that matters for it
fux hooks --install && ls .fux/index/*.jsonl | wc -l
```

**Not implemented in this change.** It is a behaviour change that presupposes
the compare doc's outcome — if the hook stops doing the work inline, the
warning is about something else entirely.

**C — When the fork is settled, re-run R5 against the same frozen
pre-registration.** The threshold does not move; what changes is the system
under test.

```bash
work/regression/2026-08-20-r5-hook-latency/evidence/reproduce.sh
```

## Unresolved

- **The fork itself is open.** Four viable responses, none of them this run's
  to pick.
- **Where exactly the line falls is bracketed, not measured.** R5 passes at
  1 000 (0.651 s) and fails at 10 000 (3.523 s); the crossing is somewhere near
  1 500–2 000 documents and nobody has measured it. It matters for improvement
  B and for nothing else.
- **Synthetic corpora only.** The *shape* — cost tracking the corpus — is
  robust and holds at three sizes. The absolute seconds belong to this surface
  (Darwin 25.3.0 arm64, Python 3.14.2) and to documents more uniform than real
  documentation.
- **The derived pass was measured as `fux build`, which rebuilds T1 *and* the
  graph plane together.** Nothing here separates them, so "derive is 47.6 %"
  does not say which half of the derived plane is expensive.
