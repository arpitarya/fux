# docs/conformance/ — the test-evidence & analysis home

Every fux-lab conformance run files its **full report + diagnosis + raw evidence**
here, so fixes are made from measured evidence, not memory. Binding: CLAUDE.md
§ "Conformance runs".

## Why this exists

fux-lab is a scratch harness — it commits nothing and is discarded. The durable
record of *what the engine actually did at scale, and what to fix* belongs in the
versioned repo. This directory is that record.

## Structure — one folder per run

```
docs/conformance/
  README.md                         this file (the convention + index)
  <date>-<run>/                     e.g. 2026-07-22-scaling-1k-5k-10k/
    report.md                       the suite's own report(s) / comparison
    <tier>.md                       per-tier reports when a run spans tiers
    ANALYSIS.md                     diagnosis → concrete fux improvements
    evidence/                       raw fux why --json, --debug=trace, doctor
```

## The flow (run → file → fix)

1. Run the suite in `fux-lab/<tier>` (`./setup.sh && ./run.sh`).
2. File the report(s) + an `ANALYSIS.md` + `evidence/` here, in one folder per run.
3. `ANALYSIS.md` names the specific fux changes worth making, with repro commands.
4. Findings that warrant an engine change **graduate** to `docs/proposals/` and,
   when accepted, an ADR — this directory stays the evidence backing them.

Measurements, not narratives. Every number carries its repro command. An
unresolved cause is stated as unresolved.

## Runs

| Run | Version | Scope | Headline |
|---|---|---|---|
| [2026-07-22-scaling-1k-5k-10k](2026-07-22-scaling-1k-5k-10k/ANALYSIS.md) | 0.23.0 | 1k→5k→10k scaling | Hybrid gap closes as lexical collapses; zero-overlap 0/14; latency linear from the start. Two failure mechanisms measured. |
| [2026-07-22-acme-payments](2026-07-22-acme-payments/ANALYSIS.md) | 0.23.0 | ~1k realistic repo (A-vs-B discriminator) | **Settles A vs B → B:** hybrid collapse is a corpus artifact (hit@5 .182→.855, parity with lexical). Three new real findings: staleness 9/12 inversions, zero-overlap dense rescue 0/6, honest-decline 0/4 on well-formed unanswerables. |
| [2026-07-23-min-confidence-calibration](2026-07-23-min-confidence-calibration/ANALYSIS.md) | 0.25.0-dev (editable, phase 6) | acme 55 answerable + 4 unanswerable + gibberish + fixture-21 + synthetic 1k/5k/10k | **No `min_confidence` value clears all 5 gates** — decline-4/4 needs floor ≥0.25, zero-false-decline needs floor ≤0.087, empty interval. Shipped permissive (0.0); follow-up filed (floor an absolute signal, not the pool-relative sentence score). |
| [2026-07-23-supersession-recovery](2026-07-23-supersession-recovery/ANALYSIS.md) | 0.25.0-dev (editable, phase 6) | acme's 12 stale-vs-current pairs, DoD 8 before/after | **Partial recovery, measured exactly:** 5/12 pairs carry a machine-readable marker, only 3/9 original `find`-inversions do; at the `answer` level 1 fully corrected, 1 de-cited (retrieval-limited), 1 already correct, 6 unmarked/unreachable. `find` ranking confirmed byte-identical (annotation only). |
| [2026-07-24-orbit-fulfillment](2026-07-24-orbit-fulfillment/ANALYSIS.md) | 0.25.0 (local wheel of `af374f0`; **not on PyPI**) | **second realistic corpus** — warehouse/fulfillment, 944 files, domain disjoint from fintech | **All three acme findings generalize.** Staleness 8/12 inversions (**meets the ≥8/12 Option-B gate**), and 5 of the 6 frontmatter-reachable pairs invert *while carrying the annotation* — 6/6 annotation coverage confirmed. Fabrication 0/4 again; absolute floor **empty** (needs ≥0.121 vs ≤0.103) and the deferred **runner-up margin check is refuted — empty AND inverted** (unanswerable margins exceed the smallest answerable ones). Zero-overlap clean dense rescue 1/6; hybrid also *demoted* one lexical top-5 hit. |
| [2026-07-24-supersession-penalty-calibration](2026-07-24-supersession-penalty-calibration/ANALYSIS.md) | 0.26.0 (local wheel, phase 7) | penalty sweep over **all four eval sets** (fixture-21 · acme-55 · orbit-53 · synthetic 1k/5k/10k) + margin re-measurement | **Safe interval NON-EMPTY: `[11, ∞)`, measured to 500.** Recovers **100% of frontmatter-reachable inversions on both corpora** (orbit 5/5, acme 3/3); every residual inversion is unmarked. **Zero hit@5 regression on any gate, any value, any question kind**; hit@1 *improves* (orbit .566→.698, acme .491→.564). Fixture + synthetic are flat because they contain **zero markers** — a no-op proof, not recovery evidence. **M4: the runner-up margin is still empty after de-confounding** — orbit's minimum survives at 1e-05 on a `how-to` question, acme's on `cross-doc` (the legitimate-consensus mode the compare doc predicted). Fabrication = **permanent no-model boundary**. |
| [2026-07-24-v0.26.0-release-verification](2026-07-24-v0.26.0-release-verification/ANALYSIS.md) | **0.26.0 — installed from PyPI** | orbit re-baselined on the published package + the Part B metric fix | **The phase-7 calibration reproduces exactly, black-box, from a published artifact**: staleness inversions **8 → 3**, hybrid hit@1 **.566 → .698**, hit@5 flat at .887, `stale-vs-current` hit@1 **.333 → .667**. First orbit run installed from PyPI rather than a frozen wheel (workaround retired). **Part B:** `zero_overlap_rescued` **2 → 1** (clean rescues only — the old metric counted lexical hits); new `zero_overlap_demoted` = **1**, which now names the lexical-hit-lost regression automatically *(filed then as "non-monotone fusion"; **phase 9 corrected that** — RRF is monotone, the cause is a near-noise dense signal)*. **Near-miss recorded:** the first re-baseline used a pre-M5 wheel (default 0) and would have pinned pre-release behaviour — caught by reading the baseline diff. |
| [2026-07-24-fusion-lexical-hit-loss](2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md) | 0.26.0 (PyPI artifact) | "does hybrid lose lexical top-5 hits?" across **all four eval sets, all question kinds** | **The filed "non-monotone fusion" finding is a MISDIAGNOSIS** — RRF is monotone by construction and **160/160 fused results reconcile to the formula with zero delta** (incl. the penalty term). The real population: **~4% on realistic corpora** (acme 2/55, orbit 2/53), roughly offset by gains (orbit net ±0, fixture net **+1**); **synthetic loses 9–64%, unexplained**. Spans **four kinds**, worst case a **`factual` question lost from lexical rank 1** — far more serious than the filed rank-5 anecdote. **Supersession penalty NOT implicated** (identical lost-sets at penalty 0 and 15). A near-duplicate/compressed-dense-spread hypothesis was **tested and rejected** (spreads comparable: 0.115 synthetic vs 0.106–0.157 orbit). |
