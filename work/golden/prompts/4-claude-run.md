---
type: Prompt
title: "Prompt 4 — Claude Code runs one rung"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 4 — Claude Code: run one rung

**Model: Sonnet** for the run; **Opus** if the report has to interpret anything
surprising. Run once per rung.

```
Execute work/golden/README.md "Phase 4 — Run" for rung <RUNG> (e.g. rung-00100).
Read CLAUDE.md §Golden answer key and §Conformance runs first. Never open
work/golden/golden-answer/. Read the questions from work/golden/questions/questions.jsonl
— it is already there; do not ask anyone for them.
1. Commit work/regression/<date>-golden-<RUNG>/PRE-REGISTRATION.md before any
   number: engine sha, rung, metrics with k named, headroom disclosure per ADR-RS.
2. Work in ~/my_programs/fux-lab/corpora/golden/<RUNG>/ with the
   pinned engine. Verify documents against work/golden/ladder/<RUNG>.sha256.
   Use the rung's own index — DO NOT re-ingest — unless the engine version differs
   from work/golden/ladder/<RUNG>.index; then re-ingest once, update the record,
   and state it in the report.
3. From inside the rung directory, for every question:
   fux ask "<q>" --json --band --top 10.
   Write evidence/predictions.jsonl: {"id","ranked":[paths],"answerable","band"}.
4. Stop. Scoring is Codex's (prompt 5). Commit only your own paths; do not push.
```
