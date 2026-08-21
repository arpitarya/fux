# W-62 — measure against the outside world

**Status:** OPEN · **Filed:** 2026-08-21 — moved from PRIORITY.md's P8 row
into the standing queue when PRIORITY.md (the P1–P8 ranked list, 2026-08-20)
was archived, its ordering role fully absorbed and its every row either DONE
or, for this one, carried forward as a normal `OPEN-WORK.md` item.
**Blocked by:** nothing structurally, but every measured half needs
`fux-lab` set up with a real, Confluence-shaped export corpus — that setup
work has not started.
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

- [ ] The public README fixed first — confirmed `origin/main` matches this
      repo's `main`, and what GitHub renders read back and checked, not
      assumed from the source file.
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
- CLAUDE.md §Litmus for any new work — the "10k-engineer mega-project,"
  never Anton, is the design point this measurement tests.
- [`work/setup/fux-lab.md`](../setup/fux-lab.md) — the environment this
  needs; currently exists but has no Confluence-shaped export corpus.
