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

| report | run | captures with a number | notes |
|---|---|---|---|
| [`2026-08-28-benchmark-v1-vs-head.html`](2026-08-28-benchmark-v1-vs-head.html) | [`2026-08-28-benchmark-v1-vs-head`](../../regression/2026-08-28-benchmark-v1-vs-head/report.md) | CAP-3 (partial) · CAP-4 · CAP-5 · CAP-6 | 🔴 **CAP-1, CAP-2 and `hit@20`/`hit@50` have none** — the ranked lists were not retained, and the capture set postdates the run by 16 days. Each says so in its own section |
| [`2026-08-28-benchmark-contested.html`](2026-08-28-benchmark-contested.html) | [`2026-08-28-benchmark-contested`](../../regression/2026-08-28-benchmark-contested/report.md) | the ranking endpoint, in this suite's own terms | 🔴 **CAP-1, CAP-2, CAP-4, CAP-5 and CAP-6 have none.** A ranking suite: no unanswerables, no byte count, and the report states outright that latency was not measured |
| [`2026-09-13-benchmark-captures.html`](2026-09-13-benchmark-captures.html) | [`2026-09-13-benchmark-captures`](../../regression/2026-09-13-benchmark-captures/report.md) | **all seven** | The first run to file the complete set. Slides 14–17 carry the **lineage** of all four benchmark runs and 🔴 **the cross-run pairs that may never be compared** |

**One filed benchmark run has no report at all:**
[`2026-09-12-benchmark-l9`](../../regression/2026-09-12-benchmark-l9/report.md).
It predates both the capture set and this directory; its numbers are filed and
were not re-run. Building its report is **W-158**, with the harness change.

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
