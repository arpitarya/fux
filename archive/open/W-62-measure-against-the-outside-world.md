# W-62 — measure against the outside world

> ## WITHDRAWN 2026-08-22 — Arpit's call, and he owns it
>
> **Verbatim:** *"Part one and part two, the whole w sixty two, remove it,
> cancel it out. That's on me. I'll own it."*
>
> **Part 3 (the public README) was completed** earlier the same day and is not
> withdrawn — see its checked box below.
>
> **Parts 1 and 2 are cancelled, not deferred and not failed.** The three-way
> comparison needed a Confluence-shaped export corpus that does not exist and
> cannot be synthesised without defeating its own purpose; the cold-start half
> needed five external people. Both are Arpit's personally from this date, and
> **no agent should re-file them** as a queue item.
>
> **What this does NOT do.** It does not answer the question. The wedge —
> whether Fux wins on private, off-disk organisational documents — remains
> **untested**, and this item's own Hazard section said an item left open
> forever is itself information. Withdrawing it changes who holds that
> question, not whether it is open. **The id is retired and not reused.**

**Status:** OPEN · **Filed:** 2026-08-21 — moved from PRIORITY.md's P8 row
into the standing queue when PRIORITY.md (the P1–P8 ranked list, 2026-08-20)
was archived, its ordering role fully absorbed and its every row either DONE
or, for this one, carried forward as a normal `OPEN-WORK.md` item.
**Blocked by:** nothing structurally. **The README half is DONE (2026-08-22).**
What remains is blocked on two things no agent can supply from here: a real,
**Confluence-shaped export corpus** in `fux-lab` (not started, and it cannot be
synthesised — the whole point is that it is not our own fixtures), and **five
external humans** who will install Fux and report their first failure.
**Picking the commercial baseline is also still open** and is part of the item.
**Closes with:** a filed [`work/regression/`](../regression/README.md) run
carrying the three-way numbers (Fux BM25F vs `rg` vs one commercial
baseline); five named first-failure reports; the public README on GitHub
verified to match `main`.
**Model:** **Sonnet** for the README fix and the harness/report scaffolding;
**Opus** for recruiting/interpreting the five external first-failure
reports and any design-point call the numbers force — that is a judgment
call on the project's wedge, not mechanical work.

## Why this exists

Fux has never been measured against anything outside its own corpus or
synthetic fixtures. PRIORITY.md's own why-column, verbatim: **0 stars;
the download pattern looks like mirrors, not adoption; the wider industry
has converged on `rg`/grep for local code search.** Fux's actual thesis —
ranking wins on **private, off-disk, enterprise-shaped documents** ("Anton
remains a convenient small-scale testbed, not the priority filter" per
CLAUDE.md's own litmus test) — has never been tested against that shape of
corpus, or against a real user's first fifteen minutes.

**This is a design-point risk, not a polish item.** If Fux does not clearly
beat `rg`/grep and a commercial baseline on task success and tokens for a
real 50-question set, or if five external installs all fail the same way,
that is evidence the design point needs to move — not a launch checklist
to tick.

## What is unmeasured

**1. The three-way comparison.** 50 real org-doc questions against a
Confluence-shaped export in `fux-lab`: Fux BM25F vs `rg` vs one commercial
baseline (unnamed in the original row — picking one is part of this item).
**Metric is agent task success and tokens spent, explicitly not p95
latency** — the question is "does an agent using this get the right answer
cheaper," not "is it fast."

**2. The cold-start experience.** Five external users install Fux and
report their *first* failure — not a curated success story, the first
thing that actually breaks for someone who is not the person who built it.

**3. The public README's accuracy.** At filing, `origin` was 17 commits
behind `main` — verify what GitHub actually renders for a stranger's first
five minutes with the project, before asking anyone to try it.

## Definition of done

- [x] The public README fixed first — **done 2026-08-22.** `git ls-remote`
      puts `refs/heads/main` at `fa3ba30`, matching this tree, so the
      *"17 commits behind"* condition at filing no longer holds and origin is
      current. The raw README served at `main` was read back and matches this
      tree. **What was stale was the content, not the push:** the status line
      claimed *"M2 shipped"* on a repo that has since shipped M3, M4 and M5
      across five releases, and the graph lane was labelled *unreleased* when
      it went out in `0.34.0`. Both fixed on contact, with a DOC-REGISTRY bump.
      ⚠ **Recorded for whoever checks this next:** the rendered GitHub HTML
      page fetched at the same moment reported **v0.25.x and 134 commits** — a
      cached rendering, contradicted by `ls-remote` and by the raw file. A
      future check that reads only the HTML page will see it too and must not
      conclude the push is missing.
- [ ] A pre-registration for the three-way comparison, written and
      committed before any number exists — metric definitions (task
      success, tokens), the judged corpus (50 questions, Confluence-shaped
      export), the three arms, and a threshold, following the same
      discipline every other measured prediction in this repo uses
      (CLAUDE.md §A pre-registered threshold may never move).
- [ ] The three-way run, filed under `work/regression/` with report +
      ANALYSIS + evidence, per `tests/test_regression_runs.py`'s contract.
- [ ] Five external users recruited, each installing independently; their
      first-failure reports, named, filed under `work/`.
- [ ] A verdict — PASS/FAIL/INCONCLUSIVE against the pre-registered
      threshold, or an honest statement that the result is ambiguous and is
      Arpit's to adjudicate (CLAUDE.md's own rule: do not adjudicate an
      ambiguous result, hand it up).

## Hazard

**Do not let this item quietly become "measure someday."** It was ranked
P8 — last, but ranked, not parked — specifically because everything above
it (P1–P7) was judged more urgent *given the design point holds*. If this
item sits open indefinitely, that itself is information: it means nothing
in the roadmap actually depends on knowing whether the wedge is real.

## Reference

- PRIORITY.md's original P8 row (archived 2026-08-21 — see
  [`archive/README.md`](../../archive/README.md) for where it moved).
- CLAUDE.md §Litmus for any new work — **10 000 documents inside a
  corporation** (Arpit, 2026-08-21), never Anton, is the design point this
  measurement tests. The quote here used to read *"10k-engineer
  mega-project"*, which was the pre-2026-08-21 litmus; the **deployment**
  filter it names is unchanged, and it is the half this item actually tests —
  a stranger's first fifteen minutes is not a corpus-size question (W-65).
- [`work/setup/fux-lab.md`](../setup/fux-lab.md) — the environment this
  needs; currently exists but has no Confluence-shaped export corpus.
