---
type: Index
description: "Every benchmark run's HTML report, one per run, dated — plus the template they are all built from."
---

# `work/benchmark/reports/` — one HTML report per benchmark run

**This directory is the only home for a benchmark's HTML report**
(Arpit, 2026-09-13). It holds **CAP-7** — nothing else. The rows, the
diagnosis and the verdicts stay with their run under
[`work/regression/`](../../regression/README.md), which is unchanged.

## The naming rule

```text
work/benchmark/reports/<yyyy-mm-dd>-<run>.html
```

**`<yyyy-mm-dd>-<run>` is the run's own directory name under `work/regression/`,
character for character, with `.html` on the end.** One run, one report, and the
pairing is mechanical rather than a matter of reading the file.

## What must be in one

**Stated once, in
[SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)** — the seven
captures, the direction of goodness on every number, and what a report does when
a run has no number for a capture. **This file does not restate it**, and
neither does the template: [`TEMPLATE.html`](TEMPLATE.html) is the *skeleton*,
one section per capture, and where it and the record disagree the template is
the defect.

## What is here

**All five were rebuilt to the capture spine on 2026-09-15** — one slide per
capture, titled by its CAP, CAP-7 none
([SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md) decisions 14 and
15). 🔴 **No number changed and nothing was re-executed**: a capture with a
filed number now has a titled slide carrying it, and one without keeps a titled
slide that says so and that the next run captures it.

| report | run | captures with a number | notes |
|---|---|---|---|
| [`2026-09-21-golden-three-engines.html`](2026-09-21-golden-three-engines.html) | **W-204 phase B — `1.0.0` vs `2.0.1` vs frozen `HEAD` on the golden ladder.** 🔴 **A SKELETON**: captures 1, 2, 5 and 6 carry findings; **3, 4 and 7 carry `nonumber`** because each needs the answer key, which is not open. The rows they will be computed from are already filed, so nothing is re-run to fill them (template rule 4: a capture with no number KEEPS its section and says so). [the run](../../regression/2026-09-21-golden-three-engines/report.md) |
| [`2026-08-28-benchmark-v1-vs-head.html`](2026-08-28-benchmark-v1-vs-head.html) | [`2026-08-28-benchmark-v1-vs-head`](../../regression/2026-08-28-benchmark-v1-vs-head/report.md) | CAP-3 (partial) · CAP-4 · CAP-5 · CAP-6 | 🔴 **CAP-1, CAP-2 and `hit@20`/`hit@50` have none** — the lists were not retained and the capture set postdates the run by 16 days. Each now says so on **its own** slide |
| [`2026-08-28-benchmark-contested.html`](2026-08-28-benchmark-contested.html) | [`2026-08-28-benchmark-contested`](../../regression/2026-08-28-benchmark-contested/report.md) | CAP-3, in this suite's own terms | 🔴 **CAP-1, CAP-2, CAP-5 and CAP-6 have none.** A ranking suite: no unanswerables, no byte count, and latency deliberately not re-measured |
| [`2026-09-12-benchmark-l9.html`](2026-09-12-benchmark-l9.html) | [`2026-09-12-benchmark-l9`](../../regression/2026-09-12-benchmark-l9/report.md) | CAP-1 · CAP-5 · CAP-6 | Regenerated 2026-09-15. **CAP-1's 600 filed lists have their own slide now**; the old page carried them as a sentence inside CAP-2 |
| [`2026-09-13-benchmark-captures.html`](2026-09-13-benchmark-captures.html) | [`2026-09-13-benchmark-captures`](../../regression/2026-09-13-benchmark-captures/report.md) | **all seven** | The first run to file the complete set. Hand-built and **kept** — re-titled, CAP-5 and CAP-6 split, and a **CAP-1 slide added** from its own `ranked-lists.jsonl`. Slides 16–19 carry the lineage of the four earlier runs |
| [`2026-09-15-node-column.html`](2026-09-15-node-column.html) | [`2026-09-15-node-column`](../../regression/2026-09-15-node-column/report.md) | CAP-6, four arms | 🔴 **This run had no report until 2026-09-15**, and CAP-7 has been mandatory since 2026-09-13. CAP-6 is read from `latency-<tier>.csv` **with the substitution stated on the page**; the other five say they have no number |

**Every filed benchmark run now has a report.** The gap W-158 named is closed.

## Three rules that are easy to get wrong

1. **A report carries no number its run does not.** It is a *rendering* of the
   filed rows, never a second source. Where the two disagree, **the report is
   wrong** and is corrected here.
2. **A capture with no number keeps its section and says so.** Deleting it
   reads as a capture that was never required — which is exactly the confusion
   the capture set exists to end. **No run is re-executed to fill a gap**; the
   reports are frozen and a better number is a new run with a new date.
3. **Every number carries its direction** — ↑ higher is better, ↓ lower is
   better, or — neither. A direction says which way the metric points and
   **never** that a difference is real or worth acting on. A benchmark rules no
   threshold.

## Provenance of the three here

⚠ **All three were rebuilt by hand on 2026-09-13**, from the filed rows of runs
that had already closed — the harness does not yet emit this shape or this path.
**That is the gap W-158 closes**; until it does, a new run's report is written
from [`TEMPLATE.html`](TEMPLATE.html) by the session that files the run. What
they replaced is in
[`archive/benchmark-reports/`](../../../archive/README.md).
