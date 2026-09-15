---
type: Report
run: 2026-09-15-differential-repaired
item: W-184
classification: surface capture
description: "The differential harness runs on this repository again — 22 144 byte-identical comparisons, zero mismatches — after two decode defects and one dead keyword argument were repaired."
filed: 2026-09-15
---

# REPORT — the differential harness, repaired and run

**Not a paired run.** No arms, no judgments, no threshold. It proves an equality
— the accelerator's output equals the scan's, byte for byte — and rules on
nothing, so it is a **surface capture** and files no verdict.

## The run

```console
$ python tools/differential/run.py --root .

queries: 692   tops: [1, 5, 20, 50]   modes: off, on
weights: [1.0, 0.5, 2.0, 500.0] on `[priority]` prefix 'archive'
undecodable: 10 file(s) walked but not UTF-8, contributing no terms —
  archive/v0.1/fux/assets/fux-lockup.png, archive/v0.26/tests_e2e/corpus/assets/logo.png,
  archive/v0.26/tests_e2e/corpus/office/spec.docx, archive/v0.26/tests_e2e/site/logo.png,
  docs/architecture-answer.png ...
comparisons: 22144
scan:   763733.7 ms total
accel:   75939.2 ms total

DIFFERENTIAL GREEN — 22144 comparisons, byte-identical in every mode
```

**22 144 comparisons, zero mismatches.** The first run through
`tools/differential/run.py` on this repository that has ever reached a
comparison.

## What was broken, and it was three things

| # | site | what it did | how it read |
|---|---|---|---|
| 1 | `queryset.py::vocabulary` | `.decode("utf-8")` on every walked file | `UnicodeDecodeError` on the first PNG — **no comparison ever ran** |
| 2 | `bench_r3.py::source_vocabulary` | the same bytes with `errors="replace"` | **ran**, and folded `png` plus a page of replacement characters into the corpus vocabulary as terms no document holds |
| 3 | `run.py::compare` | passed `archived_weight=` to both `ask`s | `TypeError` before the first comparison — **W-152 removed that prior on 2026-09-13** and no signature has accepted it since |

🔴 **Defect 2 is the worse one.** A harness that crashes gets fixed on the day
somebody runs it. A harness that invents its own query set measures something
nobody asked for and reports it green.

⚠ **Defect 3 was invisible until defect 1 was fixed** — it sat behind a crash.
Two days of a proof obligation for every ranking change, dead, with a green
unit-suite arm (`tests/derive/test_differential.py`, which builds its own
corpora and calls `compare()` with its own arguments) covering for it.

## The weight sweep now rides `[priority]`

`(1.0, 0.5, 2.0, 500.0)` exists to hold W-73's weighted bound at values that
straddle unity. The lever those values used to ride was removed; `[priority]` is
the one that survived (SR-TUNE decision 8), and it is **a better shape for the
property**: the bound has to survive *some* documents being scaled and others
not, and a global prior scaled everything it reached. The prefix defaults to the
first configured source directory — `archive` in this repository — and
`--priority-prefix` overrides it.

## Timings are not a claim

`scan 763.7 s` / `accel 75.9 s` are printed by the harness and kept because the
output is filed unedited. ⚠ **They were measured while this same session was
running a second background job on the same machine**
([SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision 12), so they
price nothing. The comparison count and the zero are what this run establishes.

## Reproduce

```console
$ python tools/differential/run.py --root .        # ~14 minutes here
$ python tools/differential/run.py --root . --tops 5 --skipping off   # ~3 minutes
```
