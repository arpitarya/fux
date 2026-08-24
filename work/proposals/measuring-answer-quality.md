---
type: Proposal
title: How answer quality is measured — the mix, the funnel, and the cost-weighted error
description: "Arpit asked what percentage of the time fux is right. A single accuracy number is not a property of fux — it is a property of (engine, corpus, query mix), and fux owns only two of the four gates it decomposes into. Proposes a scorecard: a versioned query mix, a four-gate funnel, correct-per-byte as the headline, cost-weighted error so silent failures reach it, and calibration. Nothing here is decided; §11 has the forks."
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# Measuring fux — what *"how right is it"* decomposes into

**Arpit, 2026-08-22, verbatim:** *"How do I judge this tool? Meaning, how right
is it going to be? What is the percentage that it is going to give me correct
answer? Is that even the right question to ask? Maybe what is the probability of
the next question that is being asked?"*

The second half of that question is the answer to the first half, and this file
is the shape of what follows from it.

## §0 — The claim, stated once

> **A single accuracy number is not a property of fux.** It is a property of
> **(engine, corpus, query mix)**, and of those three fux is one. The number
> further decomposes into four gates, of which fux owns two. A percentage
> published without naming its corpus and its mix is the same defect as an
> unfrozen threshold — **a number nobody can argue with**, which is to say a
> number that cannot be wrong.

Arpit's own follow-up — *the probability of the next question* — is the missing
term written out. Answer quality is an expectation over a query distribution:

```
score  =  Σ_q  P(q) · correct(q)
```

`P(q)` is currently **undeclared everywhere in this repo**. Every quality number
fux has ever produced silently assumed a uniform `P(q)` over whatever pairs the
generator happened to emit. That is a defensible default and an indefensible
*secret*.

## §1 — Why this is not a hypothetical failure mode

Fux has **already produced two runs where the number passed and the claim did
not**, and both are in the live evidence store:

1. [**P1-GATE**](../regression/2026-08-09-pruning-eval/VERDICT.md) — *"The
   numbers pass. The experiment does not test the claim."* Every corpus reported
   a hit@5 delta of exactly 0.00 points, inside the pre-registered ≤2 pt bar,
   **because the treatment had touched 0–2.5 % of documents**. A metric can be
   satisfied by a treatment that did nothing.
2. [**The budget sweep**](../regression/2026-08-22-budget-sweep/ANALYSIS.md) —
   *"A rule that outputs 'keep' on a result where the thing being kept never
   once outperformed the baseline is being satisfied by its letter and violated
   by its purpose."*

Both were caught by a human reading the analysis. Neither was caught by the
metric. **That is the gap this proposal is about**: fux's measurement discipline
(ADR-RS) is rigorous about *how a claim is frozen* and silent about *what
quantity is worth freezing*.

⚠ **A third case cannot even be cited here.** The strongest illustration of the
corpus-dependence claim — a hybrid arm moving from hit@5 `.182` to `.855` with
**no engine change**, purely because the corpus stopped being template prose —
lives in `archive/v0.26/conformance/2026-07-22-acme-payments/`, and **archive is
not evidence**. It may be named, never cited. The corpus that produced it was
lost in the 2026-08-20 `fux-lab` wipe and has not been rebuilt
([SETUP-LAB](../setup/fux-lab.md)). A measurement whose corpus no longer exists
is an anecdote — which is §10's blocker, and is itself an argument for this
file.

## §2 — The query mix: make `P(q)` a versioned artifact

A file — `mix.toml`, living with the harness, **frozen and versioned like a
pre-registration** — declaring the intent classes and their weights. Seed
classes, each of which fux has a distinct failure mode against:

| class | what it tests | seed weight |
|---|---|---|
| `factual` | one fact, one document | .25 |
| `rationale` | *why* a decision was made — prose, not keywords | .20 |
| `howto` | a procedure spanning steps | .15 |
| `currency` | **which of two documents is still true** | .15 |
| `synthesis` | the answer needs 2+ documents | .15 |
| `unanswerable` | not in the corpus at all — tests declining | .10 |

Three rules make it worth having:

1. **The weights are a declared prior, not a measurement**, until real query
   logs exist — and the file says so in its own comments. A stated prior can be
   argued with; an implicit uniform one cannot.
2. **No quality number is quotable without `mix@version` and `corpus@id` beside
   it.** Same discipline as citing a verdict rather than restating it.
3. **`currency` and `unanswerable` are gate classes, not diagnostics.** They are
   the two classes where fux fails *silently*, which is precisely why a mix that
   under-weights them flatters the engine.

