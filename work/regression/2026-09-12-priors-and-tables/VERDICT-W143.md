---
type: Verdict
description: "Arpit's pre-registered question on the four ranking priors — does any single global value clear 0 broken? — answered NO on every knob and every rung."
item: W-143
question_set_by: Arpit, 2026-09-11
run: 2026-09-12-priors-and-tables
pre_registration: work/regression/2026-09-12-priors-and-tables/PRE-REGISTRATION.md
classification: informed
name: "the four ranking priors — does any single global value clear a 0 broken bar?"
prediction: W-143
verdict: FAIL
ruling: "NO — no single global value clears the bar, for any of the four priors, on any rung"
filed: 2026-09-12
---

# Verdict — the four ranking priors: **NO**

> **`verdict: FAIL` in the frontmatter means the HYPOTHESIS failed, not the run.**
> The hypothesis under test was *"a single global value exists that clears
> `0 broken`"*. It does not. W-143 said in advance that **a run answering NO is a
> success**, and this is that run.

## The question, as it was set

**Arpit, 2026-09-11**, recorded in [W-143](../../open/W-143-four-no-op-priors.md)
before this session existed:

> **Does ANY single global value clear a `0 broken` bar?**

And the note that came with it, which is why the probe set is built the way it
is:

> `P-SUPERSEDE` did not fail because `0.5` was wrong: at `0.5` it fixed
> `q015`/`q049` and **broke `q022`/`q033`**, and *every* broken query had the
> superseded document as its correct answer. Supersession belongs to the
> **query's intent**, not to the document. **A run answering NO is a success.**

## The answer

# NO.

Not for `superseded_weight`, not for `archived_weight`, not for
`recency_half_life_days`, not for `rerank_weight` — on `rung-seed`,
`rung-00100` or `rung-01000`.

## What was measured

26 probes on the frozen golden ladder, **13 current-seeking and 13
history-seeking**, with truth read off the corpus's own declarations — a
`supersedes:` key in frontmatter, an `archived=true` line in
`.fux/sources/dirs`. **No answer key is involved**, so this verdict does not
wait on [W-145](../../open/W-145-codex-regenerates-the-key.md).

Full tables in [`report.md`](report.md) §1. The shape, on every knob:

| | current-seeking | history-seeking |
|---|---:|---:|
| shipped default | 11–12 / 13 | 8–9 / 13 |
| any value that demotes | **13 / 13** | **5 / 13**, down to **0 / 13** |

**The knob works. That is the problem.** Every value that perfects
current-seeking dismantles history-seeking in the same step, one probe for one
probe. `recency_half_life_days` at 365 days or less takes history-seeking to
**zero of thirteen**.

## The two candidates that appeared to clear, and why neither does

| candidate | where it clears | where it breaks | net |
|---|---|---|---:|
| `superseded_weight = 0.9` | `rung-00100` | `rung-seed` (`p07`), `rung-01000` (`p15`) | +1 |
| `archived_weight = 0.75` | `rung-01000` | `rung-seed` (`p20`), `rung-00100` (`p20`) | +2 |
| `rerank_weight ≥ 0.25` | `rung-01000` | `rung-seed` (`p07`); no effect at all on `rung-00100` | +1 |

Each fails **both** pre-registered guards, independently:

1. 🔴 **It clears on one rung and breaks on another, on a different probe each
   time.** A value like that has found a corpus, not a default. The
   every-rung rule was fixed in the pre-registration before these numbers
   existed, precisely because this is the loophole a post-hoc reading takes.
2. 🔴 **Its net is +1 or +2, and the floor of all floors is 6**
   ([ADR-RS](../../../docs/adr/0133_predictions.md) decision 19). A net below 6
   cannot clear α = 0.05 at any discordant count, so read on its own it is
   *no detected change* — not a pass.

## Headroom (ADR-RS decision 22b), so this is a measured negative

| direction | count |
|---|---:|
| improvement — probes not right at the default | 5–7 of 26 |
| regression — probes right at the default | 19–21 of 26 |

**Both directions have headroom**, on every rung, and every knob moved probes in
both directions. So decision 22d does not apply: this is a **measured `NO`**,
not the absence of a measurement. That distinction is the whole difference
between this verdict and [the 2026-09-11 precondition check](../2026-09-11-four-priors-headroom/report.md),
which found the knobs reached **nothing at all** on the playground.

**Labelled `unproven`** under 22c: the run carries no generator `--selftest`.
Unproven is disclosed, not voided — and here the feature-off arm *is* the
shipped default, and it moves, which is the substance 22c is asking for.

## The bias in this run pushes the other way

The probes were written by a session that had read the documents
([`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §0). **Favourable wording can
manufacture a pass; it cannot manufacture a failure.** A `YES` here would have
needed independent probes before anyone believed it. A `NO` survives the bias,
because the bias was pushing against it.

## What this verdict does and does not decide

**Does:**

- Answers Arpit's question. The remeasure he ordered on 2026-09-11 has run, on
  the corpus he ruled should be built for it, and it returns the answer W-143
  predicted was likelier.
- Establishes that the failure is **structural, not a bad constant**. A
  per-document multiplier cannot carry a per-query distinction, and the data now
  says so rather than the argument.

**Does not:**

- Change any default. Every prior stays where it ships. **The output is a
  candidate table with no recommendation**, and a default change remains Arpit's
  [ADR-TUNE](../../../docs/adr/0135_tuning.md) amendment.
- Close the knobs. That is decision (c) of the three W-143 names, and it is
  **Arpit's**, not a session's — this verdict is the evidence for it, not the
  taking of it.
- Say anything about a **query-side** mechanism. *"What do we do now?"* and
  *"what did we do before?"* wanting opposite orderings is a property of the
  question, and where that belongs is a design question nobody has opened.

## Reproduce

```bash
cd ~/my_programs/fux
for k in superseded_weight archived_weight recency_half_life_days rerank_weight; do
  .venv/bin/python tools/quality-controls/priors_sweep.py --rung rung-seed --knob $k
done
```

Per-probe rows for every (rung, knob, value): `evidence/sweep-*.jsonl` —
1 950 rows, which is what makes every count above re-testable by someone else.
