---
type: Run Report
run: 2026-10-25-w300-merged-query
item: W-300
date: 2026-10-25
classification: informed
status: PASS — ruled by Arpit 2026-10-25 (the table reads PASS; the pre-registration filed it INCONCLUSIVE → Arpit; he declared PASS)
---

# 2026-10-25 — W-300: one query over the repository and a pinned index package — **PASS (ruled by Arpit)**

**Arpit ruled PASS on 2026-10-25 (Cowork)** and kept `scope = all` as the default — see the [VERDICT](VERDICT.md). The run below is as it was filed; the proper test is W-303.

Filed by the parent session (4aad6236) from the run's own evidence files: the
building agent's harness refused to write files named `report.md` and
`ANALYSIS.md`. No number below was computed by this filing. Each is copied from
[`evidence/summary.json`](evidence/summary.json) and [`evidence/gates.json`](evidence/gates.json),
and each per-question row is in [`evidence/rows.jsonl`](evidence/rows.jsonl).

## What ran

| | |
|---|---|
| engine | W-300 at `567d8c3e` (decided arm, `scope = all`) against the engine at `9688d479` (baseline, repository alone) |
| corpus | a 6-document consumer repository ([`evidence/corpus/`](evidence/corpus/)) with the W-299 fixture index package (3 documents) pinned beside it |
| questions | 30, in [`evidence/questions.tsv`](evidence/questions.tsv), frozen with the [pre-registration](PRE-REGISTRATION.md) in `dbec142c` before any number |
| reproduce | [`evidence/REPRODUCE.sh`](evidence/REPRODUCE.sh), [`evidence/run.py`](evidence/run.py) |

## Gates

| gate | questions | differ |
|---|---|---|
| G0a: no pin, byte-identical to `9688d479` | 30 | 0 |
| G0b: `scope = repo`, byte-identical | 30 | 0 |
| G0c: this repository's own index, byte-identical | 30 | 0 |
| Node ≡ Python | 30 | 0 |

## Reading (L13 decision 4's table)

| row | result |
|---|---|
| slice floor | 16 winnable, floor 15: holds |
| C1, slice hit@1 | 16 wins, 0 losses; net 16, 10 needed, p < 0.0001: holds |
| C2, outside the slice | 0 wins, 0 losses (margin 2): holds |
| C3 | 16 wins, 0 losses: holds |
| guardrail hit@5 | 14 → 30: holds |
| guardrail grounded | 8 → 13: holds |
| table reading | **PASS** |

**Filed INCONCLUSIVE**, as the pre-registration fixed in advance:
- SR-RS decision 6: the building session wrote the questions and read the result.
- G over golden rows was not run, because of L11.
- `section@1` and latency cannot be measured on a 9-document fixture.

## Headroom (SR-RS decision 22)

Computed from [`evidence/rows.jsonl`](evidence/rows.jsonl), arms `baseline_repo` and `decided_all`, 30 questions.

| endpoint | baseline | decided | improvement headroom (baseline misses) | regression headroom (baseline hits) |
|---|---|---|---|---|
| hit@1 | 14 | 30 | 16 | 14 |
| hit@5 | 14 | 30 | 16 | 14 |

Every one of the 16 package-slice questions was a baseline miss, so the slice's improvement headroom was the whole slice. Outside the slice, the baseline hit every question it could, and none regressed.

## The void run

The first run voided itself on G0c (12 of 30 differed). The post-commit hook
re-ingested `.fux/index` in the middle of the run, so the baseline arm read a
different index. That run is kept in [`evidence/run1-void/`](evidence/run1-void/),
and the numbers above are the clean rerun's.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the 30 questions, the 6-document corpus, the pre-registration | the W-300 building agent (Claude Code, Opus 5.5) | the engine it built; the fixture package; no result (frozen in `dbec142c` first) |
| the fixture index package | the W-299 build (Claude Code) | n/a |
| `run.py`, `payloads.py`, VERDICT | the same building agent | the rows, after the run |
| this report, ANALYSIS | the parent session (4aad6236) | the evidence files only |

`informed`: the builder, the question author and the reader are one model family.
