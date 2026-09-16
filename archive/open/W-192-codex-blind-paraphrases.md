---
type: OpenItem
id: W-192
title: "W-192 — the blind paraphrases W-175 needs, which Codex's question sets are not"
description: "W-175's 🟣 read 'waiting on Codex, 2026-09-30'. Codex delivered the question sets on 2026-09-15 and they are not paraphrases — a different artifact, written against corrections that do not exist yet. Filed under SR-WORK-OPEN-QUEUE 23a so the wait names something real."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-192 — the blind paraphrases

**Model: Opus** for the prompt and the arm design; the writing is **Codex's**.

## Why this exists

[W-175](W-175-correction-generalisation.md) sat 🟣 on *"Codex's blind
paraphrases, 2026-09-30"*. **Codex became available on 2026-09-15 and wrote the
question sets** — which are not paraphrases. The date gate is void; the artifact
is still missing; and nothing in the queue was going to produce it.

## What a paraphrase is here, and why Claude cannot write one

- **M = 5 held-out paraphrases per correction, N = 12 corrections per arm**
  (accepted 2026-09-14).
- **Blind means the paraphraser sees the *question* only** — never the corrected
  document, never the correction, never a score.
- 🔴 **A paraphrase written by anyone who has seen the correction is the
  correction's own wording in disguise**, and the whole claim under test is that
  a correction helps phrasings *other* than its own. Claude cannot write these at
  any distance; neither can the session that filed the correction.

## The dependency nobody has stated plainly

⚠ **The paraphrases cannot be written before the corrections exist**, and the
corrections come from two arms that are still accruing:

| arm | the corrections come from | status |
|---|---|---|
| (i) dogfood | Arpit running fux on his own repositories, filing `fux correct` as he hits a wrong answer | **accruing** — this is elapsed time, not work |
| (ii) fux's own tree | golden-style questions over `records/`, `work/`, `docs/`; Arpit spot-checks the misses | the questions are agent work and can start |
| (iii) Codex end-to-end | Codex authors the failures **and** the paraphrases, on a corpus no Claude session graded | Codex's, start to finish |

**So this item's first job is to say which arm goes first**, because (iii) needs
nothing from anyone else and (i) needs twelve real corrections Arpit has not
filed yet.

## Definition of done

1. **Write the Codex prompt** Arpit runs — the blindness clause stated in it, not
   assumed.
2. **Name the arm order**, with (iii) as the candidate for first since it has no
   upstream.
3. Hand over the paraphrases per the two-block shape: block 1 is what the run
   reads; **block 2, if it contains anything a run could score against, is
   Arpit's** ([SR-LAW-11](../../records/0012_LAW-11-sealed-answer-key.md)).
4. W-175's harness is **already agent work and does not wait on this** — file the
   corrections, re-ingest, run the paraphrases before/after, per-query rows.

## Closes

Unblocks [W-175](W-175-correction-generalisation.md)'s measured arms.