## §3 — The funnel: four gates, four different owners

Reporting one end-to-end percentage blends four independent things and points at
none of them. Report the funnel:

```
        100  questions asked (weighted by the mix)
         ↓
    reachable   the gold document is in the index at all      → ingest / coverage
         ↓
   in window    recall@k — it is in what fux hands over       → ★ THE FUX NUMBER
         ↓
     placed     nDCG@k · MRR — where in the window            → ranking
         ↓
    answered    the consumer used it correctly                → NOT fux's
```

- **`recall@k` is the honest headline.** It is a ceiling: nothing downstream can
  exceed it, and it is the gate fux most fully controls. It also pairs exactly
  with [ADR-ANSWER](../../docs/adr/0006_answer.md)'s existing commitment to
  state the ceiling in every response — the record already says the ceiling
  matters; this measures it.
- **`placed` already exists.** `tools/pruning-eval/pruning/metrics.py` computes
  hit@5, P@10 and MRR at document level, with the aggregation rule copied from
  `_run_find` rather than reinvented. It needs generalising, not writing.
- **The `answered` gate is measured to calibrate the others and never
  optimised.** See fork 4 — it is the only part of this file that would put a
  model inside a fux process.

## §4 — The headline number: correct per 1 000 context bytes

Index-and-refer's entire claim is *answers per byte*. So accuracy at a single
budget is the wrong reading; the measurement is a **curve** — quality against
context budget — and what gets reported is the knee.

[The budget sweep](../regression/2026-08-22-budget-sweep/ANALYSIS.md) is
already this instrument, one run early: it swept budgets and compared assembly
strategies. It measured *packing*, not *quality*. Same axis, different y.

**Rule that follows:** any comparison against a baseline happens at **equal byte
budget**, or it is not a comparison. A rival that is three points better on 20×
the context is losing at the thing fux is for.

## §5 — Cost-weighted error, so the silent failures reach the headline

Counting errors treats a decline and a confidently fabricated citation as one
error each. At the design point — enterprise documents, an agent that will act
on the citation — they differ by an order of magnitude.

| failure | weight | why |
|---|---|---|
| stale document cited as current | 10 | undetectable by the reader; the wrong rule ships |
| fabricated citation on an unanswerable question | 10 | the consumer has no signal at all |
| confident wrong document | 8 | detectable only by opening it |
| miss, or an honest decline | 1 | costs a retry |
| correct but ranked 4–10 | 0.2 | costs attention, not correctness |

```
cost-weighted error  =  Σ  rate(class) · weight(class)
```

The weights are **arguable and must be argued** — that is fork 3, and the point
of writing them down is that today they are implicitly all `1.0`.

## §6 — Calibration: the property an enterprise buyer actually needs

Bucket answers by fux's own stated confidence; plot claimed against actual.
Report **ECE** plus **decline precision** (of the questions fux refused, how many
were genuinely unanswerable).

A tool at 80 % that reliably knows when it is unsure can be **bounded**, and a
bounded tool can be built on. A tool at 92 % that fails silently cannot. Given
the litmus (a very large-scale corporate mega-project, audit as a design input),
this is the more valuable of the two numbers, and nothing in the repo measures
it.

## §7 — Statistical honesty, or the deltas are theater

- **State the minimum detectable effect.** At the eval-set sizes this project
  has used, a few points of hit@5 is inside the noise. A delta reported without
  an interval invites a decision the data cannot support.
- **Use a paired bootstrap over per-query ranks.** Both arms see identical
  queries, so the paired interval is far tighter than the unpaired one — free
  precision, no extra corpus.
- **Keep the pre-registration.** ADR-RS already governs this and does not need
  amending; the mix and the cost vector simply become part of what gets frozen.
- **Held-out law.** An accepted improvement must survive a corpus **generated
  after the change was designed**. This is the rule the archived acme result
  taught at full price.

## §8 — What ships as the public claim

Not *"fux is 87 % accurate."* A scorecard, and the shape is the argument:

```
mix v1 · corpus <id> · recall@5 0.__ (±0.__) · nDCG@5 0.__
cost-weighted error _._ · _._k bytes/answer · ECE 0.__ · held-out delta ±0.__
```

Nobody in this category publishes that, which makes the honest number and the
strongest available positioning the same artifact. **Whether it goes in the
README is fork 5** — it is a public commitment, and it dates.

## §9 — What this proposal is *not*

