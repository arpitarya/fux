---
type: Proposal
title: Hybrid retrieval degraded 4× vs lexical on a 1 000-doc corpus — investigate before trusting the eval gate
description: First external conformance run (fux-lab, 1k synthetic corpus) measured hybrid at hit@5 0.182 against lexical's 0.818. Fires the recorded reopen-trigger on the RRF/reranker decision. RESOLVED 2026-07-22 by the acme-payments realistic run — the hybrid collapse is a CORPUS ARTIFACT (B): on genuine prose hybrid hit@5 recovers to 0.855, parity with lexical. Three new engine findings emerged (staleness inversions, zero-overlap dense rescue, well-formed honest-decline) — split to their own proposals.
status: proposed
timestamp: 2026-07-22T00:00:00Z
tags: [retrieval, eval, rrf, fuxvec, findings]
---

# Hybrid degraded 4× vs lexical at 1 000 documents

## ✅ VERDICT (2026-07-22) — reading B: it was the corpus, not the engine

The discriminating experiment ran: **acme-payments**, ~1 000 documents of genuine
prose diversity (`docs/conformance/2026-07-22-acme-payments/`).

- **The 4× hybrid collapse does not reproduce.** hit@5: hybrid **.182 → .855**,
  lexical **.818 → .873** — hybrid is now at **parity** with lexical (0.98×), not
  4.5× below it.
- **Cause confirmed as B (corpus artifact).** ~450 near-identical template notes
  made the dense ordering arbitrary, so RRF fused noise and demoted correct
  lexical hits. Genuine prose gives the dense plane real signal; fusion stops
  hurting. Under A (engine weakness) hybrid would have stayed collapsed on
  realistic text — it did not.
- **Consequence for the mitigations below.** #1 (dense admission threshold),
  #2 (confidence-weighted RRF), #3 (size-aware default) **lose their original
  justification** — they targeted a synthetic collapse that isn't real. Do not
  ship them off the scaling story. They remain *candidates only* if a future
  realistic corpus reproduces a real hybrid deficit.

**But the realistic run exposed three separate, corpus-independent findings** the
synthetic tiers and the 21-pair gate both missed. They graduate to their own
proposals rather than living under this (now-resolved) hybrid heading:

- **Staleness — retrieval ignores supersession** (9/12 inversions; the superseded
  doc outranks the current one). → `staleness-ranking-ignores-supersession.md`.
- **Honest-decline too permissive** (0/4 on well-formed unanswerables; fabricates
  with sources). → `honest-decline-well-formed-queries.md`.
