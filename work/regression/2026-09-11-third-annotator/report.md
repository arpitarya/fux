---
type: Run Report
run: 2026-09-11-third-annotator
classification: blind
date: 2026-09-11
---

# A third blind annotator settles the 7 `partial` goldens: grader 2 was right on all 10 disputed documents

**The item:** OPEN-WORK *"The 7 `partial` goldens"* — the exact-set disagreements
between the two blind annotators of
[`2026-08-28-annotator-agreement`](../2026-08-28-annotator-agreement/report.md),
held out of `recall@k` until a human or a third blind reader resolved them.
**Arpit, 2026-09-11:** *"you do the analysis and tell me which one is the correct one."*

## Authorship — classification `blind`

| artifact | author | could reach |
|---|---|---|
| annotator 3's judgments | a fresh Opus subagent, 2026-09-11 | the ten `docs/` files of `fux-playground` (`3b4d275`) in an isolated folder + the 7 question texts — **none** of: the goldens, annotators 1 and 2, any score, `fux` |
| the tie rule, this report, `per-query.csv` | Cowork (Opus), **informed** | everything, including both prior annotators and the goldens' `doc`/`max_rank` |

⚠ **Isolation was instructed, not enforced.** The subagent ran in a container that
also held this session's earlier tool output (which includes annotators 1 and 2).
It was told to read only the corpus folder and made 5 tool calls; that it read
nothing else is a stated instruction, not a proof.

⚠ **The relevance definition given to annotator 3 was written for this run** — the
brief annotators 1 and 2 received is not filed. It was: *the document contains
information a person asking this question would use to answer it; merely mentioning
the topic does not count.*

## The tie rule — fixed before annotator 3's output was read

- **A document is in dispute** when exactly one of annotators 1 and 2 included it.
- **Annotator 3 decides each disputed document** — 2 of 3 votes.
- A document **neither** original annotator included is **not** in dispute; two of
  three readers already excluded it, so annotator 3 alone cannot add it.

## Result

**10 documents were in dispute across the 7 questions. Annotator 3 included all 10.**
Every disputed document was one annotator 2 had added and annotator 1 had left out.

| id | question | disputed document(s) | 3rd vote | resolved set = |
|---|---|---|---|---|
| q020 | which rollback do I use for a tier that has not migrated | ADR-0019 | ✅ | annotator 2 |
| q021 | why is the soak fourteen days now instead of two | checkout postmortem | ✅ | annotator 2 |
| q027 | the rollback failed should I try it again | checkout postmortem | ✅ | annotator 2 |
| q032 | does the superseded networking ADR still apply anywhere | legacy mesh runbook | ✅ | annotator 2 |
| q039 | what happens if I never state a classification | calderctl reference | ✅ | annotator 2 |
| q042 | why is having two rollback procedures dangerous | both rollback runbooks | ✅ ✅ | annotator 2 |
| q050 | a hazard we wrote down but never actually fixed | both rollback runbooks | ✅ ✅ | annotator 2 |

**The resolved sets equal the `relevant` arrays already in `goldens/queries.jsonl`**
(the union was annotator 2's set in every case). Only `relevance` changes:
`partial` → `complete`. Per-document votes: [`evidence/per-query.csv`](evidence/per-query.csv).

## Four documents annotator 3 added that nobody else did — not applied

| id | document | annotator 3's reason |
|---|---|---|
| q020 | calderctl reference | "`calderctl mesh` — Applies only to tiers still on Helix Mesh" |
| q027 | on-call rota guide | "18 of those minutes were a second rollback attempt the runbook explicitly says not to make" |
| q032 | calderctl reference | same line as q020 |
| q032 | onboarding guide | "Helix Mesh if not [migrated]" — marked weaker |

**Excluded by the tie rule, 1 vote of 3.** Post-hoc and informed: the q027 and q020
additions read as genuine answers, which suggests the goldens' sets may still be
**incomplete** in places — the same direction the 2026-08-28 run found. That is not
resolved here and is not a reason to move the rule after the fact.

## What this run may never be used to say

- It does not grade the engine. No score was computed.
- It does not certify the other 43 sets complete.
