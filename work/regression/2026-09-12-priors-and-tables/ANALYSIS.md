---
type: Analysis
description: "What the five-item campaign diagnoses, turned into specific next steps with a repro command each, and what it leaves unresolved."
items: W-143, W-97, W-142, W-144, W-115
run: 2026-09-12-priors-and-tables
classification: informed
filed: 2026-09-12
---

# Analysis — priors, tables and headroom

**Read [`report.md`](report.md) first.** Everything below is diagnosis.

Repro commands run from `~/my_programs/fux` with `.venv/bin/python`.

---

## 1. The priors: the decision moves from *"which value"* to *"whose question"*

**What was seen.** Every value of every prior that perfects current-seeking
destroys history-seeking, one probe for one probe; `recency_half_life_days`
takes history-seeking to 0/13. No candidate clears on more than one rung, and
every clearing net is 1 or 2 against a floor of 6. [Verdict](VERDICT-W143.md).

```bash
.venv/bin/python tools/quality-controls/priors_sweep.py --rung rung-seed --knob superseded_weight
```

**What follows, specifically.** The knob is not mis-tuned — it is the wrong
shape. A **per-document multiplier** is asked to carry a **per-query**
distinction, and it cannot, so any global default is a choice about which half
of the users to serve. Three things could follow and only the third is a
session's to start:

1. **Close the knobs** — W-143's option (c). **Arpit's call**, and this verdict
   is the evidence for it rather than the taking of it.
2. **Move it query-side** — a query carries its intent, so the multiplier is
   applied per ask rather than per document. **No record has opened this**, and a
   session must not open it by implementing it.
3. **Nothing, and say so.** The priors ship at their no-op defaults and the
   documents stop describing them as tunable quality levers.

⚠ **Do not "fix" this by widening the grid.** Every value between 1.0 and 0.0
was swept, `0.0` included; the answer is not in a gap between grid points.

## 2. `rerank_weight` — this run does not change its position, and says so

Net +1 at `rung-01000`, **no effect at any value** on `rung-00100`, breaks one
probe on `rung-seed`. That is the same evidential position the hold already
rests on (+4 hand-graded, `informed`, below the floor). **The hold stands, and
nothing here is an argument for moving it.**

## 3. W-142 — the control's premise is wrong, which is worth more than a pass

**What was seen.** Turning the `heading` field weight off **entirely** changes
the heading-matched distractor count by a net of 5 across 124 queries — below
the floor. 37 queries move, so the field does *something*, but it is not what
puts those documents in the window.

```bash
.venv/bin/python tools/quality-controls/heading_control.py --rung rung-01000
```

**Diagnosis.** The `ext/sibling/` distractors share the seed documents' headings
*and* their whole vocabulary and document shape. They are winning on **body
similarity**, and the heading field is a small term on top of that. C4's
premise — *heading-matched distractors steal slots because of heading matching*
— is not supported on a corpus built specifically to support it.

**What follows, specifically.** Either

- **re-aim the control at the mechanism that is operating** — a body-similarity
  control, whose off arm is `bm25f.body`; or
- **retire the `heading` control** and say plainly that C1 and C3 rest on
  generator assertions, which is what they have rested on since 2026-08-28.

⚠ **Do not lower the floor to make this pass.** A net of 5 against a floor of 6
is the case the floor exists for, and adjudicating it by writing a looser bar is
the moving-threshold failure in a different costume.

## 4. W-144 — the mechanism is confirmed; the quality question has no instrument

**What was seen.** A third of the corpus is table-bearing, `avg_wlen` moves
151.5 → 133.8, 16 of 124 top-1 results change at `rung-01000`, and **41 of 44
top-1 changes across three rungs promote a more table-heavy document** — the
predicted direction, with one exception.

```bash
.venv/bin/python tools/quality-controls/table_flen.py --rung rung-01000 --rank --prose-probe --dilute 8
```

**But the quality endpoint saturates at every dilution** (12/12 in both arms,
0 discordant), because a `df == 1` term's idf is unreachable by length
normalisation. So:

> **The endpoint with mechanical truth has no headroom; the endpoint with
> headroom has no truth.**

**What follows, specifically.** The question is *"is the new order better"*, and
answering it needs graded relevance over the queries that actually move. Two
routes, both real:

1. **Phase 5.** The 16 top-1 movers at `rung-01000` are named in
   `evidence/tables-rung-01000-ranking.jsonl`. Once Codex scores the ladder,
   those ids can be read off directly — **no new run, no new corpus.** This is
   the cheap route and it is already paid for.
2. A purpose-built graded set over table-heavy documents, if phase 5's 16 ids
   turn out to be too few to clear the floor.

🔴 **W-144 does NOT close.** Its own text says *"a null closes this item"* — this
is not a null. The mechanism is real, one-directional, and unadjudicated.

## 5. W-115 — three corpora, three different reasons, and now the fix is specified

**What was seen.** 0 of 994 documents differ between `94231b2` and `676e973` on
the golden ladder, once the `max_phrases` 12→32 confound is attributed to W-116
where it belongs.

```bash
# both arms, same documents, no PII confound (6 documents with hits excluded)
.venv/bin/python /tmp/.../digest.py <tree>/src <rung> <clean-locs>   # see evidence/w115-arm-*.json
```

**Diagnosis, and it is the useful part.** W-115 changed heading grammar for
`.rst`/`.adoc`/`.org`, citation-path decoding, table banding for CSV/XLSX row
chunking, and heading skeletons. **The ladder carries `.md`, `.txt`, `.yaml`,
`.eml` and `.html` — not one of the formats W-115 touches.** The corpus was
never going to see it, and now that is measured rather than suspected.

**What follows, specifically.** A rung — or a sibling corpus — carrying
`.jsonl`, `.json`, `.csv`, `.xlsx` and at least one `.rst`/`.adoc` document,
**with goldens**. ⚠ **It cannot be added to a frozen rung**: the ladder was
committed before the questions were opened and that ordering is the only thing
making it blind. It is a **new corpus**, and it needs its own graded set.

⚠ **Until then, no document may cite W-115 as measured** — unchanged, and now
for the third recorded reason.

---

## 6. Unresolved, stated as unresolved

1. **Whether the priors are closed, moved query-side, or left alone.** Arpit's,
   and the evidence is filed.
2. **Whether the `heading` control is re-aimed or retired.** No record decides
   it; C1 and C3 rest on generator assertions meanwhile.
3. **Whether table `flen` makes ranking better.** Blocked on graded relevance —
   cheapest route is phase 5 against the 16 named ids.
4. **W-115's quality.** Blocked on a corpus that carries the formats it changed
   *and* has goldens. Neither half exists.
5. **Whether `weak` implies `answerable: false`** — carried over from
   [the ladder run](../2026-09-12-golden-ladder/ANALYSIS.md) §1, still the single
   decision that unblocks the most, still undecided.

---

## 7. A process note, recorded rather than buried

**This run's probe set was authored before its first number and committed after
it.** The `0 broken` bar is Arpit's and predates the session, so the *threshold*
was never at risk — but unlike [the ladder](../2026-09-12-golden-ladder/report.md),
git cannot prove the ordering of the rest.

**The mitigation is stated in [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §0
rather than assumed:** the authorship bias can manufacture a pass and cannot
manufacture a failure, and the result reported is a failure. **A `YES` from this
probe set would have needed independent probes before anyone believed it.**

⚠ **The general fix is cheap and should be habit: commit the instrument before
running it.** The ladder did; this did not; the difference cost nothing here
only because the answer went the way the bias did not.