⚠ **This does not re-file [W-62](../../archive/open/W-62-measure-against-the-outside-world.md).**
Parts 1 and 2 of that item — the three-way comparison against `rg` and a
commercial baseline, and the five external cold-start reports — were
**withdrawn by Arpit on 2026-08-22** and are his personally; its own withdrawal
note says **no agent should re-file them**. This file proposes an *internal*
contract: how fux's own quality is measured and reported against its own
corpora. It measures **fux against itself over time**, not fux against the
outside world. If the two are ever confused, this one yields.

It also does not propose changing any engine behaviour. It proposes an
**instrument**, which is the distinction
[`ranking-tuning.md`](ranking-tuning.md) already drew for ranking constants:
*the instrument is the product; the optimiser is not.*

## §10 — The blocker, stated up front

**There is no corpus to run this against.** `acme` and `orbit` were lost in the
2026-08-20 `fux-lab` wipe along with their generator, `tools/pruning-eval/` still
hard-codes reading them and cannot run, and the five-tier lab redesign Arpit
described on 2026-08-22 (**10 / 100 / 1 000 / 5 000 / 10 000**, each its own
repo) is **specified and unexecuted** — with two open questions that are his to
resolve ([SETUP-LAB](../setup/fux-lab.md)).

Consequence, and it is the honest ordering: **the mix, the funnel definitions and
the cost vector can all be written now and are worth writing now** — they are
declarations, and declaring them is most of the value. **Running them is blocked
on a corpus.** A proposal that pretends otherwise would be the third instance of
the failure in §1.

## §11 — Forks — nothing here is decided

1. **Where does `P(q)` come from before real logs exist?** A declared prior (as
   §2 sketches) · uniform-and-say-so · refuse to weight at all and report
   per-class only, never a scalar. **The third is the most defensible and the
   least usable**, which is the whole fork.
2. **Is `unanswerable` inside the gate or beside it?** Inside, and a single
   number covers fabrication; beside, and the gate stays comparable with the
   historical hit@5 series. It cannot be both.
3. **Who sets the cost weights, and are they published?** Published weights
   invite the accusation of tuning the metric to the engine; unpublished ones
   make the headline unauditable.
4. **Is the `answered` gate measured at all?** It needs a judge model. That is
   outside the maintenance path so **L3 is not violated** — but it makes the
   number non-reproducible and model-version-dependent, which is exactly what
   the frozen-threshold discipline exists to prevent. Options: don't measure it ·
   measure it with a pinned model + frozen prompt, reported separately and never
   as a gate · measure it by hand on a small slice.
5. **Does the scorecard become a public claim (README) or stay internal?**
6. **Does a query log get built to source `P(q)`?** It collides with
   [`query-log-pruning.md`](query-log-pruning.md), which already carries the
   privacy decision (committed vs local) this would inherit. If that proposal
   graduates first, this fork closes with it.

## §12 — Graduation trigger

**Graduates when a corpus exists to run it against** — the five-tier lab
redesign executed, or any single regenerated tier of ≥1 000 documents with typed
eval pairs — **and** at least one open decision is waiting on a quality number.
Until both hold it stays here, because an instrument nobody is about to read is
a wish.

Sooner, partial trigger: **if any quality figure is about to be published
externally** (README, a release note, a landing page), the mix and the funnel
must be declared first, whatever the state of the lab. A published number
without them is the defect in §0.

## References

- [ADR-RS](../../docs/adr/0036_predictions.md) — the frozen-claim discipline
  this sits inside; unamended by this proposal
- [ADR-ANSWER](../../docs/adr/0006_answer.md) — the ceiling stated in every
  response; §3's `recall@k` is that ceiling, measured
- [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md) — a passing number
  on a treatment that did nothing
- [The budget sweep](../regression/2026-08-22-budget-sweep/ANALYSIS.md) — a rule
  satisfied by its letter and violated by its purpose; also the byte-budget
  instrument §4 generalises
- [SETUP-LAB](../setup/fux-lab.md) — the lab, the wipe, and the unexecuted
  five-tier redesign
- [`ranking-tuning.md`](ranking-tuning.md) — the instrument-not-the-optimiser
  argument, and the judgment-supply constraint this shares
- [`query-log-pruning.md`](query-log-pruning.md) — the query log fork 6 would
  need, and the privacy decision it carries
- `tools/pruning-eval/pruning/metrics.py` · `evalset.py` — the existing
  document-level hit@5 / P@10 / MRR implementation and its stated eval-set
  biases; the honest-bias docstring in `evalset.py` is the tone this file
  extends
