---
type: Prompt
title: "Prompt 5 — Claude Code runs both sets on one rung and writes the hand-off report"
item: W-189
timestamp: 2026-09-15T00:00:00Z
---

# Prompt 5 — Claude Code: run both sets, write the report Arpit hands to Codex

**Model: Sonnet** for the run; **Opus** if the report has to interpret anything
surprising. Run once per rung.

**What this produces** is the artifact Arpit picks up and gives to Codex: for
every question, **what was asked, what fux answered, and which documents it
ranked** — and nothing else. 🔴 **It contains no golden answers**, because no
Claude session has one. Scoring happens in [prompt 6](6-codex-score.md), against
the key Arpit pastes there.

⚠ **Two `fux` calls per question**, so a full rung is ~250 questions × 2. Run one
rung at a time and say which one.

```
Execute work/golden/README.md "Phase 5 — Run" for rung <RUNG> (e.g. rung-00100).
Read CLAUDE.md Non-negotiable constraints (law L11) and Conformance runs first.
There is NO golden answer key anywhere and no answer reaches you by any route, a
paste included. If one does, STOP, say so, and file it before anything else.
Never open work/golden/golden-answer/ — it was deleted and is not a location.

Read the questions from work/golden/questions/set-1.jsonl and set-2.jsonl. They
are already there; do not ask anyone for them. Run BOTH sets, keeping them apart
at every step.

1. Commit work/regression/<date>-golden-<RUNG>/PRE-REGISTRATION.md before any
   number: engine sha, rung, metrics with k named, headroom disclosure per SR-RS.
2. Work in ~/my_programs/fux-lab/corpora/golden/<RUNG>/ with the pinned engine.
   Verify documents against work/golden/ladder/<RUNG>.sha256. Use the rung's own
   index — DO NOT re-ingest — unless the engine version AND engine_commit differ
   from work/golden/ladder/<RUNG>.index; then re-ingest once, update the record,
   and state it in the report.
3. From inside the rung directory, for every question in each set:
     fux ask "<q>" --json --band --top 10
     fux answer "<q>" --json
   Write evidence/predictions-set-1.jsonl and evidence/predictions-set-2.jsonl,
   one line per question, one file per set, never merged:
     {"id","ranked":[paths],"answerable":bool,"band":"..."}
4. Write the HAND-OFF, one file per set, evidence/handoff-set-N.jsonl, one line
   per question and self-contained — this is what Arpit gives Codex:
     {"id","question","answer_text","citations":[{"doc","lines"}],
      "ranked":[paths],"answerable":bool,"band":"...","rung":"<RUNG>",
      "engine_commit":"..."}
   answer_text and citations are what FUX produced. There is no golden answer in
   this file and there never will be.
5. Write report.md: the rung, the engine sha and commit, the counts per set, the
   band distribution, how many questions fux declined, the slowest and the
   emptiest results, and anything that looked wrong. Name the two handoff files
   as the thing to give Codex.
6. Stop. Scoring is Codex's (prompt 6). Commit only your own paths; do not push.
```

## What the report may and may not say

- ✅ **May:** what fux answered, what it ranked, what it declined, how long it
  took, which questions returned nothing, and any anomaly worth a second look.
- 🔴 **May not:** whether an answer is *right*. No Claude session can know that,
  and a report that guesses trains the next reader to trust a guess. **Correct /
  incorrect appears for the first time in prompt 6's output, from Codex.**
- ⚠ **Set 2 numbers carry `informed` permanently** — its author and its runner
  are the same model family. Write the label beside the number, in the report,
  every time.
- 🔴 **Never pool set 1 and set 2 into one figure.** The gap between them is the
  measurement; a mean across both erases it.

**Next:** Arpit gives `handoff-set-1.jsonl` and `handoff-set-2.jsonl` to Codex
with [prompt 6](6-codex-score.md), and pastes each key there himself.
