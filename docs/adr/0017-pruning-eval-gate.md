---
type: ADR
title: "ADR-0017: P1, the pruning-quality gate — INCONCLUSIVE, do not proceed"
description: M1's measured result. The pre-registered numeric condition is met on all three corpora (Δ hit@5 = 0.00 pts at k=128), but prune coverage shows the treatment reached 0–2.5% of documents and retained 96–100% of postings, so the experiment cannot license the inference the threshold was written to license. The scaffold stays blocked; the decision is Arpit's.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# ADR-0017: P1, the pruning-quality gate — **INCONCLUSIVE**

- **Status:** **proposed — awaiting Arpit's ruling.** The executing agent
  deliberately does not adjudicate this one; see §Decision.
- **Date:** 2026-08-09
- **Feature:** M1, the pruning-quality gate (P1) — the measurement the whole
  index-and-refer plan is sequenced behind.
- **Evidence:** [`../conformance/2026-08-09-pruning-eval/`](../conformance/2026-08-09-pruning-eval/)
- **Superseded as the P1 measurement by
  [ADR-0018](0018-pruning-criterion-rerun.md)** (2026-08-09) — the re-run this
  ADR asked for. It found **FAIL**. This document is unmodified: it is the
  record of a correct refusal, and the refusal is what produced the re-run.
- **Pre-registration (frozen before the first number):**
  [`../../tools/pruning-eval/PRE-REGISTRATION.md`](../../tools/pruning-eval/PRE-REGISTRATION.md)

---

## Headline

**The numbers pass. The experiment does not test the claim.**

At k=128 every gating corpus reports a hit@5 delta of **exactly 0.00 points** —
inside the pre-registered ≤2 pt bar with room to spare. It reports zero because
top-128 pruning **did almost nothing**: it touched 2.5 %, 1.6 % and **0.0 %** of
each corpus's documents and left 96–100 % of postings in place.

An aggregate delta of zero over a population that was not treated is not
evidence about the treatment.

## Context

P1 is the load-bearing assumption of the whole architecture: *keeping only each
document's top-k KL-ranked terms preserves ranking quality*. If it fails, the
committed index cannot be small and index-and-refer collapses back to the
snapshot designs. Published work (Carmel et al. 2001; Büttcher & Clarke 2006)
says bounded early-precision loss is expected — but nobody had measured it on
Fux's corpora with Fux's scorer, so the plan put the measurement first and made
every later milestone conditional on it.

The threshold, metric definitions, slice definitions and gold-label rules were
written down and **committed before any gating corpus ran** (commit `f5300fc`),
precisely so they could not drift toward the result.

## What was measured

**Method.** One scorer — the archived v0.26 BM25F — three arms, varying only
the index: `baseline` (full), `pruned` (top-k, with `df`/`n`/field lengths
**recomputed over the pruned postings**), and `diag` (top-k postings with
*baseline* statistics, for attribution only). Nothing under `archive/` was
modified. Harness: [`tools/pruning-eval/`](../../tools/pruning-eval/README.md).

**Harness validity, checked before believing any number:**

| check | result |
|---|---|
| baseline reproduces the archived engine's recorded fixture eval | hit@5 **0.952** / MRR **0.833** — exact match |
| baseline reproduces the lab's filed orbit lexical number | hit@5 **0.887** (n=53) — exact match |
| `k = ∞` pruning is a no-op (identical to baseline) | passes on every corpus |
| independent re-runs are byte-identical | `report.md` sha256 identical across runs |
| selector contract + harness self-checks | 23 tests green |

### The verdict table, against the pre-registered rule

| gating corpus | docs | Δ hit@5 @k=128 | ≤ 2 pts? | Δ hit@5 @k=64 |
|---|---|---|---|---|
| acme | 877 | **+0.00** | yes | **+9.09** |
| orbit | 892 | **+0.00** | yes | +0.00 |
| synth | 100 000 | **+0.00** | yes | +2.00 |

**On its letter: PASS at k=128. PASS-with-k=64 is refused** — acme's +9.09 pts
is three times the 3-pt hard bar.

### Why the k=128 row is not evidence

| corpus | documents pruned @k=128 | postings retained | eval queries whose gold doc was pruned |
|---|---|---|---|
| acme | 22 / 877 (**2.5 %**) | 96.4 % | 5 |
| orbit | 14 / 892 (**1.6 %**) | 96.9 % | 2 |
| synth | 0 / 100 000 (**0.0 %**) | **100.0 %** | 0 |

On `synth`, the "pruned" index is **byte-identical to the baseline index**. That
row is the `k = ∞` sanity arm wearing a different label. It cannot fail, and it
did not.

