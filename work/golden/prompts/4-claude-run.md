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
Read CLAUDE.md §Non-negotiable constraints (law L11) and §Conformance runs
first. Never open work/golden/golden-answer/ — there is no key file and no
answer reaches you by any route, a paste included. If one does, STOP, say so,
and file it before anything else.
Read the questions from work/golden/questions/set-a.jsonl and set-b.jsonl (today
set B is still questions/questions.jsonl) — they are already there; do not ask
anyone for them. Run BOTH sets.
1. Commit work/regression/<date>-golden-<RUNG>/PRE-REGISTRATION.md before any
   number: engine sha, rung, metrics with k named, headroom disclosure per SR-RS.
2. Work in ~/my_programs/fux-lab/corpora/golden/<RUNG>/ with the
   pinned engine. Verify documents against work/golden/ladder/<RUNG>.sha256.
   Use the rung's own index — DO NOT re-ingest — unless the engine version differs
   from work/golden/ladder/<RUNG>.index; then re-ingest once, update the record,
   and state it in the report.
3. From inside the rung directory, for every question:
   fux ask "<q>" --json --band --top 10.
   Write evidence/predictions-a.jsonl and evidence/predictions-b.jsonl —
   one file per set, never merged: {"id","ranked":[paths],"answerable","band"}.
4. Stop. Scoring is Codex's (prompt 5). Commit only your own paths; do not push.
```
