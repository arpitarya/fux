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

🔴 **`ask` carries `--why` since 2026-09-22 (W-212), and that is not cosmetic.**
[SR-WORK-QUALITY](../../../records/0056_WORK-quality.md) decision 13: the four
gates of the funnel are computed per query and **thrown away** unless the caller
asks for them, and [W-204 phase D](../../regression/2026-09-22-golden-final-score/FINAL-SCORE.md)
scored 11 716 rows without them and **could not compute the headline funnel at
all**. A run that skips the flag produces a complete-looking hand-off with the
headline metric's input missing.

```
Execute work/golden/README.md "Phase 5 — Run" for rung <RUNG> (e.g. rung-00100).
Read CLAUDE.md Non-negotiable constraints (law L11) and Conformance runs first.
No answer reaches you by any route, a paste included. If one does, STOP, say so,
and file it before anything else. A key MAY be on this machine since 2026-09-18,
at work/golden/golden-answers/ — it is Arpit's, and it is closed to you exactly
as the older spelling work/golden/golden-answer/ is. Never open, list, glob,
stat, hash or count either.

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
     fux ask "<q>" --json --band --why --top 10
     fux answer "<q>" --json
   --why is REQUIRED (SR-WORK-QUALITY decision 13). Its derivation.gates are the
   only place reachable and in_window exist, they are discarded when the query
   returns, and a filed run cannot get them back. On an arm whose ask has no
   --why (fux-engine 1.0.0), pass --no-why; that arm's gates are null, not zeros.
   Write evidence/predictions-set-1.jsonl and evidence/predictions-set-2.jsonl,
   one line per question, one file per set, never merged:
     {"id","ranked":[paths],"answerable":bool,"band":"..."}
4. Write the HAND-OFF, one file per set, evidence/handoff-set-N.jsonl, one line
   per question and self-contained — this is what Arpit gives Codex:
     {"id","question","answer_text","citations":[{"doc","lines"}],
      "ranked":[paths],"answerable":bool,"band":"...",
      "gates":{"reachable":int,"in_window":int,"placed":int,"answered":int,
               "cut_score":float},
      "rung":"<RUNG>","engine_commit":"..."}
   gates is the five integers from --why and NOTHING else from the derivation;
   it is null as a whole when the arm was not asked. answer_text and citations
   are what FUX produced. There is no golden answer in this file and there never
   will be.
5. Write report.md: the rung, the engine sha and commit, the counts per set, the
   band distribution, how many questions fux declined, HOW MANY ROWS CARRY
   FUNNEL GATES, the slowest and the emptiest results, and anything that looked
   wrong. Name the two handoff files as the thing to give Codex.
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
