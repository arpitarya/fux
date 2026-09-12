---
type: Analysis
description: "What the three instruments diagnose, turned into specific next steps with a repro command each, and what is left unresolved — including the one control this run retires and the gap its own recommendation carries."
items: W-142, W-144, W-115
run: 2026-09-12-reaim-and-instruments
classification: informed
filed: 2026-09-12
---

# Analysis — three instruments, and what each one costs

**Read [`report.md`](report.md) first.** Everything below is diagnosis.

Repro commands run from `~/my_programs/fux` with `.venv/bin/python`.

---

## 1. W-142 — the control is retired, and the lesson is about endpoints

**What was seen.** The heading-matched distractor count sits at
**2.06–2.14 per query** under every setting of `bm25f.heading` **and**
`bm25f.body`, including both fields switched off entirely. The corpus base rate
is **1.96**. `b = 42`, `c = 41`, p = 1.0000 over 83 discordant pairs.

```bash
.venv/bin/python tools/quality-controls/body_control.py --rung rung-01000
```

**Diagnosis.** 392 of 1 001 documents are `ext/sibling/`. A top-5 drawn at
random holds two of them. **The endpoint is a corpus-composition statistic
wearing a ranking statistic's clothes**, and three successive designs — C4's
boolean, the count rebuild, this re-aim — all measured the same inert number.

**What follows, specifically.**

1. **Retire it.** Done in this change: [ADR-RS](../../../docs/adr/0133_predictions.md)
   decision 22's table row, the item file, and OPEN-WORK.
2. 🔴 **Say what C1 and C3 rest on, out loud.** Generator assertions, since
   2026-08-28. That sentence is now in ADR-RS rather than pending a control.
3. **The mechanical half of the lesson is shipped:** `body_control.py` computes
   and prints the base rate **before** it runs an arm. A future distractor
   control that cannot beat its base rate says so in its first two lines.

⚠ **Do not build a fourth version of this control.** The fault is the endpoint,
not the field, and there is no third field to try. A control over these
distractors would need a different *question* — for example *does the correct
seed document rank above every sibling*, which is a `hit@1`-shaped question
against a key and therefore W-136 phase 5's job, not a control's.

---

## 2. W-144 — the number is decisive and the recommendation still has a gap

**What was seen.** 0/30 → 30/30, p ≈ 0, both controls holding, with the
transition located **between a table share of 0.26 and 0.29** — against a ladder
whose median share among table-bearing documents is **0.344**.

```bash
.venv/bin/python tools/quality-controls/w144_graded.py gen --dest ~/my_programs/fux-lab/corpora/w144-graded
.venv/bin/python tools/quality-controls/w144_graded.py run --corpus ~/my_programs/fux-lab/corpora/w144-graded
.venv/bin/python tools/quality-controls/w144_graded.py sweep --corpus ~/my_programs/fux-lab/corpora/w144-sweep
```

**Diagnosis.** The mechanism was never in doubt; what was missing was an
endpoint with both truth and headroom, and `df == 1` cost the last attempt the
second. Probe terms at `df` 4–23 fix it in one line of generator change.

**What follows, specifically.**

1. **A compare doc, and only a compare doc.**
   [`work/compare/table-tokens-in-flen.compare.md`](../../compare/table-tokens-in-flen.compare.md),
   status `proposed`. `CLAUDE.md` forbids shipping a ranking change off one
   synthetic corpus and this is one.
2. 🔴 **The gap in the recommendation, stated because it is the thing to press
   on.** Every probe's table is an **appendix**. There is no probe where the
   table *is* the answer — a rate card whose subject is its rows. Option (b)
   makes such a document shorter than it reads and gives its rare cell terms
   more idf leverage. **Not measured, and the compare doc says so.**
3. **If Arpit accepts (b)**, the code is already written and already verified:
   `split_body`'s rule agreed with the committed index on **330/330** and
   **994/994** documents. The work is the ADR amendment, the determinism check,
   and the re-measurement named in the reopen-trigger.

⚠ **Do not read 0/30 → 30/30 as an effect size.** It is a cliff because all 30
probes are built identically. **The threshold transfers; the sweep does not.**

---

## 3. W-115 — measured, and the previous diagnosis corrected

