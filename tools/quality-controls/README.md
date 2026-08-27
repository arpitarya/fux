# `tools/quality-controls/` — the two controls ADR-RS decision 15 is owed

**Status: two of three built (2026-08-27).**
⚠ **[ADR-RS](../../docs/adr/0036_predictions.md) decision 15 still reads
`NOT BUILT` and may not lose it**, because the third — the **sealed query
subset** — is not here. One item landing does not discharge a decision that
names three.

## Why these exist

*Neural Retrievers are Biased Towards LLM-Generated Content* (KDD 2024)
establishes **source bias**: retrievers rank LLM-written text higher
independently of whether it informs, and the effect reaches re-rankers.

Every fux enrichment arm added ~115 words of fluent LLM prose to nine of ten
documents **with no matched control**, so **text *presence* and text *content*
have never been separable in any number this project has filed.**

<https://arxiv.org/abs/2310.20501>

## What is here

| control | file | what it isolates |
|---|---|---|
| **content-free placebo** | [`placebo.py`](placebo.py) | *presence* of fluent LLM text, with content removed |
| **decoy queries** | [`decoys.jsonl`](decoys.jsonl) | what the system says when the corpus **cannot** answer |
| ~~sealed subset~~ | **NOT BUILT** | see below |

### The placebo

Enrichment of **matched length** carrying no information about the document it
is attached to.

- ⚠ **Every placebo draws from ONE sentence pool, so all of them share a
  vocabulary.** A placebo written *about an unrelated topic* would still be
  discriminative — its terms would match some documents better than others.
  Identical vocabulary across the corpus is what makes any remaining lift
  attributable to *presence of fluent text* and nothing else.
- **Length is matched to within a few words**, stopping on whichever side of the
  target is closer. An earlier version always overshot and gave the arm a
  systematic **+8 %** length bias — confounding length with content, the one
  confound this removes.
- **Deterministic (L3).** The source sha is the seed; no `random`, no clock, no
  model. Verified byte-identical across runs.
- ⚠ **The pool is hand-written.** A model asked for "generic text" reaches for
  the subject matter it was shown, which is the leak this control closes.
- **It installs nothing.** It writes to an output directory you name; a
  measurement swaps it in and restores afterwards.

```bash
python3 tools/quality-controls/placebo.py <corpus>/.fux/enrich /tmp/placebo
```

### The decoys

Fifteen questions that are **plausible for the playground's domain and have no
correct answer in its ten documents** — key rotation, SLAs, cluster
provisioning, parental leave, DR plans.

⚠ **A decoy is the one kind of evaluation material an agent can author without
contaminating anything: there is no correct answer, so there is nothing to fit.**
That is why these were written here and the goldens were not.

**Validate them against the corpus before trusting them** — a "decoy" the corpus
actually answers is not a decoy:

```bash
# each decoy should report terms in `missing`, or a band below `grounded`
fux ask "<decoy>" --json --band
```

### The sealed subset — deliberately absent

Decision 15 needs *"a sealed subset of queries, held by one owner, never shown to
anyone who authors an artifact, rotated when it leaks."*

⚠ **It is not built, and building it is not mechanical.** Decision 15 says so
itself: *"sealing also shrinks the visible set, which makes decision 14's power
problem worse before it makes it better; whoever builds it has to resolve that
tension rather than inherit it silently."* On 50 goldens, splitting off a sealed
holdout leaves both halves too small to resolve much. **That is a judgement
about what the measurement is for**, and it is not an agent's.

## ⚠ What the decoys found on their first run

**One of fifteen is reported `grounded`** — `d02`, *"what is the SLA we publish
for the payments API"* — with `coverage: 1.0`, `missing: []`, `separation:
0.58`, citing `policy-data-retention.md`.

**The mechanism:** `coverage` and `missing` are computed **corpus-wide**. All
four terms occur — `sla` and `publish` in the retention policy, `payments` in the
postmortem and deployment tiers, `api` in the mesh ADR — in **four different
documents**, so nothing is "missing" and the band falls through to the
separation test, which it clears.

**That is the exact failure `confidence.py`'s own docstring opens with**: telling
*"these documents answer your question"* from *"these documents are the closest
thing in a corpus that does not discuss this at all."*

⚠ **It is not a floor-value problem.** `0.58` is above the `0.5` that R10's
selection rule would have picked, so raising the floor would not have caught it.
Filed as [the decoy run](../../work/regression/2026-08-27-decoy-control/report.md);
**named, not fixed** — per-document coverage is a design change to an accepted
record.

**The other fourteen behaved correctly**: `partial`, with the absent terms named
in `missing`, which is the field the module says an agent should read first.
