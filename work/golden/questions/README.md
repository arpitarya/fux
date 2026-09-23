---
type: Reference
title: "work/golden/questions/ — the released questions, ids and text only"
item: W-189
timestamp: 2026-09-15T00:00:00Z
---

# `work/golden/questions/` — what a run is allowed to read

**One file per live set.** Each is a run's input: one JSON object per line,
`{"id", "question"}` and nothing else. The generation-1 sets retired to
[`../retired/`](../retired/).

| file | set | author | ids |
|---|---|---|---|
| `set-2-u.jsonl` | set 2-u | Claude | `s2u-001…` |
| `set-3-u.jsonl` | set 3-u, 80 questions, against seeds 23–36 | Claude, [prompt 10](../prompts/10-claude-feature-input-seed.md) | `s3u-001…` |

**Arpit commits these himself**, from block 1 of each authoring prompt's
two-block handoff. Block 2 — the key — he keeps; **no agent writes either file's
answers anywhere**.

## What they deliberately do not contain

No `answer`, no `relevant`, no `primary`, no `evidence`, no `type`, no
`answerable`, no `difficulty`, no `sealed`, no `intent`, no `exercises`. Every
one of those lets a runner score without retrieving; `answerable` and `type` are
the sharpest, because either hands over the abstention slice outright.

**Ids carry no signal either.** Each author permutes its rows with a fixed seed
and numbers them afterwards, so `s1-001…` is not ordered by type. That matters
most for the ~10 % unanswerable questions: in one id band, a runner abstains by
arithmetic and the abstention slice measures nothing.

## ⚠ These files exist before the ladder is rebuilt, and it costs something

A rung built by a session that could have read a question is `informed`
permanently. **So [prompt 4](../prompts/4-claude-corpus.md) is on its honour**:
it reads `../seed/` and nothing else, and says so in its report. Nothing
mechanical enforces it.

## Reset — 2026-09-15

🔴 **The previous `questions.jsonl` (124 rows, `g001…`) was deleted by Arpit**,
along with the provisional Claude-authored key it belonged to. **Every prediction
file and regression row keyed to those ids is orphaned** — the ids do not come
back and are never reused. Numbers already filed against them stay as filed
history and **may not be compared with anything scored on set 1 or set 2**.
