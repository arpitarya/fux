---
type: Handoff
name: W-272
description: "Arpit's ask (2026-10-10, Cowork): the test data the section-records re-test needs — generation 5's six new long documents, at least twelve short competitors and set-6-claude (about 110 questions, at least 60 tagged step10_section), authored by an isolated claude.ai chat from prompt 14. L13 decision 5 requires a fresh set: set-5-claude has already decided two section mechanisms."
item: W-272
filed: 2026-10-10
ball: closed
---

# W-272 — section records: generation-5 test data (`set-6-claude`)

**Status: CLOSED 2026-10-11.** Arpit ran prompt 14 and left blocks 1–3 in `set-6-claude-gen5/` at the repo root; on his *"yes"* (2026-10-11, Claude Code) a session moved them into place and deleted the prompt. **Block 4, the key, was never in that directory** (file names and the questions' keys were checked first: `id` and `question` only); where Arpit keeps it no agent checks (L11).

**Arpit, 2026-10-10 (Cowork):** *"create work items for whatever is needed for
sections. Create one work item for implementation and one work item if test
data needs to be generated."*

**Test data is needed.** `set-5-claude` has decided W-236 and W-269, so under
[L13](../../records/0015_LAW-13-the-standing-bar.md) decision 5 it may report a
third section mechanism but never decide it. The re-test
([W-270](../../work/open/W-270-section-retest-set-6.md)) needs a set this model family has not
tuned against, and documents built so the section term can move it
([SR-RS](../../records/0133_predictions.md) decision 23).

**Model:** the author is **Claude Opus, highest reasoning, in a brand-new plain
claude.ai chat** — no repository, no tools, no project (the A1 designation). The
check in DoD 3 is **Sonnet** against the written counts.

## Definition of done

| DoD | state | where |
|---|---|---|
| 1 · the authoring prompt, written from SR-WORK-TESTDATA | ✅ 2026-10-10 (moved from W-270) | prompt 14 (deleted by DoD 4; `git log --diff-filter=D -- work/golden/prompts/`) |
| 2 · 🔴 **Arpit** runs it in a fresh claude.ai chat; commits blocks 1–3 (documents, `seed-dates.tsv` rows, `questions/set-6-claude.jsonl`); puts block 4, the key, into `work/golden/golden-answers/` by his own hand | ✅ 2026-10-11 — blocks 1–3 committed on his *"yes"*; the key is his | [`seed/`](../../work/golden/seed/) 89–112 · [`seed-dates.tsv`](../../work/golden/seed-dates.tsv) · [`set-6-claude.jsonl`](../../work/golden/questions/set-6-claude.jsonl) |
| 3 · the released half checked against the prompt's counts: 6 new long documents, ≥ 12 short competitors, ≈ 110 question ids `s6c-…`, each `seed-dates.tsv` row present | ✅ 2026-10-11, **Sonnet**, all PASS — 6 long (2 596–3 847 words, 18–20 sections); 18 short (117–234 words): 95–106 pair two per long document, and 107–112 are each long document's **superseded predecessor** (`superseded_by:`), the `retired_competitor` shape; 110 ids `s6c-001…110`, keys `id` + `question` only; 24 date rows, 2025-01-06…2026-08-20, no duplicate path | the committing change |
| 4 · prompt 14 deleted in the change that commits its data (SR-WORK-TESTDATA: prompts are disposable copies) | ✅ 2026-10-11 | the committing change |

## What the data must carry (from prompt 14, stated by SR-WORK-TESTDATA)

- **Six new long, multi-section documents**, each answering at least nine
  questions from **different** sections, and at least **two short competitors**
  per long document that share the question's words and are wrong.
- **`set-6-claude`**: ≥ 60 `step10_section`, ~11 `unanswerable`, ≥ 35 `other`
  (harm elsewhere must be visible — it is L13's C2).
- **Why ≥ 60 tagged:** L13's slice floor is 15 winnable questions at baseline;
  W-269's 45 tagged gave 23.

## Custody

- 🔴 **The key is Arpit's** ([L11](../../records/0013_LAW-11-sealed-answer-key.md)).
  No session writes, reads or receives block 4. The tag counts DoD 3 cannot see
  are checked by the scorer's pool counts in W-270, not here.
- **The session that wrote prompt 14 read W-269's scores, so it may not author**
  (A1). So may no session that has read this item's sibling verdicts.
- `informed`, permanently (A5).

## Records this will touch

No SR affected — test data only. `work/golden/README.md` names the generation.
