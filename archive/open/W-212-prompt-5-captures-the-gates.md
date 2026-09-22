---
type: OpenItem
id: W-212
title: "W-212 — prompt 5 captures `derivation.gates`, so phase D can compute the funnel it could not"
description: "W-204 phase D ran and could not produce SR-WORK-QUALITY's funnel: `reachable` and `in window` live in `ask --json --why`'s derivation.gates, and prompt 5 never captured them. The hand-offs carry the ranked list and the answer and nothing about what was cut. Until this lands, no document may state fux's funnel and W-87's `judged` series stays unpinned."
status: open
lane: agent
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: agent
---

# W-212 — the hand-off carries no funnel, because nothing asked it to

**Model: Sonnet** — one flag in a prompt, one field in a writer, then a re-run.
Nothing to design.

## What happened

[W-204 phase D](../regression/2026-09-22-golden-final-score/report.md) scored
11 716 rows with zero join errors and produced everything it was asked for
**except step 4**, which is the one that matters most:
[SR-WORK-QUALITY](../../records/0056_WORK-quality.md)'s funnel — `reachable → in
window → placed → answered`, cost-weighted at the frozen `c = 2`, with the
risk–coverage curve beside every scalar. **It is W-87's headline.**

🔴 **The rows cannot produce it.** A hand-off carries `ranked`, `answer_text`,
`band`, `answerable`, `citations` and timings. `reachable` and `in window` are
`ask --json --why`'s `derivation.gates`, and **prompt 5 does not pass `--why`**,
so the two counts were never written down. They are not recoverable from a filed
run — the corpus, the engine sha and the tune are all pinned, but the *cut line*
was computed and discarded 11 716 times.

⚠ **This is a measurement-design defect, not a scoring one.** The scoring pass
was complete on what it was given. **The instrument was specified without one of
the fields its own headline metric needs** — the same class as W-168 step 1
shipping against a corpus with zero `ref` edges, or W-205 part 2 measuring a
failing shape that did not fail: *the data does not contain the input the metric
acts on* ([SR-RS](../../records/0133_predictions.md) decision 23).

## Definition of done

1. **Prompt 5 passes `--why`** and the hand-off writer records
   `derivation.gates` per question — `reachable`, `in_window`, `placed`,
   `answered`, `cut_score` — as their own fields. ⚠ **Not the whole derivation**:
   the per-term rows are large and the funnel needs five integers.
2. `tools/quality-controls/rung_outputs.py` and the hand-off schema move with
   it, so the `.md` and the rows cannot disagree.
3. **A test that the hand-off carries the five fields**, so the next generation
   cannot be run without them. Two strikes → a gate: this is the second time a
   golden run has been filed without an input a metric needed.
4. `tools/quality-controls/phase_d.py` computes the funnel when the fields are
   present and **says so explicitly when they are not** — never a zero.
5. Records: [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) if the funnel's
   inputs are restated there; `work/golden/README.md`'s prompt 5.

## What it unblocks

- **W-87's `judged` series** gets its first pinned run.
- **The funnel may be stated.** Until then no document may, and
  [`FINAL-SCORE.md`](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md)
  says so in terms.

⚠ **It needs a re-run of phases A and B** — roughly 12 000 `fux` calls, cheap in
machine time — and **the re-run happens on the NEXT generation of test data**,
not this one: these questions retire under L11 decision 14 the moment Arpit runs
`just golden-retire`. There is no reason to re-run a generation that is about to
become open regression data.

## Out of scope

The answer-text verdict (a judgement, not a field), difficulty banding, and
pooling. All three are W-204's and stay there.
