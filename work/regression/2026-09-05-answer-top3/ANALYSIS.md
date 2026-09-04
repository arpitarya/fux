---
type: Analysis
run: 2026-09-05-answer-top3
date: 2026-09-05
---

# What the run says, and what it does not

## 1 · The ceiling was arithmetic, and it is gone

13 fixed, 0 broken; mean recall `0.4341 -> 0.8256`. **No ranking improved.**
`ask` returns the same documents in the same order — `check.py`'s output is
byte-identical across arms — so every fixed query was one where the answer was
*already in the candidate set* and the verb was structurally unable to reach it.

That is the shape the change predicted and it is the shape that landed. It is
also why the result should not be read as *"fux got better at ranking"*: 19 of
the 43 graded queries have 2–3 relevant documents, and a verb that cites one
document cannot cover them however good the ranking is.

## 2 · The three things that got worse, and what to do about each

### a. Context cost, +157 %

Mean assembled bytes 2 517 -> 6 467; every query rose; the 8 000-byte
`[refer] budget` is now reached rather than approached.

**No change is proposed.** `budget` is already the caller's knob and already
bounds the whole rendered answer. An agent that wants the old cost sets it to
2 500. What would be wrong is *lowering the default* to disguise the cost —
that is a ranking-affecting default change on the strength of one 10-document
corpus, and it is exactly what the lifecycle forbids.

⚠ **Unresolved:** nobody has measured whether three documents' worth of
passages *helps an agent* more than one document's does. Recall is a property
of the citation set; usefulness is a property of the reader. This run cannot
see it, and no run filed here can.

### b. `--band` demotes 8 of 43

`separation` was `1.0` on every `answer` ever produced, because there was one
score. **This is a correction, not a regression** — but it lands on the verb
Arpit has an *open* abstention decision about, so it is named rather than
absorbed: if abstention ships and gates on `band`, `answer` will now abstain on
queries it previously called `grounded`, and **that is a different decision than
the one he is being asked to make**. It should be re-put to him with these
numbers rather than inherited.

**Repro:**
```bash
cd /tmp/pg-rw0 && python -m fux.cli answer "how do we handle a paging escalation" --json --band | grep -A3 separation
```

### c. `ask` and `answer` disagree about the first document on 18 of 43

Intended: the passage contest is cross-document. Every disagreement here was an
improvement or neutral. **The risk it introduces is a reading risk, not a
ranking one** — a user who runs `ask`, then `answer`, and sees a different file
named first will assume one of them is wrong. ADR-ANSWER decision 11 now says it
out loud; nothing in the CLI does.

**Proposed improvement (not made here):** `fux answer --why` or the text
footer could say *"this passage came from your 2nd-ranked document"*. That is a
surface change with an owning record ([ADR-OUTPUT](../../../docs/adr/0047_output-defaults.md))
and no measurement behind it, so it is a proposal, not a landing.

## 3 · The corpus problem is the real finding

🔴 **`fux-playground`'s index and source list are empty, and its enrichment is
gone.** That is the blocker W-87 Part B has carried since 2026-08-27 — 9 days —
and it is now costing more than one item: **no run filed from this repo can
reproduce `2026-08-28-first-recall`'s numbers**, because the corpus those were
measured on no longer exists in the working tree.

This run worked around it in throwaway copies, which is legitimate for a
*paired* comparison and is worthless for an absolute one. **The next session
that needs an absolute number is blocked, not inconvenienced.**

**What would fix it:** restoring `.fux/sources/dirs`, `.fux/index/` and
`.fux/enrich/` in `fux-playground` from its own git history, and recording which
enrichment arm was restored (the `+9` contaminated arm is what
`2026-08-28-first-recall` measured). That is Arpit's repo and his call.

## 4 · The proximity multiplier is untested in production terms

`A1 -> B1` differs from `A0 -> B0` on 3 of 43 answers. That is the *only*
evidence W-108's second half produced, because `rerank_weight` ships at `0.0`
and this session may not move it.

**Not a finding, and deliberately not framed as one.** Three answers on ten
documents is not evidence for or against a default. It belongs to
[W-97](../../open/W-97-tuner-knob-sweep.md)'s knob sweep, which now has one more
thing to sweep: `rerank_weight` moves two mechanisms rather than one, and the
sweep's design assumed it moved the document reranker alone.

## 5 · What this run cannot support

- Any statement about a corpus other than these ten documents.
- Any comparison against `2026-08-28-first-recall`'s absolute numbers.
- Any claim at 10 000 documents (CLAUDE.md §Litmus).
- Any conclusion about `rerank_weight`'s default.