The cause is document size. Top-*k* prunes a document's *vocabulary*, and these
corpora do not have much:

| corpus | distinct terms per document (median / p90 / p99 / max) |
|---|---|
| acme | 32 / 81 / 156 / 407 |
| orbit | 36 / 89 / 150 / 432 |
| synth | 46 / 62 / 67 / **72** |

The paper's size model (§5) assumes documents of ~10⁴ words — roughly **2 000
distinct terms**, of which 128 survive: a **term retention of ≈ 6 %**. Measured
retention here:

| corpus | retention @k=128 | retention @k=64 | production target |
|---|---|---|---|
| acme | **97.9 %** | 86.8 % | ≈ 6 % |
| orbit | **98.4 %** | 87.9 % | ≈ 6 % |
| synth | **100 %** | 99.8 % | ≈ 6 % |

**k=128 on a 32-term document and k=128 on a 2 000-term document are not the
same treatment.** The first is a no-op; the second discards 94 % of the
document's vocabulary. This experiment measured the first.

### The one signal that is real, and it points the wrong way

k=64 is the only setting where pruning reached a meaningful number of documents
— and it is *still* far milder than production (67 % retention among the
documents it touched, versus a 6 % target). At that mild setting:

| corpus | Δ hit@5, overall | Δ hit@5 on documents actually pruned |
|---|---|---|
| acme | +9.09 | **+9.52** (0.952 → 0.857, n=42) |
| synth | +2.00 | **+11.11** (1.000 → 0.889, n=27) |
| orbit | +0.00 | +0.00 (n=37) |

*(the per-pruned-document slice is declared **post-hoc**; it is not part of the
pre-registered verdict and is reported as a diagnostic.)*

**Failure catalogue, k=64 acme** — 5 lost top-5 hits, 4 classified `term-pruned`
and 1 `score-compressed`; 3 attributed to *missing postings* and 2 to *shifted
statistics*. The pruned-out terms are instructive: alongside expected stopwords
(`the`, `to`, `a`, `so`), the criterion also dropped **`webhook` from
`docs/api/webhooks.md`** and **`payments` from a payments document** — terms
that are frequent in the document *and* frequent in the collection, so their
KL ratio is modest even though a user would call them the document's subject.
That query fell from rank 5 to rank 88.

That is the known failure mode of a KL criterion on a topically homogeneous
corpus, and an enterprise mega-project corpus is *more* homogeneous than acme,
not less.

## Decision

**INCONCLUSIVE. Do not proceed to M0b or M2. The call is Arpit's.**

The pre-registered rule is met, and **the threshold is not being moved** — the
number is recorded as measured, in full, and the PASS on the letter is stated
plainly above. But the rule was written on the assumption that the corpora
would exercise pruning, and prune coverage shows they did not. Reporting
"P1 PASSED" from a treatment that touched 0–2.5 % of documents would be a true
sentence that creates a false belief, and the plan would then build 5 000 lines
on it.

Read in the direction the evidence actually points, the honest summary is
**negative-leaning**: the mildest version of the treatment that does anything
at all already costs 9–11 points where it lands, and production's version is an
order of magnitude more aggressive. That is an *extrapolation*, not a
measurement, and it is labelled as one.

**What is definitively settled by this run:**

- **k=64 is refused as a default.** acme −9.09 pts is 3× the hard bar. The M8
  "top-64 default" item resolves **negative** and needs no further work.
- **Rare-term loss is not the dominant failure mode at these settings** — the
  rare-term slice moved 0.00/0.00/−5.26 pts. The Bloom-signature mitigation
  (M8) is not the thing standing between this architecture and working, and
  should not be built on the strength of this run.
- **The harness is trustworthy and reusable.** It reproduces two independently
  recorded baselines exactly, is byte-reproducible, and the KL selector is
  production-ready and ported as-is.

## What would make P1 decidable

Stated so the re-run is a specification, not a research project. Any of these
resolves it; the first is the cheapest.

1. **A long-document corpus.** The eval corpora cannot reach production
   retention *at any k* — a 32-term document has nothing to prune. What is
   needed is a corpus whose documents run to 10³–10⁴ words: real Confluence/
   SharePoint pages, RFCs, long ADRs, or a synthetic generator with an open
   vocabulary and realistic document lengths. **The current
   `synth_corpus.py` cannot be tuned into this** — its closed ~50-word
   vocabulary caps document vocabulary at 72 terms by construction.

2. **Hold retention constant, not k.** Re-register the threshold against
   *term retention* (≈ 6 %) rather than an absolute k, so the treatment is
   comparable across corpora. On the current corpora that means k ≈ 2–5, which
   is obviously destructive — which is itself the finding.

