# `tools/quality-controls/` — the two controls ADR-RS decision 15 is owed

**Status: all three built (2026-08-28).**
⚠ **[ADR-RS](../../docs/adr/0036_predictions.md) decision 15 may now lose its
`NOT BUILT` marker** — the sealed subset was the one outstanding item and it is
here. **Built is not proven**: none of the three has yet been used in a run that
adjudicates anything.

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
| **sealed subset** | [`seal.py`](seal.py) | **contamination** — a query nobody who authored an artifact has read |

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

### The sealed subset

**Ruled by Arpit 2026-08-28: seal 15 of 50, and grow the set later.**

```bash
python3 tools/quality-controls/seal.py <goldens.jsonl>            # show the cut
python3 tools/quality-controls/seal.py <goldens.jsonl> --visible  # what you may read
```

- **Split by `sha256(id)`, not by shuffling.** Deterministic (L3), seedless, and
  **independent of file order**, so re-sorting `queries.jsonl` cannot silently
  change which queries are sealed.
- **Growing the corpus is a RESEAL, not an append.** A seal is named by the
  corpus it was cut from; pretending otherwise is how a "sealed" query quietly
  becomes one somebody had already authored against.
- **It hides nothing, and it is not meant to.** Anyone with the repository can
  print the cut. **What it buys is that an artifact's author can say, checkably,
  that they did not look.** BIG-bench's canary is the counter-example worth
  remembering — a marker embedded *so that* labs could exclude it, and
  reproduced by models trained on it regardless.

#### ⚠ The power tension, resolved out loud rather than inherited

Decision 15 required this: *"sealing shrinks the visible set, which makes
decision 14's power problem worse before it makes it better; whoever builds it
has to resolve that tension rather than inherit it silently."*

**35 visible and 15 sealed are both underpowered, and that is accepted rather
than hidden.** The ±2-query resolution floor still governs what a delta may
claim, and it does not loosen because a set got smaller — it gets **harder to
clear**, which is the honest direction. **Sealing buys a claim about
contamination. It buys no precision, and a run that reports a sealed number as
if it were precise is misreading this file.**

#### 🔴 The sealed half is harder than the visible half

**5 of the 9 `known_failure` goldens landed in the sealed 15** — 33 % of the
sealed set versus 11 % of the visible one.

- **This was not corrected, and correcting it would be the bug.** Balancing the
  split by difficulty means reading the scores, which is exactly the
  contamination the seal exists to prevent. The hash split is blind on purpose.
- **It means a sealed score is not comparable to a visible score**, and never
  will be at this size. Anyone reporting both must say which half.
- **It is the power problem made concrete** rather than an argument about it.
