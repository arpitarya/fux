---
type: Analysis
name: golden-rung-00100-analysis
description: "The scored result of phase 5 on rung-00100 — filed as the record of an L11 BREACH, not as citable evidence. Both sets informed; set 1's blind status is spent. Plus the pre-scoring analysis, kept unedited below."
---

# `rung-00100` — the scored run, and the breach that produced it

> 🔴 **Read the provenance block before any number below it.** Two separate
> things make every figure here non-citable, and neither is a formality.

---

## 🔴 Provenance — who scored this, how, and what it may be used for

**A 2026-09-17 Cowork Claude session was pasted BOTH answer keys** — set 1
(125 rows) and set 2 (124 rows), `key_version 1` — **and scored them in the
chat.** [L11](../../../records/0012_LAW-11-sealed-answer-key.md) reserves the
paste route to Codex and closes it to every Claude session on every surface.
**The instruction to score was void on the law's face** (L11 decision 8) and the
session complied with it.

| | |
|---|---|
| scored by | **a Cowork Claude session**, in chat, 2026-09-17 |
| against | **both keys, pasted** — the route L11 gives to Codex alone |
| prompt shape | [prompt 6E](../../golden/prompts/6E-codex-score-ephemeral.md)'s: unpooled, no per-query rows, sealed reported in aggregate only |
| per-query rows filed | 🔴 **none** — 6E writes nothing, so [SR-RS](../../../records/0133_predictions.md) decision 19's paired floor **cannot be computed from this run** |
| reproducible by an agent | 🔴 **no, by construction.** Scoring needs a key; no agent may hold one. **This is provenance, not a gap to close** — nobody is to "re-check" these numbers |
| set 1 | **`informed (L11 breach 2026-09-17)`** — its blind status is spent |
| set 2 | **`informed`, permanently** — [SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 2; its author and its runner are one model family |

🔴 **No number in this run is labelled `blind`, and none may be.** ⚠ The word
itself appears here and in `report.md` — always as a negation, never as a label
on a figure. **A `blind` label on any count in this directory is wrong on its
face.**

### Two independent reasons no number here may be cited

1. **6E's own rule.** [Prompt 6E](../../golden/prompts/6E-codex-score-ephemeral.md)
   states it in bold: *"A number from 6E may not be cited in any record, compare
   doc, CHANGELOG entry or work item, and may not be compared with any other
   golden number in either direction."* **That rule is carried forward here
   unchanged.** The numbers are filed because a declared breach must be filed
   (L11 decision 10), **not** because filing promotes them to evidence.
2. **The breach.** Set 1 was the only half of this benchmark with a clean
   authorship story. It no longer has one.

⚠ **So this directory is two things at once, and the distinction is load-bearing:**
the **prediction** run of 2026-09-16 (what fux answered and ranked — filed,
legitimate, unaffected) and a **scored overlay** added 2026-09-17 that is a
breach record. **The five items behind [W-136](../../open/W-136-golden-benchmark.md)
— W-87, W-176, W-190, W-191 — are NOT unblocked by this.** They need filed
per-query rows from prompt 6, and none exist.

### What was NOT done, deliberately

- **No re-scoring, no verification of any figure by any agent.** It is not
  possible and it was not attempted.
- **No pooled figure across the two sets** — no mean, no total, no "both sets"
  row. [SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 9.
- **No answer text, evidence quote, relevant-document name, key row, or
  per-question verdict** appears in this directory. Counts only.
- **No sealed id, question or outcome is reported individually** — sealed slices
  are aggregates.
- 🔴 **`PRE-REGISTRATION.md` was NOT edited**, although the filing instruction
  listed it. **A frozen pre-registration is never edited** (SR-RS decisions 1 and
  10b; the worked precedent is decision 18, which corrects a frozen document from
  elsewhere rather than touching it). Everything that would have gone into it is
  in this file instead.

---

## The numbers, per set, never pooled

**Run:** `rung-00100` · `engine_commit 7d17519b70616060c1f5b73a2abf4b34e5f8c50f`
(stamped on every hand-off row) · inputs
[`evidence/handoff-set-1.jsonl`](evidence/handoff-set-1.jsonl) (125) and
[`evidence/handoff-set-2.jsonl`](evidence/handoff-set-2.jsonl) (124).

⚠ **`ranked` is capped at 10 per row** — verified mechanically, max length 10 on
all 249 rows — so `rank_first_relevant ≤ 10` and **"no hit" means *not in the
top 10*, never *absent from the corpus***.

**Retrieval denominators are key-answerable ids only.** Every hit and recall
figure is **`unpooled — lower bound`**: nothing was judged into `relevant`, so a
correct document the key does not already list counts as a miss.

### Set 1 — Codex-authored · **`informed (L11 breach 2026-09-17)`**

125 questions = **113 answerable + 12 unanswerable**; **100 non-sealed + 25 sealed**.

| retrieval | non-sealed, `n = 90` | sealed, `n = 23` (aggregate only) |
|---|---:|---:|
| `hit@1` | **55.6 %** (50) | 56.5 % (13) |
| `hit@5` | **85.6 %** (77) | 82.6 % (19) |
| `recall@5` | **78.9 %** | 81.2 % |
| mean `rank_first_relevant` | **2.29** (n = 89 with a hit) | 1.90 (n = 21) |

*Every cell above: `unpooled — lower bound`, `informed (L11 breach 2026-09-17)`.*

| abstention | all | sealed slice |
|---|---:|---:|
| declined | **36** | 7 |
| `abstain_correct` | **3** | 0 |
| declined-but-answerable | 🔴 **33** | 7 |
| answered-but-unanswerable | **9** | 2 |

| answer text | all | sealed slice |
|---|---:|---:|
| `supported_and_correct` | **58** | 14 |
| `supported_but_wrong` | **31** | 4 |
| `unsupported` | **0** | 0 |
| `declined` | **36** | 7 |

### Set 2 — Claude-authored · **`informed`** (permanent)

124 questions = **112 answerable + 12 unanswerable**; **99 non-sealed + 25 sealed**.

| retrieval | non-sealed, `n = 89` | sealed, `n = 23` (aggregate only) |
|---|---:|---:|
| `hit@1` | **41.6 %** (37) | 47.8 % (11) |
| `hit@5` | **82.0 %** (73) | 73.9 % (17) |
| `recall@5` | **68.4 %** | 63.8 % |
| mean `rank_first_relevant` | **2.25** (n = 79 with a hit) | 2.21 (n = 19) |

*Every cell above: `unpooled — lower bound`, `informed`.*

| abstention | all | sealed slice |
|---|---:|---:|
| declined | **52** | 7 |
| `abstain_correct` | **4** | 0 |
| declined-but-answerable | 🔴 **48** | 7 |
| answered-but-unanswerable | **8** | 2 |

| answer text | all | sealed slice |
|---|---:|---:|
| `supported_and_correct` | **35** | 9 |
| `supported_but_wrong` | **37** | 9 |
| `unsupported` | **0** | 0 |
| `declined` | **52** | 7 |

### The join, and the one check an agent could run

**Ids complete and contiguous on both sides, no orphans, no hard stop.**
Independently re-derived here from the committed hand-offs, which needs no key:
`s1-001…s1-125` (125 unique) and `s2-001…s2-124` (124 unique), one
`engine_commit` and one `rung` across all 249 rows.

**Every count above is internally consistent**, checked as arithmetic rather than
taken on trust — `3 + 33 = 36`, `3 + 9 = 12`, `58 + 31 + 0 + 36 = 125`;
`4 + 48 = 52`, `4 + 8 = 12`, `35 + 37 + 0 + 52 = 124`; `90 + 23 = 113` and
`89 + 23 = 112` against the stated answerable counts. ⚠ **That is a consistency
check, not a verification** — a self-consistent set of counts from a key nobody
may re-read is still unverifiable.

---

## Findings

### 1 · Abstention is not independent of the band

**`band:weak` ⇔ `answerable:false` in 88/88 rows across both sets.**

This is the pre-scoring run's Finding 2 surviving contact with the key. The
consequence is unchanged and now matters more: **the band column and the decline
column carry one number**, so any stratification by band is a stratification by
decline, and a reader comparing them compares a thing with itself.

### 2 · `unsupported = 0` is mechanically checked, and the check covers a minority of rows

**For the 79 rows whose every citation resolves to a committed document, every
line of `answer_text` matches a cited document verbatim** — markdown/txt exact;
`.html`/`.eml` spans differ from raw bytes only by decoding.

🔴 **The other 170 rows cite generated sibling documents that are not committed,
so their spans cannot be re-checked.** **That is a limit of the check, not a
pass.** `unsupported = 0` is established for 79 rows and is *unestablished* —
not refuted — for 170.

⚠ **And the 79 is not reconstructible from the committed evidence.** Re-derived
here two ways: rows whose every citation sits under the committed `seed/` tree
give **96**; the same restricted to rows fux did not decline gives **65**.
Neither is 79, so **the scoring session's row set cannot be recovered**, and the
79 is recorded as reported rather than as reproduced. It is one more thing this
run cannot hand to the next reader.

### 3 · `answer_text` is an unsynthesised ranked dump, and "wrong" sometimes means "mis-ordered"

*"Agrees with the key"* was read as **the value the dump serves FIRST**.

**8 of set 1's and 4 of set 2's `supported_but_wrong` rows carried the key's
value lower in the same dump, behind a rival value.** Those are **recoverable by
ranking, not by generation** — the right bytes were fetched and put in second
place.

### 4 · ~12 rows across both sets were marginal judgement calls

Right substance from a sibling-corpus document, or a multi-part answer
half-served. **Stated so the counts are not read as sharper than they are**: on a
set this size, twelve rows is larger than most differences anyone would want to
claim.

---

## 🔴 The difficulty breakdown is BLOCKED — and was not derived

[Prompt 6E](../../golden/prompts/6E-codex-score-ephemeral.md) step 7 asks for
every count above **broken down by the key's `difficulty_band`**. **It was not
produced, and could not be.**

**Why.** The scoring session reported that **neither key carries `difficulty`,
`difficulty_static` or `difficulty_band`** — the fields present being `id`,
`question`, `answer`, `answerable`, `relevant`, `primary`, `evidence`, `type`,
`sealed`, `key_version`, `intent`, `exercises`. That is consistent with
[`work/golden/README.md`](../../golden/README.md): the band is **computed** by
[`tools/golden-difficulty/`](../../../tools/golden-difficulty/), and nothing
carries a label yet.

⚠ **Recorded as reported, not as verified.** Checking a key's shape or schema is
Arpit's and Codex's work, permanently
([SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 12). No agent
confirmed this field list and none may.

🔴 **The band was NOT derived from anything else, and must not be.** Not from
`type` — [SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) decision 13 and
[W-190](../../open/W-190-question-difficulty.md) both forbid a re-encoding of
`type`. Not from the hand-off rows. **And never from fux's own results**, which
would make every stratified claim a tautology.

**So prompt 6E step 7 is unsatisfiable as written against `key_version 1`**, and
that is a defect in the prompt rather than in the run. Filed as
[W-195](../../open/W-195-difficulty-band-breakdown.md), waiting on
[W-190](../../open/W-190-question-difficulty.md).

---

## What this run changes, and what it does not

| | |
|---|---|
| ✅ **files** | a declared L11 breach, with every number labelled and fenced |
| ✅ **establishes** | nothing citable. That is the intended outcome, not a shortfall |
| 🔴 **does not unblock** | W-87 · W-176 · W-190 · W-191 — they need prompt 6's per-query rows |
| 🔴 **does not authorise** | any engine change. **No proposal, no tuning, no ranking move may be made off these numbers**, and none was made in the session that filed them |
| 🔴 **costs** | set 1's blind status. Arpit's ruling is owed: re-authorship, or set 1 relabelled `informed` permanently — [W-196](../../../archive/open/W-196-l11-breach-2026-09-17.md) |

### A record change to PROPOSE, not to write

**[SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) has no decision covering
a key that has already reached a Claude context.** L11 decision 10 says *declare
it*; nothing says what the benchmark then **is**. The open question —
*is a set whose key has been seen retired, re-authored, or kept and relabelled?*
— is Arpit's ruling and is **not** taken here. Proposed only, in
[W-196](../../../archive/open/W-196-l11-breach-2026-09-17.md).

---
---

# What was said before anybody scored this

*Unedited, as filed 2026-09-16. Kept because the prediction run is legitimate on
its own and its reasoning is what the scored numbers above either confirmed or
did not.*

## The decline gap is the instrument working, not a result

**Set 2 declines on 41.9 % of its questions; set 1 on 28.8 %.** Same corpus, same
engine, same 100 documents, same day — **different authors.**

🔴 **Two readings survive the evidence, and nothing here chooses between them:**

| if the extra declines land on… | then it is |
|---|---|
| questions whose answers **are** in the corpus | a **recall** problem — fux is giving up on answerable questions |
| questions that are genuinely **unanswerable** | **abstention working**, and set 2 simply contains more of them |

**Only the key can tell those apart**, and the key is Codex's. A report that
picked one would be guessing in a document the next reader trusts.

⚠ **UPDATE 2026-09-17 — the key answered it, and the answer is the first
reading.** Set 2's 52 declines are **48 declined-but-answerable** against **4**
correct abstentions; set 1's 36 are **33 against 3**. **It is a recall problem in
both sets**, and the gap between them is a gap in how much of one. ⚠ **That
sentence rests on a breached key and is not citable** — see the provenance block
at the top of this file.

⚠ **What it does establish** is that question authorship changes what the engine
does, measurably, on identical data. That is the entire argument for having two
sets rather than one, and it has now been observed rather than assumed.

## `weak` ⟺ `declined`, exactly, 249 times

Not a correlation — **an identity**. Every `weak` question is declined and every
declined question is `weak`, in both sets, with no exception.

**That is [SR-CONFIDENCE](../../../records/0141_confidence.md)'s gate as Arpit
ruled it on 2026-09-14**, observed at scale. Two consequences worth stating:

1. **The band column and the decline column carry one number.** A reader
   comparing them is comparing a thing with itself.
2. 🔴 **It means `weak` is not a third state.** The confidence block presents
   four bands and this corpus exercises three, of which one *is* the decline.
   [W-176](../../open/W-176-abstention-gates.md)'s gates are built on that
   ruling; this is the first corpus-scale confirmation that the implementation
   matches it.

## The one thing here that will not reproduce

🔴 **`[bm25f] b` moved from `0.75` to `0.15` hours before this ran.**

Every ranked order in the hand-off is the **new** ranker's. The committed index
is untouched — `b` is query-time — so the same rung, the same questions and an
engine from yesterday would produce a **different** `ranked` array for many of
these 249 questions.

**Consequences, stated rather than left to be discovered:**

- **No golden number filed before 2026-09-16 may be compared with a number
  scored from these hand-offs.** They measure different rankers.
- **The hand-off carries `engine_commit` on every line** precisely so this is
  checkable later rather than remembered.
- ⚠ **Re-running phase 5 after any future ranking change produces a different
  hand-off from the same questions**, which is correct and is why the rung, the
  commit and the date are on every row.

## What this run cost, and what the next one will

**498 `fux` calls, about four minutes**, p50 71 ms for `ask` and 88 ms for
`answer`. Flat across both sets.

⚠ **`rung-10000` is 100× the corpus, not 100× the time** — retrieval is not
linear in documents — but it is the same 498 calls, and the item's own estimate
should be taken from a measured rung rather than from this one.

## What is NOT in this analysis

- **No score, no accuracy, no hit rate, no judgement of any answer.** Prompt 6's.
  ⚠ **Overtaken 2026-09-17** — scores exist above, from a breach, and are not
  citable. Prompt 6 is still the one that produces evidence.
- **No claim that either set is better or harder.** ⚠ **Still true.**
- **No comparison against another rung or another engine.** ⚠ **Still true.**
