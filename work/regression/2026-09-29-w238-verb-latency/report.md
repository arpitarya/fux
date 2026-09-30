---
type: Regression Run
name: w238-verb-latency
description: "W-238 — which fux verbs are silent long enough to need a progress bar. At rung-10000 and on this repo: identifiers (2 s / 13 s), doctor (3 s / 14 s) and enrich --check (105 s for 300 enrichment files) do; explain, graph, path, ask, find, answer and enrich --plan finish in 0.13–0.9 s and do not."
run: 2026-09-29-w238-verb-latency
item: W-238
classification: blind
status: complete
timestamp: 2026-09-29T00:00:00Z
---

# Which verbs are slow enough to need a progress bar

**A latency survey, not a ranking run.** It decides which verbs join
`cli._PROGRESS_COMMANDS` ([SR-CLI](../../../records/0101_cli-surface.md)
decision 17). Nothing is scored and it is not a paired run, so it files
**no per-query rows**: there are no queries to score.

- **Machine:** macOS, 10 cores, Python 3.14.3, shared with another session
  (load average ~3). **The threshold being judged is "noticeable", which is
  seconds, not milliseconds**, so this load does not change the verdict on
  any verb.
- **Engine:** `HEAD` `0980e962` plus W-239's speed fixes, which were built in
  the same session. W-239 does not touch any verb measured here, except that
  `identifiers` and `doctor` decode documents and so gain a little from the
  registry cache.
- **Corpora:** the scratch `rung-10000` copy that W-239 used
  (`fux-lab/scratch/w239/`), after `fux build`, and this repo (1 851 records).
  No corpus in either place declares an enrich scope. So `enrich` was
  measured a second time on the copy, with `ext enrich=true` and 300
  synthetic enrichment files of 5 questions each. Both were removed
  afterwards.

## Result

| verb | rung-10000 | this repo | bar? |
|---|---|---|---|
| `identifiers` | 2.0 s | 13.1 s | **yes** — `read`, `detect` |
| `doctor` | 3.1 s | 14.2 s | **yes** — `read`, `detect` |
| `enrich --check`, 300 files | 104.8 s | — | **yes** — `check` |
| `enrich --check`, no files | 0.9 s | — | the `check` phase has 0 files, so it never paints |
| `enrich --plan` | 0.9 s | — | no |
| `path` | 0.63 s | | no |
| `graph` (query / `--seed`) | 0.35 / 0.40 s | | no |
| `ask` · `find` · `answer --no-refer` | 0.39 · 0.33 · 0.38 s | | no |
| `explain` | 0.13 s | | no |

`verify --rerun` re-runs one `answer`, so it is bounded by the `answer` row.
It was not timed separately.

**Why `doctor` is slow:** almost all of it is one check.
`identifier families current` re-runs the `inspect` identifier lens over every
document: 45 of 48 s under the profiler on this repo
(`evidence/profile-doctor-fux.txt`). `fux identifiers` runs the same lens,
which is why the two verbs get the same two phases.

Raw numbers: `evidence/timings.txt`.

## After the change

The same scratch copy, with each verb run under `--progress` and again under
`--no-progress`:

- stdout was byte-identical in every pair: `identifiers`, `identifiers --json`,
  `doctor`, `doctor --json`, `enrich --check`, `enrich --plan`;
- the bar painted `detect 10000/10000` for `identifiers` and `doctor`, and
  `check 300/300 files` for `enrich --check`;
- `enrich --plan` painted nothing;
- with no flag and stderr not a TTY, nothing was painted.

## Reproduce

```bash
cd ~/my_programs/fux-lab/scratch/w239/rung-10000   # a doctor --fix'd copy of golden-gen2/rung-10000
F=~/my_programs/fux/.venv/bin/fux
$F build
time $F identifiers >/dev/null; time $F doctor >/dev/null
time $F path seed/01-sop-temperature-excursion.md seed/03-postmortem-nagpur-vaccine-excursion.md >/dev/null
# enrich --check: declare `ext  enrich=true` in .fux/sources/dirs, write
# enrichment files for the MISSING rows `fux enrich` prints (the shape is in
# tests_e2e/test_progress_surface.py::_enrich_all), then:
time $F enrich --check >/dev/null
```

## Authorship

Claude Code (Opus 5.5), 2026-09-29, the session that built W-238. It is
`blind`: the only thing measured is wall time, and the synthetic enrichment
questions were written only to be ranked, not to pass.
