# `tools/quality-controls/` — the controls ADR-RS decision 15 is owed

**Status: all three built (2026-08-28). One has now been USED.**
⚠ **[ADR-RS](../../docs/adr/0036_predictions.md) decision 15 may now lose its
`NOT BUILT` marker** — the sealed subset was the one outstanding item and it is
here.

**Built is not proven, and it is now proven for exactly one of them:**

| control | built | used to adjudicate |
|---|---|---|
| decoy query set | ✅ | ✅ [2026-08-27](../../work/regression/2026-08-27-decoy-control/report.md), and again 2026-08-28 |
| **`unanswerable` class** (via [the brief](BLIND-AUTHOR-BRIEF.md)) | ✅ | ✅ **[2026-08-28](../../work/regression/2026-08-28-blind-unanswerable/report.md) — 🔴 the engine abstained 0 times out of 20** |
| content-free placebo | ✅ | ❌ **never run** |
| sealed subset | ✅ | ❌ **never run** |

🔴 **The first use found a defect in the control's own procedure, not just in
the engine.** [`BLIND-AUTHOR-BRIEF.md`](BLIND-AUTHOR-BRIEF.md)'s validation loop
graded submitted questions by the engine's own `answerable` — **using the system
under test as the arbiter of the test's validity.** Followed as written it would
have discarded a perfect 20-question set as 100 % defective. Corrected in place;
ground truth now comes from a second blind reader, never from `fux`.

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
| **relevance audit** | [`relevance_audit.py`](relevance_audit.py) | whether `recall@k` needs new annotation at all, or the golden schema already carries it |
| **the blind brief** | [`BLIND-AUTHOR-BRIEF.md`](BLIND-AUTHOR-BRIEF.md) | the auditable instructions for the `unanswerable` class — **committed because its own author was not blind** |

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

Fifteen questions with **no correct answer in the playground's ten documents**.

⚠ **CORRECTED 2026-08-28 (Arpit's ruling). This section made two claims and
both were wrong.** They are left visible rather than quietly rewritten, because
the second one is the belief that produced an open blocker.

**Claim 1 — *"plausible for the playground's domain."*** Several are not.
Parental leave, supplier invoice disputes, badge systems and performance-review
calibration are **generic-enterprise filler**, not questions a reader of this
corpus would plausibly ask. ⚠ **A question that is unanswerable *and*
implausible tests almost nothing**: the system declines it for the wrong reason,
because no term matches anything, rather than because the corpus genuinely stops
short. The set is **easier than it looks**.

**Claim 2 — *"an agent can author these without contaminating anything: there
is no correct answer, so there is nothing to fit."*** 🔴 **This is the important
error.** *Correctness* is not the only thing an author can fit. **The difficulty
distribution is**, and an informed author shapes it without trying to: knowing
where the corpus is thin pulls questions toward the easy far edge, knowing where
it is dense pulls them toward the hard near edge. Neither requires a correct
answer to exist. **Claim 1 is the evidence for this** — the set drifted generic,
and its author had read the goldens.

**What survives the correction:** these fifteen remain a **valid diagnostic
control**. That was never in question. What they may not be is the scored
`unanswerable` class — see below.

⚠ **A decoy is NOT an `unanswerable` golden**, and the difference is role, not
content. A decoy is a diagnostic and is never scored; an `unanswerable` query is
**inside the gate** ([ADR-QUALITY](../../docs/adr/0044_quality-contract.md)
decision 5) and its handling is part of the headline number. Promoting these
fifteen would put informed material in a slot whose only value is that its
author had not looked. **The class is authored separately** —
[`BLIND-AUTHOR-BRIEF.md`](BLIND-AUTHOR-BRIEF.md).

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