**What was seen.** `fence`: 0/30 → 30/30, p ≈ 0, and `decoy@1` 30 → 0 at
**every** prose weight from tf 1 to 8. `depth`: identical in both arms
everywhere. Selftest proves 60/60 treated decoys separable and 0/30 placebo
decoys separable.

```bash
.venv/bin/python tools/quality-controls/w115_instrument.py gen      --dest ~/my_programs/fux-lab/corpora/w115-fence-depth
.venv/bin/python tools/quality-controls/w115_instrument.py selftest --corpus ~/my_programs/fux-lab/corpora/w115-fence-depth
.venv/bin/python tools/quality-controls/w115_instrument.py run      --corpus ~/my_programs/fux-lab/corpora/w115-fence-depth
.venv/bin/python tools/quality-controls/w115_instrument.py sweep    --corpus ~/my_programs/fux-lab/corpora/w115-sweep
```

**Diagnosis, and the useful part is the correction.** The ladder run said the
corpus lacked *the formats W-115 touches*. It did not. `.rst`, `.adoc` and
`.org` **predate** W-115 and were untouched by it; what W-115 changed is
Markdown's fence awareness, which applies to `.md`, `.txt` and every decoded
document — 800 of the ladder's documents. **The ladder had the right formats and
the wrong content**: 1 document with a fenced heading, 2 with a deep key.

**A statement about a corpus's formats is not a statement about its content, and
the two were conflated for a day.** ADR-RS decision 23b already had the right
word for it — data defect — and the fix it implies is a generator change, not a
new format list.

**What follows, specifically.**

1. **Lift the prohibition for the heading half.** *"No document may cite W-115
   as measured"* has stood since 2026-09-06. It is lifted for the fence-aware
   grammar and **not** for anything else; `depth` is cited as *Inconclusive*.
2. **`refer/_chunk.py` remains unmeasured**, deliberately. It is a
   passage-boundary change and no endpoint here touches it. **Nobody should read
   this verdict as covering it.**
3. **Nothing is amended to claim `depth` is a ranking win.**
   [ADR-DECODE](../../../docs/adr/0139_decode.md) decision 16 justifies the cap
   as noise reduction and that justification is untouched by a null on a
   ranking endpoint.

---

## 4. One process change, and it is already in the code

All three tools were about to hard-code *"net >= 6"*. That is decision 19's
**floor of all floors** — the bar before the discordant count is known — and the
real bar rises with the flips. A tool comparing against 6 alone would pass a net
of 8 on 30 discordant pairs, which decision 19's own table refuses.

`tools/quality-controls/verdict.py` now computes the **exact two-sided binomial
p-value**, reusing `resolution.py` rather than reimplementing it. It reproduces
decision 19's table exactly, and it re-reads the heading control's filed
`b=16 c=21` as **p = 0.5114**.

⚠ **This changes no filed verdict.** Every conclusion the old floor supported
was *no detected change*, and decision 19's own note says those losses are
one-sided: a null under a loose bar stays a null under a strict one.

---

## 5. Unresolved, stated as unresolved

1. **Whether a document whose table IS its subject is harmed by W-144's
   recommendation.** Not measured, named in the compare doc, and the one thing
   that could overturn option (b).
2. **W-115's `refer/_chunk.py` half.** Unmeasured; needs a passage-boundary
   endpoint, which nothing in the queue has.
3. **`depth`'s ranking effect.** Inconclusive on this endpoint. It may have one
   on a corpus with deeply-nested configs as *subjects* rather than decoys; no
   item asks for that and none should be opened on speculation.
4. **What backs C1 and C3 now.** Nothing but generator assertions. Recorded, not
   fixed — and no item is filed, because the fix is a graded key and that is
   W-136 phase 5.

---

## 6. A process note, and this time it is the good one

**The instruments and their bars were committed at `aff3c82` before the first
number, and `git log` proves it.** The priors run could not claim that and said
so; this one can. The cost was ten minutes.

⚠ **Two instruments were then edited before their first number** — the probe
sets were widened and the verdict rule was changed from a flat floor to the
exact test. **Both edits happened before any measurement existed**, both are in
git, and **neither moved a threshold**: α stayed 0.05 and the exact test is
*stricter* than the flat floor at every discordant count above 6. The
pre-registration was amended in the same change rather than left describing a
tool that no longer existed.
