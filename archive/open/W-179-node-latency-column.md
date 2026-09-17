---
type: OpenItem
id: W-179
title: "W-179 — the Node latency column: run it, so N4 stops being unmeasured"
description: "W-148 row 2 was ruled 2026-09-14 as a COLUMN in fux-benchmark rather than a second harness, and SR-WORK-BENCHMARK decision 12 carries it. The decision landed; the run did not. Filed 2026-09-15 under SR-WORK-OPEN-QUEUE 23a because W-148 was 🟡 on a run with no item behind it."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-179 — run the Node latency column

**Model: Sonnet** for the run; **Opus** for the verdict if the graph-plane cost
below turns out to dominate, because that is a claim about what a number means.

**Why this exists.** [W-148](W-148-what-the-two-readers-still-owe.md) row 2 was
ruled on 2026-09-14 — Node's latency is a **column** beside Python's in
`fux-benchmark`, not a second harness, because the question is a comparison.
[SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) decision 12 states it.
**The decision is landed and the run is not**, so W-148 sat 🟡 on *"a
`fux-benchmark` Node-column run"* with nothing in the queue that would ever
produce one. This is that thing.

## Definition of done

1. The Node column is populated in a filed `fux-benchmark` run, beside Python's,
   on the same commit and the same corpora.
2. ⚠ **The graph-plane cost is separated, not absorbed.** W-161 landed
   2026-09-15 and a Node `ask` now **rebuilds the graph plane in memory, parsing
   every committed record**, which the Python reader does not do. A run that does
   not split that out attributes a *tier's* price to the *reader* — named in
   SR-WORK-BENCHMARK decision 12 and repeated here because it is the one way this
   run produces a confidently wrong number.
3. The report is filed under `work/regression/` per SR-RS decision 10a.
4. **N4 is marked measured** — and until this lands, no document may say it is
   ([W-148](W-148-what-the-two-readers-still-owe.md)'s own standing warning).

## Environment

`fux-benchmark` — **agents and Arpit both**
([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)), so this is
agent work on the Mac, not Arpit's hands. ⚠ It is a **scratch** environment with
zero commits (SR-WORK-BENCHMARK decision 13): the harness that generates the
report lives on one machine and nothing in fux would notice it going.

## Closes

Unblocks [W-148](W-148-what-the-two-readers-still-owe.md) row 2. Does **not**
touch W-148 rows 3 or 4.
