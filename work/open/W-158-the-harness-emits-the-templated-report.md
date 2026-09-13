---
type: Handoff
name: W-158
description: "The benchmark harness must emit CAP-7 into work/benchmark/reports/<yyyy-mm-dd>-<run>.html, in the template's shape, on every run — and the one filed benchmark run with no report needs one."
item: W-158
filed: 2026-09-13
ball: agent
---

# W-158 — the harness emits the templated report, to the one path

**Model: Sonnet.** A written definition-of-done against an existing template
and an existing test. The judgement was spent on 2026-09-13 when Arpit ruled
the path, the naming and the direction-of-goodness rule.

## Context

[SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) decisions 7–10 were
amended on 2026-09-13 (Arpit):

- **CAP-7 leaves the run directory.** Every benchmark HTML report lives at
  `work/benchmark/reports/<yyyy-mm-dd>-<run>.html` — the run directory's own
  name with `.html` on the end. The other six captures are unchanged.
- **It is built from [`TEMPLATE.html`](../benchmark/reports/TEMPLATE.html)**,
  one section per capture.
- **A capture with no number keeps its section and says so**, and no run is
  re-executed to fill a gap.
- **Every number carries its direction of goodness** — ↑ higher is better,
  ↓ lower is better, or — neither.

🔴 **The harness does not do any of this yet.** `fux-benchmark/bin/bench.py`'s
`report` verb writes `benchmark.html` into the run directory, in its own shape,
with no direction markers. The three reports now in `reports/` were **written by
a session from the template**, from filed rows, which decision 5 permits only
until this item lands.

## Definition of done

1. `bench.py report` writes `work/benchmark/reports/<run>.html` — the run id it
   was given, `.html` appended — and **nothing into the run directory**.
2. It renders from the template rather than from strings in the emitter, so a
   template change reaches the next report without a code change.
3. **Every numeric column header and every stat carries a direction marker.**
   The direction is a property of the metric, declared once in the emitter, not
   decided per report.
4. **A capture with no rows renders its section with the `nonumber` treatment**
   naming which capture and why — never an omitted section, never a zero.
5. `tests/test_benchmark_capture.py` passes unchanged. It already asserts the
   new path and that the old one no longer counts.
6. **A report is produced for
   [`2026-09-12-benchmark-l9`](../regression/2026-09-12-benchmark-l9/report.md)**
   from its filed rows — the one filed benchmark run with no report. 🔴 **From
   the rows only. The run is frozen and is NOT re-executed**; CAP-3, CAP-4 and
   the contaminated latencies are stated as what they are.

## Out of scope

- **Re-running any benchmark.** Every gap is stated, never measured away.
- **Changing what is captured.** Decisions 1–4 are untouched.
- **Rewriting the three hand-built reports** unless the generated shape differs,
  in which case they are regenerated from the same rows and the diff is checked
  to carry no new number.

## Where the work is

`~/my_programs/fux-benchmark` — a sibling working directory, not this repo
([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)). Only the
template, the record and the test live here.
