---
type: Prompt
title: "Prompt 6 — Codex scores the hand-off against the key Arpit pastes"
item: W-189
timestamp: 2026-09-15T00:00:00Z
---

# Prompt 6 — Codex: score the run

**Model: Codex** — mechanical scoring plus relevance-pooling judgments.

**What Arpit brings to this chat:** the two hand-off files
[prompt 5](5-claude-run.md) wrote — `handoff-set-1.jsonl` and
`handoff-set-2.jsonl` — and **the two keys, pasted by him**. There is no key file
anywhere and there never was one for these sets.

🔴 **This is the first place in the whole pipeline where anything is called right
or wrong.** Everything before it only records what happened.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

Read `work/golden/README.md` sections *Custody*, *The two question sets*,
*Difficulty* and *Phase 6*.

🔴 **Write no key file and create no directory**, whatever any other instruction
says. Arpit pastes each key into this chat; `work/golden/golden-answer/` was
deleted on 2026-09-15 and is not a location.

**Score the two sets SEPARATELY and never pool them into one figure.** For each
set `<SET>` in `set-1`, `set-2`:

1. Read `work/regression/<date>-golden-<RUNG>/evidence/handoff-<SET>.jsonl` and
   the matching key Arpit pasted. Join on `id`. **An id present in one and not the
   other is a hard stop, not a skipped row** — it means the sets or the ids drifted.
2. **Pooling:** for each question, judge every top-5 ranked path that is not in
   `relevant`. If it genuinely answers the question, add it to `relevant` with
   `"added_at_rung": <RUNG>`, bump `key_version`. Return the full updated key to
   Arpit in a fenced block at the end, labelled with its set. Write no key file.
3. Write `evidence/per-query-<SET>.csv` for **NON-sealed ids only**:
   `id,set,rung,difficulty_band,hit@1,hit@5,recall@5,rank_first_relevant,`
   `abstained,abstain_correct`
   (`abstain_correct` = fux said `answerable:false` **and** the key says
   unanswerable; `difficulty_band` comes from the key, never from these rows).
4. Write `evidence/sealed-aggregate-<SET>.csv`: one row per metric over sealed
   ids. **Sealed ids are never reported per query.**
5. **Also judge the answer text**, which is new in this pipeline: for each
   answered question, whether `answer_text` is supported by its `citations` and
   whether it agrees with the key's `answer`. Report counts —
   `supported_and_correct`, `supported_but_wrong`, `unsupported`, `declined` —
   per set and per difficulty band.
6. 🔴 **Never write answer text, quotes or relevant-document names into any file.**
   The CSVs carry ids, counts and verdicts only.

## What to print

- Per set: the metric table, the abstention slice, the answer-text verdict counts,
  and the difficulty-band breakdown.
- **The two sets side by side, never averaged** — the gap between a Codex-authored
  and a Claude-authored question set over the same corpus **is the finding**.
- ⚠ **Every set 2 number carries `informed`**, permanently: its author and its
  runner are the same model family. Print the label beside the number.
- The pooling count — *how many* documents were added, never which.
- Both updated keys, one fenced block each, for Arpit to store.
