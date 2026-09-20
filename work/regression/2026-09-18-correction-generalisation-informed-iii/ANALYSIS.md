---
type: Analysis
name: correction-generalisation-informed-iii-analysis
description: "What the arm (iii)-shaped informed run means, what it cannot settle, and the one place the frozen instrument collides with its own result."
item: W-175
timestamp: 2026-09-18T00:00:00Z
---

# Analysis — informed arm (iii)

## 1. The result is compare doc (a), observed twice on different corpora

[The compare doc](../../compare/fux-correct.compare.md) §1 chose (b) over (a) on
one argument:

> (a) **yes, but brittle** — one phrasing fixed, the next still wrong.
> (b) **best fit** — generalises across phrasings.

**11 of 11 own questions rose; 1 of 55 paraphrases moved, by one rank, without
crossing the endpoint.** That is (a), stated as a measurement.

It now replicates. The [2026-09-18 informed run](../2026-09-18-correction-generalisation-informed/report.md)
on fux's own `records/` + `docs/` found 0 of 60 paraphrases moving top-3 and 3 of
60 rising at rank@20. This run used a **different corpus, different questions,
different paraphrases, and a patched harness**, and landed in the same place.
Two informed runs are not a blind arm, but they are no longer one anecdote.

## 2. This run weakens ANALYSIS change A's objection

The prior run's analysis said a `ctx` sweep must precede any generalisation
verdict, because *"at `ctx = 1.0` a correction cannot fix its own phrasing 8
times in 12 on 96 documents — a transfer test on a field too weak to win its own
case measures nothing."*

**Here the field was strong enough.** On 1006 documents, at default tune, the
correction put its own question in the top 3 **7 times in 11** and raised it
**11 times in 11**. The `ctx` line was doing plenty of work. **It still
transferred to nothing.**

⚠ This does not retire change A — a sweep could still find a weight at which
transfer appears, and that remains worth pre-registering. It does remove the
reading that the prior null was an artefact of a too-weak field.

## 3. Where the frozen instrument collides with its own result

🔴 **`verdict.py` returns INCONCLUSIVE at `discordant == 0`**, because SR-RS
decision 22d holds that *"a null measured where nothing could move is the absence
of a measurement."*

**That rationale does not hold here, and the harness's own headroom print is what
says so:** improvement headroom **47/55**. Forty-seven paraphrases could have
entered the top 3. None did. The mechanism that 22d exists to catch — a ceiling —
is measurably absent.

So the run produces a **well-powered null that the frozen tool is obliged to call
inconclusive**. The pre-registration also says a net of 5 or less *"is a measured
negative, whatever the flip count, and needs no further arithmetic"* — which
points the other way at the same numbers.

🔴 **Not resolved here.** A pre-registered threshold may never move
([SR-RS](../../../records/0133_predictions.md) decision 10b) and an ambiguous
result goes to Arpit, not to whoever ran it. **This file rules nothing.** What is
owed is a ruling on whether 22d's inconclusive verdict is conditioned on the
headroom check it sits next to — and that is a change to a Law-adjacent record,
not to a report.

## 4. What this run cannot settle

- **It is not blind by authorship** and never becomes so. The keep/remove call in
  the pre-registration belongs to an arm this session cannot produce.
- **The tilt check was not run.** It requires golden answers and is Codex's by
  law [L11](../../../records/0012_LAW-11-sealed-answer-key.md). KEEP is a
  **conjunction**, so no KEEP is available from this run at any net.
- **N = 11, not 12** — c-01 was refused by `fux correct` as a negative
  correction. Reported at the N that ran; not topped up.
- **One corpus, one domain.** `github/docs` is task-oriented product
  documentation with heavy near-duplicate structure. A corpus of decision records
  might transfer differently.

## 5. What c-01's refusal is worth on its own

`fux correct` **rejected** *"can I pull my paid feature usage automatically
instead of downloading a csv"* as a negative correction — the *"instead of X"*
clause read as *stop serving X*. The question is a perfectly natural thing for a
person to type. **That is a real false positive in the negative-correction guard,
found by accident**, and it is worth a queue item independent of this run.
