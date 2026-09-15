---
type: OpenItem
id: W-187
title: "W-187 — the benchmark report's spine: one slide per capture, titled by its CAP id, comparing the two arms"
description: "Arpit ruled 2026-09-15 that CAP-1..CAP-6 each get their own titled slide in the benchmark report, each an A-vs-B comparison; CAP-7 gets none because it is the report. Today's TEMPLATE.html has no CAP-1 slide and titles sections by finding. Template and emitter move together or the emitter refuses."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-187 — one slide per capture, titled by its CAP

✅ **CLOSED 2026-09-15 — BUILT the same day**, in Cowork, on Arpit's *"implement it"*.
What landed: `TEMPLATE.html` is twelve slides with a **CAP-1 slide that did not
exist**, every CAP titled `CAP-n — <capture>` **outside** its marker, and the
emitter's `<h2>`s turned into `<p class="finding">` subtitles; `report.py` gained
`_fill_ranked` and the `ranked` marker. Verified by rendering
`2026-09-13-benchmark-captures` into a **scratch root** — 0 unfilled slots, 0
missing captures, and the marker-rename refusal still fires. **No filed report was
touched** (decision 11a).

**Model: Sonnet** for the template and the emitter; **Opus** only if the
marker-vs-`<thead>` split in *Hazards* turns out to need re-deciding.

## The ruling

> **Arpit, 2026-09-15:** *"in benchmark final report the should have 1 slide
> each for all caps independently comparing it to the previous versions with the
> title of each and every cap"*

Two clarifications he gave in the same exchange:

- **CAP-7 gets no slide.** CAP-7 *is* the report; a slide comparing it to the
  previous report has no number behind it. Six CAP slides, and the record says
  so explicitly so nobody reads it as a dropped section.
- **The framing slides all stay** — cover, *which way is good*, arms, null
  control, headroom, guard rails. The spine is added around them, not instead
  of them.

Stated once in
[SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) **decision 14**,
amended in the same session. **This file restates none of the rule** — it is
the build.

## Why it is a change and not a rename

Checked against
[`work/benchmark/reports/TEMPLATE.html`](../../work/benchmark/reports/TEMPLATE.html),
2026-09-15:

| today's slide | marker | the capture it renders |
|---|---|---|
| — | — | 🔴 **CAP-1 has no slide.** The ranked lists are only ever seen through CAP-2 |
| `{{n}} of {{N}} lists differ` | `rankdiff` | CAP-2 |
| `{{the one-line finding}}` | `hits` | CAP-3 |
| `{{the one-line finding}}` | `answers` | CAP-4 |
| `{{one line}}` | `size` | CAP-5 |
| `{{one line}}` | `latency` | CAP-6 |

**Every title is a finding, not a capture.** A reader who wants CAP-5 reads six
slides to find it, and CAP-1 is not there to find at all.

## Definition of done

1. **`TEMPLATE.html` carries six capture slides**, in id order, each titled
   `CAP-n — <the capture's name>`, each with **arm A and arm B side by side**
   and the direction of goodness in the `<thead>` the emitter copies through.
2. **CAP-1 gains a slide** — the ranked lists, A against B. What it renders at
   what granularity is this item's to decide; the rows exist in
   `ranked-lists.jsonl` and nothing new is measured to fill it.
3. **The one-line finding survives** as a subtitle under the CAP title, not as
   the title. It is the most readable thing on the page and is not lost.
4. **The emitter's marker set moves in the same commit** —
   `fux-benchmark/bin/report.py`. A renamed or new marker the other side does
   not know makes it refuse, by design (SR-WORK-BENCHMARK decision 11).
5. **An absent capture keeps its titled slide** and says which one and why
   (decision 9), verified by rendering a run that is missing one.
6. **The next benchmark run's report is generated from the new template** and
   is the proof. **No existing report is rebuilt** — the three hand-written
   ones are frozen (decision 11a).

## In scope

- `work/benchmark/reports/TEMPLATE.html`.
- `~/my_programs/fux-benchmark/bin/report.py` — the marker set and the fills.
- `tests/test_benchmark_capture.py`, if a check can be made that is about the
  *template* rather than about a filed report.

## Out of scope

- **Any change to what is captured.** CAP-1…CAP-7 and their granularity are
  untouched; this is the rendering.
- **Re-running a benchmark.** Decision 9's frozen-report rule holds.
- **The Node column's shape** (decision 12) — it is a column inside CAP-6 and
  CAP-3, and this item does not re-open where it sits.

## Records amended in the same change

- [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) — **already
  amended** (decision 14, 2026-09-15). If the build learns something that makes
  decision 14 wrong, the record moves first.
- `work/benchmark/reports/README.md` restates nothing and needs no edit.

## Hazards

- 🔴 **The emitter lives in an uncommitted repo on one machine**
  (SR-WORK-BENCHMARK decision 13). A template that has moved and an emitter
  that has not is a report that cannot be generated at all — so the two commits
  are one change, and the session that does it says which machine it was on.
- ⚠ **Directions of goodness live in the template's `<thead>`, deliberately**
  (decision 11). A new CAP slide that lets the emitter write its own direction
  re-opens the defect decision 10 closed.
- ⚠ **Six titled slides make an empty capture louder.** That is the point, and
  it will make the 2026-08-28 pair look worse than they are if anyone
  regenerates them. They are frozen; do not.