- **Zero-overlap dense rescue ineffective even undiluted** (0/6 clean rescues,
  the answer *dominating* its doc). Re-motivates **chunk-level dense codes** — not
  to fix the hybrid gap (there isn't one), but because doc-level dense can't
  surface a one-sentence answer regardless of dilution. Folded into
  `../adr/0010-*` reopen context + the substrate roadmap.

This proposal stays `proposed` only to hold the zero-overlap/chunk-dense thread;
the RRF/reranker reopen-trigger it fired is **answered — no reranker or fusion
change is warranted by the evidence.**

repro: `cd fux-lab/acme && ./setup.sh && ./run.sh` ·
report: `docs/conformance/2026-07-22-acme-payments/report.md`

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

## Scaling update — 5k and 10k (2026-07-22)

The same suite, same generator, same engine (0.23.0), at three sizes. Eval
power scales with the corpus: 11 → 52 → 104 planted pairs.

Takeaway: **the 4× gap is not stable — it closes as the corpus grows, because
lexical collapses toward hybrid.**

| tier | n | lexical hit@5 | hybrid hit@5 | lexical÷hybrid |
|------|---|---------------|--------------|----------------|
| 1k   | 11  | 0.818 | 0.182 | 4.49× |
| 5k   | 52  | 0.385 | 0.192 | 2.00× |
| 10k  | 104 | 0.192 | 0.125 | 1.54× |

- lexical hit@5 roughly halves each 2× of corpus; hybrid stays ~flat (.18→.19→.13).
- By 10k both sit near a common floor (~.12–.19). Lexical's edge fell from
  +.636 to +.067 hit@5.

What this means for A vs B: **more consistent with B (corpus artifact) than A
(engine weakness worsening at scale).** Under A, hybrid should fall *further
below* lexical with scale; instead lexical falls *to* hybrid — the signature of
near-identical template prose defeating *all* retrieval as distractors multiply.

**Not settled.** Same generator → cannot separate A from B. What *is* settled:
the 1k "4× worse" headline was corpus-size-dependent and does not survive scale.

repro: `cd fux-lab/<tier> && ./setup.sh && ./run.sh`
full curve: `fux-lab/results/2026-07-22-scaling-1k-5k-10k.md`

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

The 5k/10k scaling curve (above) leans **B** — but is not proof, because it
holds the generator fixed. Only a *different* corpus can discriminate.

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

## Secondary finding — zero-overlap rescue: 0, in **both** modes, at every scale

FuxVec's headline result (ADR 0010) is rescuing questions whose answer shares no
vocabulary with them. On this corpus it rescued nothing, in either mode.

Scaling confirms it — now well-powered: **0/2 (1k) → 0/7 (5k) → 0/14 (10k).**
At 14 pairs this is no longer "too few to conclude." A solid negative result.

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

Reproduces identically at 5k and 10k — the same "top-1 stable, tail re-ranked"
line. Not a 1k artifact; the README/CHANGELOG wording is inaccurate at all scales.

## What passed (context — this is not a broken engine)

51 of 52 checks passed: byte-identical double-ingest, all three drift cases
distinguishable with correct `--strict` exit codes, honest decline on
unanswerable questions in all three verbs (`answer` returned null with zero
sources — no fabrication), citations resolving, `--lexical-only` stable across
runs, and every size/latency metric inside ±15 % of baseline.

Measured at 1 000 docs: ingest 0.46 s · per-verb latency ~0.12 s ·
state 200 B/doc (vs the 230 B/doc projection) · index 2 051 B/doc ·
cache 1 014 B/doc · lock 208 B/doc.

## Budgets flat, latency linear (5k/10k, 2026-07-22)

Two curves worth recording alongside the quality story:

- **Per-doc budgets are flat to gently declining** — no superlinear term.
  state 200→188→186 · index 2051→1851→1826 · cache 1014→831→808 · lock 208→207→207
  (B/doc, 1k→5k→10k). Economy of scale; the lean-profile constant-B/doc claim holds.
  Budgets are byte-deterministic (a cloud 1k re-run was byte-identical to the Mac run).

- **Query latency rises from the start — no flat regime.** Same-machine ask-cold
  0.36 s → 1.0 s → 1.9 s ≈ 0.20 s + 0.16 s per 1 000 docs (linear). Extrapolates to
  ~16 s at 100k, same order as ADR 0011's measured 10.6 s. Corroborates ADR 0011:
  whole index loaded per query, `postings` stored but never read at query time.

# Citations

[1] `fux-lab/1k/results/2026-07-22-1k.md` — the full run report (external harness, fux-engine 0.23.0 from PyPI).
[1a] `fux-lab/5k/results/2026-07-22-5k.md` · `fux-lab/10k/results/2026-07-22-10k.md` — the 5k and 10k tier reports (0.23.0).
[1b] `fux-lab/results/2026-07-22-scaling-1k-5k-10k.md` — the three-tier scaling comparison (method + machine caveats + the four questions answered).
[2] Internal: [`../compare/query-engine.compare.md`](../compare/query-engine.compare.md) — the reranker/RRF decision and its recorded reopen-trigger.
[3] Internal: [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/) — the zero-overlap rescue claim and the measured 0.23–0.26 noise band.
[4] Internal: [`../adr/0006-bundled-model.md`](../adr/) — the original 21-pair fixture gate now shown insufficient alone.
