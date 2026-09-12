---
type: Reference
title: "work/golden/questions/ — the released questions, ids and text only"
item: W-136
timestamp: 2026-09-12T00:00:00Z
---

# `work/golden/questions/` — what a run is allowed to read

**`questions.jsonl` is the phase-4 input.** One JSON object per line,
`{"id", "question"}` and nothing else. A session running a rung reads this file
and does not ask anyone for it.

## What it deliberately does not contain

No `answer`, no `relevant`, no `primary`, no `evidence`, no `type`, no
`answerable`, no `difficulty`, no `sealed`, no `intent`, no `exercises`. Those
live in the key, which no Claude session reads
([`../README.md`](../README.md) §*The one rule*).

**Ids carry no signal either.** The rows were permuted with a fixed seed and
renumbered afterwards, so `g001`…`g124` is not ordered by type. That matters most
for the twelve `unanswerable` questions: if they sat in one id band, a runner
could abstain by arithmetic and the abstention slice would measure nothing.

## ⚠ Released early, on purpose, and it costs something

**`../README.md` says questions are released only after every rung is frozen**,
because a rung built by a session that could have seen them is `informed` for
good. This file exists **before** the ladder is built — Arpit's instruction,
2026-09-12, so a chat agent can run the questions without being handed them.

**So phase 2 is on its honour.** The session extending the corpus 10 → 10 000
reads `../seed/` and nothing else — **not this file** — and says so in its report.
If it reads this file, the ladder is `informed` permanently and no delta measured
on it may be stated.

## The key these questions belong to

The current key is **Claude-authored and provisional** —
[W-145](../../open/W-145-codex-regenerates-the-key.md). Every number scored
against it is `informed` regardless. When Codex regenerates the key, **this file
is regenerated with it**: the ids will change, and a prediction file written
against the old ids is worthless.

## Regenerating this file from the key

Codex, holding the key, emits one line per row:

```json
{"id": "<id>", "question": "<question>"}
```

in the key's own row order, and copies no other field.