3. **Both, and pre-register again.** The pre-registration mechanism worked
   exactly as intended: it is what made this failure visible instead of
   letting a zero delta be reported as a success.

## Alternatives considered

| option | why it lost |
|---|---|
| **Report PASS and scaffold** (the letter of the rule) | The rule is satisfied by a treatment that did nothing. Building M2–M6 on it is precisely the failure the gate exists to prevent. |
| **Report FAIL** | Not supported. Nothing measured here falsifies P1 either — at the settings tested, quality held. Calling it FAIL would be as unfounded as calling it PASS, in the other direction. |
| **Lower k until it hurts, then judge** | This is threshold-moving after seeing data, and forbidden. k=64 *is* reported, but as a measurement, not as a re-registered bar. |
| **Rewrite the pre-registration to use retention** | Correct for the *next* run; illegitimate for this one. Re-registering after seeing numbers is the failure mode the discipline exists to stop. Recorded as recommendation §2. |
| **Build M2 anyway; validate later** | The plan's sequencing rule is explicit: no M2+ while P1 is unmeasured or failed. "Unmeasured" is the accurate state. |

## Consequences

**Immediately:**

- **W-01 (the M0b package scaffold) stays blocked.** No `src/`, no
  `pyproject.toml`, no version bump. `main` keeps no orphan scaffold for an
  architecture whose premise is untested.
- **W-06…W-11 (M2–M7) stay blocked** on `W-05 = PASS`, which this ADR does not
  grant.
- **P1's status in [`OPEN-WORK.md`](../OPEN-WORK.md) becomes `INCONCLUSIVE`**,
  not `PASS` and not `FAIL`.
- [`storage-architecture.compare.md`](../compare/storage-architecture.compare.md)
  is **annotated, not reopened** — its reopen-trigger is a *failed* P1, and P1
  did not fail. It is flagged as standing on an untested premise.
- **M8's top-64 item is closed negative** — that much the run does decide.

**What we now owe:**

- A re-run against a long-document corpus, with a fresh pre-registration, before
  any of M2–M6 begins. That is a new handoff (Opus — it is a measurement-design
  problem, which is exactly where a cheaper model rationalizes).
- The paper's §5 size model should carry a note that its 6 %-retention
  assumption is **unvalidated**, not merely unmeasured — M7 owns the numbers,
  but the distinction matters to a reader today.

**What got cheaper:** the harness, the selector and the pre-registration
discipline are all reusable. The next attempt is a new corpus plus a new
threshold file, not new machinery — days, not weeks.

## References (required)

- **Büttcher, S., Clarke, C.** *A Document-Centric Approach to Static Index
  Pruning in Text Retrieval Systems.* CIKM 2006 —
  https://dl.acm.org/doi/10.1145/1183614.1183684. The KL criterion implemented
  in [`kl_select.py`](../../tools/pruning-eval/pruning/kl_select.py), and the
  source of the document-centric guarantee that every document keeps
  `min(k, |vocab|)` postings.
- **Carmel, D. et al.** *Static Index Pruning for Information Retrieval
  Systems.* SIGIR 2001 — https://dl.acm.org/doi/10.1145/383952.383958. The
  term-centric baseline, and the origin of the "bounded early-precision loss"
  expectation this run set out to test.
- **The pre-registration** —
  [`tools/pruning-eval/PRE-REGISTRATION.md`](../../tools/pruning-eval/PRE-REGISTRATION.md),
  committed in `f5300fc` before the first gating corpus ran.
- **The evidence** —
  [`docs/conformance/2026-08-09-pruning-eval/`](../conformance/2026-08-09-pruning-eval/):
  `report.md`, `results.json`, `retention.json`, `ANALYSIS.md`, and the exact
  reproduce command.
- **The prediction under test** —
  [`docs/paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md) §5
  (size model, the ~6 % retention assumption) and §8 (P1's threshold).
- **The archived baselines used as correctness checks** — archived ADR-0006
  (fixture lexical eval: hit@5 0.952 / MRR 0.833) and the filed orbit run
  (`archive/v0.26/conformance/2026-07-24-orbit-fulfillment/report.md`,
  hit@5 0.887 lexical-only, n=53).
- **On pre-registration as a defence against outcome-dependent analysis:**
  Nosek, B. et al., *The preregistration revolution*, PNAS 115(11), 2018 —
  https://doi.org/10.1073/pnas.1708274114. This ADR is the mechanism working:
  the threshold held, and the *coverage* check written into the same document
  is what exposed that the threshold was not measuring what it assumed.
