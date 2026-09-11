---
type: OpenItem
id: W-138
title: "W-138 — reconcile every artifact with L9 (each sibling environment has one job)"
description: "L9 (2026-09-11) makes fux-playground Arpit's hands only, fux-lab the home of every measurement on golden test data ≤10k, and fux-benchmark speed + ranked lists across two versions. Every doc, tool, test and plan that still uses the playground as an instrument, or mixes the roles, is void in that part and is rewritten here."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-138 — reconcile every artifact with L9

**Model: Opus** — it rewrites parts of accepted records under a new law, and
deciding what a record *meant* before L9 versus what survives is judgment no
test catches.

**The law:** `CLAUDE.md` §Non-negotiable constraints, L9. **Its rationale:**
[ADR-LAW-9](../../docs/adr/0011_LAW-9-environments.md). **Forward only** —
filed runs stand as measured and are never edited.

## Found 2026-09-11 (`grep -rn playground`, excluding frozen material)

| group | files | what to do |
|---|---|---|
| **Setup docs** | `work/setup/fux-playground.md`, `fux-lab.md`, `fux-benchmark.md`, `README.md` | Rewrite to L9's roles; link ADR-LAW-9, never restate it. SETUP-PLAYGROUND stops saying *grades*; SETUP-BENCHMARK loses the golden ladder and gains the two-version rule and corpus shape (from the law) |
| **Tools and tests that read the playground** | `tools/differential/playground_grade.py`, `tools/quality-controls/relevance_audit.py` + `README.md`, `tools/vector-gate/README.md`, `tests/test_golden_schema.py`, `tests/test_doc_links.py` | Retarget to the lab's golden data, or retire. **Then add a test**: nothing under `src/ tools/ tests/ scripts/` references `fux-playground` except as a named exclusion — ADR-LAW-9's veto 1, made mechanical |
| **Records** | ADR-RS, ADR-QUALITY, ADR-ACCELERATOR, ADR-CONFIDENCE, ADR-ANSWER; `docs/GLOSSARY.md` (*playground*) | Rewrite, in place, every sentence that makes the playground an instrument. Each record's `laws:` gains `L9` where it now binds |
| **Plans** | `work/benchmark/RUNBOOK-TUNER.md`, `PRE-REGISTRATION-TUNER.md` (W-97's veto leg), `PRE-REGISTRATION-NODE.md`, `RUNBOOK-BENCHMARK.md`, `README.md`; detail files W-87, W-97, W-106, W-107; `proposals/unblock-2026-09-05.md` R-11, `proposals/search-v3.md` | Move each playground dependency to fux-lab golden data (blocked on W-136) or say it is dropped. ⚠ A **frozen** pre-registration is never edited — supersede it with a new one instead |
| **State docs** | `work/INTERVIEW.md`, `CLAUDE.md` mentions (e.g. *"R10 waits on fux-playground"*) | Fact corrections |

**Do not touch:** `work/regression/**`, `archive/**`, past `WORKLOG.md` entries.

## Definition of done

1. Every row above handled; `grep -rn fux-playground` outside frozen material
   returns only L9, ADR-LAW-9, SETUP-PLAYGROUND and the new guard test.
2. The guard test exists and passes; `uv run pytest -q tests tests_e2e` green.
3. OPEN-WORK rows that still name the playground as an input are updated in the
   same change; IMPLEMENTATION + WORKLOG entries; DOC-REGISTRY bumps; this file
   to `archive/open/`.

## Prompt

```
Execute work/open/W-138-reconcile-with-l9.md exactly.
Read CLAUDE.md §Non-negotiable constraints (L0, L9) and ADR-LAW-9 first.
Never open work/golden/golden-answer/. Never edit work/regression/, archive/,
or past WORKLOG entries; supersede a frozen pre-registration, never edit it.
Records link to L9 and never restate it. Add the guard test. Run both suites.
Commit only your own paths; do not push. Finish with the close-out list.
```
