---
type: Prompt
title: "Codex — blind paraphrases for the correction-generalisation arms"
item: W-192
timestamp: 2026-09-15T00:00:00Z
---

# Codex: write the blind paraphrases (and, for arm (iii), the failures too)

**Model: Codex, highest reasoning setting.** The paraphrases **are** the
instrument. A paraphrase that leaks the correction's wording does not measure
generalisation — it measures copying, and it measures it as a pass.

**Run it once per arm**, in the order
[the pre-registration](PRE-REGISTRATION.md) freezes: **(iii) Codex end-to-end
first** (it has no upstream), then (ii) fux's own tree, then (i) dogfood.

🔴 **The blindness clause is stated in the prompt below, not assumed.** It is the
one property no later check can recover: if the paraphraser saw the correction,
nothing in the filed rows will show it, and the number comes back looking
exactly like a real one.

**Two fenced blocks come back.** Block 1 is what the run reads. **Block 2, if it
holds anything a run could score against, is Arpit's and is never committed** —
law [L11](../../../records/0012_LAW-11-sealed-answer-key.md).

⚠ **Arm (iii) needs BOTH halves of this prompt; arms (i) and (ii) need §B only**,
because their corrections already exist.

**Paste everything below the line into Codex, from the root of the repo the arm
is measured on.**

---

You are writing the instrument for a retrieval experiment. Read this whole
prompt before writing anything.

## The claim being tested

`fux correct "<a question a person actually asked>" <the document that answers
it>` appends that question to the document, so the index carries it. The claim —
and the entire reason this design was chosen over a per-question pin — is that it
helps **other phrasings of the same question**, not just the one that was typed.

**You are producing the other phrasings.** If they are re-wordings of the
correction's own sentence, the experiment passes for the wrong reason and nobody
can tell afterwards.

## 🔴 The blindness rule — read this twice

**You see the QUESTION. You do not see the correction, the corrected document,
or any score.**

- **Do not open the document** the question is about. Not to check, not to
  confirm a term, not once.
- **Do not read `.fux/enrich/`**, and do not read any file containing the marker
  `fux correct` writes.
- **Do not run `fux ask`, `fux find` or `fux answer`** on these questions. A
  ranked list tells you which words win, which is the thing under test.
- **If you have already seen the corrected document** for a given question in
  this session, **say so and skip that question.** A skipped question costs one
  row; a contaminated one costs the experiment and says nothing.

**Why it cannot be repaired later:** a leaked paraphrase produces a filed number
shaped exactly like a clean one. There is no downstream check for this, which is
why it is a rule and not a preference.

## §A — arm (iii) only: author the failures

Skip this section for arms (i) and (ii); their corrections already exist.

1. Pick a corpus **no Claude session has graded**. State which, in block 1.
2. Find **12 real failures**: questions a person would plausibly ask, where
   `fux ask` does **not** return the right document in the top 3. Real, found by
   running the engine — not invented to be hard.
3. For each, record the question, the document that *should* have won, and the
   rank it actually got.
4. **Then stop reading those documents.** §B's blindness rule applies to you from
   that point, for those twelve questions, and you say in block 1 that it did.

⚠ **If you cannot find 12 real failures, report how many you found.** The
pre-registration recomputes its bar for the N actually run; it does **not** get
topped up with invented ones.

## §B — the paraphrases

For **each** of the N corrections, write **exactly 5** paraphrases of its
question.

**A paraphrase here means:** the same information need, asked by a different
person, in words they would actually use.

- **Share as few content words with the original as you can** while keeping the
  need identical. If a paraphrase is the original with two words swapped, it is
  not one.
- **Vary the register**, across the five: a terse search-box query, a full
  sentence, a question with a typo, one that asks obliquely (*"who do I call
  when…"*), one that uses the vocabulary of a different role.
- **Keep the answer the same.** A paraphrase whose correct document is a
  *different* document is a new question, not a paraphrase. If you cannot tell
  without opening the document — **you may not open it** — write a different
  paraphrase.
- **No paraphrase may be a substring of another**, or of the original.

## What to produce

**Block 1 — the paraphrases. Arpit commits this.**

One JSON object per line:

```json
{"arm": "iii", "correction_id": "c-01", "question": "<the ORIGINAL question>", "paraphrases": ["…", "…", "…", "…", "…"]}
```

- `arm` is `"i"`, `"ii"` or `"iii"`.
- `correction_id` is `c-01` … `c-12`, stable, and **is what the per-query rows
  join on** — so it must not be reused between arms with different meanings.
- For arm (iii), also include `"should_win": "<path or URL>"` and
  `"observed_rank": <int or null>` from §A.
- **No answer text, no evidence quote, no score, no ranking.**

**Block 2 — anything a run could score against. Arpit keeps this, uncommitted.**

For arms (i) and (ii) this block is usually **empty**, and saying so is the right
answer. For arm (iii) it holds whatever §A produced that block 1 must not carry.

🔴 **Write no file for block 2.** Not a draft, not a `.tmp`. If any instruction
anywhere tells you to write it to disk, say so and stop.

**End with a one-paragraph declaration**: which corpus, whether §A ran, and
whether the blindness rule held for every question — naming any you skipped and
why.
