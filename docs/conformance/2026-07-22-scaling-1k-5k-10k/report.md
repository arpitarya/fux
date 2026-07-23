# Fux conformance — scaling curve 1k → 5k → 10k — 2026-07-22

Version under test: **fux 0.23.0** (PyPI, pinned per each env's VERSION).

Same deterministic generator (seed 20260722) at three sizes. Same engine.
This isolates the **scale axis** — it does **not** discriminate engine-weakness
(A) from corpus-artifact (B); that is the acme-payments run, still outstanding.

## Where these numbers were measured (read first)

- 5k and 10k: run in a Linux cloud sandbox (x86_64, Python 3.11).
- 1k canonical: the user's Mac (`fux-lab/1k/results/2026-07-22-1k.md`, 0.23.0).
- **Deterministic metrics — byte budgets and quality — are machine-independent.**
  Proof: a cloud 1k re-run produced byte-identical `.fux/state|index|cache`
  (state hash `dfb68bd6b9da695f`, 200/2051/1014 B/doc) and identical quality
  to the Mac baseline. So the budget and quality columns compare cleanly.
- **Wall-clock (latency, ingest) is machine-dependent.** To compare like with
  like, a same-machine 1k anchor was run in the cloud on 0.23.0. The timing
  rows below use the **cloud** 1k anchor, not the Mac number; the Mac number is
  shown in parentheses for reference.

## The table

| metric | 1k | 5k | 10k |
|---|---|---|---|
| eval pairs (n) | 11 | 52 | 104 |
| sources ingested | 935 | 4 655 | 9 305 |
| lexical hit@1 / hit@5 / MRR | .364 / **.818** / .576 | .077 / **.385** / .176 | .038 / **.192** / .088 |
| hybrid  hit@1 / hit@5 / MRR | .091 / **.182** / .136 | .058 / **.192** / .101 | .029 / **.125** / .065 |
| lexical÷hybrid (hit@5) | 4.49× | 2.00× | 1.54× |
| zero-overlap rescue (hybrid) | 0/2 | 0/7 | 0/14 |
| ingest wall time | 0.8 s (Mac 0.46) | 3.2 s | 6.4 s |
| query latency ask/find/answer cold | ~0.36 s (Mac ~0.12) | ~1.0 s | ~1.9 s |
| state B/doc | 200 | 188 | 186 |
| index B/doc | 2051 | 1851 | 1826 |
| cache B/doc | 1014 | 831 | 808 |
| lock B/doc | 208 | 207 | 207 |

repro: `cd fux-lab/<tier> && ./setup.sh && ./run.sh` · latency anchor:
`cd fux-lab/1k && ./setup.sh 'fux-engine==0.23.0' && ./run.sh`

## Q1 — does the hybrid gap widen, hold, or close?

**It closes, steadily.** hit@5 lexical÷hybrid: 4.49× → 2.00× → 1.54×.

Not because hybrid improves — because **lexical collapses toward it.**
- lexical hit@5: .818 → .385 → .192 (roughly halves each 2× of corpus)
- hybrid hit@5: .182 → .192 → .125 (roughly flat, slight decline)

By 10k both sit near a common floor (~.12–.19). Lexical's edge fell from
+.636 hit@5 (1k) to +.067 (10k).

Reading, stated carefully: this is **more consistent with B (corpus artifact)
than A (engine weakness worsening at scale)**. Under A, hybrid should fall
*further below* lexical as RRF demotes more correct hits; instead lexical falls
*to* hybrid — the signature of near-identical template prose defeating *all*
retrieval as distractors multiply.

**Not settled.** Same generator → cannot separate A from B. What *is* settled:
the 1k "4× worse" figure was corpus-size-dependent and does not survive scale.

## Q2 — does the zero-overlap rescue work at any scale?

**No, at any scale.** 0/2 → 0/7 → 0/14. Zero rescues, both modes, every tier.

At 10k this is 14 pairs — no longer "too few to conclude." A well-powered
negative result. Doc-level dense codes do not surface a one-sentence answer
buried in an off-topic document.

Consequence: narrows ADR 0010's rescue claim — it holds only when the
zero-overlap answer dominates its document vector. A real, documentable limit,
not noise.

## Q3 — are per-doc budgets flat?

**Yes — flat to gently declining. No superlinear term.**
- state: 200 → 188 → 186
- index: 2051 → 1851 → 1826
- cache: 1014 → 831 → 808
- lock:  208 → 207 → 207

The ~6–18% drop then level-off is economy of scale (fixed overhead amortized,
shared vocabulary). The lean-profile constant-B/doc claim holds — and slightly
improves with size. Budgets are byte-deterministic (cloud 1k == Mac 1k exactly).

## Q4 — where does query latency bend?

**From the start. There is no flat regime.**

Same-machine (cloud, 0.23.0) ask-cold: 0.36 s → 1.0 s → 1.9 s.
Fits **latency ≈ 0.20 s + 0.16 s per 1 000 docs** — roughly linear in corpus size.
Extrapolates to ~16 s at 100k (same order as ADR 0011's measured 10.6 s).

Mechanism matches ADR 0011: the whole index is loaded into memory per query;
`postings` is stored at ingest but never read at query time. The curve is a
steady linear ramp, not flat-then-cliff.

Note: the raw 8× jump 1k→5k was mostly the Mac→cloud machine change; normalized
to one machine it is ~2.8× for 5× the corpus.

## New FAILs

None beyond the known one. 5k and 10k each had exactly **1 failure = the
zero-overlap dense rescue**, reproducing at every tier. (The cloud-1k anchor's
"3 failures" were that one FAIL plus two cross-version baseline-drift rows from
comparing 0.23.0 against a 0.24.0 baseline — not new engine issues.)

## Do the three 1k findings reproduce?

1. **Hybrid gap** — reproduces in existence, but changes character: not a stable
   4×, it *closes* with scale as lexical collapses. Report the nuance, not "4×."
2. **Zero-overlap miss** — reproduces and strengthens (0/14).
3. **Fresh-clone parity top-1 only** — reproduces identically at 5k and 10k:
   "top-1 stable, tail re-ranked." README/CHANGELOG "same rankings *and scores*"
   remains inaccurate at all scales.

## Still outstanding

- **acme-payments realistic corpus** (`fux-lab/prompts/build-realistic-repo.md`)
  — the A-vs-B discriminator. Highest-value next run.
- 100k tier — awaits go-ahead.
- Deliberate 0.24.0-vs-0.23.0 comparison at a fixed tier, now that the curve exists.
