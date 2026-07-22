---
type: Proposal
title: Hybrid retrieval degraded 4× vs lexical on a 1 000-doc corpus — investigate before trusting the eval gate
description: First external conformance run (fux-lab, 1k synthetic corpus) measured hybrid at hit@5 0.182 against lexical's 0.818. Fires the recorded reopen-trigger on the RRF/reranker decision. Cause not yet isolated — corpus artifact vs engine weakness.
status: proposed
timestamp: 2026-07-22T00:00:00Z
tags: [retrieval, eval, rrf, fuxvec, findings]
---

# Hybrid degraded 4× vs lexical at 1 000 documents

## What was measured

First run of the independent conformance harness (`fux-lab`, env `1k`) against
**fux-engine 0.23.0** from PyPI. 1 000 synthetic documents, 11 planted eval
pairs, 52 checks.

| engine mode | hit@1 | hit@5 | MRR |
|-------------|-------|-------|-----|
| `--lexical-only` | 0.364 | **0.818** | 0.576 |
| hybrid (default) | 0.091 | **0.182** | 0.136 |

Lexical found 9 of 11 planted answers in the top 5; **hybrid found 2**. On the
overlap subset (n=9) the gap is the same shape: lexical hit@5 **1.000**,
hybrid **0.222**.

This is the opposite direction from the engine's own gate, which measured
hybrid ≥ lexical on the 21-pair fixture set (ADR 0006, later beaten by FuxVec
in ADR 0010 at hit@5 1.000).

## Why it matters

**Hybrid is the default.** Every `fux ask/find/answer` without `--lexical-only`
takes this path. If the degradation generalizes, the default is worse than the
flag on corpora of realistic size.

It also **fires a recorded reopen-trigger**: `compare/query-engine.compare.md`
closed the reranker question with "revisit only if an eval set shows RRF
leaving quality on the table." An eval set now has.

## Two readings — the cause is NOT yet isolated

Both are plausible; the honest position is that this needs one experiment, not
a redesign.

**A. Engine weakness — RRF has no quality floor.** Fusion gives the dense list
equal standing regardless of whether it carries signal. When dense ranking is
near-random, RRF actively *demotes* correct lexical hits by interleaving noise.
Nothing in the pipeline detects "the dense list is worthless here."

**B. Corpus artifact — the test data is adversarial for dense.** The synthetic
generator produces ~450 markdown notes from one paragraph template, differing
mainly by topic term. Sign-quantized 256-bit codes over near-identical prose
are near-identical, so dense ordering is close to arbitrary. Real corpora have
far more lexical diversity.

If **B** dominates, this is a "don't fuse noise" hardening opportunity, not a
retrieval bug. If **A** dominates, the default engine mode is wrong at scale.

## The discriminating experiment

Run the same suite against the **realistic corpus**
(`fux-lab/prompts/build-realistic-repo.md` — acme-payments, ~1 000 documents
with genuine prose diversity, real reference structure, and typed eval kinds).

- Hybrid recovers on realistic text → reading **B**; ship a dense-quality guard
  and note the limit.
- Hybrid still degrades → reading **A**; the RRF weighting or the dense-global
  admission rule needs revisiting, and the engine's 21-pair fixture gate is too
  small to protect the default.

Either way the fixture-scale gate has been shown insufficient on its own.

## Candidate mitigations (only after the experiment)

- **Admission threshold on dense-global** — require a minimum cosine before a
  document may enter the fused list at all (the run shows noise scores are
  measurable; ADR 0010 already recorded the 0.23–0.26 noise band vs 0.34 rescue).
- **Confidence-weighted RRF** — weight each list by its own score dispersion, so
  a flat/degenerate dense ranking contributes proportionally less.
- **Corpus-size-aware default** — hybrid only above a diversity/size threshold.
- **Non-mitigation, still valuable:** if hybrid genuinely doesn't help some
  corpora, `fux doctor` (handoff 0005) should be able to *say so* by running the
  eval both ways and reporting which mode wins.

## Secondary finding — zero-overlap rescue: 0 of 2, in **both** modes

FuxVec's headline result (ADR 0010) is rescuing questions whose answer shares no
vocabulary with them. On this corpus it rescued neither planted pair, in either
mode.

Likely mechanism, worth confirming: the planted zero-overlap sentence sits
inside a document that is otherwise *about something else*, so the **document**
vector is dominated by the surrounding topical text. Doc-level dense retrieval
cannot surface a one-sentence answer buried in an off-topic document.

If confirmed, that is a **real and documentable limitation** of doc-level dense
search, not a bug — and it argues for chunk-level dense codes as a future
option. It also means ADR 0010's rescue claim holds only when the zero-overlap
answer dominates its document.

## Tertiary finding — fresh-clone scores are not identical, only top-1 stable

The suite's fresh-clone check (remove `.fux/index/`, answer from committed
state) passed on **top-1 parity**, but recorded:

> lower-rank scores differ — state plane is quantized (codes/sigs); top-1
> stable, tail re-ranked

The v0.23 claim, as written in README and CHANGELOG, is that a fresh clone
answers with "the *same rankings and scores*". Measured here: top-1 identical,
**tail order and scores differ**. Either the claim needs narrowing to "top-1
stable, tail approximate", or the state plane needs whatever it lacks to make
the stronger claim true. This is a documentation-accuracy issue at minimum.

## What passed (context — this is not a broken engine)

51 of 52 checks passed: byte-identical double-ingest, all three drift cases
distinguishable with correct `--strict` exit codes, honest decline on
unanswerable questions in all three verbs (`answer` returned null with zero
sources — no fabrication), citations resolving, `--lexical-only` stable across
runs, and every size/latency metric inside ±15 % of baseline.

Measured at 1 000 docs: ingest 0.46 s · per-verb latency ~0.12 s ·
state 200 B/doc (vs the 230 B/doc projection) · index 2 051 B/doc ·
cache 1 014 B/doc · lock 208 B/doc.

# Citations

[1] `fux-lab/1k/results/2026-07-22-1k.md` — the full run report (external harness, fux-engine 0.23.0 from PyPI).
[2] Internal: [`../compare/query-engine.compare.md`](../compare/query-engine.compare.md) — the reranker/RRF decision and its recorded reopen-trigger.
[3] Internal: [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/) — the zero-overlap rescue claim and the measured 0.23–0.26 noise band.
[4] Internal: [`../adr/0006-bundled-model.md`](../adr/) — the original 21-pair fixture gate now shown insufficient alone.
