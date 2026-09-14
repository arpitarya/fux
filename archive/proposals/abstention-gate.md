---
type: Proposal
title: "The abstention gate — what should 0 abstentions out of 20 block?"
description: "fux reports answerable: true on every one of 20 blind-authored unanswerable questions, twice, fourteen days apart. The engine can only abstain when nothing matches at all. Three options — disclose, gate quality claims, or build abstention and measure it in fux-lab — with a recommendation and a graduation trigger."
status: proposed
timestamp: 2026-09-11T00:00:00Z
---

# The abstention gate — what should *0 of 20* block?

**Parked from the *Blocked on Arpit* inbox on 2026-09-11, at his instruction.**
**Option C graduated on 2026-09-13 to [`compare/abstention-gates.compare.md`](../compare/abstention-gates.compare.md); A and B are still owed a ruling here.**
Nothing here is decided and nothing is built.

---

## 1 · The finding

- **20 questions a blind session wrote to sound answerable, and a second blind
  session ruled unanswerable.** fux said `answerable: true` on **all 20**
  ([2026-08-28](../regression/2026-08-28-blind-unanswerable/report.md)).
- **Re-run 2026-09-11: still 20 of 20, 0 ids flipped** — after five ranking
  changes ([the re-run](../regression/2026-09-11-blind-unanswerable-rerun/report.md)).
  Improvement headroom was 20 and proven, so the null is real.
- **Band, separation and `SEPARATION_FLOOR` are demonstrated not to be the
  lever.** Four ids changed band; none changed answerability. `u017` slid to
  `weak` and still reported `answerable: true`.

**Why it happens** — [SR-CONFIDENCE](../../records/0141_confidence.md)
decision 3: `answerable` is `false` **only when nothing scored above zero**. A
question built from the corpus's own words — *"the names of all four regions"*,
where the corpus says *"four regions"* and never names them — always scores
something, so it can never abstain.

**Why it matters** — [SR-WORK-QUALITY](../../records/0056_WORK-quality.md)
decision 5 puts `unanswerable` **inside** the quality gate. Today every
`recall@k` headline describes **the answerable half only**, and an agent asking
fux something the documents do not say gets a confident, cited answer.

⚠ **A contradiction worth naming:** SR-CONFIDENCE's own band table says a
`weak` result means *"do not answer"*, while the same result carries
`answerable: true`. An agent that reads the boolean — which is what decision 5
tells it to read — answers anyway.

---

## 2 · The options

| | option | what changes | cost | risk |
|---|---|---|---|---|
| **A** | **Disclose only** | `fux doctor` gains a row: *"`answerable` was false in 0 of the last N answers"* — a fact, never a recommendation (the re-run's ANALYSIS, improvement 1). Reports keep printing the unanswerable class beside the headline | small | agents still get confident answers to questions nobody can answer; the gap is visible, not smaller |
| **B** | **Gate quality claims** | Until the `unanswerable` class scores above 0, **no quality number is quoted without *"abstains 0 of N"* beside it**, and the funnel's `answered` gate reports that class as failing. An SR-WORK-QUALITY amendment, no code | small | none to the engine; it makes every headline honest and less flattering |
| **C** | **Build abstention, measure it in fux-lab** | A compare doc picks a mechanism, then a build item. Candidates: **C1** turn on the per-document coverage gate (`doc_coverage`, off since a 2026-08-28 measurement); **C2** make `weak` imply `answerable: false`, resolving the contradiction above; **C3** a passage-level check in the refer plane — the fetched bytes must contain the query's content terms together | medium–large | a mechanism that abstains too often refuses real questions; that is why it must be pre-registered with both directions' headroom |

### What C must not do

- 🔴 **Never tune or threshold on these 20 questions.** They exposed the problem;
  fitting a floor to them is the moving-threshold failure. They stay a frozen
  control.
- **Measure only in fux-lab, on the golden test data** — [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md).
  The golden set's `unanswerable` class (about 10 % of ~100 questions, W-136) is
  the fresh, blind set.
- ⚠ **Power:** about 10 unanswerable questions against a baseline of 0 means only a
  large effect clears SR-RS decision 19's floor (a net of 6). If C is chosen,
  the golden key may need more `unanswerable` questions — a Codex task, never
  Claude's.
- **Pre-register both directions** (SR-RS decision 22): more abstentions on
  unanswerable questions, and no new abstentions on answerable ones.

---

## 3 · Recommendation

**B now, then C.**

- **B** costs one amendment and stops every quality headline from overstating fux
  today.
- **A alone is not enough** — it discloses the gap and leaves the contradiction
  between `weak` and `answerable` in place.
- **C is the real fix**, but it needs the golden ladder (W-136) to exist and a
  compare doc to choose between C1–C3; starting it before either would repeat
  the playground mistake SR-WORK-ENVIRONMENTS exists to stop.

---

## 4 · Graduation trigger

**Graduates when Arpit picks A, B, C or a combination.**

- **A** → a `fux doctor` build item.
- **B** → an SR-WORK-QUALITY amendment, filed as an `adr update` item.
- **C** → a compare doc under `work/compare/` (C1 vs C2 vs C3), then a build item
  whose measured run waits on W-136's frozen ladder.

---

## References

- [2026-08-28 run](../regression/2026-08-28-blind-unanswerable/report.md) ·
  [2026-09-11 re-run](../regression/2026-09-11-blind-unanswerable-rerun/report.md) and its
  [ANALYSIS](../regression/2026-09-11-blind-unanswerable-rerun/ANALYSIS.md)
- [SR-CONFIDENCE](../../records/0141_confidence.md) decisions 3 and 5 ·
  [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) decision 5 ·
  [SR-RS](../../records/0133_predictions.md) decisions 19 and 22 ·
  [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)
- Rajpurkar, Jia & Liang, *Know What You Don't Know: Unanswerable Questions for
  SQuAD*, ACL 2018 — https://arxiv.org/abs/1806.03822
- Kamath, Jia & Liang, *Selective Question Answering under Domain Shift*, ACL 2020 —
  https://arxiv.org/abs/2006.09462
- El-Yaniv & Wiener, *On the Foundations of Noise-free Selective Classification*,
  JMLR 11, 2010 — https://jmlr.org/papers/v11/el-yaniv10a.html
